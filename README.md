# computer-use-agent

A production‑ready Python template for building LLM **agents** using **uv** for packaging & dev, **Ruff** for lint/format, **Pyright** for type checking, and **pytest** for tests. It also includes an **AGENTS.md** that documents your agents, tools, guardrails, and run conventions.

## Quickstart

```bash
# 1) Install uv (see https://docs.astral.sh/uv/)
# 2) Create & sync env (installs deps & dev-deps)
uv sync --dev

# 3) Set your API key (OpenAI by default; add others as needed)
export OPENAI_API_KEY=sk-...

# 4) Run the starter agent
uv run agent-starter

# 5) Lint / type-check / test
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest -q
```

## What’s inside
- **uv** project + lockfile, modern `pyproject.toml`
- **AGENTS.md** with roster, tools, guardrails, eval/obs and PR conventions
- **Ruff** lint + formatter; **Pyright** type checking
- **pytest** + coverage
- **OpenAI Agents SDK** starter agent + sample tool
- GitHub Actions CI (setup-uv) and a multi‑stage Dockerfile
- Pre‑commit hooks (Ruff)

See `AGENTS.md` for how to add/modify agents and tools.
