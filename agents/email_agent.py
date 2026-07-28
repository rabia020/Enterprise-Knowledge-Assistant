# agents/email_agent.py

import json
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from tools.n8n_client import get_emails, send_email
from state import AgentState
from agents.reporter import generate_report


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
    temperature=0
)


# ==========================================================
# EMAIL AGENT
# ==========================================================

def email_agent(state: AgentState) -> AgentState:

    query_type = state.get(
        "query_type",
        "email"
    )

    print(
        f"[Email Agent] Processing query type: {query_type}"
    )


    # ======================================================
    # WORKFLOW 1 — NORMAL EMAIL REQUEST
    # ======================================================

    if query_type == "email":

        return prepare_new_email(
            state
        )


    # ======================================================
    # WORKFLOW 2 — COMPLAINT EMAIL ANALYSIS
    # ======================================================

    if query_type == "complaint":

        return analyze_complaint_emails(
            state
        )


    # ======================================================
    # FALLBACK
    # ======================================================

    print(
        "[Email Agent] Unknown email workflow."
    )


    return {

        "emails": [],

        "messages": [

            "[Email Agent] No supported email workflow."

        ]

    }


# ==========================================================
# WORKFLOW 1
# PREPARE NEW EMAIL
# ==========================================================

def prepare_new_email(
    state: AgentState
) -> AgentState:

    query = state.get(
        "query",
        ""
    )


    print(
        "[Email Agent] Preparing new email draft..."
    )


    prompt = f"""
You are an email drafting assistant.

The user wants to send an email.

Extract the recipient and create a professional email draft.

USER REQUEST:
{query}


IMPORTANT RULES:

1. Extract the recipient email address from the request.

2. Create an appropriate subject.

3. Write a professional email body.

4. Use ONLY information provided in the user request.

5. Do NOT invent:
   - deadlines
   - links
   - exam portals
   - contact email addresses
   - phone numbers
   - policies
   - fees
   - passing scores
   - organization details

6. If a detail is not provided, do not add it.

7. Output ONLY valid JSON.

OUTPUT FORMAT:

{{
    "to": "recipient email",
    "subject": "email subject",
    "body": "complete email body"
}}
"""


    try:

        response = llm.invoke(
            prompt
        )


        content = response.content.strip()


        if content.startswith(
            "```"
        ):

            content = (

                content
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```",
                    ""
                )
                .strip()

            )


        email_data = json.loads(
            content
        )


        recipient = email_data.get(
            "to",
            ""
        )

        subject = email_data.get(
            "subject",
            ""
        )

        body = email_data.get(
            "body",
            ""
        )


        if not recipient:

            raise ValueError(
                "No recipient email found."
            )


        print(
            f"[Email Agent] Draft prepared for {recipient}"
        )

        proposed_actions = [

            {

                "tool": "SendEmail_Tool",

                "args": {

                    "to": recipient,

                    "subject": subject,

                    "message": body

                }

            }

        ]

        emails = [

            {

                "to": recipient,

                "subject": subject,

                "body": body,

                "email_type": "new_email"

            }

        ]

        # ------------------------------------------------------
        # Generate the report HERE, using local variables from
        # this same function call — not a value read back from
        # state in a separate node later.
        # ------------------------------------------------------

        report_text = generate_report(

            query=query,

            query_type="email",

            emails=emails

        )

        return {

            "emails": emails,

            "proposed_actions": proposed_actions,

            "report": report_text,

            "messages": [

                (

                    "[Email Agent] "
                    f"Email draft prepared for {recipient}"

                )

            ]

        }


    except Exception as e:

        print(
            f"[Email Agent] Draft generation error: {e}"
        )


        return {

            "emails": [],

            "proposed_actions": [],

            "error": str(e),

            "messages": [

                (

                    "[Email Agent] "
                    "Failed to prepare email draft."

                )

            ]

        }


# ==========================================================
# WORKFLOW 2
# FETCH AND ANALYZE COMPLAINT EMAILS
# ==========================================================

def analyze_complaint_emails(
    state: AgentState
) -> AgentState:

    print(
        "[Email Agent] Fetching complaint emails from n8n..."
    )


    raw_emails = get_emails(

        label="complaints",

        days=30

    )


    if not raw_emails:

        print(
            "[Email Agent] No complaint emails returned."
        )


        return {

            "emails": [],

            "proposed_actions": [],

            "messages": [

                "[Email Agent] No complaint emails found."

            ]

        }


    print(
        f"[Email Agent] Got "
        f"{len(raw_emails)} complaint emails"
    )


    structured = []


    for email in raw_emails[:10]:

        try:

            response = llm.invoke(

                f"""
Analyze this customer complaint email.

Return ONLY valid JSON:

{{
    "sender": "email address",
    "subject": "original subject line",
    "summary": "one sentence summary",
    "category": "billing|shipping|product|support|other",
    "sentiment": "negative|neutral|positive",
    "severity": "low|medium|high"
}}

Subject:
{email.get('subject', '')}

Body:
{email.get('body', '')[:600]}

JSON only.
"""

            )


            content = (

                response.content
                .strip()
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```",
                    ""
                )

            )


            parsed = json.loads(
                content
            )


            parsed["original_body"] = (

                email.get(
                    "body",
                    ""
                )[:600]

            )


            structured.append(
                parsed
            )


        except Exception as e:

            print(
                f"[Email Agent] "
                f"Parse error: {e}"
            )


            structured.append(

                {

                    "sender": email.get(
                        "sender",
                        "unknown"
                    ),

                    "subject": email.get(
                        "subject",
                        "Complaint"
                    ),

                    "summary": email.get(
                        "subject",
                        "Complaint"
                    ),

                    "category": "other",

                    "sentiment": "negative",

                    "severity": "medium",

                    "original_body": email.get(
                        "body",
                        ""
                    )[:600]

                }

            )


    log = "\n".join(

        [

            (

                f"- {e.get('sender')}: "
                f"{e.get('summary')} "
                f"[{e.get('severity', '').upper()}]"

            )

            for e in structured

        ]

    )

    query = state.get("query", "")

    # ------------------------------------------------------
    # Generate the report HERE, using the just-computed
    # `structured` list directly — not a value read back
    # from state in a separate node.
    # ------------------------------------------------------

    report_text = generate_report(

        query=query,

        query_type="complaint",

        emails=structured

    )

    return {

        "emails": structured,

        "proposed_actions": [

            {

                "tool": "SendComplaintReplies",

                "args": {

                    "count": len(structured)

                }

            }

        ],

        "report": report_text,

        "messages": [

            (

                f"[Email Agent] "
                f"{len(structured)} complaint emails analyzed:\n"
                f"{log}"

            )

        ]

    }


# ==========================================================
# SEND NEW EMAIL AFTER APPROVAL
# ==========================================================

def send_new_email(
    state: AgentState
) -> AgentState:

    emails = state.get(
        "emails",
        []
    )


    if not emails:

        print(
            "[Email Agent] No email draft found."
        )


        return state


    if state.get(
        "approved"
    ) is not True:

        print(
            "[Email Agent] "
            "Email not approved. Skipping send."
        )


        return state


    sent = 0

    failed = 0


    for email in emails:

        if email.get(
            "email_type"
        ) != "new_email":

            continue


        recipient = email.get(
            "to",
            ""
        )

        subject = email.get(
            "subject",
            ""
        )

        body = email.get(
            "body",
            ""
        )


        if not recipient:

            print(
                "[Email Agent] "
                "Missing recipient."
            )


            failed += 1

            continue


        success = send_email(

            to=recipient,

            subject=subject,

            body=body

        )


        if success:

            print(
                f"[Email Agent] "
                f"Email sent to {recipient}"
            )

            sent += 1


        else:

            print(
                f"[Email Agent] "
                f"Failed to send email to {recipient}"
            )

            failed += 1


    return {

        **state,

        "messages": (

            state.get(
                "messages",
                []
            )

            + [

                (

                    "[Email Agent] "
                    f"New emails: {sent} sent, "
                    f"{failed} failed"

                )

            ]

        )

    }


# ==========================================================
# SEND COMPLAINT REPLIES AFTER APPROVAL
# ==========================================================

def send_email_replies(
    state: AgentState
) -> AgentState:

    emails = state.get(
        "emails",
        []
    )


    if not emails:

        print(
            "[Email Agent] "
            "No complaint emails to reply to."
        )


        return state


    if state.get(
        "approved"
    ) is not True:

        print(
            "[Email Agent] "
            "Not approved — skipping replies."
        )


        return state


    print(
        f"[Email Agent] "
        f"Sending replies to {len(emails)} emails..."
    )


    sent = 0

    failed = 0


    for email in emails:

        if email.get(
            "email_type"
        ) == "new_email":

            continue


        sender = email.get(
            "sender",
            ""
        )


        subject = email.get(
            "subject",
            "Your complaint"
        )


        if not sender:

            continue


        try:

            response = llm.invoke(

                f"""
You are a professional customer support agent.

Write a polite and helpful reply to this customer complaint.

Be empathetic, acknowledge the issue,
and provide next steps.

Keep the reply under 150 words.

Customer email:

Subject:
{subject}

Body:
{email.get(
    'original_body',
    email.get(
        'summary',
        ''
    )
)}

Write ONLY the email body.
"""

            )


            reply_body = response.content.strip()


        except Exception as e:

            print(
                f"[Email Agent] "
                f"Reply generation error: {e}"
            )


            reply_body = (

                "Thank you for contacting us. "
                "We have received your complaint "
                "and our team will review it."

            )


        success = send_email(

            to=sender,

            subject=f"Re: {subject}",

            body=reply_body

        )


        if success:

            sent += 1

            print(
                f"[Email Agent] "
                f"Reply sent to {sender}"
            )


        else:

            failed += 1

            print(
                f"[Email Agent] "
                f"Reply failed for {sender}"
            )


    return {

        **state,

        "messages": (

            state.get(
                "messages",
                []
            )

            + [

                (

                    "[Email Agent] "
                    f"Replies: {sent} sent, "
                    f"{failed} failed"

                )

            ]

        )

    }