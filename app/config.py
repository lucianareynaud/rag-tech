from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core RAG configuration
    TOP_K: int = 3
    THRESHOLD: float = 0.4
    
    # Model configuration
    MODEL: str = "granite3.1-moe:1b"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # Ollama configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    model_config = SettingsConfigDict(extra="ignore")

settings = Settings()
