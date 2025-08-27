from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.schemas import QueryRequest, QueryResponse
from app.agents import run_pipeline

app = FastAPI(title="Zubale Minimal RAG", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Zubale Minimal RAG API", "endpoints": ["/health", "/query", "/docs"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=422, detail="query must be a non-empty string")
    result = run_pipeline(req.query.strip())
    return JSONResponse(content=result)
