from sentence_transformers import SentenceTransformer
import chromadb
from pypdf import PdfReader
import os

# Embedding model
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

# ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("company_docs")


def load_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def chunk_text(text, chunk_size=500, overlap=100):

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunks.append(text[start:end])

        start = end - overlap

    return chunks


# Fix: use filename in the ID


def ingest_pdf(file_path):
    text   = load_pdf(file_path)
    chunks = chunk_text(text)
    base   = os.path.basename(file_path).replace(".pdf", "")  # ← ADD

    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()
        collection.add(
            ids=[f"{base}_chunk_{i}"],          # ← unique per file
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{ 
                "source": os.path.basename(file_path),
                "chunk": i
                }]
        )
    print(f"Ingested {len(chunks)} chunks from {file_path}")

if __name__ == "__main__":
    ingest_pdf("documents/company_policy.pdf")