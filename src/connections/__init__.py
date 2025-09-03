"""VM Connection abstraction layer"""

from .base import VMConnection, ConnectionResult, ActionResult
from .vnc_connection import VNCConnection
from .rdp_connection import RDPConnection


def create_connection(connection_type: str) -> VMConnection:
    """Factory function to create connection based on type"""
    if connection_type.lower() == "vnc":
        return VNCConnection()
    elif connection_type.lower() == "rdp":
        return RDPConnection()
    else:
        raise ValueError(f"Unsupported connection type: {connection_type}")


__all__ = [
    "VMConnection",
    "ConnectionResult", 
    "ActionResult",
    "VNCConnection",
    "RDPConnection",
    "create_connection"
]