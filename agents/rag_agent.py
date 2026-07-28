# agents/rag_agent.py
from rag.retrieve import retrieve_docs

def rag_agent(state):
    query = state["query"]
    print(f"[RAG Agent] Retrieving docs for: {query}")

    docs = retrieve_docs(query)
    context = "\n\n".join(docs) if docs else "No relevant documents found."

    print(f"[RAG Agent] Retrieved {len(docs)} chunks")

    return {
        "docs":    docs,      # ← only return what changed
        "context": context
    }