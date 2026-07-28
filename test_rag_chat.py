from rag.retrieve import retrieve_docs

question = input("Question: ")

docs = retrieve_docs(question)

print("\nRetrieved Documents:\n")

for i, doc in enumerate(docs, start=1):
    print("=" * 50)
    print(f"Document {i}")
    print("=" * 50)
    print(doc)