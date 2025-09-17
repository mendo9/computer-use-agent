import base64
import json
import os
import re
from typing import Literal

import httpx
from agent.computers import AsyncComputerHandler
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

VM_PROXY_URL = os.getenv("VM_PROXY_URL", "").rstrip("/")


def _client():
    return httpx.AsyncClient(timeout=30.0)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4))
async def _cmd(command: str, params: dict | None = None):
    if not VM_PROXY_URL:
        raise RuntimeError("VM_PROXY_URL is required for REMOTE mode")

    async with _client() as c:
        r = await c.post(f"{VM_PROXY_URL}/cmd", json={"command": command, "params": params or {}})
        r.raise_for_status()

        # Computer-server returns SSE format: "data: {json}\n\n"
        content = await r.aread()
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        # Extract the last JSON data from SSE format
        data_lines = re.findall(r"data: (.+?)(?:\n\n|\n$)", content, re.DOTALL)
        if not data_lines:
            raise RuntimeError(f"No data found in response: {content}")

        try:
            result = json.loads(data_lines[-1].strip())
            if isinstance(result, dict) and (result.get("success") is False or "error" in result):
                raise RuntimeError(f"Computer-server error: {result.get('error', 'Unknown error')}")
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse response: {data_lines[-1]}") from e


class WindowsComputerInterface(AsyncComputerHandler):
    """Interface for controlling a remote Windows computer via computer-server."""

    async def get_environment(self) -> Literal["windows", "mac", "linux", "browser"]:
        return "windows"

    async def get_dimensions(self) -> tuple[int, int]:
        res = await _cmd("get_screen_size", {})
        if "size" in res:
            return int(res["size"].get("width")), int(res["size"].get("height"))
        else:
            raise RuntimeError("No size data found in response")

    async def get_cursor_position(self) -> tuple[int, int]:
        """Get the current position of the mouse cursor"""
        res = await _cmd("get_cursor_position", {})
        if "position" in res:
            return int(res["position"].get("x")), int(res["position"].get("y"))
        else:
            raise RuntimeError("No cursor position data found in response")

    async def screenshot(self) -> str:
        res = await _cmd("screenshot", {})
        # Computer-server returns base64 string in image_data field
        if "image_data" in res:
            return res["image_data"]
        else:
            raise RuntimeError("No image data found in response")

    async def click(self, x: int, y: int, button: str = "left") -> None:
        cmd = {"left": "left_click", "right": "right_click", "middle": "middle_click"}.get(
            button, "left_click"
        )
        await _cmd(cmd, {"x": x, "y": y})

    async def type(self, text: str) -> None:
        await _cmd("type_text", {"text": text})

    async def keypress(self, keys) -> None:
        if isinstance(keys, str):
            await _cmd("press_key", {"key": keys})
        else:
            await _cmd("hotkey", {"keys": keys})

    async def move(self, x: int, y: int) -> None:
        await _cmd("move_cursor", {"x": x, "y": y})

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        await _cmd("scroll", {"x": x, "y": y, "scroll_x": scroll_x, "scroll_y": scroll_y})


class WindowsComputer:
    """Computer-like wrapper for remote Windows computer, matching the Lume VM pattern."""

    def __init__(self, vm_proxy_url: str = None):
        self.vm_proxy_url = vm_proxy_url or VM_PROXY_URL
        if not self.vm_proxy_url:
            raise ValueError("VM_PROXY_URL must be provided either as parameter or environment variable")

        # Set the global URL for the _cmd function
        global VM_PROXY_URL
        VM_PROXY_URL = self.vm_proxy_url

        self.interface = WindowsComputerInterface()

    async def screenshot_bytes(self) -> bytes:
        """Take a screenshot and return as bytes for image processing."""
        # Get base64 string from interface
        b64_string = await self.interface.screenshot()
        # Decode to bytes
        return base64.b64decode(b64_string)

    async def __aenter__(self):
        """Async context manager entry - test connection."""
        try:
            # Test connection by getting screen size
            await self.interface.get_dimensions()
            logger.info(f"Connected to Windows computer-server at {self.vm_proxy_url}")
            return self
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Windows computer-server at {self.vm_proxy_url}: {e}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup if needed."""
        logger.info("Disconnected from Windows computer-server")


def get_computer_windows() -> WindowsComputer:
    """
    Get a WindowsComputer instance connected to a remote Windows VM.

    Expects a computer-server to be running on the Windows VM.
    Configure VM_PROXY_URL environment variable to point to the Windows VM.
    """
    vm_url = os.getenv("VM_PROXY_URL")
    if not vm_url:
        raise RuntimeError(
            "VM_PROXY_URL environment variable is required. "
            "Set it to http://YOUR_WINDOWS_VM_IP:8000"
        )

    computer = WindowsComputer(vm_url)
    logger.info(f"Created Windows computer instance for {vm_url}")
    return computer