from __future__ import annotations
from app.config import settings
import logging
import requests

logger = logging.getLogger("llm")

class LLM:
    def __init__(self):
        self.model = settings.MODEL
        self._ollama_url = settings.OLLAMA_BASE_URL
        
        # Test Ollama connection
        try:
            response = requests.get(f"{self._ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"Ollama client configured for {settings.OLLAMA_BASE_URL}")
            else:
                raise ConnectionError(f"Ollama server returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama server at {self._ollama_url}: {e}")
            raise RuntimeError(f"Ollama server is required but not available at {self._ollama_url}") from e

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Ollama + Granite 3.1 MoE 1B"""
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
        
        try:
            response = requests.post(
                f"{self._ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                if result:
                    return result
                else:
                    logger.warning("Ollama returned empty response")
                    return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
            else:
                logger.error(f"Ollama HTTP error: {response.status_code}")
                raise RuntimeError(f"Ollama server error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Failed to generate response: {e}") from e
