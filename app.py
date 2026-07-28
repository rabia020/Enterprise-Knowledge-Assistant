# ==========================================================
# app.py
# ENTERPRISE AI KNOWLEDGE ASSISTANT API
# ==========================================================
#
# Reverted back to supervisor.py's pipeline: intent
# classification, complaint analysis, document RAG reports,
# and memory are restored. On top of that:
#
#   - calendar requests now actually create a calendar event
#     on approval (supervisor.py's calendar_agent_node +
#     memory_save_node calendar branch — this never existed
#     before, calendar was silently routed to research_agent)
#   - human_review is now only triggered when there's an
#     actual action to approve (email / calendar / complaint);
#     plain document/research queries no longer pause for an
#     approval that had nothing behind it
#   - proposed_actions is now populated for every action type,
#     so the review UI shows what's about to happen instead of
#     just report text
# ==========================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from supervisor import build_supervisor_graph
from rag.rag_chat import ask_rag
from tools.n8n_client import get_emails


# ==========================================================
# FASTAPI APPLICATION
# ==========================================================

app = FastAPI(
    title="Enterprise AI Knowledge Assistant",
    version="1.0.0",
    description=(
        "Internal AI assistant for enterprise knowledge retrieval, "
        "email analysis, task automation, reporting, and workflow execution."
    )
)


# ==========================================================
# BUILD GRAPH ONCE
# ==========================================================

try:

    app_graph = build_supervisor_graph()

    print("✅ Supervisor graph initialized successfully")

except Exception:

    print("\n❌ ERROR INITIALIZING SUPERVISOR GRAPH")

    import traceback

    traceback.print_exc()

    app_graph = None


# ==========================================================
# STORE PAUSED SESSIONS
# ==========================================================

paused_sessions = {}


# ==========================================================
# ROOT ENDPOINT
# ==========================================================

@app.get("/")
def home():

    return {

        "status": "running",

        "service": "Enterprise AI Knowledge Assistant",

        "message": (
            "Internal AI assistant API is running successfully."
        )

    }


# ==========================================================
# REQUEST MODELS
# ==========================================================

class ChatRequest(BaseModel):

    query: str

    user: str = "default"

    session_id: str = "default"


class ReviewRequest(BaseModel):

    session_id: str

    decision: str

    comment: str = ""


class RagRequest(BaseModel):

    question: str


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "graph_loaded": app_graph is not None,

        "paused_sessions": len(paused_sessions)

    }


# ==========================================================
# EMAIL ENDPOINT
# ==========================================================

@app.get("/emails")
def read_emails():

    try:

        emails = get_emails(

            label="complaints",

            days=30

        )

        return {

            "status": "success",

            "count": len(emails),

            "emails": emails

        }

    except Exception as e:

        import traceback

        traceback.print_exc()

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ==========================================================
# CHAT ENDPOINT
# ==========================================================

@app.post("/chat")
async def chat(req: ChatRequest):

    if app_graph is None:

        raise HTTPException(

            status_code=500,

            detail=(
                "Supervisor graph is not initialized. "
                "Check the FastAPI terminal."
            )

        )

    # ------------------------------------------------------
    # FIX: reject empty/missing session ids with a clear
    # error instead of the generic 422 the Streamlit 422 bug
    # produced (that root cause is fixed on the client side
    # in chat_panel.py / streamlit_app.py, this is a backstop).
    # ------------------------------------------------------

    if not req.session_id or not req.session_id.strip():

        raise HTTPException(

            status_code=422,

            detail="session_id must be a non-empty string."

        )

    try:

        print("\n" + "=" * 70)
        print("NEW ENTERPRISE AI REQUEST")
        print("=" * 70)
        print(f"User       : {req.user}")
        print(f"Session ID : {req.session_id}")
        print(f"Query      : {req.query}")
        print("=" * 70)

        # ==================================================
        # INITIAL STATE
        # ==================================================

        initial_state = {

            "query": req.query,

            "user": req.user,

            "plan": [],

            "emails": [],

            "context": "",

            "report": "",

            "messages": [

                HumanMessage(
                    content=req.query
                )

            ],

            "approved": None,

            "approval_comment": "",

            "query_type": "",

            "memory_context": None,

            "proposed_actions": []

        }

        config = {

            "configurable": {

                "thread_id": req.session_id

            }

        }

        # ==================================================
        # RUN GRAPH
        # ==================================================

        result = app_graph.invoke(

            initial_state,

            config=config

        )

        snapshot = app_graph.get_state(config)

        current_state = snapshot.values or result or {}

        report = (

            current_state.get("report")

            or current_state.get("final_response")

            or ""

        )

        proposed_actions = current_state.get(

            "proposed_actions",

            []

        )

        # ==================================================
        # HUMAN REVIEW REQUIRED
        # ==================================================

        if snapshot.next:

            print("\n⏸️ GRAPH PAUSED FOR HUMAN APPROVAL")

            paused_sessions[req.session_id] = True

            return {

                "status": "awaiting_approval",

                "message": (

                    "The AI has prepared a response "
                    "and proposed actions for review."

                ),

                "session_id": req.session_id,

                "query": req.query,

                "report": report,

                "final_response": report,

                "proposed_actions": proposed_actions,

                "next": list(snapshot.next)

            }

        # ==================================================
        # COMPLETED WITHOUT REVIEW
        # (document / research queries — nothing to approve)
        # ==================================================

        print("\n✅ GRAPH COMPLETED")

        return {

            "status": "completed",

            "session_id": req.session_id,

            "report": report,

            "final_response": report,

            "proposed_actions": proposed_actions,

            "emails": len(

                current_state.get("emails", [])

            ),

            "approved": current_state.get("approved"),

            "execution_status": current_state.get("status"),

            "error": current_state.get("error")

        }

    except Exception as e:

        print("\n❌ CHAT ENDPOINT ERROR")

        import traceback

        traceback.print_exc()

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ==========================================================
# HUMAN REVIEW ENDPOINT
# ==========================================================

@app.post("/review")
async def review(req: ReviewRequest):

    decision = req.decision.strip().lower()

    if decision not in ("approve", "reject"):

        raise HTTPException(

            status_code=400,

            detail="Decision must be either 'approve' or 'reject'."

        )

    if req.session_id not in paused_sessions:

        raise HTTPException(

            status_code=404,

            detail=f"No paused session found for {req.session_id}"

        )

    config = {

        "configurable": {

            "thread_id": req.session_id

        }

    }

    try:

        print("\n" + "=" * 70)
        print("HUMAN REVIEW")
        print("=" * 70)
        print(f"Session : {req.session_id}")
        print(f"Decision: {decision}")
        print(f"Comment : {req.comment}")
        print("=" * 70)

        # ==================================================
        # RESUME GRAPH
        # ==================================================

        final_state = app_graph.invoke(

            Command(

                resume={

                    "decision": decision,

                    "comment": req.comment

                }

            ),

            config=config

        )

        paused_sessions.pop(req.session_id, None)

        final_report = (

            final_state.get("report")

            or final_state.get("final_response")

            or ""

        )

        return {

            "status": "approved" if decision == "approve" else "rejected",

            "approved": decision == "approve",

            "session_id": req.session_id,

            "report": final_report,

            "final_response": final_report,

            "proposed_actions": final_state.get("proposed_actions", []),

            "execution_status": final_state.get("status"),

            "error": final_state.get("error")

        }

    except Exception as e:

        print("\n❌ REVIEW ERROR")

        import traceback

        traceback.print_exc()

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


# ==========================================================
# RAG ENDPOINT
# ==========================================================

@app.post("/rag")
async def rag(req: RagRequest):

    try:

        answer = ask_rag(req.question)

        return {

            "status": "success",

            "answer": answer

        }

    except Exception as e:

        print("\n❌ RAG ERROR")

        import traceback

        traceback.print_exc()

        raise HTTPException(

            status_code=500,

            detail=str(e)

        )


print("\n========== REGISTERED ROUTES ==========")

for route in app.routes:
    print(route.path, getattr(route, "methods", None))

print("=======================================\n")