
import json
import os
from app.vector_store import VectorStore, DocChunk
import numpy as np, faiss

CRAWLED_FILE = "data/crawled_docs/netskope_docs.json"
VECTOR_STORE_DIR = "data/vector_store"

CHUNK_SIZE = 800
OVERLAP = 150

def chunk_text(text: str, chunk_size: int, overlap: int):
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        yield text[start:end]
        if end == n:
            break
        start = max(0, end - overlap)

def ingest():
    with open(CRAWLED_FILE, "r", encoding="utf-8") as f:
        pages = json.load(f)

    vs = VectorStore(store_dir=VECTOR_STORE_DIR)

    chunks = []
    for page in pages:
        for i, chunk in enumerate(chunk_text(page["text"], CHUNK_SIZE, OVERLAP)):
            chunks.append(
                DocChunk(
                    doc_id=f"{page['url']}#chunk{i}",
                    text=f"{page['title']}\n{chunk}"
                )
            )

    vs.chunks = chunks
    vs.build_from_dir = None  # safety
    vs.index = None

    embeddings = vs.model.encode([c.text for c in chunks], normalize_embeddings=True)
    
    embeddings = np.array(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    vs.index = faiss.IndexFlatIP(dim)
    vs.index.add(embeddings)

    vs.save()
    print(f"Ingested {len(chunks)} chunks into FAISS")

if __name__ == "__main__":
    ingest()

