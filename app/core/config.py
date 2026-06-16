from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Aletheia Local MVP"
    app_version: str = "0.1.0"
    environment: str = "local"

    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"

    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "aletheia_memory"
    qdrant_vector_size: int = 768

    vosk_model_path: str = "/app/models/vosk/vosk-model-small-es-0.42"
    stt_sample_rate: int = 16000

    piper_model_path: str = "/app/models/piper/es_MX-claude-high.onnx"
    piper_config_path: str = "/app/models/piper/es_MX-claude-high.onnx.json"
    tts_output_dir: str = "/app/storage/tts"
    tts_default_emotion: str = "neutral"

    # =========================
    # LATENCY OPTIMIZATION
    # =========================

    ollama_num_predict: int = 220
    ollama_temperature: float = 0.7
    ollama_top_p: float = 0.9
    ollama_num_ctx: int = 3072
    ollama_keep_alive: str = "30m"

    memory_search_limit: int = 4
    significant_memory_prompt_limit: int = 4
    bond_event_prompt_limit: int = 4
    initiative_action_prompt_limit: int = 3

    async_memory_persistence: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()