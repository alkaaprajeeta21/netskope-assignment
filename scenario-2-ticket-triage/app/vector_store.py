import os
import json
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import time

@dataclass
class DocChunk:
    doc_id: str
    text: str

class VectorStore:
    def __init__(self, store_dir: str, model_name: str = "all-MiniLM-L6-v2"):
        self.store_dir = store_dir
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks: List[DocChunk] = []

    def _paths(self):
        return (
            os.path.join(self.store_dir, "faiss.index"),
            os.path.join(self.store_dir, "chunks.json"),
            os.path.join(self.store_dir, "meta.json"),
        )

    def load(self) -> bool:
        idx_path, chunks_path, meta_path = self._paths()
        if not (os.path.exists(idx_path) and os.path.exists(chunks_path) and os.path.exists(meta_path)):
            return False

        self.index = faiss.read_index(idx_path)
        with open(chunks_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.chunks = [DocChunk(**x) for x in raw]
        return True

    def save(self):
        os.makedirs(self.store_dir, exist_ok=True)
        idx_path, chunks_path, meta_path = self._paths()
        faiss.write_index(self.index, idx_path)
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump([c.__dict__ for c in self.chunks], f, ensure_ascii=False, indent=2)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"model_name": self.model_name, "chunks": len(self.chunks)}, f, indent=2)

    def build_from_dir(self, docs_dir: str, chunk_size: int = 800, overlap: int = 120):
        self.chunks = []
        for name in sorted(os.listdir(docs_dir)):
            path = os.path.join(docs_dir, name)
            if not os.path.isfile(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            for i, chunk in enumerate(_chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
                self.chunks.append(DocChunk(doc_id=f"{name}#chunk{i}", text=chunk))

        embs = self.model.encode([c.text for c in self.chunks], normalize_embeddings=True)
        embs = np.array(embs, dtype=np.float32)
        dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embs)

    def query(self, q: str, k: int = 4) -> List[Tuple[DocChunk, float]]:
        if self.index is None or not self.chunks:
            return []
        q_emb = self.model.encode([q], normalize_embeddings=True)
        q_emb = np.array(q_emb, dtype=np.float32)
        scores, idxs = self.index.search(q_emb, k)
        out = []
        for rank, (i, s) in enumerate(zip(idxs[0], scores[0]), start=1):
            if i < 0 or i >= len(self.chunks):
                continue
            out.append((self.chunks[i], float(s)))
        return out

def _chunk_text(text: str, chunk_size: int, overlap: int):
    if chunk_size <= 0:
        yield text
        return
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        yield text[start:end]
        if end == n:
            break
        start = max(0, end - overlap)
