import textwrap

import streamlit as st

from auth import login
from manager_panel import show_manager_panel
from employee_panel import show_employee_panel
from chat_panel import show_chat_panel


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================================
# LOAD CSS
# ==========================================================

def load_css():

    try:

        with open(
            "assets/style.css",
            "r",
            encoding="utf-8"
        ) as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

    except FileNotFoundError:

        pass


load_css()


# ==========================================================
# SESSION STATE
# ==========================================================

DEFAULT_SESSION = {

    "page": "landing",

    "logged_in": False,

    "user": None,

    "messages": [],

    "selected_tool": None,

    "pending_review": None,

    "agent_session_id": None,

    # New fields for the internal AI workflow
    "last_response": "",

    "last_status": None,

    "last_tool_results": [],

    "last_error": None,

}


for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ==========================================================
# LANDING PAGE
# ==========================================================

def landing_page():

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    _, center, _ = st.columns(
        [1, 2, 1]
    )

    with center:

        st.markdown(
            textwrap.dedent(
                """
                <div style="text-align:center;padding:20px;">

                    <h1>
                        🤖 Enterprise Knowledge Assistant
                    </h1>

                    <h3 style="color:#2563EB;">
                        AI-Powered Workplace Automation
                    </h3>

                    <br>

                    <h4>
                        👋 Welcome to the Enterprise AI Workspace
                    </h4>

                    <p style="font-size:18px;">

                        An internal AI assistant for employees and managers
                        to work with company information, emails, documents,
                        reports, and workplace workflows.

                    </p>

                </div>
                """
            ),
            unsafe_allow_html=True
        )

        st.markdown("---")

        st.subheader("Continue As")

        manager_col, employee_col = st.columns(2)

        with manager_col:

            if st.button(
                "👨‍💼 Manager",
                use_container_width=True,
                type="primary"
            ):

                st.session_state.page = "manager_login"

                st.rerun()

        with employee_col:

            if st.button(
                "👩‍💻 Employee",
                use_container_width=True
            ):

                st.session_state.page = "employee_login"

                st.rerun()

        st.markdown(
            "<br>",
            unsafe_allow_html=True
        )

        st.info(
            textwrap.dedent(
                """
                **Enterprise AI Capabilities**

                📧 Analyze and manage work-related emails

                📄 Search internal company knowledge

                📊 Generate business summaries and reports

                📅 Create calendar events

                📝 Prepare tasks and action items

                💬 Send internal notifications

                🔐 Require human approval before sensitive actions
                """
            )
        )


# ==========================================================
# LOGIN PAGE
# ==========================================================

def login_page():

    _, center, _ = st.columns(
        [1, 2, 1]
    )

    with center:

        if st.button(
            "← Back",
            use_container_width=True
        ):

            st.session_state.page = "landing"

            st.rerun()

        st.markdown("---")

        if st.session_state.page == "manager_login":

            st.title("👨‍💼 Manager Login")

            expected_role = "manager"

        else:

            st.title("👩‍💻 Employee Login")

            expected_role = "employee"

        st.write(
            "Sign in to access your internal enterprise AI workspace."
        )

        username = st.text_input(
            "Username",
            placeholder="Enter your username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        st.markdown("")

        login_btn = st.button(
            "Login",
            use_container_width=True,
            type="primary"
        )

        st.info(
            "If you do not have an account, please contact your administrator."
        )

        if login_btn:

            if not username.strip() or not password.strip():

                st.warning(
                    "Please enter both username and password."
                )

                return

            user = login(
                username.strip(),
                password
            )

            if user is None:

                st.error(
                    "Invalid username or password."
                )

                return

            # ------------------------------------------
            # Verify selected role
            # ------------------------------------------

            if user["role"] != expected_role:

                st.error(
                    f"This account belongs to a "
                    f"{user['role'].capitalize()}, "
                    f"not a "
                    f"{expected_role.capitalize()}."
                )

                return

            # ------------------------------------------
            # Login success
            # ------------------------------------------

            st.session_state.logged_in = True

            st.session_state.page = "dashboard"

            st.session_state.user = user

            st.session_state.messages = []

            st.session_state.pending_review = None

            st.session_state.agent_session_id = None

            st.session_state.last_response = ""

            st.session_state.last_status = None

            st.session_state.last_tool_results = []

            st.session_state.last_error = None

            name = (

                user.get("full_name")

                or user["username"]

            )

            st.success(
                f"Welcome, {name}!"
            )

            st.rerun()


# ==========================================================
# LOGOUT
# ==========================================================

def logout():

    st.session_state.logged_in = False

    st.session_state.page = "landing"

    st.session_state.user = None

    st.session_state.messages = []

    st.session_state.selected_tool = None

    st.session_state.pending_review = None

    st.session_state.agent_session_id = None

    st.session_state.last_response = ""

    st.session_state.last_status = None

    st.session_state.last_tool_results = []

    st.session_state.last_error = None

    st.rerun()


# ==========================================================
# SIDEBAR
# ==========================================================

def render_sidebar(user, display_name):

    with st.sidebar:

        st.markdown(
            textwrap.dedent(
                """
                <div style="text-align:center;">

                    <h2>
                        🤖 Enterprise AI
                    </h2>

                    <p>
                        Knowledge Assistant
                    </p>

                </div>
                """
            ),
            unsafe_allow_html=True
        )

        st.markdown("---")

        st.success(
            f"Welcome, {display_name}"
        )

        st.write(
            f"**Username:** {user['username']}"
        )

        st.write(
            f"**Role:** {user['role'].capitalize()}"
        )

        if user.get("email"):

            st.write(
                f"**Email:** {user['email']}"
            )

        st.markdown("---")

        st.subheader(
            "⚡ Quick Actions"
        )

        st.caption(
            "Use the AI Assistant to describe your task in natural language."
        )

        st.button(
            "📧 Email Assistant",
            use_container_width=True,
            disabled=True
        )

        st.button(
            "📅 Schedule Meeting",
            use_container_width=True,
            disabled=True
        )

        st.button(
            "📄 Search Documents",
            use_container_width=True,
            disabled=True
        )

        st.button(
            "📊 Generate Report",
            use_container_width=True,
            disabled=True
        )

        st.markdown("---")

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            logout()


# ==========================================================
# DASHBOARD
# ==========================================================

def dashboard():

    user = st.session_state.user

    display_name = (

        user.get("full_name")

        or user["username"]

    ).strip()

    # ======================================================
    # SIDEBAR
    # ======================================================

    render_sidebar(
        user,
        display_name
    )

    # ======================================================
    # HEADER
    # ======================================================

    if user["role"] == "manager":

        st.title(
            "🛠 Manager Workspace"
        )

    else:

        st.title(
            "👨‍💼 Employee Workspace"
        )

    st.write(
        f"Hello **{display_name}**, "
        "what would you like the Enterprise AI Assistant to help with?"
    )

    st.caption(
        "This assistant is designed for internal company workflows and knowledge operations."
    )

    st.markdown("")

    # ======================================================
    # WORKSPACE OVERVIEW
    # ======================================================

    col1, col2 = st.columns(2)

    with col1:

        with st.container():

            st.markdown(
                "### 📧 Email Intelligence"
            )

            st.write(
                """
                Review work emails, identify action items,
                deadlines, meeting requests, and follow-ups.
                """
            )

        st.markdown("")

        with st.container():

            st.markdown(
                "### 📅 Workplace Scheduling"
            )

            st.write(
                """
                Prepare calendar events and meeting-related
                actions from natural-language requests.
                """
            )

    with col2:

        with st.container():

            st.markdown(
                "### 📄 Internal Knowledge Search"
            )

            st.write(
                """
                Search internal company documents and
                retrieve relevant organizational knowledge.
                """
            )

        st.markdown("")

        with st.container():

            st.markdown(
                "### 📊 Business Intelligence"
            )

            st.write(
                """
                Analyze internal information and generate
                summaries, insights, and reports.
                """
            )

    st.markdown("---")

    # ======================================================
    # MANAGER WORKSPACE
    # ======================================================

    if user["role"] == "manager":

        tab1, tab2 = st.tabs(
            [
                "💬 AI Assistant",
                "📂 Document Management"
            ]
        )

        with tab1:

            show_chat_panel()

        with tab2:

            show_manager_panel()

    # ======================================================
    # EMPLOYEE WORKSPACE
    # ======================================================

    else:

        tab1, tab2 = st.tabs(
            [
                "💬 AI Assistant",
                "👤 My Profile"
            ]
        )

        with tab1:

            show_chat_panel()

        with tab2:

            show_employee_panel()


# ==========================================================
# MAIN APPLICATION
# ==========================================================

def main():

    # ------------------------------------------------------
    # Logged-in user
    # ------------------------------------------------------

    if st.session_state.logged_in:

        dashboard()

        return

    # ------------------------------------------------------
    # Landing page
    # ------------------------------------------------------

    if st.session_state.page == "landing":

        landing_page()

    # ------------------------------------------------------
    # Manager login
    # ------------------------------------------------------

    elif st.session_state.page == "manager_login":

        login_page()

    # ------------------------------------------------------
    # Employee login
    # ------------------------------------------------------

    elif st.session_state.page == "employee_login":

        login_page()

    # ------------------------------------------------------
    # Fallback
    # ------------------------------------------------------

    else:

        st.session_state.page = "landing"

        st.rerun()


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    main()