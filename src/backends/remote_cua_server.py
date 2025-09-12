import base64
import os
from typing import Literal

import httpx
from agent.computers import AsyncComputerHandler
from tenacity import retry, stop_after_attempt, wait_exponential

VM_PROXY_URL = os.getenv("VM_PROXY_URL", "").rstrip("/")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
CLIENT_CERT_PATH = os.getenv("CLIENT_CERT_PATH") or None
CLIENT_KEY_PATH = os.getenv("CLIENT_KEY_PATH") or None
CA_CERT_PATH = os.getenv("CA_CERT_PATH") or True


def _headers():
    h = {"Content-Type": "application/json"}
    if PROXY_API_KEY:
        h["X-API-Key"] = PROXY_API_KEY
    return h


def _client():
    kwargs = {"timeout": 30.0, "verify": CA_CERT_PATH}
    if CLIENT_CERT_PATH and CLIENT_KEY_PATH:
        kwargs["cert"] = (CLIENT_CERT_PATH, CLIENT_KEY_PATH)
    return httpx.AsyncClient(**kwargs)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=4))
async def _cmd(command: str, params: dict | None = None):
    if not VM_PROXY_URL:
        raise RuntimeError("VM_PROXY_URL is required for REMOTE mode")
    params = params or {}
    async with _client() as c:
        r = await c.post(
            f"{VM_PROXY_URL}/cmd", headers=_headers(), json={"command": command, "params": params}
        )
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if ct.startswith("application/json"):
            return await r.json()
        # fallback: assume bytes (e.g., screenshot)
        return {"image": r.content}


class RemoteCuaComputer(AsyncComputerHandler):
    async def get_environment(self) -> Literal["windows", "mac", "linux", "browser"]:
        return "windows"

    async def get_dimensions(self) -> tuple[int, int]:
        res = await _cmd("get_screen_size", {})
        return int(res["width"]), int(res["height"])

    async def get_current_url(self) -> str:
        res = await _cmd("get_current_url", {})
        return str(res["url"])

    async def screenshot(self) -> str:
        res = await _cmd("screenshot", {})
        b64 = res.get("image_b64")
        if not b64 and (blob := res.get("image")):
            b64 = base64.b64encode(blob if isinstance(blob, bytes) else bytes(blob)).decode()
        return f"data:image/png;base64,{b64}"

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

    async def wait(self, ms: int = 1000) -> None:
        import asyncio

        await asyncio.sleep(ms / 1000)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        await _cmd("scroll", {"x": x, "y": y, "scroll_x": scroll_x, "scroll_y": scroll_y})
