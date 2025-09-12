import asyncio

from src.agent_runner import run_prompt


def run():
    prompt = (
        "On macOS, open TextEdit (use Spotlight if needed). "
        "Create a new plain text document and type 'hello from cua (mac)'. "
        "Save to Desktop as hello_mac.txt and confirm saved."
    )
    asyncio.run(run_prompt(prompt))


if __name__ == "__main__":
    run()
