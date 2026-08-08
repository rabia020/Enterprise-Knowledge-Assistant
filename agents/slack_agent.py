# agents/slack_agent.py

import json
import re
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from tools.n8n_client import get_calendar_events, get_calendar_events_by_date
from agents.reporter import generate_report
from state import AgentState

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


def _extract_event_details_from_query(query: str) -> dict:
    """
    Extract date and event name from user query.
    """
    prompt = f"""
Extract the event details from this query:
"{query}"

Return ONLY valid JSON:
{{
    "date": "the day/date mentioned (e.g., 'sunday', 'today', '2026-08-09')",
    "event_name": "the event name or purpose mentioned",
    "time": "the time mentioned if any"
}}

If a detail is not mentioned, use an empty string.
"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        print(f"[Slack Agent] Event extraction error: {e}")
        return {"date": "", "event_name": "", "time": ""}


def _parse_events_from_message(message: str) -> list:
    """
    Parse events from the n8n response message.
    """
    events = []
    
    if not message:
        return events
    
    # Pattern: "- **Time:** 9:00 PM – 10:00 PM (PKT)\n- **Event:** Weekly Report Sharing"
    event_patterns = re.findall(
        r'(?:[-*]?\s*\*\*Time:\*\*\s*([^\n]+)\s*[-*]?\s*\*\*Event:\*\*\s*([^\n]+))',
        message,
        re.IGNORECASE
    )
    
    for match in event_patterns:
        events.append({
            "title": match[1].strip(),
            "start_time": match[0].strip(),
            "end_time": "",
            "date": ""
        })
    
    # Pattern 2: "Weekly Report Sharing - Time: 9:00 PM – 10:00 PM (PKT)"
    if not events:
        pattern2 = r'([^\n]+?)\s*[-–]\s*Time:\s*([^\n]+?)(?:\s*[-–]\s*Description:\s*([^\n]+))?'
        matches = re.findall(pattern2, message, re.IGNORECASE)
        
        for match in matches:
            events.append({
                "title": match[0].strip(),
                "start_time": match[1].strip(),
                "end_time": "",
                "description": match[2].strip() if len(match) > 2 and match[2] else "",
                "date": ""
            })
    
    return events


def _format_event_details_for_slack(events: list) -> str:
    """
    Format event details for Slack message.
    """
    if not events:
        return ""
    
    details = "\n\n*📅 EVENT DETAILS:*\n"
    
    for event in events:
        title = event.get('title', 'Untitled Event')
        details += f"• *{title}*\n"
        
        if event.get('date'):
            details += f"  • Date: {event['date']}\n"
        
        if event.get('start_time'):
            details += f"  • Time: {event['start_time']}"
            if event.get('end_time') and event['end_time'] != event['start_time']:
                details += f" - {event['end_time']}"
            details += "\n"
        
        if event.get('description'):
            details += f"  • Description: {event['description']}\n"
    
    return details


def _fetch_calendar_context_for_slack(query: str) -> str:
    """
    Fetch calendar event details for Slack message.
    """
    event_details = _extract_event_details_from_query(query)
    
    date_str = event_details.get("date", "")
    event_name = event_details.get("event_name", "")
    
    if not date_str:
        # Check for day names
        days = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "today", "tomorrow"]
        for day in days:
            if day in query.lower():
                date_str = day
                break
    
    if date_str:
        try:
            print(f"[Slack Agent] Fetching calendar events for: {date_str}")
            result = get_calendar_events_by_date(date_str, event_name if event_name else None)
            
            if result.get("success") and result.get("message"):
                message = result["message"]
                events = _parse_events_from_message(message)
                
                if events:
                    return _format_event_details_for_slack(events)
                
                # If we have a message with event info
                if "No events" not in message and "not found" not in message.lower():
                    return f"\n📅 Event Info:\n{message}\n"
        except Exception as e:
            print(f"[Slack Agent] Calendar fetch error: {e}")
    
    return ""


def slack_agent_node(state: AgentState) -> AgentState:
    """
    Slack Agent Node - Prepares Slack message proposals.
    """
    print("[Slack Agent] Preparing Slack message proposal...")

    query = state.get("query", "")

    # Fetch calendar context
    calendar_context = _fetch_calendar_context_for_slack(query)

    prompt = f"""
You are a Slack message drafting assistant.

The user wants to send a Slack message.

Extract the target channel and the message text.

USER REQUEST:
{query}

CALENDAR CONTEXT (use this for event details):
{calendar_context}

RULES:

1. Extract the channel if mentioned (e.g. "#general"). If no
   channel is mentioned, use "#general" as the default.
2. If CALENDAR CONTEXT is present above and the user refers to
   an event, use those real details (title/date/time) in the
   message.
3. Do not invent details beyond the user request and, if
   present, CALENDAR CONTEXT.
4. Make the message informative with actual event details.
5. Output ONLY valid JSON.

OUTPUT FORMAT:

{{
    "channel": "#channel-name",
    "message": "the message text with event details"
}}
"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        slack_data = json.loads(content)

    except Exception as e:
        print(f"[Slack Agent] Extraction error: {e}")
        slack_data = {
            "channel": "#general",
            "message": query
        }

    proposed_actions = [
        {
            "tool": "Send_Slack",
            "args": {
                "channel": slack_data.get("channel", "#general"),
                "message": slack_data.get("message", query)
            }
        }
    ]

    print(f"[Slack Agent] Proposed message: {proposed_actions[0]['args']}")

    report_text = generate_report(
        query=query,
        query_type="slack",
        proposed_actions=proposed_actions
    )

    return {
        "proposed_actions": proposed_actions,
        "report": report_text
    }