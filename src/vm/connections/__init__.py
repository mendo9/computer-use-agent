"""VM Connection Module

Provides connection abstractions for remote VMs via VNC and RDP protocols.
"""

from .base import ActionResult, ConnectionResult, VMConnection
from .desktop_connection import DesktopConnection
from .rdp_connection import RDPConnection
from .vnc_connection import VNCConnection


def create_connection(connection_type: str) -> VMConnection:
    """Factory function to create VM connections"""
    if connection_type.lower() == "vnc":
        return VNCConnection()
    elif connection_type.lower() == "rdp":
        return RDPConnection()
    elif connection_type.lower() == "desktop":
        return DesktopConnection()
    else:
        raise ValueError(f"Unsupported connection type: {connection_type}")


__all__ = [
    "ActionResult",
    "ConnectionResult",
    "DesktopConnection",
    "RDPConnection",
    "VMConnection",
    "VNCConnection",
    "create_connection",
]
