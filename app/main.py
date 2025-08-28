from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from app.schemas import QueryRequest, QueryResponse
from app.agents import run_pipeline
import json
import os

app = FastAPI(title="rag-tech", version="1.0.0")

# Serve static files (frontend)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

class PrettyJSONResponse(Response):
    media_type = "application/json"
    
    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False, indent=2).encode("utf-8")

@app.get("/")
def root():
    """Serve the frontend UI"""
    static_index = os.path.join(static_dir, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    else:
        # Fallback to API info if no frontend
        return JSONResponse({
            "message": "rag-tech API", 
            "endpoints": ["/health", "/query", "/docs"],
            "frontend": "Frontend not found. Add static/index.html to enable UI."
        })

@app.get("/health", response_class=PrettyJSONResponse)
def health():
    return {"status": "ok"}

@app.post("/query", response_class=PrettyJSONResponse)
def query(req: QueryRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=422, detail="query must be a non-empty string")
    result = run_pipeline(req.query.strip())
    return result
