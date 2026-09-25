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

Re-ingesting a folder reconciles its stored sources: after every markdown file is
successfully read and embedded, chunks and vectors for absent paths under that
folder are deleted. A successfully scanned empty folder clears that folder's
stored chunks. Paths are scoped by directory components, so siblings and sources
outside the requested root are preserved. Folder aliases are resolved before
scanning; directory symlinks inside the tree are not traversed.

Missing roots, traversal/read errors, and embedding failures abort ingestion
without pruning absent sources. Earlier successful per-file replacements may
remain if a later file fails; ingestion is not a whole-folder transaction. As
before, scans do not provide a snapshot of concurrent filesystem edits, so avoid
changing the folder or issuing overlapping ingestions during reconciliation.
