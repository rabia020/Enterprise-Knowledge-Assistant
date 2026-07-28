# agents/reporter.py
#
# ==========================================================
# RESTRUCTURED: this is no longer a separate LangGraph node.
#
# It WAS registered as its own node ("reporter"), receiving
# state (including query_type and proposed_actions) from
# whichever specialist node ran just before it. Debug tracing
# showed those two fields reliably vanished specifically on
# the hop INTO this node, even though every other field (and
# even the same values read by conditional-edge router
# functions immediately after the specialist node) came
# through fine. Rather than fight that further, this is now
# a plain function each specialist node calls DIRECTLY, using
# query_type/proposed_actions/etc. that are already sitting
# in its own local scope — no inter-node hand-off required for
# the fields that were breaking.
# ==========================================================

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


llm = ChatGroq(

    model="openai/gpt-oss-120b",

    api_key=os.getenv(
        "GROQ_API_KEY"
    ),

    temperature=0.2

)


def generate_report(

    query: str,

    query_type: str,

    context: str = "No documents retrieved.",

    emails: list | None = None,

    proposed_actions: list | None = None

) -> str:

    print(f"[Reporter] Generating report for query_type = '{query_type}'")

    emails = emails or []

    proposed_actions = proposed_actions or []


    # ======================================================
    # EMAIL DATA
    # ======================================================

    email_lines = "\n".join(

        [

            (

                f"To: {email.get('to', '')}\n"
                f"Subject: {email.get('subject', '')}\n"
                f"Body: {email.get('body', '')}"

            )

            for email in emails

            if email.get("email_type") == "new_email"

        ]

    )

    if not email_lines:

        email_lines = "No new email draft."


    # ======================================================
    # COMPLAINT DATA
    # ======================================================

    complaint_lines = "\n".join(

        [

            (

                f"- {email.get('sender')}: "
                f"{email.get('summary')} "
                f"[{email.get('category')} | "
                f"{email.get('severity')}]"

            )

            for email in emails

            if email.get("email_type") != "new_email"

        ]

    )

    if not complaint_lines:

        complaint_lines = "No complaint emails."


    # ======================================================
    # EMAIL REQUEST
    # ======================================================

    if query_type == "email":

        prompt = f"""
You are the final review and approval preparation agent.

The user requested an email.

Your job is to display the prepared email clearly for human approval.

USER REQUEST:
{query}

PREPARED EMAIL:
{email_lines}


IMPORTANT RULES:

1. Do not create a research report.

2. Do not invent information.

3. Do not add information that is not present
   in the prepared email.

4. Do not modify the recipient.

5. Do not add fictional links, deadlines,
   contact details, policies, or facts.

6. Clearly state that the email is awaiting
   human approval before sending.


Return ONLY the following format:

# Email Approval Request

## Recipient

[recipient]

## Subject

[subject]

## Message

[email body]

## Approval Required

The email is prepared and is waiting for human approval before it is sent.
"""


    # ======================================================
    # CALENDAR REQUEST
    # ======================================================

    elif query_type == "calendar":

        event_args = (
            proposed_actions[0].get("args", {})
            if proposed_actions
            else {}
        )

        prompt = f"""
You are the final review and approval preparation agent.

The user requested a calendar event to be created.

Your job is to display the prepared event clearly for human approval.

USER REQUEST:
{query}

PROPOSED EVENT:
Title: {event_args.get('title', '')}
Date/Time: {event_args.get('start', '')}
Description: {event_args.get('description', '')}


IMPORTANT RULES:

1. Do not create a research report or an analysis section.

2. Do not invent information not present above.

3. Do not add attendees, locations, reminders, or any detail
   not explicitly provided.

4. Clearly state that the event is awaiting human approval
   before it is created.


Return ONLY the following format:

# Calendar Event Approval Request

## Title

[title]

## Date / Time

[date/time, or "Not specified" if empty]

## Description

[description, or "None" if empty]

## Approval Required

The event is prepared and is waiting for human approval before it is created.
"""


    # ======================================================
    # COMPLAINT REPORT
    # ======================================================

    elif query_type == "complaint":

        prompt = f"""
You are a senior customer-support analyst.

Prepare a professional complaint analysis report.

USER REQUEST:
{query}

COMPLAINT EMAIL DATA:
{complaint_lines}


Use ONLY the information in the complaint data.

Do not invent facts.

Format:

# Customer Complaint Report

## Executive Summary

## Key Issues

## Trends

## Recommendations

## Next Steps

## Approval Required

Clearly state that any customer replies or external actions
require human approval.
"""


    # ======================================================
    # DOCUMENT REPORT
    # ======================================================

    elif query_type == "document":

        prompt = f"""
You are a document analysis assistant.

Prepare a concise report based ONLY on the retrieved document context.

USER REQUEST:
{query}

DOCUMENT CONTEXT:
{context}


Do not invent information.

Format:

# Document Analysis Report

## Summary

## Key Findings

## Relevant Information

## Recommendations

## Conclusion
"""


    # ======================================================
    # RESEARCH REPORT
    # ======================================================

    else:

        prompt = f"""
You are a research assistant.

Prepare a research report based ONLY on the available information.

USER REQUEST:
{query}

AVAILABLE CONTEXT:
{context}


Do not invent unsupported facts.

Format:

# Research Report

## Overview

## Key Facts

## Analysis

## Conclusion
"""


    response = llm.invoke(prompt)

    report = response.content

    print(f"[Reporter] Done — {len(report)} chars")

    return report