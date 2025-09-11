from __future__ import annotations

from agents import Runner
from rich.console import Console

from .agents.starter import starter_agent
from .config import Settings

console = Console()


def main() -> None:
    # Validate env and show a friendly banner
    Settings.require()
    agent = starter_agent()
    console.rule("[bold]python-agent-template-uv[/]")
    console.print("Running StarterAgent...\n")
    result = Runner().run(agent, "Say hello and tell me the current time using the tool.")
    console.print("\n[b]Agent output[/]:")
    console.print(result)  # The Agents SDK pretty-prints responses
