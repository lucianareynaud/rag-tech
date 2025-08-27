from __future__ import annotations
import os, pickle, logging, random
from dataclasses import dataclass
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

# Try to import faiss, fallback to numpy-based similarity if not available
try:
    import faiss
    FAISS_AVAILABLE = True
    logger = logging.getLogger("rag")
    logger.info("Using FAISS for vector similarity")
except ImportError:
    FAISS_AVAILABLE = False
    from sklearn.metrics.pairwise import cosine_similarity
    logger = logging.getLogger("rag")
    logger.warning("FAISS not available, using sklearn cosine similarity fallback")

logging.basicConfig(level=logging.INFO)

SEED = 0
random.seed(SEED)
np.random.seed(SEED)

@dataclass
class Chunk:
    doc_id: str
    text: str

# Function removed - normalization handled directly by sentence-transformers with normalize_embeddings=True

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
    text = " ".join(text.split())
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+chunk_size]
        chunks.append(chunk)
        i += chunk_size - overlap
        if i >= len(text):
            break
    return chunks

class Indexer:
    def __init__(self, embedding_model: str):
        self.model = SentenceTransformer(embedding_model)

    def build(self, input_dir: str, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        chunks: List[Chunk] = []
        for fname in sorted(os.listdir(input_dir)):
            if not fname.endswith((".md", ".txt")):
                continue
            with open(os.path.join(input_dir, fname), "r", encoding="utf-8") as f:
                txt = f.read()
            for piece in chunk_text(txt):
                if not piece.strip():
                    continue
                chunks.append(Chunk(doc_id=fname, text=piece))

        texts = [c.text for c in chunks]
        if not texts:
            raise RuntimeError("No texts found to index.")
        embeddings = self.model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True
        ).astype("float32")

        meta = [{"doc_id": c.doc_id, "text": c.text} for c in chunks]

        if FAISS_AVAILABLE:
            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)
            faiss.write_index(index, os.path.join(storage_dir, "faiss.index"))
        else:
            # Store embeddings directly for numpy-based similarity
            np.save(os.path.join(storage_dir, "embeddings.npy"), embeddings)

        with open(os.path.join(storage_dir, "meta.pkl"), "wb") as f:
            pickle.dump(meta, f)

        logger.info("Indexed %d chunks from %d files", len(chunks), len(set(c.doc_id for c in chunks)))

class Retriever:
    def __init__(self, embedding_model: str, storage_dir: str, top_k: int = 3):
        self.model = SentenceTransformer(embedding_model)
        self.storage_dir = storage_dir
        with open(os.path.join(storage_dir, "meta.pkl"), "rb") as f:
            self.meta = pickle.load(f)
        self.top_k = top_k
        
        if FAISS_AVAILABLE:
            self.index = faiss.read_index(os.path.join(storage_dir, "faiss.index"))
            self.embeddings = None
        else:
            self.index = None
            self.embeddings = np.load(os.path.join(storage_dir, "embeddings.npy"))

    def search(self, query: str, k: int | None = None) -> List[Dict]:
        k = k or self.top_k
        q = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        
        if FAISS_AVAILABLE:
            scores, idxs = self.index.search(q, k)
            # Stable tie-breaker by doc_id
            pairs = sorted(
                zip(scores[0], idxs[0]),
                key=lambda x: (-x[0], self.meta[x[1]]["doc_id"] if x[1] != -1 else "")
            )
            hits = []
            for score, idx in pairs:
                if idx == -1:
                    continue
                m = self.meta[idx]
                hits.append({"doc_id": m["doc_id"], "text": m["text"], "score": float(score)})
        else:
            # Fallback: use sklearn cosine similarity
            similarities = cosine_similarity(q.reshape(1, -1), self.embeddings)[0]
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:k]
            # Stable tie-breaker by doc_id
            pairs = [(similarities[idx], idx) for idx in top_indices]
            pairs = sorted(pairs, key=lambda x: (-x[0], self.meta[x[1]]["doc_id"]))
            
            hits = []
            for score, idx in pairs:
                m = self.meta[idx]
                hits.append({"doc_id": m["doc_id"], "text": m["text"], "score": float(score)})
        
        return hits
