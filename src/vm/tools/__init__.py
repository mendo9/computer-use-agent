"""Tools module for VM interaction"""

from ocr.verification import ActionVerifier, VerificationResult
from vm.tools.input_actions import ActionResult, InputActions
from vm.tools.screen_capture import ScreenCapture

__all__ = [
    "ActionResult",
    "ActionVerifier",
    "InputActions",
    "ScreenCapture",
    "VerificationResult",
]
