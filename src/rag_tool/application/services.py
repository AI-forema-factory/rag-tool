from dataclasses import dataclass
from pathlib import Path

from rag_tool.domain.chunking import chunk_markdown
from rag_tool.domain.models import SearchResult
from rag_tool.domain.ports import ChunkRepository, DocumentSource, Embedder


@dataclass(frozen=True, slots=True)
class IngestReport:
    files: int
    chunks: int


class IngestService:
    def __init__(self, source: DocumentSource, embedder: Embedder, repository: ChunkRepository) -> None:
        self._source = source
        self._embedder = embedder
        self._repository = repository

    def ingest_folder(self, folder: Path) -> IngestReport:
        folder = folder.resolve()
        seen: set[str] = set()
        files = chunks = 0
        for path in self._source.list_markdown(folder):
            source_path = str(path)
            file_chunks = chunk_markdown(source_path, self._source.read_text(path))
            vectors = self._embedder.embed_passages([c.text for c in file_chunks]) if file_chunks else []
            self._repository.replace_source(source_path, file_chunks, vectors)
            seen.add(source_path)
            files += 1
            chunks += len(file_chunks)
        # Never reconcile after an interrupted scan, read, or embedding operation.
        self._repository.remove_absent_sources(folder, seen)
        return IngestReport(files=files, chunks=chunks)


class QueryService:
    def __init__(self, embedder: Embedder, repository: ChunkRepository) -> None:
        self._embedder = embedder
        self._repository = repository

    def query(self, question: str, top_k: int = 3) -> list[SearchResult]:
        return self._repository.search(self._embedder.embed_query(question), top_k)
