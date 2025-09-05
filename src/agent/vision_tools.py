"""Professional AI Agent Function Tools for Computer Vision Automation

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

from ocr.verification.verification import ActionVerifier
from ocr.vision.finder import UIFinder


@dataclass
class VisionToolsConfig:
    """Configuration for vision tools"""

    models_dir: Path = Path(__file__).parent.parent / "ocr" / "models"
    yolo_model_path: str | None = None
    confidence_threshold: float = 0.6
    use_ui_focused: bool = True
    ocr_language: str = "en"

    def __post_init__(self):
        if self.yolo_model_path is None:
            self.yolo_model_path = str(self.models_dir / "yolov8s.onnx")


# Global configuration instance
_config = VisionToolsConfig()
_ui_finder: UIFinder | None = None
_verifier: ActionVerifier | None = None


def _get_ui_finder() -> UIFinder:
    """Get or create UIFinder instance"""
    global _ui_finder, _config

    if _ui_finder is None:
        _ui_finder = UIFinder(
            yolo_model_path=_config.yolo_model_path,
            yolo_confidence=_config.confidence_threshold,
            use_gpu=False,  # Default to CPU for compatibility
        )

    return _ui_finder


def _get_verifier() -> ActionVerifier:
    """Get or create ActionVerifier instance"""
    global _verifier

    if _verifier is None:
        ui_finder = _get_ui_finder()
        _verifier = ActionVerifier(ui_finder, ui_finder.ocr_reader)

    return _verifier


def take_screenshot(save_path: str | None = None) -> np.ndarray:
    """
    Take a screenshot of the current desktop

    Args:
        save_path: Optional path to save the screenshot

    Returns:
        Screenshot as numpy array

    Example:
        screenshot = take_screenshot("/tmp/screen.png")
    """
    # This is a placeholder - would need to be implemented per platform
    # For now, return a dummy image
    from vm.connections.desktop_connection import DesktopConnection

    conn = DesktopConnection()
    success, image = conn.capture_screen()

    if not success or image is None:
        raise RuntimeError("Failed to capture screenshot")

    if save_path:
        cv2.imwrite(save_path, image)

    return image


def analyze_screen(prompt: str, screenshot: np.ndarray | None = None) -> dict[str, Any]:
    """
    Analyze the current screen and return detailed information

    Args:
        prompt: Natural language prompt describing what to analyze
        screenshot: Optional screenshot to analyze (takes new one if None)

    Returns:
        Dictionary with analysis results

    Example:
        result = analyze_screen("What buttons and input fields are visible?")
        print(f"Found {len(result['ui_elements'])} UI elements")
    """
    if screenshot is None:
        screenshot = take_screenshot()

    ui_finder = _get_ui_finder()

    # Find all UI elements
    ui_elements = ui_finder.find_ui_elements(screenshot)

    # Find clickable elements specifically
    clickable_elements = ui_finder.find_clickable_elements(screenshot)

    # Find input fields
    input_fields = ui_finder.find_input_fields(screenshot)

    # Extract text content
    text_detections = ui_finder.ocr_reader.read_text(screenshot)

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
            for elem in ui_elements
        ],
        "clickable_elements": len(clickable_elements),
        "input_fields": len(input_fields),
        "text_content": [
            {
                "text": text.text,
                "confidence": text.confidence,
                "bbox": text.rect_bbox,
                "center": text.center,
            }
            for text in text_detections
        ],
        "summary": {
            "total_elements": len(ui_elements),
            "clickable_count": len(clickable_elements),
            "input_fields_count": len(input_fields),
            "text_blocks_count": len(text_detections),
        },
    }


def find_element(description: str, screenshot: np.ndarray | None = None) -> dict[str, Any] | None:
    """
    Find a specific UI element by description

    Args:
        description: Natural language description of the element to find
        screenshot: Optional screenshot to search in

    Returns:
        Element information dictionary or None if not found

    Example:
        element = find_element("Submit button")
        element = find_element("Username input field")
        element = find_element("Settings menu")
    """
    if screenshot is None:
        screenshot = take_screenshot()

    ui_finder = _get_ui_finder()

    # Try finding by text first
    elements = ui_finder.find_element_by_text(screenshot, description)

    if not elements:
        # Fall back to analyzing all elements and finding best match
        all_elements = ui_finder.find_ui_elements(screenshot)

        # Simple keyword matching for now (could be enhanced with NLP)
        keywords = description.lower().split()
        best_match = None
        best_score = 0

        for element in all_elements:
            score = 0

            # Score based on text content
            if element.text:
                text_lower = element.text.lower()
                for keyword in keywords:
                    if keyword in text_lower:
                        score += 10

            # Score based on element type
            if element.description:
                desc_lower = element.description.lower()
                for keyword in keywords:
                    if keyword in desc_lower:
                        score += 5

            if score > best_score:
                best_score = score
                best_match = element

        elements = [best_match] if best_match else []

    if not elements:
        return None

    # Return the best element
    best_element = max(elements, key=lambda x: x.confidence)

    return {
        "type": best_element.element_type,
        "bbox": best_element.bbox,
        "center": best_element.center,
        "confidence": best_element.confidence,
        "text": best_element.text,
        "description": best_element.description,
        "clickable": True,  # Assume found elements are clickable
    }


def click_element(
    element: dict[str, Any] | tuple[int, int], button: str = "left"
) -> dict[str, Any]:
    """
    Click on a UI element or coordinates

    Args:
        element: Element dict from find_element() or (x, y) coordinates
        button: Mouse button ("left", "right", "middle")

    Returns:
        Action result dictionary

    Example:
        element = find_element("Submit button")
        result = click_element(element)

        # Or click coordinates directly
        result = click_element((100, 200))
    """
    if isinstance(element, tuple):
        x, y = element
    elif isinstance(element, dict) and "center" in element:
        x, y = element["center"]
    else:
        raise ValueError("Element must be a dictionary with 'center' key or (x, y) tuple")

    # Take before screenshot for verification
    before_screenshot = take_screenshot()

    # Perform click (this would need platform-specific implementation)
    from vm.connections.desktop_connection import DesktopConnection

    conn = DesktopConnection()
    action_result = conn.click(x, y, button)

    # Wait a moment for UI to update
    time.sleep(0.5)

    # Take after screenshot
    after_screenshot = take_screenshot()

    return {
        "success": action_result.success,
        "message": action_result.message,
        "coordinates": (x, y),
        "button": button,
        "screen_changed": not np.array_equal(before_screenshot, after_screenshot),
    }


def type_text_in_field(text: str, field_element: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Type text in an input field

    Args:
        text: Text to type
        field_element: Optional field element to click first (from find_element)

    Returns:
        Action result dictionary

    Example:
        field = find_element("Username field")
        result = type_text_in_field("john.doe", field)

        # Or just type without clicking a field first
        result = type_text_in_field("Hello world")
    """
    # Click field first if provided
    if field_element:
        click_result = click_element(field_element)
        if not click_result["success"]:
            return {
                "success": False,
                "message": f"Failed to click field: {click_result['message']}",
                "text": text,
            }

        # Wait for field to become active
        time.sleep(0.2)

    # Type text (platform-specific implementation needed)
    from vm.connections.desktop_connection import DesktopConnection

    conn = DesktopConnection()
    action_result = conn.type_text(text)

    return {
        "success": action_result.success,
        "message": action_result.message,
        "text": text,
        "field_clicked": field_element is not None,
    }


def verify_action(expected_outcome: str, screenshot: np.ndarray | None = None) -> dict[str, Any]:
    """
    Verify that an action had the expected outcome

    Args:
        expected_outcome: Natural language description of what should have happened
        screenshot: Optional screenshot to verify against

    Returns:
        Verification result dictionary

    Example:
        result = verify_action("Login form should be submitted")
        result = verify_action("Settings dialog should be open")
        result = verify_action("Text should be entered in the field")
    """
    if screenshot is None:
        screenshot = take_screenshot()

    verifier = _get_verifier()

    # Use the verifier to check if expected elements are present
    verification_result = verifier.verify_element_present(screenshot, expected_outcome)

    return {
        "success": verification_result.success,
        "message": verification_result.message,
        "confidence": verification_result.confidence,
        "expected_outcome": expected_outcome,
        "elements_found": len(verification_result.found_elements or []),
    }


def wait_for_element(
    description: str, max_attempts: int = 10, delay: float = 1.0
) -> dict[str, Any] | None:
    """
    Wait for a specific element to appear

    Args:
        description: Element description to wait for
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds

    Returns:
        Element information or None if timeout

    Example:
        element = wait_for_element("Loading complete message", max_attempts=30)
    """
    for attempt in range(max_attempts):
        element = find_element(description)
        if element:
            return element

        if attempt < max_attempts - 1:
            time.sleep(delay)

    return None


def scroll_screen(direction: str = "down", pixels: int = 400) -> dict[str, Any]:
    """
    Scroll the screen

    Args:
        direction: "up", "down", "left", "right"
        pixels: Number of pixels to scroll

    Returns:
        Action result dictionary

    Example:
        result = scroll_screen("down", 300)
    """
    from vm.connections.desktop_connection import DesktopConnection

    conn = DesktopConnection()

    # Convert direction to scroll delta
    dy = 0
    if direction == "down":
        dy = pixels
    elif direction == "up":
        dy = -pixels

    action_result = conn.scroll(0, dy)  # Only vertical scroll for now

    return {
        "success": action_result.success,
        "message": action_result.message,
        "direction": direction,
        "pixels": pixels,
    }


def configure_vision_tools(
    models_dir: str | None = None,
    confidence_threshold: float = 0.6,
    use_ui_focused: bool = True,
    ocr_language: str = "en",
) -> None:
    """
    Configure the vision tools settings

    Args:
        models_dir: Path to models directory
        confidence_threshold: Minimum confidence for detections
        use_ui_focused: Whether to use UI-focused YOLO classes
        ocr_language: Language for OCR recognition

    Example:
        configure_vision_tools(confidence_threshold=0.7, use_ui_focused=True)
    """
    global _config, _ui_finder, _verifier

    # Update configuration
    if models_dir:
        _config.models_dir = Path(models_dir)
        _config.yolo_model_path = str(_config.models_dir / "yolov8s.onnx")

    _config.confidence_threshold = confidence_threshold
    _config.use_ui_focused = use_ui_focused
    _config.ocr_language = ocr_language

    # Reset instances to pick up new config
    _ui_finder = None
    _verifier = None
