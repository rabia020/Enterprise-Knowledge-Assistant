import requests
import uuid

# ==========================================================
# N8N CONFIG
# ==========================================================
#
# N8N_ACTION_URL → deterministic workflow: Webhook -> Switch
#                   (on `action`) -> real Gmail/Slack/Calendar/
#                   Jira node -> a TOOL-FREE narration LLM node
#                   (writes one confirmation sentence, cannot
#                   call anything) -> Respond to Webhook.
#                   The execution itself is never decided by an
#                   LLM — only the confirmation wording is.
#
# N8N_AGENT_URL  → your existing AI Agent workflow (Mistral +
#                   CompanyKnowledge / tool nodes), used only
#                   for open-ended conversational RAG queries.
# ==========================================================

N8N_BASE = "http://localhost:5678/webhook"

# --------------------------------------------------------
# TEMPORARY: pointing both at the same webhook because the
# separate deterministic "copilot-actions" workflow discussed
# earlier was never built in n8n — posting to it 404'd
# ("not registered"). Both action calls and RAG queries now go
# through your existing /copilot AI Agent workflow, same as
# before this whole discussion started.
#
# Trade-off to keep in mind: this means the AI Agent itself
# decides how to interpret each action call (e.g. it could
# re-parse "create_calendar_event" args differently than what
# the human approved), rather than executing exactly and only
# what was approved. If you want that guarantee back, build
# the Webhook -> Switch(on `action`) -> real Gmail/Slack/
# Calendar/Jira node workflow at a NEW path (e.g.
# /copilot-actions) and change N8N_ACTION_URL back to point at
# it — I can help wire that up whenever you're ready.
# --------------------------------------------------------

N8N_ACTION_URL = f"{N8N_BASE}/copilot"
N8N_AGENT_URL = f"{N8N_BASE}/copilot"


# ----------------------------
# INTERNAL POST HELPER
# ----------------------------
def _post(url: str, payload: dict, timeout: int = 15):
    """
    Internal helper — all tools use this.
    `url` selects which n8n webhook the request goes to.
    """

    payload["request_id"] = str(uuid.uuid4())

    try:
        print(f"[n8n_client] POST {url} — action: {payload.get('action')}")
        response = requests.post(url, json=payload, timeout=timeout)

        print("Status Code:", response.status_code)
        print("Content-Type:", response.headers.get("Content-Type"))
        print("Raw Response:")
        print(response.text)

        response.raise_for_status()

        try:
            return response.json()
        except Exception as e:
            print("[n8n_client] JSON Parse Error:", e)
            return None

    except requests.exceptions.ConnectionError:
        print("[n8n_client] ❌ n8n not reachable (check port 5678)")
    except requests.exceptions.Timeout:
        print("[n8n_client] ❌ n8n request timed out")
    except requests.exceptions.HTTPError as e:
        print(f"[n8n_client] ❌ HTTP error {e.response.status_code}")
        print(e.response.text[:300])
    except Exception as e:
        print(f"[n8n_client] ❌ Unexpected error: {e}")

    return None


def _extract(data, success_key="success"):
    """
    Common shape returned by the action webhook after the
    narration node:
        {"success": true/false, "message": "<natural language>", "raw": {...}}
    Falls back gracefully if the workflow hasn't been updated
    to include "message" yet.
    """

    if not isinstance(data, dict):
        return False, "", {}

    success = bool(data.get(success_key, False))
    message = data.get("message", "")
    raw = data.get("raw", data)

    return success, message, raw


# =========================================================
# 1. GET EMAILS
# =========================================================
def get_emails(label: str = "complaints", days: int = 30) -> list:
    data = _post(N8N_ACTION_URL, {
        "action": "get_emails",
        "label": label,
        "days": days,
    })

    if data is None:
        return []

    # get_emails returns a list of emails directly (in "raw"
    # or top-level "emails"), not a simple success/message pair
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if "emails" in data:
            return data.get("emails", [])
        raw = data.get("raw", {})
        if isinstance(raw, dict):
            return raw.get("emails", [])
        if isinstance(raw, list):
            return raw

    return []


# =========================================================
# 2. SEND EMAIL
# =========================================================
def send_email(to: str, subject: str, body: str) -> bool:
    """
    Returns True/False as before (unchanged call signature so
    existing callers in email_agent.py / executor.py keep working).
    Use send_email_verbose() if you also want the AI-narrated
    confirmation sentence.
    """

    success, _message, _raw = _extract(_post(N8N_ACTION_URL, {
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "chatInput": (
            f"Send an email to {to} with subject '{subject}' "
            f"and body: {body}"
        ),
    }))

    return success


def send_email_verbose(to: str, subject: str, body: str) -> dict:
    """
    Same call, but returns the full result including the
    natural-language confirmation from the narration node, e.g.:
        {"success": True, "message": "Your email to ... has been sent."}
    """

    data = _post(N8N_ACTION_URL, {
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "chatInput": (
            f"Send an email to {to} with subject '{subject}' "
            f"and body: {body}"
        ),
    })

    success, message, raw = _extract(data)

    return {"success": success, "message": message, "raw": raw}


# =========================================================
# 3. CREATE CALENDAR EVENT
# =========================================================
def create_calendar_event(title: str, date: str, description: str = "") -> dict:
    data = _post(N8N_ACTION_URL, {
        "action": "create_calendar_event",
        "title": title,
        "date": date,
        "description": description,
        "chatInput": (
            f"Create a calendar event titled '{title}' "
            f"at {date or 'the time specified'}"
            + (f", description: {description}" if description else "")
        ),
    })

    success, message, raw = _extract(data)

    result = raw if isinstance(raw, dict) else {}
    result.setdefault("success", success)
    result.setdefault("message", message)

    return result


# =========================================================
# 4. SEND SLACK MESSAGE
# =========================================================
def send_slack_message(channel: str, message: str) -> bool:
    success, _msg, _raw = _extract(_post(N8N_ACTION_URL, {
        "action": "send_slack",
        "channel": channel,
        "message": message,
        "chatInput": f"Send a Slack message to {channel}: {message}",
    }))

    return success


def send_slack_message_verbose(channel: str, message: str) -> dict:
    data = _post(N8N_ACTION_URL, {
        "action": "send_slack",
        "channel": channel,
        "message": message,
        "chatInput": f"Send a Slack message to {channel}: {message}",
    })

    success, msg, raw = _extract(data)

    return {"success": success, "message": msg, "raw": raw}


# =========================================================
# 5. CREATE JIRA TICKET
# =========================================================
def create_jira_ticket(summary: str, description: str, priority: str = "Medium") -> dict:
    data = _post(N8N_ACTION_URL, {
        "action": "create_jira_ticket",
        "summary": summary,
        "description": description,
        "priority": priority,
    })

    success, message, raw = _extract(data)

    result = raw if isinstance(raw, dict) else {}
    result.setdefault("success", success)
    result.setdefault("message", message)

    return result


# =========================================================
# 5b. UPDATE JIRA STATUS
# =========================================================
def update_jira_status(issue_key: str, status: str) -> dict:
    data = _post(N8N_ACTION_URL, {
        "action": "update_jira_status",
        "issue_key": issue_key,
        "status": status,
    })

    success, message, raw = _extract(data)

    result = raw if isinstance(raw, dict) else {}
    result.setdefault("success", success)
    result.setdefault("message", message)

    return result


# =========================================================
# 6. RAG QUERY  (AGENTIC — the one place the AI Agent
#    workflow's own tool-calling belongs)
# =========================================================
def send_rag_query(query: str):
    data = _post(N8N_AGENT_URL, {
        "chatInput": query,
    })

    if data is None:
        return {
            "status": "failed",
            "error": "No response from n8n"
        }

    return data


# =========================================================
# 7. CONNECTION TEST
# =========================================================
def test_connection() -> bool:
    try:
        response = requests.get(
            "http://localhost:5678/healthz",
            timeout=5
        )

        ok = response.status_code == 200

        status_label = "✅ OK" if ok else "❌ FAIL"

        print(f"[n8n_client] n8n health check: {status_label}")

        return ok

    except Exception:
        print("[n8n_client] ❌ n8n not reachable")
        return False


# =========================================================
# MANUAL TEST BLOCK
# =========================================================
if __name__ == "__main__":

    print("Testing n8n connection...")
    test_connection()

    print("\nTesting email (verbose)...")
    print(send_email_verbose("test@example.com", "Hello", "Test email"))

    print("\nTesting Slack (verbose)...")
    print(send_slack_message_verbose("#general", "Hello from system"))

    print("\nTesting Calendar...")
    print(create_calendar_event("Meeting", "2026-01-01"))

    print("\nTesting Jira...")
    print(create_jira_ticket("Bug Fix", "Fix login issue"))

    print("\nTesting RAG (via AI Agent)...")
    print(send_rag_query("What are our top customer complaints this month?"))