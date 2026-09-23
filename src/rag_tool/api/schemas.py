from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    path: str = Field(description="Folder to ingest recursively; every *.md file is chunked and embedded.")


class IngestResponse(BaseModel):
    files: int
    chunks: int


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=100)


class QueryResult(BaseModel):
    text: str
    source_path: str
    start_line: int = Field(description="1-indexed, inclusive")
    end_line: int = Field(description="1-indexed, inclusive")
    score: float = Field(description="Cosine similarity; higher is more relevant")


class QueryResponse(BaseModel):
    results: list[QueryResult]
