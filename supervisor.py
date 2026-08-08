# supervisor.py

import os
import json
import operator

from typing import (
    Annotated,
    TypedDict,
    List,
    Dict,
    Any,
    Optional
)

from dotenv import load_dotenv

from langchain_core.messages import (
    HumanMessage,
    SystemMessage
)

from langchain_groq import ChatGroq

from langgraph.graph import (
    StateGraph,
    END
)

from langgraph.checkpoint.memory import MemorySaver

from langgraph.types import (
    interrupt,
    Command
)


from agents.email_agent import (
    email_agent,
    prepare_new_email,
    list_recent_emails,
    prepare_broadcast_email,
    analyze_complaint_emails,
    send_email_replies,
    send_new_email,
    send_broadcast_emails
)

from agents.rag_agent import (
    rag_agent
)

from agents.reporter import (
    generate_report
)

from memory.memory_store import (
    get_memory_store
)

from tools.n8n_client import (
    send_slack_message,
    create_calendar_event,
    get_calendar_events
)


# ==========================================================
# ENVIRONMENT
# ==========================================================

load_dotenv()


# ==========================================================
# MEMORY
# ==========================================================

memory_store = get_memory_store()


# ==========================================================
# STATE
# ==========================================================

class AgentState(TypedDict):

    query: str

    emails: List[
        Dict[str, Any]
    ]

    context: str

    report: str

    messages: Annotated[
        list,
        operator.add
    ]

    query_type: str

    plan: list

    user: str

    session_id: str

    memory_context: Optional[
        Dict
    ]

    approved: Optional[
        bool
    ]

    approval_comment: Optional[
        str
    ]

    # --------------------------------------------------
    # NEW: what the human is actually being asked to
    # approve, as structured tool calls. This is what
    # was missing before — the review UI had nothing to
    # show for calendar (or anything except email) and
    # memory_save_node had nowhere to read the details
    # back from after approval.
    # --------------------------------------------------

    proposed_actions: List[
        Dict[str, Any]
    ]


# ==========================================================
# LLM
# ==========================================================

llm = ChatGroq(

    model="openai/gpt-oss-120b",

    api_key=os.getenv(
        "GROQ_API_KEY"
    ),

    temperature=0.2

)


# ==========================================================
# MEMORY LOAD
# ==========================================================

def memory_load_node(
    state: AgentState
) -> AgentState:

    return memory_store.memory_load_node(
        state
    )


# ==========================================================
# MEMORY SAVE + APPROVED EXECUTION
# ==========================================================

def memory_save_node(
    state: AgentState
) -> AgentState:

    """
    Executes approved actions.

    Normal email:
        prepare email
        HITL approval
        send new email

    Calendar:
        prepare event
        HITL approval
        create calendar event

    Complaint:
        analyze complaints
        HITL approval
        send complaint replies
        notify Slack
        create follow-up calendar event

    Finally:
        save memory
    """


    query_type = state.get(
        "query_type"
    )


    approved = state.get(
        "approved"
    )


    # ======================================================
    # APPROVED NORMAL EMAIL
    # ======================================================

    if (

        approved is True

        and query_type == "email"

    ):

        state = send_new_email(
            state
        )


    # ======================================================
    # APPROVED BROADCAST EMAIL
    # ======================================================

    if (

        approved is True

        and query_type == "email_broadcast"

    ):

        state = send_broadcast_emails(
            state
        )


    # ======================================================
    # APPROVED CALENDAR EVENT
    # (this branch did not exist before — calendar requests
    # were routed to research_agent and never actually
    # created an event, approved or not)
    # ======================================================

    if (

        approved is True

        and query_type == "calendar"

    ):

        proposed = state.get(
            "proposed_actions",
            []
        )

        if proposed:

            args = proposed[0].get(
                "args",
                {}
            )

            try:

                result = create_calendar_event(

                    title=args.get(
                        "title",
                        "Event"
                    ),

                    date=args.get(
                        "start",
                        ""
                    ),

                    duration=args.get(
                        "duration",
                        ""
                    ),

                    description=args.get(
                        "description",
                        ""
                    )

                )

                print(
                    f"[memory_save] Calendar event created: {result}"
                )

                state = {

                    **state,

                    "messages": (

                        state.get("messages", [])

                        + [f"[Calendar] Event created: {result}"]

                    )

                }

            except Exception as e:

                print(
                    f"[memory_save] Calendar creation error: {e}"
                )

        else:

            print(
                "[memory_save] Calendar approved but no "
                "proposed_actions found — nothing to create."
            )


    # ======================================================
    # APPROVED SLACK MESSAGE
    # (new — Slack requests previously had no execution path
    # at all since they never had a dedicated query_type)
    # ======================================================

    if (

        approved is True

        and query_type == "slack"

    ):

        proposed = state.get(
            "proposed_actions",
            []
        )

        if proposed:

            args = proposed[0].get(
                "args",
                {}
            )

            try:

                success = send_slack_message(

                    channel=args.get(
                        "channel",
                        "#general"
                    ),

                    message=args.get(
                        "message",
                        ""
                    )

                )

                print(
                    f"[memory_save] Slack message sent: {success}"
                )

                state = {

                    **state,

                    "messages": (

                        state.get("messages", [])

                        + [f"[Slack] Message sent: {success}"]

                    )

                }

            except Exception as e:

                print(
                    f"[memory_save] Slack send error: {e}"
                )

        else:

            print(
                "[memory_save] Slack approved but no "
                "proposed_actions found — nothing to send."
            )


    # ======================================================
    # APPROVED COMPLAINT
    # ======================================================

    if (

        approved is True

        and query_type == "complaint"

    ):

        state = send_email_replies(
            state
        )


        # --------------------------------------------------
        # SLACK NOTIFICATION
        # --------------------------------------------------

        try:

            send_slack_message(

                channel="#complaints",

                message=(

                    "Report approved:\n"

                    f"{state.get('report', '')[:200]}"

                )

            )


            print(
                "[memory_save] "
                "Slack notified"
            )


        except Exception as e:

            print(
                f"[memory_save] "
                f"Slack error: {e}"
            )


        # --------------------------------------------------
        # CALENDAR FOLLOW-UP
        # --------------------------------------------------

        try:

            create_calendar_event(

                title=(
                    "Follow-up: complaint review"
                ),

                date="",

                description=(
                    state.get(
                        "query",
                        ""
                    )
                )

            )


            print(
                "[memory_save] "
                "Calendar event created"
            )


        except Exception as e:

            print(
                f"[memory_save] "
                f"Calendar error: {e}"
            )


    # ======================================================
    # SAVE MEMORY
    # ======================================================

    return memory_store.memory_save_node(state)


# ==========================================================
# AUTO-COMPLETE (no approval needed — pure info requests)
# ==========================================================
#
# Document/research queries have nothing to approve — there's
# no side effect to gate. Previously EVERY query type paused
# for human_review, so a plain question would sit waiting for
# an approval that had nothing behind it. This still saves
# memory (so conversation history keeps working) but skips
# the approval pause entirely.
# ==========================================================

def auto_complete_node(
    state: AgentState
) -> AgentState:

    return memory_store.memory_save_node(state)


# ==========================================================
# HUMAN REVIEW
# ==========================================================

def human_review(
    state: AgentState
) -> AgentState:

    decision = interrupt(

        {

            "message": (

                "Please review the prepared report "
                "and approve or reject the proposed action."

            ),

            "report": state.get(
                "report",
                ""
            ),

            "proposed_actions": state.get(
                "proposed_actions",
                []
            )

        }

    )


    # ------------------------------------------------------
    # SUPPORT BOTH STRING AND DICTIONARY RESUME
    # ------------------------------------------------------

    if isinstance(
        decision,
        dict
    ):

        decision_value = (

            decision.get(
                "decision",
                ""
            )

        )

        comment = (

            decision.get(
                "comment",
                ""
            )

        )

    else:

        decision_value = decision

        comment = ""

    decision_value = str(
        decision_value
    ).lower().strip()


    approved = (

        decision_value
        == "approve"

    )


    print(

        "[HumanReview] "
        f"Decision received: "
        f"{decision_value}"

    )


    return {

        "approved": approved,

        "approval_comment": (

            ""

            if approved

            else comment

        )

    }


# ==========================================================
# REVIEW ROUTER
# ==========================================================

def route_after_review(
    state: AgentState
):

    if state.get(
        "approved"
    ) is True:

        return "memory_save"


    return END


# ==========================================================
# ROUTE AFTER SPECIALIST (only pause for approval when
# there's an actual action to approve)
# ==========================================================

def route_after_specialist(
    state: AgentState
):

    query_type = state.get(
        "query_type",
        "research"
    )

    if query_type in ("document", "research", "calendar_read", "email_read"):

        return "auto_complete"

    return "human_review"


# ==========================================================
# SUPERVISOR CLASSIFICATION
# ==========================================================

def supervisor_node(
    state: AgentState
) -> AgentState:

    print(
        "[Supervisor] Classifying request..."
    )


    query = state.get(
        "query",
        ""
    )


    query_lower = query.lower()


    # ======================================================
    # EXPLICIT EMAIL READ PRIORITY
    # (checked BEFORE compose-email keywords — "enlist recent
    # emails", "list emails", "show my inbox" etc. are reads,
    # not requests to draft a new email. Previously these fell
    # through to query_type="email", which only knows how to
    # draft a NEW email — it would fail with "No recipient
    # email found" since there's nothing to draft.)
    # ======================================================

    email_read_verbs = [

        "list",

        "enlist",

        "show",

        "view",

        "check",

        "read",

        "what's in",

        "whats in"

    ]

    email_read_nouns = [

        "email",

        "emails",

        "inbox",

        "mail"

    ]

    has_email_read_verb = any(

        verb in query_lower

        for verb in email_read_verbs

    )

    has_email_read_noun = any(

        noun in query_lower

        for noun in email_read_nouns

    )

    if has_email_read_verb and has_email_read_noun:

        print(

            "[Supervisor] "
            "Explicit email READ (list/view inbox) detected"

        )


        return {

            "query_type": "email_read"

        }


    # ======================================================
    # EXPLICIT SLACK PRIORITY
    # (new — this category never existed before. Slack requests
    # had nowhere correct to go in classification, so they fell
    # through to the LLM classifier, which only ever knew about
    # email/calendar/document/research/complaint and forced
    # Slack messages into "email" — hence "send message to
    # slack hello everyone!" showing an Email Approval Request.
    # Checked BEFORE the broadcast-email check since "send" +
    # "message" alone would otherwise look like a broadcast.)
    # ======================================================

    if "slack" in query_lower:

        print(

            "[Supervisor] "
            "Explicit Slack message detected"

        )


        return {

            "query_type": "slack"

        }


    # ======================================================
    # EXPLICIT BROADCAST EMAIL PRIORITY
    # (checked BEFORE compose-email keywords — "email to all
    # employees" contains "email to", which would otherwise
    # match the compose flow below and try to extract ONE
    # literal recipient address, always failing since "all
    # employees" isn't an address.)
    # ======================================================

    broadcast_send_verbs = [

        "email",

        "notify",

        "send",

        "mail",

        "message"

    ]

    broadcast_target_phrases = [

        "all employees",

        "all staff",

        "everyone in the company",

        "entire company",

        "whole company",

        "the whole company",

        "whole team",

        "entire team",

        "all users",

        "everybody",

        "all members",

        "all my employees"

    ]

    has_broadcast_verb = any(

        verb in query_lower

        for verb in broadcast_send_verbs

    )

    has_broadcast_target = any(

        phrase in query_lower

        for phrase in broadcast_target_phrases

    )

    if has_broadcast_verb and has_broadcast_target:

        print(

            "[Supervisor] "
            "Broadcast email to all employees detected"

        )


        return {

            "query_type": "email_broadcast"

        }


    # ======================================================
    # EXPLICIT EMAIL PRIORITY
    # ======================================================

    email_keywords = [

        "send email",

        "send an email",

        "send mail",

        "send a mail",

        "write an email",

        "write to",

        "compose an email",

        "draft an email",

        "email to",

        "mail to",

        "reply to",

        "forward this email"

    ]


    if any(

        keyword in query_lower

        for keyword in email_keywords

    ):

        query_type = "email"


        print(

            "[Supervisor] "
            "Explicit email action detected"

        )


        return {

            "query_type": query_type

        }


    # ======================================================
    # EXPLICIT CALENDAR READ PRIORITY
    # (checked BEFORE create-keywords — a request to list/view
    # events is a read, needs no approval, and must never be
    # classified as "calendar" (create).
    #
    # FIX: this used to match on a standalone "enlist" keyword,
    # which incorrectly hijacked unrelated requests like
    # "enlist most recent emails in the inbox" into the
    # calendar path. Now requires BOTH a listing verb AND a
    # calendar-specific noun to be present, so a listing verb
    # alone is never enough.
    # ======================================================

    calendar_read_verbs = [

        "list",

        "enlist",

        "show",

        "view",

        "check",

        "what's on",

        "whats on",

        "upcoming"

    ]

    calendar_read_nouns = [

        "event",

        "events",

        "calendar",

        "schedule",

        "scheduled",

        "meeting",

        "meetings"

    ]

    has_read_verb = any(

        verb in query_lower

        for verb in calendar_read_verbs

    )

    has_calendar_noun = any(

        noun in query_lower

        for noun in calendar_read_nouns

    )

    if has_read_verb and has_calendar_noun:

        print(

            "[Supervisor] "
            "Explicit calendar READ (list/view) detected"

        )


        return {

            "query_type": "calendar_read"

        }


    # ======================================================
    # EXPLICIT CALENDAR PRIORITY
    # ======================================================

    calendar_keywords = [

        "create calendar",

        "create an event",

        "schedule a meeting",

        "schedule meeting",

        "add to calendar",

        "book a meeting",

        "set up a meeting",

        "create event"

    ]


    if any(

        keyword in query_lower

        for keyword in calendar_keywords

    ):

        print(

            "[Supervisor] "
            "Explicit calendar action detected"

        )


        return {

            "query_type": "calendar"

        }


    # ======================================================
    # LLM CLASSIFICATION
    # ======================================================

    classify_prompt = SystemMessage(

        content="""

You are the Supervisor Agent.

Classify the user's PRIMARY INTENT.

Always prioritize the action
the user wants to perform.

Return exactly ONE word.

Allowed categories:

email
document
research
complaint
calendar
calendar_read
slack


SLACK:

Use slack when the user wants to post/send a message to
Slack or a team channel.


EMAIL:

Use email when the user wants to:

- send an email
- write an email
- draft an email
- compose an email
- reply to an email
- forward an email
- read emails
- search emails
- summarize emails
- analyze emails


DOCUMENT:

Use document when the user wants
to search company documents
or uploaded knowledge.


RESEARCH:

Use research when the user explicitly
wants research, investigation,
comparison, or analysis of a topic.


COMPLAINT:

Use complaint when the user wants
to analyze customer complaints
or process complaint emails.


CALENDAR:

Use calendar ONLY when the user wants to
CREATE, schedule, or book a new meeting
or event.


CALENDAR_READ:

Use calendar_read when the user wants to
VIEW, list, show, or check existing
calendar events or their schedule —
no new event is being created.

Return ONLY ONE WORD.
"""

    )


    response = llm.invoke(

        [

            classify_prompt,

            HumanMessage(
                content=query
            )

        ]

    )


    raw = (

        response.content
        .strip()
        .lower()

    )


    print(

        f"[Supervisor] "
        f"Classifier response: {raw}"

    )


    if "calendar_read" in raw:

        query_type = "calendar_read"


    elif "calendar" in raw:

        query_type = "calendar"


    elif "slack" in raw:

        query_type = "slack"


    elif "complaint" in raw:

        query_type = "complaint"


    elif "document" in raw:

        query_type = "document"


    elif "email" in raw:

        query_type = "email"


    else:

        query_type = "research"


    print(

        f"[Supervisor] "
        f"Query type: {query_type}"

    )


    return {

        "query_type": query_type

    }


# ==========================================================
# ROUTER
# ==========================================================

def supervisor_router(
    state: AgentState
):

    query_type = state.get(
        "query_type",
        "research"
    )


    return {

        "email": "email_agent",

        "email_read": "email_read_agent",

        "email_broadcast": "email_broadcast_agent",

        "complaint": "complaint_agent",

        "document": "rag_agent",

        "research": "research_agent",

        "calendar": "calendar_agent",

        "calendar_read": "calendar_read_agent",

        "slack": "slack_agent"

    }.get(

        query_type,

        "research_agent"

    )


# ==========================================================
# PLANNER
# ==========================================================

def planner_node(
    state: AgentState
) -> AgentState:

    print(
        f"[TRACE] planner_node received query_type = "
        f"{state.get('query_type', '<<MISSING>>')!r}"
    )

    plan_prompt = SystemMessage(

        content="""

You are a planning agent.

Create a concise plan for the specialist agent.

Do not execute actions.

Return 3-5 concise numbered steps.
"""

    )


    response = llm.invoke(

        [

            plan_prompt,

            HumanMessage(

                content=(

                    f"Query: "
                    f"{state['query']}\n"

                    f"Type: "
                    f"{state.get('query_type', '')}"

                )

            )

        ]

    )


    plan_steps = [

        line.strip()

        for line in response.content.strip().split(
            "\n"
        )

        if line.strip()

    ]


    print(

        f"[Planner] "
        f"{len(plan_steps)}-step plan created"

    )


    return {

        "plan": plan_steps

    }


# ==========================================================
# RESEARCH AGENT
# ==========================================================

def research_agent_node(
    state: AgentState
) -> AgentState:

    research_prompt = SystemMessage(

        content="""

You are a research assistant.

Provide a thorough answer
based only on the user's request.

Do not invent unsupported details.
"""

    )


    response = llm.invoke(

        [

            research_prompt,

            HumanMessage(

                content=state["query"]

            )

        ]

    )

    return {

        "report": response.content

    }


# ==========================================================
# CALENDAR AGENT
# (new — turns the request into a proposed calendar action
# that human_review can show and memory_save_node can execute
# after approval)
# ==========================================================

def calendar_agent_node(
    state: AgentState
) -> AgentState:

    print(
        "[Calendar Agent] Preparing calendar event proposal..."
    )

    print(
        f"[TRACE] calendar_agent_node received query_type = "
        f"{state.get('query_type', '<<MISSING>>')!r}"
    )

    query = state.get(
        "query",
        ""
    )

    prompt = f"""
You are a calendar-event drafting assistant.

The user wants to create a calendar event.

Extract the event details from the request.

USER REQUEST:
{query}

RULES:

1. Extract a concise event title.
2. Extract the date/time exactly as given. If no date/time is
   mentioned, leave it as an empty string — do not invent one.
3. Extract the duration/end time if mentioned (e.g. "for 1
   hour", "until 6pm", "for 30 minutes"). If not mentioned,
   leave it as an empty string — do not invent one.
4. Extract a description only if explicitly present. Do not
   invent details, locations, attendees, or times.
5. Output ONLY valid JSON.

OUTPUT FORMAT:

{{
    "title": "event title",
    "date": "date or datetime as given, or empty string",
    "duration": "duration/end time as given, or empty string",
    "description": "event description or empty string"
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

        event_data = json.loads(content)

    except Exception as e:

        print(
            f"[Calendar Agent] Extraction error: {e}"
        )

        event_data = {

            "title": query[:60] if query else "Event",

            "date": "",

            "duration": "",

            "description": query

        }

    proposed_actions = [

        {

            "tool": "CreateCalendarEvent_Tool",

            "args": {

                "title": event_data.get(
                    "title",
                    "Event"
                ),

                "start": event_data.get(
                    "date",
                    ""
                ),

                "duration": event_data.get(
                    "duration",
                    ""
                ),

                "description": event_data.get(
                    "description",
                    ""
                )

            }

        }

    ]

    print(
        f"[Calendar Agent] Proposed event: "
        f"{proposed_actions[0]['args']}"
    )

    outgoing = {

        "proposed_actions": proposed_actions

    }

    # ------------------------------------------------------
    # Generate the report HERE, in the same function that
    # just computed proposed_actions — using local variables,
    # not a value read back from state in a later node. This
    # is what fixes the "always shows Research Report" bug.
    # ------------------------------------------------------

    outgoing["report"] = generate_report(

        query=state.get("query", ""),

        query_type="calendar",

        proposed_actions=proposed_actions

    )

    print(
        f"[TRACE] calendar_agent_node returning keys = "
        f"{sorted(outgoing.keys())}"
    )

    return outgoing


# ==========================================================
# SLACK AGENT
# (new — Slack requests previously had no dedicated workflow
# at all and were misclassified into the email flow. This
# extracts channel + message and proposes a Send_Slack action,
# gated by the same human-approval flow as everything else.)
# ==========================================================

def slack_agent_node(
    state: AgentState
) -> AgentState:

    print(
        "[Slack Agent] Preparing Slack message proposal..."
    )

    query = state.get(
        "query",
        ""
    )

    # --------------------------------------------------------
    # FIX: this node never fetched real calendar data, so it
    # could only write generic text like "the scheduled event
    # is still on track" instead of the actual title/time —
    # mirrors _maybe_fetch_calendar_context in email_agent.py.
    # --------------------------------------------------------

    calendar_context = ""

    event_words = [
        "event", "meeting", "schedule", "scheduled", "appointment"
    ]

    if any(word in query.lower() for word in event_words):

        try:

            cal_result = get_calendar_events(query)

            calendar_context = cal_result.get("message", "") or ""

        except Exception as e:

            print(
                f"[Slack Agent] Calendar context lookup failed: {e}"
            )

    calendar_section = (

        f"\nCALENDAR CONTEXT (real event data — use this to fill "
        f"in the actual title/date/time; do not invent anything "
        f"beyond what's here):\n{calendar_context}\n"

        if calendar_context

        else ""

    )

    prompt = f"""
You are a Slack message drafting assistant.

The user wants to send a Slack message.

Extract the target channel and the message text.

USER REQUEST:
{query}
{calendar_section}

RULES:

1. Extract the channel if mentioned (e.g. "#general"). If no
   channel is mentioned, use "#general" as the default.
2. If CALENDAR CONTEXT is present above and the user refers to
   an event, use those real details (title/date/time) in the
   message instead of generic phrasing.
3. Do not invent details beyond the user request and, if
   present, CALENDAR CONTEXT.
4. Output ONLY valid JSON.

OUTPUT FORMAT:

{{
    "channel": "#channel-name",
    "message": "the message text"
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

        slack_data = json.loads(content)

    except Exception as e:

        print(
            f"[Slack Agent] Extraction error: {e}"
        )

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

    print(
        f"[Slack Agent] Proposed message: {proposed_actions[0]['args']}"
    )

    report_text = generate_report(

        query=query,

        query_type="slack",

        proposed_actions=proposed_actions

    )

    return {

        "proposed_actions": proposed_actions,

        "report": report_text

    }


# ==========================================================
# CALENDAR READ AGENT
# (new — read-only lookups like "list my events this week".
# No proposed_actions, no approval needed — this just fetches
# and displays, same category as document/research queries.)
# ==========================================================

def calendar_read_agent_node(
    state: AgentState
) -> AgentState:

    print(
        "[Calendar Read Agent] Fetching calendar events..."
    )

    query = state.get(
        "query",
        ""
    )

    try:

        result = get_calendar_events(query)

        message = result.get("message", "")

        if not message:

            message = "No calendar events were found for this request."

    except Exception as e:

        print(
            f"[Calendar Read Agent] Error fetching events: {e}"
        )

        message = (
            "Sorry, I couldn't retrieve calendar events "
            "right now — the calendar service may be unavailable."
        )

    report_text = f"# Calendar Events\n\n{message}"

    print(
        f"[Calendar Read Agent] Done — {len(report_text)} chars"
    )

    return {

        "report": report_text,

        "proposed_actions": []

    }


# ==========================================================
# BUILD GRAPH
# ==========================================================

def build_supervisor_graph():

    graph = StateGraph(
        AgentState
    )


    # ======================================================
    # NODES
    # ======================================================

    graph.add_node("memory_load", memory_load_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("planner", planner_node)
    graph.add_node("email_agent", prepare_new_email)
    graph.add_node("email_read_agent", list_recent_emails)
    graph.add_node("email_broadcast_agent", prepare_broadcast_email)
    graph.add_node("complaint_agent", analyze_complaint_emails)
    graph.add_node("rag_agent", rag_agent)
    graph.add_node("research_agent", research_agent_node)
    graph.add_node("calendar_agent", calendar_agent_node)
    graph.add_node("calendar_read_agent", calendar_read_agent_node)
    graph.add_node("slack_agent", slack_agent_node)
    graph.add_node("human_review", human_review)
    graph.add_node("memory_save", memory_save_node)
    graph.add_node("auto_complete", auto_complete_node)


    # ======================================================
    # ENTRY
    # ======================================================

    graph.set_entry_point("memory_load")

    graph.add_edge("memory_load", "supervisor")


    # ======================================================
    # SUPERVISOR → PLANNER
    # ======================================================

    graph.add_conditional_edges(

        "supervisor",

        supervisor_router,

        {

            "email_agent": "planner",

            "email_read_agent": "planner",

            "email_broadcast_agent": "planner",

            "complaint_agent": "planner",

            "rag_agent": "planner",

            "research_agent": "planner",

            "calendar_agent": "planner",

            "calendar_read_agent": "planner",

            "slack_agent": "planner"

        }

    )


    # ======================================================
    # PLANNER → SPECIALIST
    # ======================================================

    graph.add_conditional_edges(

        "planner",

        supervisor_router,

        {

            "email_agent": "email_agent",

            "email_read_agent": "email_read_agent",

            "email_broadcast_agent": "email_broadcast_agent",

            "complaint_agent": "complaint_agent",

            "rag_agent": "rag_agent",

            "research_agent": "research_agent",

            "calendar_agent": "calendar_agent",

            "calendar_read_agent": "calendar_read_agent",

            "slack_agent": "slack_agent"

        }

    )


    # ======================================================
    # SPECIALIST → (HITL only if there's something to approve)
    #
    # Each specialist now generates its own "report" text
    # directly (using query_type/proposed_actions that are
    # already in its own local scope), so there's no longer a
    # hand-off through a separate "reporter" node for these to
    # go missing on.
    # ======================================================

    for specialist_node in (
        "email_agent",
        "email_read_agent",
        "email_broadcast_agent",
        "complaint_agent",
        "rag_agent",
        "research_agent",
        "calendar_agent",
        "calendar_read_agent",
        "slack_agent"
    ):

        graph.add_conditional_edges(

            specialist_node,

            route_after_specialist,

            {

                "human_review": "human_review",

                "auto_complete": "auto_complete"

            }

        )


    # ======================================================
    # HITL ROUTING
    # ======================================================

    graph.add_conditional_edges(

        "human_review",

        route_after_review,

        {

            "memory_save": "memory_save",

            END: END

        }

    )


    # ======================================================
    # SAVE → END
    # ======================================================

    graph.add_edge("memory_save", END)
    graph.add_edge("auto_complete", END)


    # ======================================================
    # CHECKPOINT
    # ======================================================

    return graph.compile(
        checkpointer=MemorySaver()
    )


# ==========================================================
# RUN AGENT (manual/CLI testing)
# ==========================================================

def run_agent(

    query: str,

    user: str = "default",

    session_id: str = "default"

) -> str:


    app = build_supervisor_graph()


    initial_state: AgentState = {

        "query": query,

        "emails": [],

        "context": "",

        "report": "",

        "messages": [

            HumanMessage(

                content=query

            )

        ],

        "query_type": "",

        "plan": [],

        "user": user,

        "session_id": session_id,

        "memory_context": None,

        "approved": None,

        "approval_comment": "",

        "proposed_actions": []

    }


    config = {

        "configurable": {

            "thread_id": session_id

        }

    }


    print(

        f"\n{'=' * 60}\n"

        f"Query : {query}\n"

        f"User  : {user}\n"

        f"Session: {session_id}\n"

        f"{'=' * 60}"

    )


    result = app.invoke(

        initial_state,

        config=config

    )


    snapshot = app.get_state(config)


    if not snapshot.next:

        print(

            "\nCompleted without requiring approval."

        )

        return result.get("report", "")


    print(

        "\nREPORT GENERATED — "
        "AWAITING APPROVAL"

    )


    print(

        result.get(

            "report",

            "No report generated."

        )

    )


    while True:

        decision = input(

            "Approve this report? "
            "(approve / reject): "

        ).strip().lower()


        if decision in (

            "approve",

            "reject"

        ):

            break


        print(

            "Please type exactly "
            "'approve' or 'reject'."

        )


    final_result = app.invoke(

        Command(

            resume={

                "decision": decision,

                "comment": ""

            }

        ),

        config=config

    )


    if final_result.get("approved"):

        print(

            "\nReport approved — "
            "approved actions executed."

        )

    else:

        print(

            "\nReport rejected — "
            "nothing executed."

        )


    return final_result.get("report", "")
