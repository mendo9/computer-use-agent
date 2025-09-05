"""
Adapters that satisfy scaffolding.adapters protocols using your existing connections.

TODO: Wire these to your repo's VNC/RDP classes. The signatures below are minimal.
"""

from __future__ import annotations

from dataclasses import dataclass

# Example: wrap your real VNC/RDP
# from connections.vnc_connection import VNCConnection
# from connections.rdp_connection import RDPConnection


@dataclass
class DummyConnection:
    """Replace with real implementation. Must implement connect/disconnect/capture/is_connected."""

    def connect(self): ...
    def disconnect(self): ...
    def capture(self):
        raise NotImplementedError("Implement capture() to return ndarray-like BGR image")

    def is_connected(self) -> bool:
        return True


@dataclass
class DummyController:
    """Replace with real implementation. Must implement move/click/double_click/type_text/key/scroll."""

    def move(self, x: int, y: int): ...
    def click(self, x: int, y: int, button: str = "left"): ...
    def double_click(self, x: int, y: int, button: str = "left"): ...
    def type_text(self, text: str): ...
    def key(self, *keys: str): ...
    def scroll(self, dy: int): ...
