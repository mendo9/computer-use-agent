"""
Agent demo that exposes scaffolding tools to a model via OpenAI Agents SDK.
Usage:
  uv run python -m my_project.agent_demo "Click the 'Submit' button"
"""

from __future__ import annotations

import asyncio
import os

from agents import Agent, Runner

from ocr.adapters.input import Input
from ocr.adapters.screen import Screen
from ocr.runtime.context import Session
from ocr.vision.detector import YOLODetector
from ocr.vision.ocr import OCRReader

from . import tools as my_tools
from .backends import DummyConnection, DummyController

INSTRUCTIONS = """
You are a GUI automation agent that operates from screenshots only.
Use the available tools to understand the screen and perform actions.
Strategy:
1) Use list_ui or find_text to locate targets.
2) Use click_text and scroll to navigate.
3) Use type_text to enter data.
4) Confirm success by looking for expected text on screen.
Always explain the sequence of tool calls you will make.
"""


async def main(user_goal: str):
    # Wire backends (replace Dummy* with your real VNC/RDP adapters)
    screen = Screen(DummyConnection())
    controller = DummyController()
    inp = Input(controller)

    # Perception
    yolo = YOLODetector(onnx_path=os.getenv("YOLO_ONNX_PATH", ""))
    ocr = OCRReader()

    # Session for tools
    session = Session(screen=screen, input=inp, detector=yolo, ocr=ocr)

    # Build agent with function tools
    agent = Agent(
        name="App Controller",
        instructions=INSTRUCTIONS,
        tools=[
            my_tools.list_ui,
            my_tools.find_text,
            my_tools.click_text,
            my_tools.type_text,
            my_tools.scroll,
        ],
        context=session,
    )

    result = await Runner.run(agent, input=user_goal, max_turns=8)
    # Print the final output so you can see reasoning
    print("=== FINAL OUTPUT ===")
    print(result.final_output)


if __name__ == "__main__":
    import sys

    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "Click the 'Submit' button"))
