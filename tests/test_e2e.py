from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from rag_tool.api.app import create_app
from rag_tool.infrastructure.settings import Settings

FIXTURES = Path(__file__).parent / "fixtures" / "docs"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    app = create_app(Settings(db_path=tmp_path / "rag.db"))
    with TestClient(app) as c:
        yield c


def test_ingest_then_query_returns_relevant_chunk(client: TestClient) -> None:
    ingest = client.post("/ingest", json={"path": str(FIXTURES)})
    assert ingest.status_code == 200, ingest.text
    assert ingest.json()["files"] == 3
    assert ingest.json()["chunks"] > 0

    resp = client.post("/query", json={"question": "How do I roll back a deployment to the previous version?"})
    assert resp.status_code == 200, resp.text
    results = resp.json()["results"]

    assert len(results) == 3  # default top_k
    top = results[0]
    assert top["source_path"] == str((FIXTURES / "guides" / "kubernetes.md").resolve())
    assert top["text"].strip()
    assert 1 <= top["start_line"] <= top["end_line"]
    assert results == sorted(results, key=lambda r: r["score"], reverse=True)
