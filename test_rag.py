#from agents.rag_agent import search
from agents.rag_agent import rag_agent

# fake input state
state = {
    "query": "relocation policy",
    "emails": []
}

result = rag_agent(state)

print("\n--- RAW OUTPUT STATE ---\n")
print(result)

print("\n--- CONTEXT ONLY ---\n")
print(result["context"])