"""Core types shared across all automation modules"""

import time
from dataclasses import dataclass


@dataclass
class ActionResult:
    """Result of an automation action (local or remote)"""

    success: bool
    message: str
    timestamp: float | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class ConnectionResult:
    """Result of connection operation"""

    success: bool
    message: str
    timestamp: float | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
