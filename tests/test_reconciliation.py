"""Deterministic API/storage checks; no model download or relevance thresholds."""
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import rag_tool.api.app as api
from rag_tool.infrastructure.filesystem import MarkdownFolderSource
from rag_tool.infrastructure.settings import EMBEDDING_DIM, Settings


class FixedEmbedder:
    def __init__(self, *args):
        pass

    def embed_passages(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        return [1.0] + [0.0] * (EMBEDDING_DIM - 1)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "FastEmbedEmbedder", FixedEmbedder)
    root = tmp_path / "docs"
    other = tmp_path / "docs-other"
    root.mkdir()
    other.mkdir()
    for folder, name in [(root, "removed"), (root, "retained"), (other, "other")]:
        (folder / f"{name}.md").write_text((f"# {name}\n" + "content " * 300 + "\n") * 3)
    db = tmp_path / "rag.db"
    with TestClient(api.create_app(Settings(db_path=db)), raise_server_exceptions=False) as client:
        for folder in (root, other):
            assert client.post("/ingest", json={"path": str(folder)}).status_code == 200
        yield client, root, other, db


def snapshot(db):
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT source_path, start_line, end_line, text FROM chunks ORDER BY 1,2").fetchall()


def query_paths(client):
    response = client.post("/query", json={"question": "anything", "top_k": 100})
    assert response.status_code == 200
    return {row["source_path"] for row in response.json()["results"]}


def test_deleted_sources_disappear_from_query_and_storage(setup):
    client, root, other, db = setup
    removed = root / "removed.md"
    before = snapshot(db)
    assert sum(row[0] == str(removed) for row in before) > 1
    removed.unlink()
    assert client.post("/ingest", json={"path": str(root / ".." / root.name)}).status_code == 200
    assert str(removed) not in query_paths(client)
    expected = [row for row in before if row[0] != str(removed)]
    assert snapshot(db) == expected
    assert query_paths(client) == {str(root / "retained.md"), str(other / "other.md")}
    assert client.post("/ingest", json={"path": str(root)}).status_code == 200
    assert snapshot(db) == expected
    # Verify no orphan vectors using the real sqlite-vec connection.
    from rag_tool.infrastructure.sqlite_repository import connect
    conn = connect(db)
    assert conn.execute("SELECT count(*) FROM chunk_vectors").fetchone()[0] == len(expected)
    conn.close()


def test_empty_root_cleans_only_that_root(setup):
    client, root, other, db = setup
    for path in root.glob("*.md"):
        path.unlink()
    response = client.post("/ingest", json={"path": str(root)})
    assert response.status_code == 200
    assert response.json() == {"files": 0, "chunks": 0}
    assert query_paths(client) == {str(other / "other.md")}
    assert {row[0] for row in snapshot(db)} == {str(other / "other.md")}


@pytest.mark.parametrize("failure", ["missing", "not_directory", "scan", "read", "embed"])
def test_failed_ingestion_never_prunes(setup, monkeypatch, failure):
    client, root, other, db = setup
    before = snapshot(db)
    (root / "removed.md").unlink()
    target = root
    if failure == "missing":
        target = root / "missing"
    elif failure == "not_directory":
        target = root / "retained.md"
    elif failure == "scan":
        def incomplete(self, folder):
            yield root / "retained.md"
            raise PermissionError("incomplete scan")
        monkeypatch.setattr(MarkdownFolderSource, "list_markdown", incomplete)
    elif failure == "read":
        def unreadable(self, path):
            raise PermissionError("unreadable document")
        monkeypatch.setattr(MarkdownFolderSource, "read_text", unreadable)
    else:
        def failed(self, texts):
            raise RuntimeError("embedding failed")
        monkeypatch.setattr(FixedEmbedder, "embed_passages", failed)
    assert client.post("/ingest", json={"path": str(target)}).status_code >= 400
    assert snapshot(db) == before


def test_filesystem_propagates_traversal_errors(tmp_path, monkeypatch):
    import os
    def failed_scan(path):
        raise PermissionError("cannot enumerate directory")
    monkeypatch.setattr(os, "scandir", failed_scan)
    with pytest.raises(PermissionError):
        list(MarkdownFolderSource().list_markdown(tmp_path))


def test_nested_root_and_symlink_alias_are_scoped(setup):
    client, root, other, db = setup
    nested = root / "nested_%"
    nested.mkdir()
    removed = nested / "gone.md"
    removed.write_text("# Nested\nremove me")
    assert client.post("/ingest", json={"path": str(root)}).status_code == 200
    expected = [row for row in snapshot(db) if row[0] != str(removed)]
    removed.unlink()
    alias = root.parent / "alias"
    alias.symlink_to(nested, target_is_directory=True)
    assert client.post("/ingest", json={"path": str(alias)}).status_code == 200
    assert snapshot(db) == expected
    assert str(removed) not in query_paths(client)
