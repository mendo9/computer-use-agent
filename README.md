# Computer Use Agent with CUA

A production-ready computer use agent built with **CUA (Computer Use Agent)** framework, **uv** for packaging, and comprehensive **TDD** test coverage. This agent can control Windows VMs via HTTPS proxy or run locally on macOS for development.

## Quick Start

```bash
# 1) Install uv (see https://docs.astral.sh/uv/)
# 2) Create & sync env (installs deps & dev-deps)
uv sync --dev

# 3) Set your API keys
export OPENAI_API_KEY=sk-...
cp .env.example .env  # Edit with your settings

# 4) Run tests
uv run pytest -q

# 5) Lint / type-check
uv run ruff format .
uv run ruff check .
uv run pyright
```

## Local Development Setup (macOS)

For local development and testing on macOS:

```bash
# 1) Install the CUA computer server
uv add cua-computer-server

# 2) Start the computer server (in a separate terminal)
uv run -m computer_server

# 3) Grant macOS permissions:
# - System Settings → Privacy & Security → Accessibility → Add Terminal/Python
# - System Settings → Privacy & Security → Screen Recording → Add Terminal/Python

# 4) Set local mode and run demo
export COMPUTER_MODE=local_host
uv run -m src.tasks.demo_macos_textedit
```

## Architecture

**Backends:**
- **Remote Mode**: Self-hosted Windows VM via HTTPS proxy with mTLS
- **Local Mode**: macOS desktop via `cua-computer-server` 

**Models:**
- **Default**: `omniparser+openai/gpt-4o` (OmniParser + GPT-4o)
- **Custom Vision**: Optional PaddleOCR/OpenCV integration
- **Configurable**: Support for Claude, local models

**Features:**
- Azure Service Bus queue consumer for task processing
- Comprehensive test coverage with TDD approach
- File-specific test structure matching source code
- Production-ready configuration and error handling

## What's Inside
- **CUA Framework**: Computer use agent with vision grounding
- **TDD Tests**: 79 tests with file-specific organization
- **Dual Backends**: Remote Windows VM + local macOS support
- **Vision Integration**: OmniParser + custom OCR options
- **Queue Processing**: Azure Service Bus consumer
- **Modern Python**: uv + Ruff + Pyright + pytest

See `AGENTS.md` for detailed agent architecture and development guide.
