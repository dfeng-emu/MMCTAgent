# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MMCTAgent is a Multi-Modal Critical Thinking Agent Framework for visual reasoning tasks. It provides two main agents:
- **ImageAgent**: Static image understanding using object detection (YOLOv8), OCR (TrOCR), scene recognition (InstructBLIP/mPLUG), and ViT
- **VideoAgent**: Video understanding with transcript retrieval, frame analysis, chapter generation, and critic validation

The framework uses a vendor-agnostic provider system supporting Azure OpenAI, OpenAI, FAISS, and custom implementations.

## Build & Install

```bash
pip install -e ".[all]"         # Full install (image + video + MCP)
pip install -e ".[image-agent]" # Image pipeline only
pip install -e ".[video-agent]" # Video pipeline only
pip install -e ".[dev]"         # Dev dependencies (pytest, black, isort, mypy)
```

## Common Commands

```bash
# Run tests
pytest                       # All tests
pytest -m unit               # Unit tests only
pytest -m integration        # Integration tests only
pytest -m "not slow"         # Skip slow tests

# Formatting & linting
black . --line-length 100
isort . --profile black --line-length 100
mypy mmct/

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start MCP server
python mcp_server/main.py

# Start ingestion consumer (Event Hub)
python app/ingestion_consumer.py
```

## Architecture

### Provider Injection Pattern

All agents receive their dependencies through Pydantic config classes defined in `mmct/config/providers.py`:
- `ImageAgentProviderConfig` → requires LLM provider
- `VideoAgentProviderConfig` → requires LLM, embedding, image embedding, 3 vector DBs, storage
- `IngestionProviderConfig` → extends video config with transcription provider

Provider implementations live in `mmct/providers/`:
- `base/` — abstract base classes (BaseLLMProvider, BaseEmbeddingProvider, BaseStorageProvider, etc.)
- `azure_providers/` — Azure OpenAI, Cognitive Services, Storage, Search
- `openai_providers/` — Direct OpenAI API
- `custom_providers/` — Local implementations (CLIP embeddings, FAISS search)

### Agent Orchestration

- **ImageAgent** (`mmct/image_pipeline/agents/image_agent.py`): Uses AutoGen for planner/critic multi-agent orchestration
- **VideoAgent** (`mmct/video_pipeline/agents/video_agent.py`): Uses Swarm orchestration for video Q&A
- **IngestionPipeline** (`mmct/video_pipeline/core/ingestion/ingestion_pipeline.py`): Sequential pipeline — audio extraction → transcription → frame extraction → chapter generation → indexing

### Application Layer

- `app/main.py` — FastAPI app with routes: `/query-on-images`, `/query-on-videos`, `/ingest-video`, `/ingest-video-queue`, `/health`
- `app/ingestion_consumer.py` — Separate Event Hub consumer for async ingestion
- `mcp_server/` — FastMCP server exposing agents as MCP tools (video_agent, image_agent, video_ingestion, context retrieval, frame queries)

### Docker

Three-layer Docker setup:
1. `Dockerfile.base` — Python 3.10 + system deps (ffmpeg, OpenGL)
2. `app/Dockerfile.main` — FastAPI app on port 8000
3. `mcp_server/Dockerfile.mcp` — MCP server on port 8000

## Configuration

- `config/providers.yaml` — Provider configuration with environment variable substitution
- `examples/.env.example` — Template for required environment variables (Azure OpenAI, Storage, Search, Speech)
- `infra/infra_config.yaml` — Azure infrastructure deployment configuration

## Code Style

- **Black**: line-length=100, target Python 3.8
- **isort**: black-compatible profile, line_length=100
- **mypy**: strict mode enabled; azure/openai/autogen modules have missing import ignores

## Azure Infrastructure

- Naming convention: `msrxct-mmct-*`
- Region: **eastus** (AOAI in **swedencentral** due to quota)
- Auth strategy: **Managed Identity only** (no API keys)
- See `.claude/CLAUDE.md` for detailed setup progress, TODOs, and troubleshooting tips (gitignored)
