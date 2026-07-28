import streamlit as st
from auth import login
import requests
import os

# -----------------------------
# CONFIG
# -----------------------------
N8N_WEBHOOK = "http://localhost:5678/webhook/copilot"
UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="AI Copilot", layout="wide")

st.title("🤝 Your Personal Assistant")
st.subheader("AI Copilot for Chat + Company Knowledge + Automation")

# -----------------------------
# ROLE SYSTEM
# -----------------------------
st.sidebar.header("🔐 Access Control")

role = st.sidebar.selectbox(
    "Select Role",
    ["Employee", "Manager"]
)

# Manager can also act as employee
mode = st.sidebar.radio(
    "Mode",
    ["Chat Mode", "Document Upload Mode"] if role == "Manager" else ["Chat Mode"]
)

st.sidebar.markdown("---")
st.sidebar.info("Managers can upload documents + use chat. Employees only use chat.")

# -----------------------------
# SESSION STATE
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# DOCUMENT UPLOAD (MANAGER ONLY)
# -----------------------------
if role == "Manager" and mode == "Document Upload Mode":
    st.subheader("📂 Upload Company Documents (RAG Knowledge Base)")

    uploaded_file = st.file_uploader(
        "Upload PDF / TXT / DOCX",
        type=["pdf", "txt", "docx"]
    )

    if uploaded_file:
        file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File saved: {uploaded_file.name}")

        # Trigger backend ingestion (IMPORTANT: your RAG pipeline should run here)
        try:
            ingest_response = requests.post(
                "http://localhost:5678/webhook/ingest",
                json={"file_path": file_path},
                timeout=120
            )

            if ingest_response.status_code == 200:
                st.success("Document successfully indexed into RAG system")
            else:
                st.warning(f"Ingestion response: {ingest_response.text}")

        except Exception as e:
            st.error(f"Failed to send file to RAG pipeline: {str(e)}")

# -----------------------------
# CHAT MODE
# -----------------------------
st.subheader("💬 Chat with your Assistant")

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input box
user_message = st.chat_input("Ask something...")

if user_message:
    # show user message
    with st.chat_message("user"):
        st.markdown(user_message)

    st.session_state.messages.append(
        {"role": "user", "content": user_message}
    )

    # send to backend (n8n / agent)
    try:
        with st.spinner("Thinking..."):

            response = requests.post(
                N8N_WEBHOOK,
                json={
                    "message": user_message,
                    "role": role
                },
                timeout=120
            )

        # DEBUG (you can remove later)
        st.info(f"DEBUG | status: {response.status_code}")

        if response.text.strip():

            try:
                data = response.json()

                if isinstance(data, list):
                    data = data[0]
                elif not isinstance(data, dict):
                    data = {}

                ai_response = (
                    data.get("output")
                    or data.get("text")
                    or data.get("message")
                    or data.get("reply")
                    or str(data)
                )

            except Exception:
                ai_response = response.text

        else:
            ai_response = "⚠️ Empty response from backend"

    except requests.exceptions.Timeout:
        ai_response = "⏱️ Request timed out"
    except requests.exceptions.ConnectionError:
        ai_response = "❌ Backend not reachable (n8n not running)"
    except Exception as e:
        ai_response = f"❌ Error: {str(e)}"

    # show assistant response
    with st.chat_message("assistant"):
        st.markdown(ai_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": ai_response}
    )