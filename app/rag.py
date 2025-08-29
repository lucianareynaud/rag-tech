from __future__ import annotations
import os, json, logging, random
from dataclasses import dataclass
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag")

SEED = 0
random.seed(SEED)
np.random.seed(SEED)

@dataclass
class Chunk:
    doc_id: str
    text: str

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 80) -> List[str]:
    text = " ".join(text.split())
    out: List[str] = []
    i = 0
    while i < len(text):
        out.append(text[i:i+chunk_size])
        i += max(1, chunk_size - overlap)
    return [c for c in out if c.strip()]

class _Embedder:
    def __init__(self, model_name: str):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")

    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        # For E5 models, adding appropriate prefixes improves performance
        if is_query:
            prefixed_texts = [f"query: {text}" for text in texts]
        else:
            prefixed_texts = [f"passage: {text}" for text in texts]
        
        vecs = self.model.encode(prefixed_texts, convert_to_numpy=True, normalize_embeddings=True)
        return vecs.astype("float32")

class Indexer:
    """
    Builds a lightweight index:
      - storage/index.npz : matrix [N,D] (L2-normalized vectors, float32)
      - storage/meta.json : list [{doc_id, text}]
    """
    def __init__(self, embedding_model: str):
        self.embedder = _Embedder(embedding_model)

    def build(self, input_dir: str, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        chunks: List[Chunk] = []
        for fname in sorted(os.listdir(input_dir)):
            if not fname.endswith((".md", ".txt")):
                continue
            with open(os.path.join(input_dir, fname), "r", encoding="utf-8") as f:
                txt = f.read()
            for piece in chunk_text(txt):
                chunks.append(Chunk(doc_id=fname, text=piece))

        if not chunks:
            raise RuntimeError("No texts found to index.")

        texts = [c.text for c in chunks]
        vecs = self.embedder.encode(texts)  # [N,D] already normalized by sentence-transformers

        np.savez_compressed(os.path.join(storage_dir, "index.npz"), vectors=vecs)
        meta = [{"doc_id": c.doc_id, "text": c.text} for c in chunks]
        with open(os.path.join(storage_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)

        logger.info("Indexed %d chunks from %d files", len(chunks), len(set(c.doc_id for c in chunks)))

class Retriever:
    """
    Cosine search in NumPy (dot product, since vectors are already L2-normalized).
    """
    def __init__(self, embedding_model: str, storage_dir: str, top_k: int = 3):
        self.embedder = _Embedder(embedding_model)
        idx_path = os.path.join(storage_dir, "index.npz")
        meta_path = os.path.join(storage_dir, "meta.json")
        if not (os.path.isfile(idx_path) and os.path.isfile(meta_path)):
            raise RuntimeError("Index not found. Run `python -m scripts.ingest`.")
        self.vectors = np.load(idx_path)["vectors"].astype("float32")  # [N,D], normalized
        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.top_k = top_k

    def search(self, query: str, k: int | None = None) -> List[Dict]:
        k = k or self.top_k
        q_vec = self.embedder.encode([query], is_query=True)[0]  # [D], normalized
        # Cosine similarity = dot product (already normalized)
        scores = self.vectors @ q_vec  # [N]
        idxs = np.argpartition(-scores, kth=min(k, len(scores)-1))[:k]
        # Stable sorting by (-score, doc_id)
        pairs = sorted(
            ((float(scores[i]), i) for i in idxs),
            key=lambda x: (-x[0], self.meta[x[1]]["doc_id"])
        )
        hits: List[Dict] = []
        for score, i in pairs:
            m = self.meta[i]
            hits.append({"doc_id": m["doc_id"], "text": m["text"], "score": float(score)})
        return hits
