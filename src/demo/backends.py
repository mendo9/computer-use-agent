"""
Adapters that satisfy scaffolding.adapters protocols using your existing connections.

Wires VM connections to work with the new OCR scaffolding system using the VMConnection abstraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vm.connections.base import VMConnection


@dataclass
class ConnectionAdapter:
    """Generic adapter that implements the Connection protocol for the OCR system using VMConnection abstraction."""

    vm_connection: VMConnection
    host: str
    port: int
    credentials: dict[str, Any]

    def connect(self) -> None:
        result = self.vm_connection.connect(self.host, self.port, **self.credentials)
        if not result.success:
            raise ConnectionError(f"VM connection failed: {result.message}")

    def disconnect(self) -> None:
        result = self.vm_connection.disconnect()
        if not result.success:
            raise ConnectionError(f"Disconnect failed: {result.message}")

    def capture(self) -> Any:
        success, frame = self.vm_connection.capture_screen()
        if not success or frame is None:
            raise RuntimeError("Failed to capture screen")
        return frame

    def is_connected(self) -> bool:
        return self.vm_connection.is_connected


@dataclass
class ControllerAdapter:
    """Generic controller adapter that implements the Controller protocol for input actions using VMConnection abstraction."""

    vm_connection: VMConnection

    def move(self, x: int, y: int) -> None:
        # Move functionality depends on specific VM connection implementation
        # Some implementations may not support mouse move without click
        pass

    def click(self, x: int, y: int, button: str = "left") -> None:
        result = self.vm_connection.click(x, y, button)
        if not result.success:
            raise RuntimeError(f"Click failed: {result.message}")

    def double_click(self, x: int, y: int, button: str = "left") -> None:
        # Double click by clicking twice with small delay
        self.click(x, y, button)
        import time

        time.sleep(0.1)
        self.click(x, y, button)

    def type_text(self, text: str) -> None:
        result = self.vm_connection.type_text(text)
        if not result.success:
            raise RuntimeError(f"Type text failed: {result.message}")

    def key(self, *keys: str) -> None:
        for key in keys:
            result = self.vm_connection.key_press(key)
            if not result.success:
                raise RuntimeError(f"Key press failed: {result.message}")

    def scroll(self, dy: int) -> None:
        # Scrolling implementation depends on specific VM connection
        # This is a placeholder - actual implementation may vary
        pass
