from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aletheia Local MVP"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "aletheia_memory"

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
