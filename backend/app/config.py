from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- App ---
    app_name: str = "Research Paper Assistant"
    cors_origins: str = "http://localhost:3000"

    # --- Database ---
    # No default: must be set via .env / environment. Avoids ever shipping a
    # hardcoded credential in tracked code.
    database_url: str

    # --- Storage ---
    storage_dir: str = "/app/storage"

    # --- LLM provider selection ---
    llm_provider: str = "groq"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/auto"

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1"

    # --- Embeddings ---
    embedding_provider: str = "local"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # --- Ingestion ---
    unstructured_strategy: str = "fast"  # "fast" | "hi_res"
    chunk_target_tokens: int = 650
    chunk_overlap_tokens: int = 120

    # --- Retrieval ---
    retrieval_top_k: int = 8

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
