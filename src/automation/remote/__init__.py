"""Remote VM automation module"""

from .agents import AppControllerAgent, VMNavigatorAgent, VMSession, VMTarget
from .connections import DesktopConnection, RDPConnection, VNCConnection, create_connection
from .tools import InputActions, ScreenCapture

__all__ = [
    # Connections
    "VNCConnection",
    "RDPConnection",
    "DesktopConnection",
    "create_connection",
    # Agents
    "VMNavigatorAgent",
    "AppControllerAgent",
    "VMSession",
    "VMTarget",
    # Tools
    "ScreenCapture",
    "InputActions",
]
