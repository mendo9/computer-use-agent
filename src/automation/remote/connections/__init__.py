"""Remote VM connection implementations"""

from .desktop import DesktopConnection
from .rdp import RDPConnection
from .vnc import VNCConnection

__all__ = ["DesktopConnection", "RDPConnection", "VNCConnection"]


def create_connection(connection_type: str):
    """Factory function to create appropriate connection type"""
    connection_types = {
        "vnc": VNCConnection,
        "rdp": RDPConnection,
        "desktop": DesktopConnection,
    }

    conn_class = connection_types.get(connection_type.lower())
    if not conn_class:
        raise ValueError(f"Unknown connection type: {connection_type}")

    return conn_class()
