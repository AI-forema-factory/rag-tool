.PHONY: setup test lint run

HOST ?= 127.0.0.1
PORT ?= 8000

# Install deps and pre-download the embedding model into ./.models so tests run offline.
setup:
	uv sync
	uv run python -m rag_tool.infrastructure.download_model

lint:
	uv run lint-imports

# HF_HUB_OFFLINE makes any attempted model download fail instead of silently hitting the network.
test: lint
	HF_HUB_OFFLINE=1 uv run pytest -v

run:
	uv run uvicorn rag_tool.api.app:create_app --factory --host $(HOST) --port $(PORT)
