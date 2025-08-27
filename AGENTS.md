# AGENTS.md — project guide for coding agents

This file is the **single source of truth for agents in this repo**. It tells AI coding agents (and humans!) how this project is structured, how to run it, and how to safely extend it. Inspired by OpenAI’s AGENTS.md format and best practices for the Agents SDK.

## 1) Agent roster
- **starter_agent** — a minimal, general‑purpose assistant with a `now_iso` tool.

Add new agents under `src/agent_template/agents/`, each with:
- `name`: descriptive, unique
- `instructions`: clear, outcome‑oriented; avoid vague “be helpful” phrasing
- `tools`: pick from `src/agent_template/tools` or add new
- Optional: `handoff_description`, `guardrails` and per‑agent config

## 2) Models & budgets
- Default model: configured via env (see `Settings`).
- Start with your best model to set a quality baseline, then down‑shift to faster/cheaper models where acceptable.
- Track token+latency in CI runs to guard regressions.

## 3) Tools registry
Add tools in `src/agent_template/tools/`:
- Prefer **typed** Python functions decorated with `@function_tool`.
- Ensure **idempotence** where possible and add **docstrings**—these render as tool descriptions for the model.
- Write **unit tests** and add examples in docstrings.

## 4) Guardrails & safety
- Implement lightweight **validators** (e.g., Pydantic) and **allow‑lists** for risky actions.
- Add **tripwires** for irreversible ops and route to a **human‑in‑the‑loop** when thresholds are exceeded.
- Keep prompts **explicit** about boundaries; see `src/agent_template/agents/prompts.py`.

## 5) Orchestration
- Prefer a **single agent with tools** first; split to multi‑agent only when prompts or tool selection get unwieldy.
- Use runs with exit conditions (final output tool, no tool calls, max turns).

## 6) Observability
- Log structured events via `structlog`.
- (Optional) Add OpenTelemetry exporters and Phoenix / New Relic integration in `src/agent_template/telemetry/`.

## 7) Evaluation
- Keep a small **golden set** under `eval/` (inputs + expected traits).
- Add **pytest** checks for tool correctness and policy adherence.
- Gate merges on eval pass + lint + type‑check.

## 8) Local commands
```bash
# Sync dev env
uv sync --dev

# Run starter agent
uv run agent-starter

# Lint / format
uv run ruff format . && uv run ruff check .

# Type-check
uv run pyright

# Tests
uv run pytest -q
```

## 9) PR conventions for agent changes
- Include **before/after behaviors** and **risk notes**.
- Update **AGENTS.md** and **eval/** if tool contracts or prompts change.
- CI must pass: ruff, pyright, pytest, minimal evals.

## 10) Environment
Copy `.env.example` to `.env` and set required keys. The OpenAI Python SDK will read `OPENAI_API_KEY`.
