import uuid
import requests
import streamlit as st

from rag.rag_chat import ask_rag


# ==========================================================
# CONFIGURATION
# ==========================================================

FASTAPI_BASE_URL = "http://127.0.0.1:8000"


# ==========================================================
# INITIALIZE SESSION STATE
# ==========================================================

def initialize_chat_state():

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "pending_review" not in st.session_state:
        st.session_state.pending_review = None

    # FIX: the original check was `"agent_session_id" not in
    # st.session_state`. Because streamlit_app.py pre-populates this
    # key with None for every user, that check was always False and
    # a UUID was never generated — None got sent straight to FastAPI
    # and caused the 422 "Input should be a valid string" error.
    # Checking truthiness instead of key-presence fixes it, and also
    # self-heals if it's ever reset to None/"" elsewhere.
    if not st.session_state.get("agent_session_id"):
        st.session_state.agent_session_id = str(uuid.uuid4())

    if "review_comment" not in st.session_state:
        st.session_state.review_comment = ""

    # --------------------------------------------------------
    # FIX: Streamlit forbids reassigning a widget-bound
    # session_state key (like "review_comment", used by the
    # st.text_area below) after that widget has already been
    # instantiated in the current script run. submit_review()
    # used to do exactly that right after Approve/Reject,
    # which crashed with:
    #   "st.session_state.review_comment cannot be modified
    #    after the widget with key review_comment is
    #    instantiated."
    # The action itself had already executed by that point —
    # only this cleanup step was broken. Instead, submit_review()
    # now just sets a plain flag, and we consume that flag here,
    # BEFORE the text_area widget is created below — which is
    # the one place Streamlit allows it.
    # --------------------------------------------------------

    if st.session_state.get("_clear_review_comment"):
        st.session_state.review_comment = ""
        st.session_state["_clear_review_comment"] = False


# ==========================================================
# DISPLAY CHAT MESSAGE
# ==========================================================

def display_message(role, content):

    with st.chat_message(role):

        st.markdown(
            content
        )


# ==========================================================
# HUMAN REVIEW UI
# ==========================================================

def render_human_review():

    review_data = st.session_state.get(
        "pending_review"
    )

    if not review_data:

        return False


    st.warning(
        "⚠️ Human Approval Required"
    )


    st.header(
        "📋 Review AI-Generated Actions"
    )


    st.info(
        "The AI has analyzed your request and prepared "
        "the following actions. Nothing will be executed "
        "until you approve it."
    )


    st.subheader(
        "🔍 Original Request"
    )


    original_query = (

        review_data.get(
            "query"
        )

        or ""

    )


    st.code(
        original_query
    )


    st.subheader(
        "📄 Generated Report"
    )


    report = (

        review_data.get(
            "report"
        )

        or review_data.get(
            "final_response"
        )

        or review_data.get(
            "output"
        )

        or ""

    )


    if report:

        st.markdown(
            report
        )

    else:

        st.info(
            "No report was generated."
        )


    proposed_actions = (

        review_data.get(
            "proposed_actions"
        )

        or review_data.get(
            "planned_actions"
        )

        or []

    )


    if proposed_actions:

        st.subheader(
            "⚙️ Proposed Actions"
        )


        for index, action in enumerate(

            proposed_actions,

            start=1

        ):

            if isinstance(
                action,
                dict
            ):

                tool = action.get(
                    "tool",
                    "Unknown Action"
                )

                args = action.get(
                    "args",
                    {}
                )

                st.markdown(

                    f"**{index}. {tool}**"

                )

                st.json(
                    args
                )

            else:

                st.markdown(

                    f"**{index}. {action}**"

                )


    review_comment = st.text_area(

        "Optional review comment",

        placeholder=(

            "Add feedback or reason for your decision..."

        ),

        key="review_comment"

    )


    st.divider()


    st.subheader(
        "What would you like to do?"
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(

            "✅ Approve",

            use_container_width=True,

            type="primary"

        ):

            submit_review(

                session_id=review_data.get(
                    "session_id"
                ),

                decision="approve",

                comment=review_comment

            )


    with col2:

        if st.button(

            "❌ Reject",

            use_container_width=True

        ):

            submit_review(

                session_id=review_data.get(
                    "session_id"
                ),

                decision="reject",

                comment=review_comment

            )


    return True


# ==========================================================
# MAIN CHAT PANEL
# ==========================================================

def show_chat_panel():

    initialize_chat_state()


    st.subheader(
        "💬 AI Assistant"
    )


    assistant_mode = st.radio(

        "Assistant Mode",

        [

            "📚 Company Knowledge (RAG)",

            "🤖 AI Agent (Automation)"

        ],

        horizontal=True

    )


    st.markdown("---")


    for message in st.session_state.messages:

        display_message(

            message.get(
                "role",
                "assistant"
            ),

            message.get(
                "content",
                ""
            )

        )


    if render_human_review():

        return


    user_message = st.chat_input(

        "Ask your Enterprise AI Assistant..."

    )


    if not user_message:

        return


    st.session_state.messages.append({

        "role": "user",

        "content": user_message

    })


    display_message(

        "user",

        user_message

    )


    # ======================================================
    # RAG MODE
    # ======================================================

    if assistant_mode == (

        "📚 Company Knowledge (RAG)"

    ):

        try:

            with st.spinner(

                "Searching company knowledge..."

            ):

                answer = ask_rag(

                    user_message

                )


        except Exception as e:

            answer = (

                "❌ RAG Error:\n\n"

                f"{str(e)}"

            )


        st.session_state.messages.append({

            "role": "assistant",

            "content": answer

        })


        display_message(

            "assistant",

            answer

        )


        return


    # ======================================================
    # AI AGENT MODE
    # ======================================================

    current_user = (

        st.session_state.get(

            "user",

            {}

        )

        or {}

    )


    username = current_user.get(

        "username",

        "default"

    )


    # FIX: guarantee a real session id string is always sent, even
    # if something upstream managed to null it out again.
    session_id = (
        st.session_state.get("agent_session_id")
        or str(uuid.uuid4())
    )

    st.session_state.agent_session_id = session_id


    payload = {

        "query": user_message,

        "user": username,

        "session_id": session_id

    }


    try:

        with st.spinner(

            "AI Agent is planning and executing..."

        ):

            response = requests.post(

                f"{FASTAPI_BASE_URL}/chat",

                json=payload,

                timeout=300

            )


        if response.status_code != 200:

            error = (

                f"❌ Backend Error: "
                f"HTTP {response.status_code}\n\n"

                f"Details:\n"

                f"{response.text}"

            )


            st.error(
                error
            )


            return


        try:

            data = response.json()


        except ValueError:

            st.error(

                "❌ FastAPI returned invalid JSON:\n\n"

                f"{response.text}"

            )


            return


        if data.get(

            "status"

        ) == "awaiting_approval":


            st.session_state.pending_review = {

                # FIX: fall back to the session_id we just sent, in
                # case the backend response ever omits it — this was
                # the other place a None could sneak back in and
                # break the later /review call.
                "session_id": data.get(

                    "session_id"

                ) or session_id,

                "query": data.get(

                    "query",

                    user_message

                ),

                "report": data.get(

                    "report",

                    ""

                ),

                "final_response": data.get(

                    "final_response",

                    ""

                ),

                "output": data.get(

                    "output",

                    ""

                ),

                "proposed_actions": data.get(

                    "proposed_actions",

                    data.get(

                        "planned_actions",

                        []

                    )

                ),

                "planned_actions": data.get(

                    "planned_actions",

                    []

                ),

                "next": data.get(

                    "next",

                    []

                )

            }


            st.rerun()


        final_response = (

            data.get(

                "final_response"

            )

            or data.get(

                "report"

            )

            or data.get(

                "output"

            )

            or data.get(

                "message"

            )

            or data.get(

                "response"

            )

            or "The request was completed."

        )


        st.session_state.messages.append({

            "role": "assistant",

            "content": final_response

        })


        display_message(

            "assistant",

            final_response

        )


    except requests.exceptions.Timeout:

        st.error(

            "⏱️ The request timed out.\n\n"

            "The backend may still be processing "
            "your request."

        )


    except requests.exceptions.ConnectionError:

        st.error(

            "❌ Cannot connect to FastAPI.\n\n"

            "Make sure Uvicorn is running:\n\n"

            "`uvicorn app:app --reload`"

        )


    except Exception as e:

        st.error(

            f"❌ Unexpected error:\n\n"

            f"{str(e)}"

        )


# ==========================================================
# SUBMIT HUMAN REVIEW
# ==========================================================

def submit_review(

    session_id,

    decision,

    comment=""

):


    if not session_id:

        st.error(

            "❌ Missing session ID. "
            "Cannot submit review."

        )

        return


    try:

        with st.spinner(

            "Processing your decision..."

        ):

            response = requests.post(

                f"{FASTAPI_BASE_URL}/review",

                json={

                    "session_id": session_id,

                    "decision": decision,

                    "comment": comment

                },

                timeout=300

            )


        if response.status_code != 200:

            st.error(

                f"❌ Review Error:\n\n"

                f"{response.text}"

            )

            return


        try:

            data = response.json()


        except ValueError:

            st.error(

                "❌ Invalid JSON returned by "
                "the review endpoint."

            )

            return


        if decision == "approve":

            st.success(

                "✅ Actions approved and executed."

            )

        else:

            st.warning(

                "❌ Actions rejected. "
                "Nothing was executed."

            )


        final_response = (

            data.get(

                "final_response"

            )

            or data.get(

                "report"

            )

            or data.get(

                "output"

            )

            or data.get(

                "message"

            )

            or ""

        )


        if final_response:

            st.session_state.messages.append({

                "role": "assistant",

                "content": final_response

            })


        st.session_state.pending_review = None

        st.session_state["_clear_review_comment"] = True


        st.rerun()


    except requests.exceptions.ConnectionError:

        st.error(

            "❌ Cannot connect to FastAPI."

        )


    except Exception as e:

        st.error(

            f"❌ Review failed:\n\n"

            f"{str(e)}"

        )