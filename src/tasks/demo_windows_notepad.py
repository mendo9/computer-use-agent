import asyncio

from src.agent_runner import run_prompt


def run():
    prompt = (
        "Open Notepad. Type 'hello from cua'. "
        "Save the file to the Desktop as hello.txt. "
        "Verify the file exists."
    )
    asyncio.run(run_prompt(prompt))


if __name__ == "__main__":
    run()
