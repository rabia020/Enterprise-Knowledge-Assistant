from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("company_docs")


def retrieve_docs(query: str, top_k: int = 3):

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Return only the retrieved document texts
    if results["documents"] and len(results["documents"]) > 0:
        return results["documents"][0]

    return []


if __name__ == "__main__":

    query = input("Question: ")

    docs = retrieve_docs(query)

    print("\nRetrieved Documents:\n")

    for i, doc in enumerate(docs, start=1):
        print("=" * 60)
        print(f"Chunk {i}")
        print("=" * 60)
        print(doc)