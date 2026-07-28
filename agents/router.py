import os
import json

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from state import AgentState


# ==========================================================
# LLM
# ==========================================================

load_dotenv()


llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)


# ==========================================================
# TOOL MAP
# ==========================================================

TOOL_MAP = {

    "email": "SendEmail_Tool",

    "slack": "Send_Slack",

    "task": "Jira_Tool",

    "calendar": "CreateCalendarEn",

    "research": "RAG_Tool"

}


# ==========================================================
# ROUTER
# ==========================================================

def router(state: AgentState) -> AgentState:

    print("[Router] Running...")


    plan = state.get("plan", [])

    tool_calls = []


    for step in plan:

        agent = step.get("agent")

        task = step.get("task", "")


        tool_name = TOOL_MAP.get(agent)


        # ----------------------------------------------
        # AGENTS WITHOUT DIRECT TOOL SUPPORT
        # ----------------------------------------------

        if agent in ("analysis", "report"):

            print(
                f"[Router] {agent} is a reasoning step "
                "and does not create a tool call."
            )

            continue


        if not tool_name:

            print(
                f"[Router] Unknown agent: {agent}"
            )

            continue


        # ----------------------------------------------
        # EXTRACT TOOL ARGUMENTS
        # ----------------------------------------------

        prompt = f"""
You are a strict tool argument extractor.

Convert the task below into valid JSON arguments.

TASK:
{task}

TOOL:
{tool_name}

RULES:

- Output ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.
- Do not invent missing information.
- Use the exact tool name.
- Extract all relevant arguments.

TOOL SCHEMAS:

SendEmail_Tool:
{{
    "to": "recipient email",
    "subject": "email subject",
    "message": "email body"
}}

Send_Slack:
{{
    "channel": "#channel",
    "message": "Slack message"
}}

CreateCalendarEn:
{{
    "title": "event title",
    "start": "date or datetime"
}}

Jira_Tool:
{{
    "title": "task title",
    "description": "task description"
}}

RAG_Tool:
{{
    "query": "research query"
}}

Return:

{{
    "tool": "{tool_name}",
    "args": {{}}
}}
"""


        try:

            response = llm.invoke(prompt)


            content = response.content.strip()


            if content.startswith("```"):

                content = (
                    content
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )


            tool_call = json.loads(content)


            if "tool" not in tool_call:

                tool_call["tool"] = tool_name


            if "args" not in tool_call:

                tool_call["args"] = {}


        except Exception as e:

            print(
                "[Router] JSON error:",
                e
            )


            tool_call = {

                "tool": tool_name,

                "args": {

                    "task": task

                }

            }


        tool_calls.append(tool_call)


    print(
        f"[Router] Created {len(tool_calls)} tool calls"
    )


    return {

        "tool_calls": tool_calls,

        "messages": [

            "[Router] Proposed actions created"

        ],

        "status": "routed"

    }