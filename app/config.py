"""إعدادات المشروع — يقرأ من ملف .env"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str
    admin_chat_id: int
    bot_username: str = "grad_assistant_bot"

    # OpenRouter (Kimi 2.5)
    openrouter_api_key: str
    openrouter_model: str = "moonshotai/kimi-k2"

    # OpenAI (Embeddings)
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"

    # RAG
    similarity_threshold: float = 0.35
    top_k_results: int = 5
    chunk_size: int = 800
    chunk_overlap: int = 150

    # Server
    webhook_url: str = ""
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # ChromaDB
    chroma_persist_dir: str = "./data/chromadb"
    chroma_collection: str = "grad_studies"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
