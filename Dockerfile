# Production-ready Dockerfile for uv-based Python project (no dev deps in final image)
# - Locks deps inside the build (deterministic)
# - Installs only runtime deps in final image
# - Runs as non-root
# - Small final image (python:3.12-slim)

# ---------- Base image (common) ----------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONOPTIMIZE=2
# Install system deps if needed (kept minimal)
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# ---------- Builder: uv + lock + install (no dev) ----------
FROM base AS builder
# Bring in uv binary
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /usr/local/bin/uv
WORKDIR /app

# Copy project metadata first for layer caching
COPY pyproject.toml /app/

# Create or refresh lock deterministically for Python 3.12
# (Respects [tool.uv] python = "3.12")
RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock

# Install ONLY runtime deps into a local venv (no project yet, and no dev deps)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Now copy the source and install the project into the same venv
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---------- Final runtime image ----------
FROM base AS runtime
WORKDIR /app

# Create a non-root user
RUN useradd -m -u 10001 appuser

# Copy the entire app (including .venv from builder)
COPY --from=builder /app /app

# Put venv on PATH
ENV PATH="/app/.venv/bin:${PATH}"

USER appuser
EXPOSE 8000

# Default command: run the CLI entry point
CMD ["uv", "run", "agent-starter"]
