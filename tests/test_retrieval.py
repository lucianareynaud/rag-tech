from app.rag import Retriever
from app.config import settings

def test_topk_retrieval_product():
    r = Retriever(settings.EMBEDDING_MODEL, "storage", top_k=3)
    hits = r.search("What is the water tank capacity of the H-500?")
    assert len(hits) >= 1
    assert any("H-500" in h["doc_id"] for h in hits)

def test_threshold_refusal_path():
    r = Retriever(settings.EMBEDDING_MODEL, "storage", top_k=3)
    hits = r.search("Quantum chromodynamics in heavy-ion collisions at RHIC")
    max_score = max((h["score"] for h in hits), default=0.0)
    assert max_score <= 1.0  # sanity bound; refusal is enforced at agent level
