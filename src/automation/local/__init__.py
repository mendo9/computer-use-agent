"""Local Desktop Automation Module

Provides local mouse/keyboard control capabilities for desktop automation.
"""

from .desktop_control import DesktopControl
from .form_interface import FormFiller

__all__ = ["DesktopControl", "FormFiller"]
