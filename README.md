# zubale-rag-minimal

Minimal, deterministic RAG + 2-agent LangGraph service with FastAPI.

## Why this design

* **Determinism & Simplicity:** FAISS (IP on L2-normalized vectors) + MiniLM for fast, stable retrieval.
* **Safety:** Score threshold → explicit fallback to avoid hallucinations.
* **Portability:** Runs fully offline via `LLM_PROVIDER=stub`; optionally calls OpenAI if keys provided.
* **Clarity:** Two explicit agents (Retriever → Responder) in LangGraph.

## Quickstart

```bash
./demo_local.sh
# Opens: http://localhost:8000
```

### Manual setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.ingest
uvicorn app.main:app --reload
```

### Docker

```bash
docker build -t zubale-rag .
docker run --rm -p 8000:8000 --env-file .env zubale-rag
```

## API

`POST /query`

```json
{ "user_id": "luciana", "query": "Warranty of Z-123 blender?" }
```

Response:

```json
{
  "answer": "...",
  "sources": [{"doc_id":"Z-123.md","score":0.81}],
  "meta": {"top_k":3,"threshold":0.55,"latency_ms":123}
}
```

## Testing

```bash
# Run tests
pytest -q

# Test API directly
curl -X POST http://localhost:8000/query \
 -H 'Content-Type: application/json' \
 -d '{"query":"What is the jar capacity of Z-123 blender?"}'
```
