from pathlib import Path

from fastapi import FastAPI, HTTPException

from rag_tool.api.schemas import IngestRequest, IngestResponse, QueryRequest, QueryResponse, QueryResult
from rag_tool.application.services import IngestService, QueryService
from rag_tool.infrastructure.embedder import FastEmbedEmbedder
from rag_tool.infrastructure.filesystem import MarkdownFolderSource
from rag_tool.infrastructure.settings import EMBEDDING_DIM, Settings
from rag_tool.infrastructure.sqlite_repository import SqliteVecChunkRepository, connect


def create_app(settings: Settings | None = None) -> FastAPI:
    """Composition root. Wiring happens eagerly so a missing sqlite-vec aborts startup."""
    settings = settings or Settings()
    conn = connect(settings.db_path)
    repository = SqliteVecChunkRepository(conn, dim=EMBEDDING_DIM)
    embedder = FastEmbedEmbedder(settings.model_cache_dir)
    ingest_service = IngestService(MarkdownFolderSource(), embedder, repository)
    query_service = QueryService(embedder, repository)

    app = FastAPI(title="rag-tool", description="Local retrieval over markdown. Retrieval only; no generation.")

    @app.post("/ingest", response_model=IngestResponse)
    def ingest(req: IngestRequest) -> IngestResponse:
        try:
            report = ingest_service.ingest_folder(Path(req.path))
        except NotADirectoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return IngestResponse(files=report.files, chunks=report.chunks)

    @app.post("/query", response_model=QueryResponse)
    def query(req: QueryRequest) -> QueryResponse:
        results = query_service.query(req.question, req.top_k)
        return QueryResponse(
            results=[
                QueryResult(
                    text=r.chunk.text,
                    source_path=r.chunk.source_path,
                    start_line=r.chunk.start_line,
                    end_line=r.chunk.end_line,
                    score=r.score,
                )
                for r in results
            ]
        )

    return app
