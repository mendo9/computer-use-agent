"""Local Desktop Automation Package

Provides local mouse/keyboard control capabilities separate from VM/remote control.
This package handles direct interaction with the local desktop environment.

Key Components:
- desktop_control.py: Local macOS desktop automation (moved from vm/connections/)
- form_interface.py: High-level form entry interface combining OCR + automation

Usage:
    from automation import DesktopControl, FormFiller

    # Low-level desktop automation
    desktop = DesktopControl()
    desktop.click(100, 200)
    desktop.type_text("Hello World")

    # High-level form filling
    form_filler = FormFiller()
    form_filler.fill_field("Username", "john.doe")
    form_filler.click_button("Submit")
"""

from .desktop_control import DesktopControl
from .form_interface import FormFiller

__version__ = "1.0.0"

__all__ = [
    "DesktopControl",
    "FormFiller",
]
