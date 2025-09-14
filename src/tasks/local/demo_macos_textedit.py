import asyncio

from src.agent_runner import run_prompt


def run():
    prompt = (
        "On macOS, open TextEdit (Please try pressing 'Command (⌘) + Spacebar' to open Spotlight). "
        "Create a new plain text document and type 'hello from cua (mac)'. "
        "Save to Desktop as hello_mac.txt and confirm saved."
    )
    asyncio.run(run_prompt(prompt))


if __name__ == "__main__":
    run()
