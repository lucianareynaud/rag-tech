SYSTEM_PROMPT = """You are a helpful assistant. Answer questions based only on the provided information. If the information is not available, say so clearly."""

def render_user_prompt(query: str, contexts: list[dict]) -> str:
    # Simplify the format for better model comprehension
    ctx_texts = []
    for i, c in enumerate(contexts, 1):
        ctx_texts.append(f"Source {i} ({c['doc_id']}): {c['text']}")
    
    context_block = "\n\n".join(ctx_texts) if ctx_texts else "No information available."
    
    return f"""Information available:
{context_block}

Question: {query}

Answer:"""
