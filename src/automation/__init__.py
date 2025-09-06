"""Unified Automation Package

Provides both local and remote automation capabilities with a unified API.

Structure:
- core/: Shared types and base classes (ActionResult, ConnectionResult, VMConnection)
- local/: Local desktop automation (DesktopControl, FormFiller)
- remote/: VM/remote automation
  - connections/: VM connection implementations (VNC, RDP, Desktop)
  - agents/: VM automation agents (VMNavigator, AppController)
  - tools/: VM interaction tools (ScreenCapture, InputActions)
- orchestrator.py: Main VM automation orchestrator

Usage:
    # Local automation
    from automation.local import DesktopControl, FormFiller
    
    # Remote automation
    from automation.remote import VNCConnection, VMNavigatorAgent
    from automation.orchestrator import VMAutomation
    
    # Shared types
    from automation.core import ActionResult, ConnectionResult
"""

# Core types
from .core import ActionResult, ConnectionResult

# Local automation
from .local import DesktopControl, FormFiller

# Remote automation
from .remote import (
    AppControllerAgent,
    DesktopConnection,
    InputActions,
    RDPConnection,
    ScreenCapture,
    VMNavigatorAgent,
    VMSession,
    VMTarget,
    VNCConnection,
    create_connection,
)

# Orchestrator
from .orchestrator import VMAutomation, VMConfig

__version__ = "2.0.0"

__all__ = [
    # Core types
    "ActionResult",
    "ConnectionResult",
    # Local automation
    "DesktopControl",
    "FormFiller",
    # Remote connections
    "VNCConnection",
    "RDPConnection",
    "DesktopConnection",
    "create_connection",
    # Remote agents
    "VMNavigatorAgent",
    "AppControllerAgent",
    "VMSession",
    "VMTarget",
    # Remote tools
    "ScreenCapture",
    "InputActions",
    # Orchestrator
    "VMAutomation",
    "VMConfig",
]
