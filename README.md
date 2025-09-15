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

For local development and testing on macOS using Lume VM:

```bash
# 1) Install Lume CLI
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/lume/scripts/install.sh)"

# 2) Run demo with automatic VM creation
uv run -m src.tasks.lume_computer_demo

# 3) For TextEdit demo with VM
uv run -m src.tasks.demo_macos_textedit
```

**Important Network Requirements:**
- The VM runs on a local IP (e.g., `192.168.64.x`) with computer server on port 8000
- Your IDE/terminal must have **local networking enabled** to connect to the VM
- **Cursor IDE**: Enable "Allow local network connections" in settings
- **VS Code**: Ensure local network access isn't blocked by firewall
- **Terminal**: Should work by default, but check firewall settings if connection fails

The `src/backends/lume_vm.py` automatically creates and manages the VM instance using the `macos-sequoia-cua_15.4` image.

## Architecture

**Backends:**
- **Remote Mode**: Self-hosted Windows VM via HTTPS proxy with mTLS
- **Lume VM Mode**: Virtualized macOS via Lume (Apple Virtualization.framework) 

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
