from __future__ import annotations
from typing import TypedDict, List, Dict, Any
import time
import logging
from langgraph.graph import StateGraph, START, END

from app.config import settings
from app.rag import Retriever
from app.llm import LLM
from app.prompts import SYSTEM_PROMPT, render_user_prompt

logger = logging.getLogger("agents")

class GraphState(TypedDict, total=False):
    query: str
    contexts: List[Dict[str, Any]]
    answer: str
    sources: List[Dict[str, Any]]
    meta: Dict[str, Any]

retriever = Retriever(settings.EMBEDDING_MODEL, "storage", top_k=settings.TOP_K)
llm = LLM()

def retriever_agent(state: GraphState) -> GraphState:
    q = state["query"]
    t0 = time.time()
    hits = retriever.search(q, settings.TOP_K)
    for h in hits:
        logger.info("hit doc_id=%s score=%.3f", h["doc_id"], h["score"])
    elapsed = int((time.time() - t0) * 1000)
    state["contexts"] = hits
    state["meta"] = {"top_k": settings.TOP_K, "threshold": settings.THRESHOLD, "latency_ms": elapsed}
    return state

def responder_agent(state: GraphState) -> GraphState:
    hits = state.get("contexts", [])
    max_score = max((h["score"] for h in hits), default=0.0)
    if max_score < settings.THRESHOLD or not hits:
        state["answer"] = ("I couldn't find sufficiently reliable information in the catalog to answer that. "
                          "Please rephrase or try a different query.")
        state["sources"] = []
        return state
    user_prompt = render_user_prompt(state["query"], hits)
    answer = llm.generate(SYSTEM_PROMPT, user_prompt)
    state["answer"] = answer
    state["sources"] = [{"doc_id": h["doc_id"], "score": round(h["score"], 3), "text": h["text"]} for h in hits]
    return state

def build_graph():
    g = StateGraph(GraphState)
    g.add_node("retrieve", retriever_agent)
    g.add_node("respond", responder_agent)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "respond")
    g.add_edge("respond", END)
    return g.compile()

graph = build_graph()

def run_pipeline(query: str) -> Dict[str, Any]:
    init: GraphState = {"query": query}
    out: GraphState = graph.invoke(init)
    return {"answer": out["answer"], "sources": out.get("sources", []), "meta": out.get("meta", {})}
