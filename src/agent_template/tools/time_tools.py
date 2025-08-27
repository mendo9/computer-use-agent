from __future__ import annotations

from datetime import UTC, datetime

from agents import function_tool


@function_tool
def now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(UTC).isoformat()
