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

## User Preferences

- **Describe before acting**: Before every code change AND every bash command, write 1 brief sentence describing what you're about to do. Dennis is a screen reader user and this helps track what's happening.
- **No markdown tables**: Use hierarchical bullet point lists instead of markdown tables — tables are hard to read with a screen reader.

## Azure Infrastructure Setup Progress

### Subscription & Environment

- Subscription: **MSR-CreativeTechnologyDev** (`811ec329-e461-437e-b635-ca3f8391d02c`)
- Naming convention: `msrxct-mmct-*` (team: MSRx Creative Technology, project: mmct)
- Region: **eastus**
- Auth strategy: **Managed Identity only** (no API keys, `disableLocalAuth: true`)

### Resume This Session

```bash
cd C:\Users\v-fengdennis\repos\MMCTAgent && claude --resume mmct-azure-setup
```

### Completed

- Resource group `msrxct-mmct-rg` created in eastus
- Updated `infra/bash_scripts/00-setup-env-vars.sh` with `msrxct-mmct-*` naming for all resources
- Updated `infra/infra_config.yaml` — only AOAI deployment enabled, everything else disabled
- Set `operatingSystem.windows: true` in infra_config.yaml (required for az CLI path resolution)
- Azure OpenAI (`msrxct-mmct-aoai`) deployed in **swedencentral** (eastus had no GPT-4o GlobalStandard quota)
  - 4 models: gpt-4o, gpt-4o-mini, text-embedding-ada-002, whisper
- Azure AI Search (`msrxct-mmct-search`) deployed in eastus (standard tier)
- Azure Blob Storage (`msrxctmmctsa`) deployed in eastus with 6 containers
- Azure Speech Service (`msrxct-mmct-speech`) deployed in eastus
- Azure Event Hubs (`msrxct-mmct-eventhub`) deployed in eastus
- Managed Identity (`msrxct-mmct-identity`) created in eastus

### Troubleshooting Tips

- **venv required**: The deploy scripts use Python/pyyaml. Activate `.venv` before running: `source .venv/Scripts/activate`
- **Windows paths**: `operatingSystem.windows` must be `true` in `infra_config.yaml` or az CLI gets `/c/Users/...` paths that fail
- **Quota errors**: The ARM template deploys all models at once. If one model exceeds quota, the entire deployment fails. Check quota with: `az cognitiveservices usage list --location <region> --query "[?contains(name.value,'gpt-4o')]" --output table`
- **Deploy scripts are idempotent**: Safe to re-run — they check if resources exist before creating
- **RBAC requires Owner/UAA**: The Contributor role cannot create role assignments. Elevate via PIM to Owner or User Access Administrator first
- **PIM elevation expires every 8 hours**: If `az` commands fail with `AuthorizationFailed`, re-elevate your permissions
- **MSYS path mangling**: Git Bash converts `/subscriptions/...` to `C:\subscriptions\...`, causing `MissingSubscription` errors. Fix: set `export MSYS_NO_PATHCONV=1` at the top of any script that passes Azure resource scope paths to `az` commands
