from collections.abc import Sequence
from pathlib import Path

from fastembed import TextEmbedding

from rag_tool.infrastructure.settings import EMBEDDING_MODEL


class FastEmbedEmbedder:
    def __init__(self, cache_dir: Path) -> None:
        self._model = TextEmbedding(model_name=EMBEDDING_MODEL, cache_dir=str(cache_dir))

    def embed_passages(self, texts: Sequence[str]) -> list[list[float]]:
        return [v.tolist() for v in self._model.passage_embed(list(texts))]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._model.query_embed(text))).tolist()
