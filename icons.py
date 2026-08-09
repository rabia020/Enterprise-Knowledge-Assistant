"""
Centralized inline SVG icon set for the Enterprise Knowledge Assistant.

All icons:
- Use a 24x24 viewBox
- Use currentColor so CSS controls their color
- Are returned as complete SVG elements
"""

# ==========================================================
# SVG HELPER
# ==========================================================

def _svg(paths, viewbox="0 0 24 24"):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{viewbox}" fill="none" '
        f'stroke="currentColor" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'{paths}'
        f'</svg>'
    )


# ==========================================================
# BRAND / ROBOT
# ==========================================================

ICON_ROBOT = _svg(
    '<rect x="4" y="7" width="16" height="13" rx="3"/>'
    '<path d="M12 3v4"/>'
    '<circle cx="12" cy="2.5" r="1"/>'
    '<circle cx="9" cy="13" r="1"/>'
    '<circle cx="15" cy="13" r="1"/>'
    '<path d="M8 17h8"/>'
)


# ==========================================================
# USERS / ROLES
# ==========================================================

ICON_MANAGER = _svg(
    '<circle cx="12" cy="8" r="3"/>'
    '<path d="M5 20c.8-3.5 3.2-5 7-5s6.2 1.5 7 5"/>'
    '<path d="M19 5v4M17 7h4"/>'
)

ICON_EMPLOYEE = _svg(
    '<circle cx="12" cy="8" r="3"/>'
    '<path d="M5 20c.8-3.5 3.2-5 7-5s6.2 1.5 7 5"/>'
)

ICON_USER = _svg(
    '<circle cx="12" cy="8" r="3"/>'
    '<path d="M5 21c.8-3.8 3.2-6 7-6s6.2 2.2 7 6"/>'
)


# ==========================================================
# COMMUNICATION
# ==========================================================

ICON_MAIL = _svg(
    '<rect x="3" y="5" width="18" height="14" rx="2"/>'
    '<path d="m3 7 9 6 9-6"/>'
)

ICON_CHAT = _svg(
    '<path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 8.8 8.8 0 0 1-4-.9L4 20l1.5-3.3A7.4 7.4 0 0 1 4 11.5 7.5 7.5 0 0 1 12 4a7.5 7.5 0 0 1 8 7.5Z"/>'
)

ICON_SEARCH = _svg(
    '<circle cx="10.8" cy="10.8" r="6.8"/>'
    '<path d="m16 16 5 5"/>'
)


# ==========================================================
# DOCUMENTS / REPORTS
# ==========================================================

ICON_DOC = _svg(
    '<path d="M6 3h8l4 4v14H6z"/>'
    '<path d="M14 3v5h5"/>'
    '<path d="M9 13h6M9 17h6"/>'
)

ICON_CHART = _svg(
    '<path d="M4 19V9"/>'
    '<path d="M10 19V5"/>'
    '<path d="M16 19v-7"/>'
    '<path d="M22 19H2"/>'
)

ICON_BRIEFCASE = _svg(
    '<rect x="3" y="7" width="18" height="13" rx="2"/>'
    '<path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    '<path d="M3 12h18"/>'
    '<path d="M10 12v2h4v-2"/>'
)


# ==========================================================
# CALENDAR / TASKS
# ==========================================================

ICON_CALENDAR = _svg(
    '<rect x="3" y="5" width="18" height="16" rx="2"/>'
    '<path d="M16 3v4M8 3v4M3 10h18"/>'
    '<path d="M8 14h2M14 14h2M8 18h2"/>'
)

ICON_TASKS = _svg(
    '<rect x="4" y="3" width="16" height="18" rx="2"/>'
    '<path d="m8 8 1.5 1.5L12 7"/>'
    '<path d="M14 9h3"/>'
    '<path d="m8 14 1.5 1.5L12 13"/>'
    '<path d="M14 15h3"/>'
)


# ==========================================================
# SECURITY
# ==========================================================

ICON_SHIELD = _svg(
    '<path d="M12 3 20 6v5c0 5-3.3 8.5-8 10-4.7-1.5-8-5-8-10V6z"/>'
    '<path d="m9 12 2 2 4-4"/>'
)

ICON_LOCK = _svg(
    '<rect x="5" y="10" width="14" height="11" rx="2"/>'
    '<path d="M8 10V7a4 4 0 0 1 8 0v3"/>'
    '<circle cx="12" cy="15.5" r="1"/>'
)

ICON_EYE = _svg(
    '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/>'
    '<circle cx="12" cy="12" r="2.5"/>'
)


# ==========================================================
# NAVIGATION
# ==========================================================

ICON_ARROW_RIGHT = _svg(
    '<path d="M5 12h14"/>'
    '<path d="m13 6 6 6-6 6"/>'
)

ICON_ARROW_LEFT = _svg(
    '<path d="M19 12H5"/>'
    '<path d="m11 18-6-6 6-6"/>'
)

ICON_PLUS = _svg(
    '<path d="M12 5v14M5 12h14"/>'
)

ICON_GEAR = _svg(
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-1.8 1.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6V20h-2.6v-.1a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1-1.8-1.8.1-.1A1.7 1.7 0 0 0 8 15a1.7 1.7 0 0 0-1.6-1H6v-2.6h.1A1.7 1.7 0 0 0 8 10a1.7 1.7 0 0 0-.3-1.9l-.1-.1 1.8-1.8.1.1a1.7 1.7 0 0 0 1.9.3 1.7 1.7 0 0 0 1-1.6V5H15v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1 1.8 1.8-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.1V14h-.1a1.7 1.7 0 0 0-1.6 1Z"/>'
)

ICON_LOGOUT = _svg(
    '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
    '<path d="m16 17 5-5-5-5"/>'
    '<path d="M21 12H9"/>'
)


# ==========================================================
# HTML HELPER
# ==========================================================

def md_html(html):
    """
    Safely normalize multiline HTML before passing it to
    st.markdown(..., unsafe_allow_html=True).

    Streamlit can interpret indented multiline HTML as a
    Markdown code block. Removing per-line indentation and
    joining the HTML into one line prevents that behavior.
    """

    if html is None:
        return ""

    html = str(html).strip()

    return " ".join(
        line.strip()
        for line in html.splitlines()
        if line.strip()
    )