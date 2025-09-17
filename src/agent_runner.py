import asyncio
import logging

from agent import ComputerAgent
from loguru import logger

from src import config
from src.backends.lume_vm import get_computer_lume
from src.backends.remote_cua_server import RemoteCuaComputer


async def make_computer():
    mode = config.COMPUTER_MODE
    if mode == "remote":
        return RemoteCuaComputer()
    elif mode == "lume":
        return get_computer_lume()
    raise RuntimeError(f"Unsupported COMPUTER_MODE={mode}")


def build_agent(computer):
    model = config.OPENAI_MODEL
    logger.info("Using model: {}", model)

    return ComputerAgent(
        model=model,  # e.g., "omniparser+openai/gpt-4o"
        tools=[computer],
        trajectory_dir=config.TRAJECTORY_DIR,
        only_n_most_recent_images=5,
        max_retries=3,
        verbosity=logging.DEBUG,
        screenshot_delay=1,
        telemetry_enabled=False,
    )


async def run_prompt(prompt: str):
    computer = await make_computer()

    # async for result in agent.run(prompt):
    #     if (
    #         result.get("output")
    #         and len(result["output"]) > 0
    #         and result["output"][-1]["type"] == "message"
    #     ):
    #         print("Agent:", result["output"][-1]["content"][0]["text"])

    # Collect all results
    full_result = ""
    try:
        agent = build_agent(computer)
        async for item in agent.run(prompt):
            logger.info("Agent processing step")

            # Process output if available
            outputs = item.get("output", [])
            for output in outputs:
                output_type = output.get("type")
                if output_type == "message":
                    logger.debug(f"Message: {output}")
                    content = output.get("content", [])
                    for content_part in content:
                        if content_part.get("text"):
                            full_result += f"Message: {content_part.get('text', '')}\n"
                elif output_type == "tool_use":
                    logger.debug(f"Tool use: {output}")
                    tool_name = output.get("name", "")
                    full_result += f"Tool: {tool_name}\n"
                elif output_type == "tool_result":
                    logger.debug(f"Tool result: {output}")
                    result_content = output.get("content", "")
                    if isinstance(result_content, list):
                        for item in result_content:
                            if item.get("type") == "text":
                                full_result += f"Result: {item.get('text', '')}\n"
                    else:
                        full_result += f"Result: {result_content}\n"

        # Add separator between steps
        full_result += "\n" + "-" * 20 + "\n"

    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Don't close immediately - keep VM running for inspection
        print("Demo finished. VM kept running for inspection.")
        print("Screenshots saved to /tmp/step*.png")
        try:
            # Only disconnect if the computer has a disconnect method (Lume VMs)
            if hasattr(computer, "disconnect"):
                await computer.disconnect()
                print("Disconnected from VM (VM kept running)")
            else:
                print("Remote computer doesn't require disconnect")
        except Exception as e:
            print(f"Error during disconnect: {e}")

    return full_result


if __name__ == "__main__":
    asyncio.run(run_prompt("Open a text editor and type 'hello from cua'"))
