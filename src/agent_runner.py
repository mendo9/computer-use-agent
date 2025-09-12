import asyncio

from agent import ComputerAgent
from loguru import logger

from src import config
from src.backends.local_host import get_computer_local_host
from src.backends.remote_cua_server import RemoteCuaComputer


async def make_computer():
    mode = config.COMPUTER_MODE
    if mode == "remote":
        return RemoteCuaComputer()
    elif mode == "local_host":
        return get_computer_local_host()
    raise RuntimeError(f"Unsupported COMPUTER_MODE={mode}")


def build_agent(computer):
    model = config.OPENAI_MODEL
    logger.info("Using model: {}", model)
    return ComputerAgent(
        model=model,  # e.g., "omniparser+openai/gpt-4o"
        tools=[computer],  # computer tool (plus any extra tools you add)
        trajectory_dir=config.TRAJECTORY_DIR,
        only_n_most_recent_images=3,
        max_retries=3,
        screenshot_delay=0.5,
    )


async def run_prompt(prompt: str):
    computer = await make_computer()
    agent = build_agent(computer)
    async for item in agent.run(prompt):
        kind = item.get("type")
        if kind == "message":
            logger.info("[LLM] {}", item.get("content"))
        elif kind == "computer_call":
            logger.info("[CALL] {}", item.get("content"))
        elif kind == "computer_call_output":
            logger.info("[OUT ] {}", item.get("content"))


if __name__ == "__main__":
    asyncio.run(run_prompt("Open a text editor and type 'hello from cua'"))
