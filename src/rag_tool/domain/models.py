from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chunk:
    """A contiguous span of a source document. Lines are 1-indexed and inclusive."""

    source_path: str
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True, slots=True)
class SearchResult:
    chunk: Chunk
    score: float
