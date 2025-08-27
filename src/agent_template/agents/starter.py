from __future__ import annotations

from agents import Agent

from ..prompts import BASE_INSTRUCTIONS
from ..tools.time_tools import now_iso


def starter_agent() -> Agent:
    return Agent(
        name="StarterAgent",
        instructions=BASE_INSTRUCTIONS,
        tools=[now_iso],
    )
