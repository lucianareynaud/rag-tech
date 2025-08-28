from __future__ import annotations
from app.config import settings
import logging

logger = logging.getLogger("llm")

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
        elif self.provider == "ollama":
            try:
                import requests
                self._ollama_url = settings.OLLAMA_BASE_URL
                # Test connection
                response = requests.get(f"{self._ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Ollama client configured for {settings.OLLAMA_BASE_URL}")
                else:
                    logger.warning(f"Ollama server not responding, falling back to stub mode")
            except ImportError:
                logger.warning("Requests not available, falling back to stub mode")
            except Exception as e:
                logger.warning(f"Ollama connection failed: {e}, falling back to stub mode")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Try Ollama first if configured
        if self.provider == "ollama" and hasattr(self, '_ollama_url'):
            try:
                import requests
                payload = {
                    "model": self.model,
                    "prompt": f"System: {system_prompt}\n\nUser: {user_prompt}\n\nAssistant:",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 150,
                        "stop": ["\n\n", "---", "User:", "System:"]
                    }
                }
                response = requests.post(
                    f"{self._ollama_url}/api/generate",
                    json=payload,
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json().get('response', '').strip()
                    return result if result else self._stub_generate(user_prompt)
                else:
                    logger.error(f"Ollama HTTP error: {response.status_code}")
                    return self._stub_generate(user_prompt)
            except Exception as e:
                logger.error(f"Ollama generation failed: {e}, falling back to stub")
                return self._stub_generate(user_prompt)
        
        # Try OpenAI if configured
        elif self.provider == "openai" and self._client is not None:
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role":"system","content":system_prompt},
                        {"role":"user","content":user_prompt},
                    ],
                    temperature=0.1
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"OpenAI generation failed: {e}, falling back to stub")
                return self._stub_generate(user_prompt)
        
        # Fallback to stub
        else:
            return self._stub_generate(user_prompt)
    
    def _stub_generate(self, user_prompt: str) -> str:
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
                    doc_id = p.split("=",1)[1].rstrip("]")
                    doc_ids.append(doc_id)
                    break
        doc_ids_str = ", ".join(f"[{d}]" for d in doc_ids)
        return (f"Here is what the catalog indicates based on the most relevant context. {doc_ids_str}\n\n"
                f"- See {doc_ids_str} for details.")
