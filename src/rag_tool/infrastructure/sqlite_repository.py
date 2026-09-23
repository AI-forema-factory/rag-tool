import sqlite3
import threading
from collections.abc import Sequence
from pathlib import Path

import sqlite_vec

from rag_tool.domain.models import Chunk, SearchResult
from rag_tool.domain.ports import Vector


class VectorExtensionError(RuntimeError):
    """sqlite-vec could not be loaded. There is deliberately no fallback."""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    if not hasattr(conn, "enable_load_extension"):
        conn.close()
        raise VectorExtensionError(
            "this Python's sqlite3 module was built without extension loading; sqlite-vec cannot be loaded"
        )
    try:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        (version,) = conn.execute("SELECT vec_version()").fetchone()
    except Exception as exc:
        conn.close()
        raise VectorExtensionError(f"failed to load sqlite-vec extension: {exc}") from exc
    if not version:
        conn.close()
        raise VectorExtensionError("sqlite-vec loaded but vec_version() returned nothing")
    return conn


class SqliteVecChunkRepository:
    def __init__(self, conn: sqlite3.Connection, dim: int) -> None:
        self._conn = conn
        self._lock = threading.Lock()
        with self._lock, self._conn:
            self._conn.executescript(
                f"""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    start_line INTEGER NOT NULL,
                    end_line INTEGER NOT NULL,
                    text TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS chunks_source_path ON chunks(source_path);
                CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vectors USING vec0(
                    embedding float[{dim}] distance_metric=cosine
                );
                """
            )

    def replace_source(self, source_path: str, chunks: Sequence[Chunk], vectors: Sequence[Vector]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        with self._lock, self._conn:
            old_ids = [r[0] for r in self._conn.execute("SELECT id FROM chunks WHERE source_path = ?", (source_path,))]
            self._conn.executemany("DELETE FROM chunk_vectors WHERE rowid = ?", [(i,) for i in old_ids])
            self._conn.execute("DELETE FROM chunks WHERE source_path = ?", (source_path,))
            for chunk, vector in zip(chunks, vectors):
                cur = self._conn.execute(
                    "INSERT INTO chunks (source_path, start_line, end_line, text) VALUES (?, ?, ?, ?)",
                    (chunk.source_path, chunk.start_line, chunk.end_line, chunk.text),
                )
                self._conn.execute(
                    "INSERT INTO chunk_vectors (rowid, embedding) VALUES (?, ?)",
                    (cur.lastrowid, sqlite_vec.serialize_float32(list(vector))),
                )

    def search(self, vector: Vector, top_k: int) -> list[SearchResult]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT c.source_path, c.start_line, c.end_line, c.text, v.distance
                FROM (
                    SELECT rowid, distance FROM chunk_vectors
                    WHERE embedding MATCH ? AND k = ?
                ) AS v
                JOIN chunks AS c ON c.id = v.rowid
                ORDER BY v.distance
                """,
                (sqlite_vec.serialize_float32(list(vector)), top_k),
            ).fetchall()
        return [
            SearchResult(chunk=Chunk(path, start, end, text), score=1.0 - distance)
            for path, start, end, text, distance in rows
        ]
