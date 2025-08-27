from __future__ import annotations
from app.config import settings

class LLM:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.MODEL
        self._client = None
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            from openai import OpenAI
            kwargs = {}
            if settings.OPENAI_BASE_URL:
                kwargs["base_url"] = settings.OPENAI_BASE_URL
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY, **kwargs)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider != "openai" or self._client is None:
            # Stub: deterministic, extractive synthesis from context.
            lines = user_prompt.splitlines()
            ctx_lines = [ln for ln in lines if ln.startswith("[CTX ")]
            if not ctx_lines:
                return ("I couldn't find sufficiently reliable information in the catalog to answer that. "
                        "Please rephrase or try a different query.")
            doc_ids = []
            for ln in ctx_lines[:2]:
                parts = ln.split()
                for p in parts:
                    if p.startswith("doc_id="):
                        doc_ids.append(p.split("=",1)[1])
                        break
            doc_ids_str = ", ".join(f"[{d}]" for d in doc_ids)
            return (f"Here is what the catalog indicates based on the most relevant context. {doc_ids_str}\n\n"
                    f"- See {doc_ids_str} for details.")
        # OpenAI path
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_prompt},
            ],
            temperature=0.1
        )
        return resp.choices[0].message.content.strip()
