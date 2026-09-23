from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_")

    db_path: Path = Path("data/rag.db")
    model_cache_dir: Path = Path(".models")
