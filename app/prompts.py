SYSTEM_PROMPT = """You are a careful assistant that answers strictly from the provided CONTEXT.
Rules:
* If the context is insufficient or low-confidence, say you cannot answer and suggest rephrasing.
* Otherwise, answer concisely and factually.
* Include a short bullet summary at the end.
* Cite sources by doc_id in brackets, e.g., [Z-123.md].
* Never invent facts not present in CONTEXT.
"""

def render_user_prompt(query: str, contexts: list[dict]) -> str:
    ctx = []
    for i, c in enumerate(contexts, 1):
        ctx.append(f"[CTX {i}] doc_id={c['doc_id']} score={c['score']:.3f}\n{c['text']}\n")
    ctx_block = "\n".join(ctx) if ctx else "(no context)"
    return f"""QUERY:
{query}

CONTEXT:
{ctx_block}

INSTRUCTIONS:
* First, determine if context is sufficient.
* If sufficient, answer; then add bullet summary and cite doc_ids in brackets.
* If insufficient, return the safe fallback."""
