import os
import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from state import AgentState


load_dotenv()


# ==========================================================
# LLM
# ==========================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


# ==========================================================
# PLANNER
# ==========================================================

def planner(state: AgentState) -> AgentState:

    print("[Planner] Running...")

    query = state.get("query", "")


    prompt = f"""
You are the planning engine of an internal Enterprise Knowledge Worker AI Assistant.

This assistant is used by employees and managers inside an organization.

The assistant can:

1. Read and analyze emails
2. Search company documents
3. Create Jira tasks
4. Send emails
5. Send Slack messages
6. Create calendar events
7. Generate summaries and reports

IMPORTANT ARCHITECTURE:

The system follows this principle:

READ → ANALYZE → PREPARE ACTIONS → HUMAN APPROVAL → EXECUTE

Never assume that external actions should be executed immediately.

Your task is ONLY to create an execution plan.

Do not execute any tools.

AVAILABLE AGENTS:

- research
- analysis
- report
- email
- slack
- task
- calendar

--------------------------------------------------

PLANNING RULES:

1. Understand the user's intent.

2. Break complex requests into logical steps.

3. Use "research" when the system must retrieve or inspect information.

4. Use "analysis" when retrieved information must be analyzed.

5. Use "report" when a summary or report is requested.

6. Use "email" when an email must be prepared or sent.

7. Use "slack" when a Slack message must be prepared or sent.

8. Use "task" when a Jira task must be created.

9. Use "calendar" when a calendar event must be created.

10. External actions such as sending emails, creating Jira tasks,
    sending Slack messages, or creating calendar events must eventually
    require human approval.

11. Do not invent information that is not present in the request
    or retrieved data.

12. Output ONLY valid JSON.

--------------------------------------------------

OUTPUT FORMAT:

{{
    "intent": "short description",
    "entities": {{
        "people": [],
        "dates": [],
        "emails": [],
        "tasks": []
    }},
    "requires_tools": true,
    "confidence": 0.0,
    "plan": [
        {{
            "agent": "research",
            "task": "clear task instruction"
        }}
    ]
}}

--------------------------------------------------

EXAMPLE:

User:

"Review my recent work emails, identify action items,
create Jira tasks for important items, and send me a summary email."

Output:

{{
    "intent": "analyze recent emails and prepare Jira tasks and summary email",
    "entities": {{
        "people": [],
        "dates": [],
        "emails": [],
        "tasks": []
    }},
    "requires_tools": true,
    "confidence": 0.95,
    "plan": [
        {{
            "agent": "research",
            "task": "Retrieve and review recent work-related emails."
        }},
        {{
            "agent": "analysis",
            "task": "Identify important action items, deadlines, and follow-up requirements."
        }},
        {{
            "agent": "task",
            "task": "Prepare Jira tasks for important action items."
        }},
        {{
            "agent": "email",
            "task": "Prepare a summary email containing the identified action items."
        }}
    ]
}}

--------------------------------------------------

USER QUERY:

{query}
"""


    response = llm.invoke(prompt)


    print("[Planner] Raw response:")

    print(response.content)


    try:

        content = response.content.strip()

        if content.startswith("```"):

            content = (
                content
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        plan_data = json.loads(content)


    except Exception as e:

        print("[Planner] JSON Error:", e)

        plan_data = {

            "intent": "fallback execution",

            "entities": {},

            "requires_tools": True,

            "confidence": 0.3,

            "plan": [

                {

                    "agent": "research",

                    "task": query

                }

            ]

        }


    return {

        "plan": plan_data.get("plan", []),

        "messages": [

            f"[Planner] Intent: "
            f"{plan_data.get('intent', 'unknown')}"

        ],

        "status": "planned"

    }