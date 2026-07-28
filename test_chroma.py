import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection("company_docs")

print("Collection Count:", collection.count())