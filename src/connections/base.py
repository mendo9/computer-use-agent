"""Base classes for VM connection abstraction"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class ConnectionResult:
    """Result of connection operation"""

    success: bool
    message: str
    timestamp: float | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class ActionResult:
    """Result of input action"""

    success: bool
    message: str
    timestamp: float | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class VMConnection(ABC):
    """Abstract base class for VM connections"""

    def __init__(self):
        self.is_connected = False
        self.connection_info = {}

    @abstractmethod
    def connect(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> ConnectionResult:
        """Connect to VM"""

    @abstractmethod
    def disconnect(self) -> ConnectionResult:
        """Disconnect from VM"""

    @abstractmethod
    def capture_screen(self) -> tuple[bool, np.ndarray | None]:
        """Capture screenshot, returns (success, image_array)"""

    @abstractmethod
    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Click at coordinates"""

    @abstractmethod
    def type_text(self, text: str) -> ActionResult:
        """Type text"""

    @abstractmethod
    def key_press(self, key: str) -> ActionResult:
        """Press key"""

    def get_connection_info(self) -> dict[str, Any]:
        """Get connection information"""
        return self.connection_info.copy()
