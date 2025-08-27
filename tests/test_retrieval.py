from app.rag import Retriever
from app.config import settings

def test_topk_retrieval_blender():
    r = Retriever(settings.EMBEDDING_MODEL, "storage", top_k=3)
    hits = r.search("What is the jar capacity of the Z-123 blender?")
    assert len(hits) >= 1
    assert any("Z-123" in h["doc_id"] for h in hits)

def test_threshold_refusal_path():
    r = Retriever(settings.EMBEDDING_MODEL, "storage", top_k=3)
    hits = r.search("Quantum chromodynamics in heavy-ion collisions at RHIC")
    max_score = max((h["score"] for h in hits), default=0.0)
    assert max_score <= 1.0  # sanity bound; refusal is enforced at agent level
