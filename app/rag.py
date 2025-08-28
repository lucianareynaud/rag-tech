from __future__ import annotations
import os, json, logging, random
from dataclasses import dataclass
from typing import List, Dict
import numpy as np
from fastembed import TextEmbedding

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

def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    mat = mat.astype("float32", copy=False)
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-12
    return mat / norms

class _Embedder:
    def __init__(self, model_name: str):
        self.model = TextEmbedding(model_name=model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        # FastEmbed retorna um iterável de listas; convertendo para np.array float32
        vecs = list(self.model.embed(texts))
        arr = np.asarray(vecs, dtype="float32")
        return _l2_normalize(arr)

class Indexer:
    """
    Constrói um índice leve:
      - storage/index.npz : matriz [N,D] (vetores L2-normalizados, float32)
      - storage/meta.json : lista [{doc_id, text}]
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
        vecs = self.embedder.encode(texts)  # [N,D] L2-normalizado

        np.savez_compressed(os.path.join(storage_dir, "index.npz"), vectors=vecs)
        meta = [{"doc_id": c.doc_id, "text": c.text} for c in chunks]
        with open(os.path.join(storage_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)

        logger.info("Indexed %d chunks from %d files", len(chunks), len(set(c.doc_id for c in chunks)))

class Retriever:
    """
    Busca por cosseno em NumPy (dot product, pois os vetores já estão L2-normalizados).
    """
    def __init__(self, embedding_model: str, storage_dir: str, top_k: int = 3):
        self.embedder = _Embedder(embedding_model)
        idx_path = os.path.join(storage_dir, "index.npz")
        meta_path = os.path.join(storage_dir, "meta.json")
        if not (os.path.isfile(idx_path) and os.path.isfile(meta_path)):
            raise RuntimeError("Index not found. Run `python -m scripts.ingest`.")
        self.vectors = np.load(idx_path)["vectors"].astype("float32")  # [N,D], L2-normalized
        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.top_k = top_k

    def search(self, query: str, k: int | None = None) -> List[Dict]:
        k = k or self.top_k
        q_vec = self.embedder.encode([query])[0]  # [D], L2-normalized
        # Similaridade por cosseno = produto interno (já normalizado)
        scores = self.vectors @ q_vec  # [N]
        idxs = np.argpartition(-scores, kth=min(k, len(scores)-1))[:k]
        # Ordenação estável por (-score, doc_id)
        pairs = sorted(
            ((float(scores[i]), i) for i in idxs),
            key=lambda x: (-x[0], self.meta[x[1]]["doc_id"])
        )
        hits: List[Dict] = []
        for score, i in pairs:
            m = self.meta[i]
            hits.append({"doc_id": m["doc_id"], "text": m["text"], "score": float(score)})
        return hits
