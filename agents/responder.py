from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()


# ==========================================================
# LLM
# ==========================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2
)


# ==========================================================
# RESPONDER
# ==========================================================

def responder(state):

    print("[Responder] Running...")

    query = state.get("query", "")

    tool_results = state.get(
        "tool_results",
        []
    )


    # ======================================================
    # PREPARE TOOL RESULTS
    # ======================================================

    formatted_results = []

    for item in tool_results:

        tool = item.get(
            "tool",
            "Unknown Tool"
        )

        result = item.get(
            "result",
            {}
        )

        formatted_results.append(

            f"""
TOOL: {tool}

RESULT:
{result}
"""

        )


    tool_context = "\n".join(
        formatted_results
    )


    # ======================================================
    # RESPONSE PROMPT
    # ======================================================

    prompt = f"""
You are the final response and reporting agent
for an internal Enterprise AI Assistant.

This system is used by company employees and managers
to analyze internal information and prepare business actions.

You must produce a professional internal report.

USER REQUEST:
{query}

DATA AND TOOL RESULTS:
{tool_context}


IMPORTANT RULES:

1. Use ONLY information present in the tool results.
2. Do NOT invent emails, numbers, dates, names, policies, or facts.
3. If information is missing, clearly say:
   "No information was found."
4. Do NOT create fictional data.
5. Do NOT claim an action was completed unless the tool result confirms it.
6. If the user requested proposed actions, clearly label them as:
   "PROPOSED ACTIONS".
7. If an action requires human approval, clearly state:
   "WAITING FOR HUMAN APPROVAL".
8. If the user requested email or Jira tasks, show the proposed content clearly.
9. Keep the report professional and useful for an internal manager.


RESPONSE STRUCTURE:

# Internal Work Report

## Executive Summary

Briefly summarize what was found.

## Findings

List important information discovered from the available data.

## Action Items

List action items identified from the data.

For each action item include:

- Action
- Owner, if known
- Deadline, if known
- Priority
- Source

## Proposed Actions

List any proposed actions that require approval.

Examples:

- Create Jira task
- Send email
- Send Slack notification
- Schedule meeting

## Approval Required

Clearly state whether approval is required.

## Recommended Next Steps

Provide concise next steps.

Return ONLY the final report.
"""


    # ======================================================
    # CALL LLM
    # ======================================================

    response = llm.invoke(
        prompt
    )


    final_response = response.content


    print(
        "[Responder] Report generated successfully"
    )


    # ======================================================
    # RETURN BOTH FIELDS
    # ======================================================

    return {

        **state,

        "report": final_response,

        "final_response": final_response,

        "messages": (

            state.get(
                "messages",
                []
            )

            + [

                "[Responder] Generated internal report"

            ]

        ),

        "status": "report_generated"

    }