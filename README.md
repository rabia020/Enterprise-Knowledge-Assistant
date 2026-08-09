# Enterprise AI Knowledge Worker Copilot

An AI-powered enterprise copilot designed to automate workplace tasks, retrieve organizational knowledge, manage emails and calendars, communicate through Slack, and assist employees with research and complaint processing.

The system uses a multi-agent architecture built with **Python, LangGraph, LangChain, Groq LLMs, RAG, ChromaDB, PostgreSQL, and n8n-based workflow automation**.

It combines intelligent intent classification, task planning, specialized AI agents, Retrieval-Augmented Generation (RAG), human-in-the-loop approval, external tool integration, and persistent memory into a single enterprise assistant.

---

## 🚀 Key Features

- 🤖 Multi-agent AI architecture
- 🧠 Supervisor-based intelligent request routing
- 📋 Automatic task planning
- 📚 Enterprise document question answering using RAG
- 📧 Email reading, drafting, sending, and broadcast communication
- 📅 Google Calendar event creation and calendar lookup
- 💬 Slack messaging and notifications
- 🔎 General research and information analysis
- 👤 Human-in-the-loop approval for sensitive actions
- 🧠 Persistent conversation and task memory
- 🔐 Role-based enterprise interface
- 🔄 n8n workflow automation
- 🗃️ ChromaDB vector database for document retrieval
- 🧩 Modular specialist agents
- ⚡ Groq-powered LLM inference
- 🌐 Streamlit-based user interface

---

# 🏗️ System Architecture

The system follows a supervisor-based multi-agent architecture.

```text
                         ┌──────────────────────┐
                         │        USER          │
                         │  Employee / Manager  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Streamlit UI      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │    Memory Load       │
                         │   Previous Context   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   SUPERVISOR AGENT   │
                         │ Intent Classification│
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       PLANNER        │
                         │ Task Planning        │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        ┌───────────┐        ┌─────────────┐       ┌─────────────┐
        │ Email     │        │ RAG / Docs  │       │ Research    │
        │ Agents    │        │ Agent       │       │ Agent       │
        └─────┬─────┘        └──────┬──────┘       └──────┬──────┘
              │                     │                     │
              ▼                     ▼                     ▼
        ┌───────────┐        ┌─────────────┐       ┌─────────────┐
        │ Calendar  │        │ Slack       │       │ Complaint   │
        │ Agent     │        │ Agent       │       │ Agent       │
        └─────┬─────┘        └──────┬──────┘       └──────┬──────┘
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │   ACTION REQUIRED?     │
                       └───────────┬────────────┘
                                   │
                         ┌─────────┴─────────┐
                         │                   │
                        YES                  NO
                         │                   │
                         ▼                   ▼
                ┌─────────────────┐   ┌───────────────┐
                │  HUMAN REVIEW   │   │ AUTO COMPLETE │
                │ Approve / Reject│   │ Read-only     │
                └────────┬────────┘   └───────┬───────┘
                         │                    │
                    ┌────┴────┐              │
                    │         │              │
                 APPROVE    REJECT            │
                    │         │              │
                    ▼         ▼              │
             ┌────────────┐   END            │
             │   ACTION   │                  │
             │ EXECUTION  │                  │
             └─────┬──────┘                  │
                   │                         │
                   ▼                         │
             ┌──────────────┐                │
             │ Memory Save  │◄───────────────┘
             └──────┬───────┘
                    │
                    ▼
                   END

                   