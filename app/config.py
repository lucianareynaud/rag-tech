from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    TOP_K: int = 3
    THRESHOLD: float = 0.55
    MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_PROVIDER: str = "stub"  # "openai" or "stub"
    OPENAI_API_KEY: str | None = None
    OPENAI_BASE_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
