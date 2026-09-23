"""Pre-download the embedding model into the pinned cache dir (`make setup`)."""

from rag_tool.infrastructure.embedder import FastEmbedEmbedder
from rag_tool.infrastructure.settings import EMBEDDING_MODEL, Settings

if __name__ == "__main__":
    cache_dir = Settings().model_cache_dir
    FastEmbedEmbedder(cache_dir).embed_query("warmup")
    print(f"{EMBEDDING_MODEL} ready in {cache_dir.resolve()}")
