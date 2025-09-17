import asyncio
import json

from azure.servicebus.aio import ServiceBusClient
from loguru import logger

from src.agent_runner import run_prompt
from src.config import SB_CONNECTION_STRING, SB_QUEUE_NAME
from src.models import WorkItem

PROMPT_TEMPLATE = (
    "You are a computer-use agent. Use the provided tools to operate the UI.\n"
    "Task: {task}\n"
    "Row data: {payload}\n"
    "Rules:\n"
    "- Never guess coordinates; always use grounding (OmniParser or available tools) before clicking.\n"
    "- After each action, take a screenshot and verify the result.\n"
)


async def handle_message(body: dict):
    item = WorkItem(**body)
    prompt = PROMPT_TEMPLATE.format(task=item.task, payload=json.dumps(item.payload))
    await run_prompt(prompt)


async def consume():
    if not SB_CONNECTION_STRING or not SB_QUEUE_NAME:
        raise RuntimeError("SB_CONNECTION_STRING and SB_QUEUE_NAME are required")
    async with (
        ServiceBusClient.from_connection_string(SB_CONNECTION_STRING) as client,
        client.get_queue_receiver(queue_name=SB_QUEUE_NAME) as receiver,
    ):
        async for msg in receiver:
            try:
                payload = json.loads(str(msg))
                await handle_message(payload)
                await receiver.complete_message(msg)
            except Exception:
                logger.exception("Failed to process message")
                await receiver.abandon_message(msg)


if __name__ == "__main__":
    asyncio.run(consume())
