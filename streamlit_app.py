import streamlit as st

from auth import login
from manager_panel import show_manager_panel
from employee_panel import show_employee_panel
from chat_panel import show_chat_panel

from icons import (
    ICON_ROBOT,
    ICON_MANAGER,
    ICON_EMPLOYEE,
    ICON_MAIL,
    ICON_DOC,
    ICON_CHART,
    ICON_CALENDAR,
    ICON_TASKS,
    ICON_SHIELD,
    ICON_ARROW_RIGHT,
    ICON_CHAT,
)


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# LOAD CSS
# ==========================================================

def load_css():
    """Load the application stylesheet."""

    css_path = "assets/style.css"

    try:
        with open(css_path, "r", encoding="utf-8") as file:
            css = file.read()

        st.markdown(
            f"<style>{css}</style>",
            unsafe_allow_html=True,
        )

    except FileNotFoundError:
        st.warning(
            "assets/style.css was not found. "
            "The application will continue with default styling."
        )


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
    "last_response": "",
    "last_status": None,
    "last_tool_results": [],
    "last_error": None,
}


for key, default_value in DEFAULT_SESSION.items():

    if key not in st.session_state:

        # Make mutable objects independent per session
        if isinstance(default_value, list):
            st.session_state[key] = []
        elif isinstance(default_value, dict):
            st.session_state[key] = {}
        else:
            st.session_state[key] = default_value


# ==========================================================
# HTML RENDER HELPER
# ==========================================================

def render_html(html):
    """
    Safely render an HTML fragment in Streamlit.

    Each line is stripped and then joined into a single line
    before being passed to Streamlit. This prevents indented
    HTML from being interpreted as a Markdown code block.
    """

    if html is None:
        return

    cleaned_html = " ".join(
        line.strip()
        for line in str(html).strip().splitlines()
        if line.strip()
    )

    if cleaned_html:
        st.markdown(
            cleaned_html,
            unsafe_allow_html=True,
        )


# ==========================================================
# RESET CHAT STATE
# ==========================================================

def reset_chat():

    st.session_state.messages = []
    st.session_state.selected_tool = None
    st.session_state.pending_review = None
    st.session_state.agent_session_id = None
    st.session_state.last_response = ""
    st.session_state.last_status = None
    st.session_state.last_tool_results = []
    st.session_state.last_error = None


# ==========================================================
# ROLE CARD
# ==========================================================

def role_card(
    icon_svg,
    title,
    subtitle,
    button_key,
    primary=False,
):
    """
    Display a visual role card and a Streamlit button.
    Colors are unchanged from the original design.
    """

    if primary:

        card_background = (
            "linear-gradient(135deg, #14b8b0, #0d9488)"
        )

        title_color = "#ffffff"
        subtitle_color = "rgba(255,255,255,0.86)"
        arrow_color = "#ffffff"

        icon_background = "rgba(255,255,255,0.20)"
        icon_color = "#ffffff"

    else:

        card_background = "#142a3b"

        title_color = "#f1f5f9"
        subtitle_color = "#a9b6c9"
        arrow_color = "#7c8aa0"

        icon_background = "#10283b"
        icon_color = "#ffffff"

    render_html(
        f"""
        <div style="
            background:{card_background};
            border:1px solid rgba(255,255,255,0.10);
            border-radius:16px;
            padding:16px 20px;
            display:flex;
            align-items:center;
            gap:14px;
            min-height:66px;
            box-sizing:border-box;
            margin-bottom:8px;
        ">
            <div style="
                width:44px;
                height:44px;
                min-width:44px;
                border-radius:12px;
                background:{icon_background};
                color:{icon_color};
                display:flex;
                align-items:center;
                justify-content:center;
            ">
                {icon_svg}
            </div>
            <div style="flex:1;min-width:0;">
                <div style="
                    font-weight:800;
                    font-size:16px;
                    color:{title_color};
                    line-height:1.3;
                    white-space:nowrap;
                ">
                    {title}
                </div>
                <div style="
                    font-size:13px;
                    color:{subtitle_color};
                    margin-top:3px;
                    line-height:1.4;
                    white-space:nowrap;
                    overflow:hidden;
                    text-overflow:ellipsis;
                ">
                    {subtitle}
                </div>
            </div>
            <div style="color:{arrow_color};display:flex;align-items:center;">
                {ICON_ARROW_RIGHT}
            </div>
        </div>
        """
    )

    return st.button(
        "Continue",
        key=button_key,
        use_container_width=True,
        type="primary" if primary else "secondary",
    )


# ==========================================================
# LANDING PAGE
# ==========================================================

def landing_page():

    st.markdown(
        "<div style='height:16px'></div>",
        unsafe_allow_html=True,
    )

    # Wider center column so the heading fits on one line and
    # role-card subtitles fit on one line, matching the reference.
    left, center, right = st.columns([1, 4.2, 1])

    with center:

        render_html(
            f"""
            <div class="eka-hero-wrap">
                <div class="eka-logo-badge">
                    {ICON_ROBOT}
                </div>
                <div style="margin-top:16px;">
                    <span class="eka-eyebrow">
                        ✦ AI WORKPLACE COPILOT
                    </span>
                </div>
                <div class="eka-h1">
                    Enterprise Knowledge Assistant
                </div>
                <div class="eka-sub">
                    One secure workspace for company policies,
                    leave rules and AI-powered workplace automation.
                </div>
            </div>
            """
        )

        st.markdown(
            "<div style='height:22px'></div>",
            unsafe_allow_html=True,
        )

        render_html(
            """
            <div style="
                text-align:center;
                font-weight:800;
                color:#f1f5f9;
                font-size:17px;
                margin-bottom:12px;
            ">
                Continue As
            </div>
            """
        )

        manager_col, employee_col = st.columns(2)

        with manager_col:

            manager_clicked = role_card(
                ICON_MANAGER,
                "Manager",
                "Team insights, users and document control",
                "landing_manager_btn",
                primary=True,
            )

        with employee_col:

            employee_clicked = role_card(
                ICON_EMPLOYEE,
                "Employee",
                "Policies, leave answers and daily automation",
                "landing_employee_btn",
                primary=False,
            )

        if manager_clicked:
            st.session_state.page = "manager_login"
            st.rerun()

        if employee_clicked:
            st.session_state.page = "employee_login"
            st.rerun()

        # --------------------------------------------------
        # CAPABILITIES
        # --------------------------------------------------

        st.markdown(
            "<div style='height:18px'></div>",
            unsafe_allow_html=True,
        )

        capabilities = [
            (ICON_MAIL, "Analyze and manage work-related emails"),
            (ICON_DOC, "Search internal company knowledge"),
            (ICON_CHART, "Generate business summaries and reports"),
            (ICON_CALENDAR, "Create calendar events"),
            (ICON_TASKS, "Prepare tasks and action items"),
            (ICON_SHIELD, "Human approval before sensitive actions"),
        ]

        def _cap_row(icon, label):
            return (
                '<div style="display:flex;align-items:center;gap:12px;'
                'padding:8px 0;color:#a9b6c9;font-size:14px;">'
                '<span style="width:30px;height:30px;min-width:30px;'
                'border-radius:9px;background:rgba(20,184,176,0.14);'
                'color:#2dd4bf;display:flex;align-items:center;'
                f'justify-content:center;">{icon}</span>'
                f'<span>{label}</span></div>'
            )

        left_items = "".join(_cap_row(i, l) for i, l in capabilities[:3])
        right_items = "".join(_cap_row(i, l) for i, l in capabilities[3:])

        render_html(
            f"""
            <div style="
                background:rgba(255,255,255,0.025);
                border:1px solid rgba(255,255,255,0.08);
                border-radius:22px;
                padding:22px 26px;
            ">
                <div style="
                    font-size:12px;
                    font-weight:700;
                    letter-spacing:0.08em;
                    text-transform:uppercase;
                    color:#7c8aa0;
                    margin-bottom:6px;
                ">
                    Enterprise AI Capabilities
                </div>
                <div style="display:flex;gap:35px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:230px;">{left_items}</div>
                    <div style="flex:1;min-width:230px;">{right_items}</div>
                </div>
            </div>
            """
        )

        st.markdown(
            "<div style='height:30px'></div>",
            unsafe_allow_html=True,
        )


# ==========================================================
# LOGIN PAGE
# ==========================================================

def login_page():

    left, center, right = st.columns([1, 1.35, 1])

    with center:

        st.markdown(
            "<div style='height:18px'></div>",
            unsafe_allow_html=True,
        )

        if st.button("←  Back", key="login_back_btn", type="secondary"):
            st.session_state.page = "landing"
            st.rerun()

        if st.session_state.page == "manager_login":
            title = "Manager Login"
            icon = ICON_MANAGER
            expected_role = "manager"
        else:
            title = "Employee Login"
            icon = ICON_EMPLOYEE
            expected_role = "employee"

        # ----------------------------------------------------
        # Everything below lives inside ONE real st.container,
        # which style.css turns into the white card. Native
        # widgets (text_input, button) render correctly inside
        # it -- unlike raw HTML spanning multiple st.markdown
        # calls, which cannot stay "open" across calls.
        # ----------------------------------------------------

        with st.container(key="login_card"):

            render_html(
                f"""
                <div style="
                    display:flex;
                    gap:14px;
                    align-items:flex-start;
                    margin-bottom:18px;
                ">
                    <div style="
                        width:44px;
                        height:44px;
                        min-width:44px;
                        border-radius:12px;
                        background:#0e1b2e;
                        color:#ffffff;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                    ">
                        {icon}
                    </div>
                    <div>
                        <div style="
                            font-size:21px;
                            font-weight:800;
                            color:#0f172a;
                        ">
                            {title}
                        </div>
                        <div style="
                            font-size:10px;
                            color:#64748b;
                            margin-top:3px;
                            line-height:1.5;
                        ">
                            Sign in to access your internal
                            enterprise AI workspace.
                        </div>
                    </div>
                </div>
                """
            )

            render_html(
                '<div style="color:#0f172a;font-weight:700;'
                'font-size:14px;margin:4px 0 5px 0;">Username</div>'
            )

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                label_visibility="collapsed",
                key="login_username_field",
            )

            render_html(
                '<div style="color:#0f172a;font-weight:700;'
                'font-size:14px;margin:12px 0 5px 0;">Password</div>'
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                label_visibility="collapsed",
                key="login_password_field",
            )

            st.markdown(
                "<div style='height:8px'></div>",
                unsafe_allow_html=True,
            )

            login_clicked = st.button(
                "Login",
                use_container_width=True,
                type="primary",
                key="login_submit_btn",
            )

            render_html(
                """
                <div style="
                    background:#eef4fb;
                    border-radius:12px;
                    padding:12px 16px;
                    color:#2f5f92;
                    font-size:11px;
                    text-align:center;
                    margin-top:12px;
                ">
                    If you do not have an account, please contact your administrator.
                </div>
                """
            )

        if login_clicked:

            if not username.strip() or not password.strip():
                st.warning("Please enter both username and password.")
                return

            user = login(username.strip(), password)

            if user is None:
                st.error("Invalid username or password.")
                return

            if user["role"] != expected_role:
                st.error(
                    f"This account belongs to a "
                    f"{user['role'].capitalize()}, not a "
                    f"{expected_role.capitalize()}."
                )
                return

            # ------------------------------------------------
            # SUCCESSFUL LOGIN -> routes to the matching
            # dashboard via dashboard()'s role check below.
            # ------------------------------------------------

            st.session_state.logged_in = True
            st.session_state.page = "dashboard"
            st.session_state.user = user

            reset_chat()

            name = user.get("full_name") or user.get("username") or "User"

            st.success(f"Welcome, {name}!")

            st.rerun()


# ==========================================================
# LOGOUT
# ==========================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.page = "landing"
    st.session_state.user = None

    reset_chat()

    st.rerun()


# ==========================================================
# SIDEBAR
# ==========================================================

# ==========================================================
# SIDEBAR
# ==========================================================

def render_sidebar():

    with st.sidebar:

        # --------------------------------------------------
        # APP BRANDING
        # --------------------------------------------------

        render_html(
            f"""
            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                padding:4px 4px 18px 4px;
            ">
                <div style="
                    width:34px;
                    height:34px;
                    border-radius:9px;
                    background:linear-gradient(135deg,#14b8b0,#0d9488);
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                    {ICON_ROBOT}
                </div>

                <div style="
                    color:#f1f5f9;
                    font-weight:700;
                    font-size:16px;
                ">
                    AI Assistant
                </div>
            </div>
            """
        )

        # --------------------------------------------------
        # NEW CHAT
        # --------------------------------------------------

        if st.button(
            "＋  New Chat",
            use_container_width=True,
            type="primary",
            key="sidebar_new_chat_btn",
        ):
            reset_chat()
            st.rerun()

        # --------------------------------------------------
        # CHAT HISTORY
        # --------------------------------------------------

        render_html(
            """
            <div style="
                color:#7c8aa0;
                font-size:11.5px;
                font-weight:700;
                letter-spacing:0.08em;
                text-transform:uppercase;
                margin:18px 4px 8px 4px;
            ">
                Chat History
            </div>
            """
        )

        user_messages = [
            message.get("content", "")
            for message in st.session_state.messages
            if message.get("role") == "user"
        ]

        # No chat history
        if not user_messages:

            render_html(
                f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:10px;
                    padding:9px 10px;
                    border-radius:9px;
                    color:#a9b6c9;
                    font-size:13.5px;
                ">
                    {ICON_CHAT}

                    <span>
                        No conversations yet
                    </span>
                </div>
                """
            )

        # Existing chat history
        else:

            for message in user_messages[-8:][::-1]:

                preview = (
                    message[:32] + "..."
                    if len(message) > 32
                    else message
                )

                render_html(
                    f"""
                    <div style="
                        display:flex;
                        align-items:center;
                        gap:10px;
                        padding:9px 10px;
                        border-radius:9px;
                        color:#a9b6c9;
                        font-size:13.5px;
                        margin-bottom:2px;
                        white-space:nowrap;
                        overflow:hidden;
                        text-overflow:ellipsis;
                    ">
                        {ICON_CHAT}

                        <span>
                            {preview}
                        </span>
                    </div>
                    """
                )

        # --------------------------------------------------
        # PUSH SETTINGS / LOGOUT TOWARD BOTTOM
        # --------------------------------------------------

        st.markdown(
            "<div style='height:24px'></div>",
            unsafe_allow_html=True,
        )

        st.divider()

        # --------------------------------------------------
        # SETTINGS
        # --------------------------------------------------

        st.button(
            "⚙️  Settings",
            use_container_width=True,
            type="secondary",
            key="sidebar_settings_btn",
            disabled=True,
        )

        # --------------------------------------------------
        # LOGOUT
        # --------------------------------------------------

        if st.button(
            "⎋  Logout",
            use_container_width=True,
            type="secondary",
            key="sidebar_logout_btn",
        ):
            logout()


# ==========================================================
# TOP BAR
# ==========================================================

def render_topbar(user, display_name):

    initials = display_name[:1].upper() if display_name else "U"

    col_title, col_user = st.columns([3, 1])

    with col_title:

        render_html(
            """
            <div>
                <div style="font-size:22px;font-weight:800;color:#f1f5f9;">
                    Enterprise Knowledge Assistant
                </div>
                <div style="font-size:13px;color:#7c8aa0;margin-top:2px;">
                    AI-powered Workplace Automation
                </div>
            </div>
            """
        )

    with col_user:

        render_html(
            f"""
            <div style="display:flex;align-items:center;justify-content:flex-end;gap:12px;">
                <div style="text-align:right;line-height:1.25;">
                    <div style="color:#f1f5f9;font-weight:700;font-size:14px;">
                        {display_name}
                    </div>
                    <div style="color:#7c8aa0;font-size:12.5px;">
                        {user['role'].capitalize()}
                    </div>
                </div>
                <div style="
                    width:38px;height:38px;border-radius:999px;
                    background:linear-gradient(135deg,#14b8b0,#0d9488);
                    color:#ffffff;display:flex;align-items:center;
                    justify-content:center;font-weight:700;font-size:15px;
                ">
                    {initials}
                </div>
            </div>
            """
        )

    st.markdown(
        "<div style='border-bottom:1px solid rgba(255,255,255,0.08);"
        "margin:14px 0 24px 0;'></div>",
        unsafe_allow_html=True,
    )


# ==========================================================
# DASHBOARD  (routes to Manager or Employee workspace by role)
# ==========================================================

def dashboard():

    user = st.session_state.user

    display_name = (
        user.get("full_name") or user.get("username") or "User"
    ).strip()

    render_sidebar()

    render_topbar(user, display_name)

    if user["role"] == "manager":
        workspace_label = "Manager Workspace"
        workspace_icon = "🛠"
    else:
        workspace_label = "Employee Workspace"
        workspace_icon = "🎒"

    render_html(
        f"""
        <div style="font-size:26px;font-weight:800;color:#f1f5f9;margin-bottom:4px;">
            {workspace_icon} {workspace_label}
        </div>
        <div style="color:#a9b6c9;font-size:15px;margin-bottom:26px;">
            Hello <strong style="color:#f1f5f9;">{display_name}</strong>,
            what would you like the Enterprise AI Assistant to help with?
        </div>
        """
    )

   

    # --------------------------------------------------------
    # ROLE-BASED DASHBOARD ROUTING
    #   manager  -> AI Assistant + Document Management
    #   employee -> AI Assistant + My Profile
    # --------------------------------------------------------

    if user["role"] == "manager":

        tab1, tab2 = st.tabs(["💬 AI Assistant", "📂 Document Management"])

        with tab1:
            show_chat_panel()

        with tab2:
            show_manager_panel()

    else:

        tab1, tab2 = st.tabs(["💬 AI Assistant", "👤 My Profile"])

        with tab1:
            show_chat_panel()

        with tab2:
            show_employee_panel()


# ==========================================================
# MAIN APPLICATION
# ==========================================================

def main():

    if st.session_state.logged_in:
        dashboard()
        return

    if st.session_state.page == "landing":
        landing_page()
        return

    if st.session_state.page == "manager_login":
        login_page()
        return

    if st.session_state.page == "employee_login":
        login_page()
        return

    st.session_state.page = "landing"
    st.rerun()


if __name__ == "__main__":
    main()