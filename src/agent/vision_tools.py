"""Professional AI Agent Function Tools for Computer Vision Automation

Updated to use the unified OCR architecture instead of the old UIFinder system.
Provides standardized function tools for AI agents to automate computer interactions
using computer vision. Designed to work with any AI framework - just provide prompts.

Example usage:
    # Initialize once
    tools = VisionToolsConfig()

    # Use in AI agent functions
    screen_info = analyze_screen("What buttons and text are visible?")
    element = find_element("Submit button")
    result = click_element(element)
    verify_action("Form was submitted successfully")
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ocr import (
    find_elements_by_text,
    verify_click_success,
    verify_element_present,
)


@dataclass
class VisionToolsConfig:
    """Configuration for vision tools"""

    models_dir: Path = Path(__file__).parent.parent / "ocr" / "models"
    confidence_threshold: float = 0.6
    ocr_language: str = "en"

    def __post_init__(self):
        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config = VisionToolsConfig()


def configure_vision_tools(confidence_threshold: float = 0.6, ocr_language: str = "en"):
    """Configure vision tools settings"""
    global _config
    _config.confidence_threshold = confidence_threshold
    _config.ocr_language = ocr_language


def _capture_screen() -> np.ndarray | None:
    """Capture current screen using local desktop automation"""
    try:
        from automation.desktop_control import DesktopControl

        desktop = DesktopControl()
        success, screenshot = desktop.capture_screen()
        return screenshot if success else None
    except ImportError:
        # Fallback for environments without local automation
        return None
    except Exception:
        return None


def analyze_screen(prompt: str) -> dict[str, Any]:
    """
    Analyze screen contents with natural language prompt

    Args:
        prompt: Natural language description of what to analyze

    Returns:
        Dict with analysis results
    """
    screenshot = _capture_screen()
    if screenshot is None:
        return {"error": "Screen capture not available", "elements": [], "text": []}

    try:
        # Use analyze_screen_content for complete analysis
        from ocr import analyze_screen_content

        analysis = analyze_screen_content(
            screenshot, prompt, confidence_threshold=_config.confidence_threshold
        )

        return {
            "prompt": prompt,
            "ui_elements": [
                {
                    "type": elem.element_type,
                    "bbox": elem.bbox,
                    "center": elem.center,
                    "confidence": elem.confidence,
                    "text": elem.text,
                    "description": elem.description,
                }
                for elem in analysis.ui_elements
            ],
            "text_elements": [
                {
                    "type": elem.element_type,
                    "bbox": elem.bbox,
                    "center": elem.center,
                    "confidence": elem.confidence,
                    "text": elem.text,
                    "description": elem.description,
                }
                for elem in analysis.text_elements
            ],
            "total_elements": len(analysis.ui_elements),
            "total_text_regions": len(analysis.text_elements),
            "summary": analysis.summary,
        }
    except Exception as e:
        return {"error": f"Screen analysis failed: {e}", "elements": [], "text": []}


def find_element(description: str) -> dict[str, Any] | None:
    """
    Find UI element by description

    Args:
        description: Natural language description of element to find

    Returns:
        Dict with element info or None if not found
    """
    screenshot = _capture_screen()
    if screenshot is None:
        return {"error": "Screen capture not available"}

    try:
        elements = find_elements_by_text(
            screenshot, description, confidence_threshold=_config.confidence_threshold
        )

        if not elements:
            return None

        # Return the most confident element
        best_element = max(elements, key=lambda x: x.confidence)

        return {
            "element_type": best_element.element_type,
            "bbox": best_element.bbox,
            "center": best_element.center,
            "confidence": best_element.confidence,
            "text": best_element.text,
            "description": best_element.description,
        }

    except Exception as e:
        return {"error": f"Element search failed: {e}"}


def click_element(element: dict[str, Any]) -> dict[str, Any]:
    """
    Click on element or coordinates

    Args:
        element: Element dict with center coordinates

    Returns:
        Dict with click result
    """
    if "error" in element:
        return element

    if "center" not in element:
        return {"error": "Element missing center coordinates"}

    try:
        # Take before screenshot for verification
        before_screenshot = _capture_screen()
        if before_screenshot is None:
            return {"error": "Cannot capture screen for verification"}

        # Perform click using local desktop automation
        x, y = element["center"]
        try:
            from automation.desktop_control import DesktopControl

            desktop = DesktopControl()
            click_result = desktop.click(x, y)
            if not click_result.success:
                return {"error": f"Click failed: {click_result.message}"}
        except ImportError:
            return {"error": "Desktop automation not available"}
        except Exception as e:
            return {"error": f"Click failed: {e}"}

        # Wait for UI to update
        time.sleep(1.0)

        # Take after screenshot and verify
        after_screenshot = _capture_screen()
        if after_screenshot is None:
            return {"error": "Cannot capture screen after click"}

        verification = verify_click_success(before_screenshot, after_screenshot)

        return {
            "action": "click",
            "target": element,
            "success": verification.success,
            "message": verification.message,
            "confidence": verification.confidence,
        }

    except Exception as e:
        return {"error": f"Click failed: {e}"}


def type_text_in_field(text: str, field: dict[str, Any]) -> dict[str, Any]:
    """
    Type text in input field

    Args:
        text: Text to type
        field: Field element dict

    Returns:
        Dict with typing result
    """
    if "error" in field:
        return field

    try:
        # First click on field to focus it
        click_result = click_element(field)
        if not click_result.get("success", False):
            return {
                "error": f"Could not focus field: {click_result.get('message', 'Unknown error')}"
            }

        # Type text using local desktop automation
        try:
            from automation.desktop_control import DesktopControl

            desktop = DesktopControl()
            type_result = desktop.type_text(text)
            if not type_result.success:
                return {"error": f"Text input failed: {type_result.message}"}
        except ImportError:
            return {"error": "Desktop automation not available"}
        except Exception as e:
            return {"error": f"Text input failed: {e}"}

        # Wait for text to appear
        time.sleep(0.5)

        # Verify text was entered correctly
        screenshot = _capture_screen()
        if screenshot is None:
            return {"error": "Cannot capture screen for text verification"}

        # Use field bbox for verification if available
        if "bbox" in field:
            # TODO: Implement text input verification using extract_text_from_region
            pass

        return {
            "action": "type_text",
            "text": text,
            "field": field,
            "success": True,  # Placeholder
            "message": f"Typed '{text}' in field",
        }

    except Exception as e:
        return {"error": f"Text input failed: {e}"}


def verify_action(expected: str) -> dict[str, Any]:
    """
    Verify action outcomes

    Args:
        expected: Expected outcome description

    Returns:
        Dict with verification result
    """
    screenshot = _capture_screen()
    if screenshot is None:
        return {"error": "Screen capture not available for verification"}

    try:
        # Use the clean verification system
        result = verify_element_present(
            screenshot, expected, confidence_threshold=_config.confidence_threshold
        )

        return {
            "action": "verify",
            "expected": expected,
            "success": result.success,
            "message": result.message,
            "confidence": result.confidence,
        }

    except Exception as e:
        return {"error": f"Verification failed: {e}"}


def wait_for_element(description: str, max_attempts: int = 10) -> dict[str, Any]:
    """
    Wait for element to appear

    Args:
        description: Element description to wait for
        max_attempts: Maximum number of attempts

    Returns:
        Dict with wait result
    """
    for attempt in range(max_attempts):
        element = find_element(description)

        if element and "error" not in element:
            return {
                "action": "wait_for_element",
                "description": description,
                "success": True,
                "attempts": attempt + 1,
                "element": element,
            }

        if attempt < max_attempts - 1:
            time.sleep(1.0)

    return {
        "action": "wait_for_element",
        "description": description,
        "success": False,
        "attempts": max_attempts,
        "message": f"Element '{description}' not found after {max_attempts} attempts",
    }


def scroll_screen(direction: str, pixels: int = 100) -> dict[str, Any]:
    """
    Scroll screen content

    Args:
        direction: Scroll direction ("up", "down", "left", "right")
        pixels: Number of pixels to scroll

    Returns:
        Dict with scroll result
    """
    try:
        # Implement scrolling using local desktop automation
        from automation.desktop_control import DesktopControl

        desktop = DesktopControl()

        # Get screen center for scroll position
        screenshot = _capture_screen()
        if screenshot is None:
            return {"error": "Cannot capture screen for scrolling"}

        height, width = screenshot.shape[:2]
        center_x, center_y = width // 2, height // 2

        scroll_result = desktop.scroll(center_x, center_y, direction, max(1, pixels // 100))

        return {
            "action": "scroll",
            "direction": direction,
            "pixels": pixels,
            "success": scroll_result.success,
            "message": scroll_result.message,
        }

    except Exception as e:
        return {"error": f"Scroll failed: {e}"}


def take_screenshot(path: str) -> dict[str, Any]:
    """
    Capture screen image

    Args:
        path: Path to save screenshot

    Returns:
        Dict with screenshot result
    """
    screenshot = _capture_screen()
    if screenshot is None:
        return {"error": "Screen capture not available"}

    try:
        cv2.imwrite(path, screenshot)
        return {
            "action": "screenshot",
            "path": path,
            "success": True,
            "message": f"Screenshot saved to {path}",
        }

    except Exception as e:
        return {"error": f"Screenshot save failed: {e}"}


# Export the main functions for AI agent use
__all__ = [
    "VisionToolsConfig",
    "analyze_screen",
    "click_element",
    "configure_vision_tools",
    "find_element",
    "scroll_screen",
    "take_screenshot",
    "type_text_in_field",
    "verify_action",
    "wait_for_element",
]
