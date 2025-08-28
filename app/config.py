from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Core RAG configuration
    TOP_K: int = 3
    THRESHOLD: float = 0.4
    
    # Model configuration
    MODEL: str = "granite3.1-moe:1b"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # LLM provider configuration
    LLM_PROVIDER: str = "ollama"  # "openai", "ollama", or "stub"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Optional OpenAI configuration (override via environment if needed)
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None

    model_config = SettingsConfigDict(extra="ignore")

settings = Settings()
