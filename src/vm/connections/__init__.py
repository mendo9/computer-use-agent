"""VM Connection abstraction layer"""

from vm.connections.base import ActionResult, ConnectionResult, VMConnection
from vm.connections.rdp_connection import RDPConnection
from vm.connections.vnc_connection import VNCConnection


def create_connection(connection_type: str) -> VMConnection:
    """Factory function to create connection based on type"""
    if connection_type.lower() == "vnc":
        return VNCConnection()
    elif connection_type.lower() == "rdp":
        return RDPConnection()
    else:
        raise ValueError(f"Unsupported connection type: {connection_type}")


__all__ = [
    "ActionResult",
    "ConnectionResult",
    "RDPConnection",
    "VMConnection",
    "VNCConnection",
    "create_connection",
]
