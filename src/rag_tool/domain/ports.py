from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Protocol

from rag_tool.domain.models import Chunk, SearchResult

Vector = Sequence[float]


class Embedder(Protocol):
    def embed_passages(self, texts: Sequence[str]) -> list[Vector]: ...

    def embed_query(self, text: str) -> Vector: ...


class ChunkRepository(Protocol):
    def replace_source(self, source_path: str, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> None:
        """Atomically replace all chunks previously stored for `source_path`."""
        ...

    def search(self, vector: Vector, top_k: int) -> list[SearchResult]: ...


class DocumentSource(Protocol):
    def list_markdown(self, folder: Path) -> Iterable[Path]: ...

    def read_text(self, path: Path) -> str: ...
