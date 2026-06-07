from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aletheia Local MVP"
    app_version: str = "0.1.0"
    environment: str = "local"

    log_level: str = "INFO"

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "aletheia_memory"
    qdrant_vector_size: int = 768

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()