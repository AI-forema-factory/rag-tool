# rag-tool

Local retrieval service for AI agents. Ingests a folder of Markdown, embeds chunks with
fastembed `BAAI/bge-small-en-v1.5`, stores them in SQLite + sqlite-vec, and returns the
top-k matching chunks. **Retrieval only — no LLM generation.**

## Usage

```sh
make setup   # uv sync + pre-download the model into ./.models
make test    # import-linter contracts + pytest (offline)
make run     # uvicorn on 127.0.0.1:8000
```

```sh
curl -s localhost:8000/ingest -H 'content-type: application/json' -d '{"path": "/abs/path/to/docs"}'
# {"files": 3, "chunks": 7}

curl -s localhost:8000/query -H 'content-type: application/json' -d '{"question": "...", "top_k": 3}'
# {"results": [{"text", "source_path", "start_line", "end_line", "score"}, ...]}
```

`start_line`/`end_line` are 1-indexed and inclusive; `score` is cosine similarity.
Re-ingesting a file replaces its previous chunks.

Config (env): `RAG_DB_PATH` (default `data/rag.db`), `RAG_MODEL_CACHE_DIR` (default `.models`).

If sqlite-vec cannot be loaded, startup fails with `VectorExtensionError`; there is no fallback.

## Layout

`src/rag_tool/{domain,application,infrastructure,api}` — dependencies point inward only
(api → infrastructure → application → domain), enforced by import-linter
(`[tool.importlinter]` in `pyproject.toml`). Domain and application must not import
fastapi, pydantic, fastembed or sqlite-vec.
