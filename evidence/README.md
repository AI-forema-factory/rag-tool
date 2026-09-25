# rag-tool issue #2 evidence

Base: `882641b1ac4934471a391479558eff651377f2bf`.
The test-only commit `35d0d80` preserves the initial failing regression against
unchanged production code. The PR head contains the fix and final logs.

Environment: Linux x86_64, CPython 3.12.14, uv 0.12.19.
Dependencies: unchanged uv.lock, SHA-256
`84dbc7298b78acae3e72ccd46beaa522b49b4f1220c74b6eab4179374684e6b3`.
Model: BAAI/bge-small-en-v1.5 via Qdrant/bge-small-en-v1.5-onnx-Q,
snapshot `aa8f8b060edb00e03bfdd08813a2949946c8ba55`, ONNX SHA-256
`51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431`.

Commands (repository root):

| Command | Exit | Result/log |
| --- | --- | --- |
| `uv sync --frozen` | 0 | Installed 53 locked packages and Python 3.12.14 |
| `HF_HUB_OFFLINE=1 timeout 60 .venv/bin/pytest -v tests/test_reconciliation.py` on test-only commit | 1 | 3 failed, 5 passed; baseline.log |
| Same command after fix, before added nested-root case | 0 | 8 passed; regression.log |
| `uv run --frozen python -m rag_tool.infrastructure.download_model` | 0 | model-setup.log |
| `UV_FROZEN=1 timeout 120 make test` on final source | 0 | 2 architecture contracts kept, 10 tests passed; final-checks.log |
| `git diff --check` | 0 | No whitespace errors |

Reproduce baseline in a separate checkout at `35d0d80`, run `uv sync --frozen`,
then the baseline command above. No model is needed for the regression suite.
For final checks, install locked dependencies, download the model, then run
`UV_FROZEN=1 make test`. The Makefile sets HF_HUB_OFFLINE=1 for pytest.

The regression uses a fixed nonzero embedding with the real FastAPI routes and
SQLite vector storage, querying all fixture chunks (below top_k=100) without
relevance thresholds. Fixtures live only in pytest temporary directories.
Checks cover deletion of multiple chunks, no orphan vectors, retained content,
a sibling root with a common prefix, repeated ingestion, empty root, missing and
non-directory roots, interrupted scans, traversal/read/embedding errors, nested
root scope, wildcard characters and a symlink alias.

Limitations: per-file updates are not rolled back after later failures; absent
sources are not pruned on failure. Scanning is not a snapshot and overlapping
filesystem writes/ingestions are outside this fix. Directory symlinks are not
traversed, matching existing behavior. The existing Starlette/httpx deprecation
warning remains. Model download is needed only for the existing relevance test.

Execution notes: initial sandbox API test hung and was terminated; the same
command ran outside the sandbox in under a second. Network calls also required
the approved outside-sandbox path. An initial commit failed for missing Git
identity; retried with command-local Maya Chen/noreply@paperclip.ing identity.
One file append used a redundant repository prefix and failed harmlessly; it was
corrected before final validation. No shared configuration was modified.

Independent review remains pending with Arun Patel in Paperclip. No merge or
deployment is part of this work. Usage/cost telemetry unavailable to this report.
