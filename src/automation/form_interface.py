"""High-Level Form Entry Interface

Combines OCR vision capabilities with local desktop automation to provide
easy form filling functionality. This bridges the gap between "what to click"
(from OCR) and "how to click it" (from automation).

Usage:
    form_filler = FormFiller()
    form_filler.fill_field("Username", "john.doe")
    form_filler.fill_field("Password", "secret123")
    form_filler.click_button("Submit")
"""

import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

import numpy as np

from automation.desktop_control import ActionResult, DesktopControl
from ocr import find_elements_by_text


class FormFiller:
    """High-level interface for automated form filling using OCR + local automation"""

    def __init__(self):
        """Initialize form filler with desktop control and OCR capabilities"""
        self.desktop = DesktopControl()
        self.last_screenshot: np.ndarray | None = None
        self.screenshot_cache_time: float = 0

    def _get_current_screenshot(self, max_age: float = 1.0) -> np.ndarray | None:
        """Get current screenshot with caching to avoid excessive captures"""
        import time

        current_time = time.time()

        # Use cached screenshot if recent enough
        if self.last_screenshot is not None and current_time - self.screenshot_cache_time < max_age:
            return self.last_screenshot

        # Capture fresh screenshot
        success, screenshot = self.desktop.capture_screen()
        if success:
            self.last_screenshot = screenshot
            self.screenshot_cache_time = current_time
            return screenshot
        return None

    def find_field_by_label(
        self, label_text: str, confidence_threshold: float = 0.6
    ) -> dict[str, Any] | None:
        """
        Find form field by its label text

        Args:
            label_text: Text to search for (e.g., "Username", "Email", "Password")
            confidence_threshold: Minimum OCR confidence

        Returns:
            Dictionary with field information or None if not found

        Example:
            field = form_filler.find_field_by_label("Username")
            if field:
                print(f"Found field at {field['center']}")
        """
        screenshot = self._get_current_screenshot()
        if screenshot is None:
            return None

        try:
            elements = find_elements_by_text(
                screenshot,
                label_text,
                confidence_threshold=confidence_threshold,
                case_sensitive=False,
            )

            if elements:
                # Get the best match
                best_element = max(elements, key=lambda x: x.confidence)

                return {
                    "text": best_element.text,
                    "center": best_element.center,
                    "bbox": best_element.bbox,
                    "confidence": best_element.confidence,
                    "description": best_element.description,
                }

        except Exception as e:
            print(f"Error finding field by label '{label_text}': {e}")

        return None

    def find_input_field_near(
        self, label_center: tuple, search_radius: int = 100
    ) -> dict[str, Any] | None:
        """
        Find input field near a label

        Args:
            label_center: (x, y) coordinates of label
            search_radius: Radius to search for input fields

        Returns:
            Dictionary with input field information or None if not found
        """
        screenshot = self._get_current_screenshot()
        if screenshot is None:
            return None

        try:
            # Look for common input field indicators near the label
            input_indicators = ["textfield", "input", "field", "_", "____"]

            label_x, label_y = label_center

            # Search for input elements in the vicinity
            for indicator in input_indicators:
                elements = find_elements_by_text(
                    screenshot,
                    indicator,
                    confidence_threshold=0.3,
                    search_radius=search_radius,
                    case_sensitive=False,
                )

                # Find closest element to label
                closest_element = None
                min_distance = float("inf")

                for element in elements:
                    ex, ey = element.center
                    distance = ((ex - label_x) ** 2 + (ey - label_y) ** 2) ** 0.5

                    if distance <= search_radius and distance < min_distance:
                        min_distance = distance
                        closest_element = element

                if closest_element:
                    return {
                        "center": closest_element.center,
                        "bbox": closest_element.bbox,
                        "confidence": closest_element.confidence,
                        "distance_from_label": min_distance,
                    }

        except Exception as e:
            print(f"Error finding input field near {label_center}: {e}")

        return None

    def fill_field(
        self, label_text: str, value: str, click_offset: tuple = (0, 25)
    ) -> ActionResult:
        """
        Fill a form field by finding its label and entering text

        Args:
            label_text: Label text to search for
            value: Text to enter in the field
            click_offset: (x, y) offset from label to click (default: slightly below)

        Returns:
            ActionResult indicating success or failure

        Example:
            result = form_filler.fill_field("Username", "john.doe")
            result = form_filler.fill_field("Email", "john@example.com")
        """
        try:
            # Find the label
            field_info = self.find_field_by_label(label_text)
            if not field_info:
                return ActionResult(False, f"Could not find field with label: {label_text}")

            label_x, label_y = field_info["center"]

            # Try to find actual input field near label
            input_field = self.find_input_field_near((label_x, label_y))
            if input_field:
                # Click on the actual input field
                click_x, click_y = input_field["center"]
            else:
                # Click near the label with offset
                offset_x, offset_y = click_offset
                click_x = label_x + offset_x
                click_y = label_y + offset_y

            # Click to focus the field
            click_result = self.desktop.click(click_x, click_y)
            if not click_result.success:
                return ActionResult(False, f"Failed to click field: {click_result.message}")

            # Clear field (select all and delete)
            self.desktop.key_press("cmd+a")  # Select all

            # Type the value
            type_result = self.desktop.type_text(value)
            if not type_result.success:
                return ActionResult(False, f"Failed to type text: {type_result.message}")

            return ActionResult(True, f"Successfully filled '{label_text}' with '{value}'")

        except Exception as e:
            return ActionResult(False, f"Error filling field '{label_text}': {e}")

    def click_button(self, button_text: str, confidence_threshold: float = 0.6) -> ActionResult:
        """
        Click a button by its text

        Args:
            button_text: Text on the button (e.g., "Submit", "Login", "OK")
            confidence_threshold: Minimum OCR confidence

        Returns:
            ActionResult indicating success or failure

        Example:
            result = form_filler.click_button("Submit")
            result = form_filler.click_button("Login")
        """
        try:
            button_info = self.find_field_by_label(button_text, confidence_threshold)
            if not button_info:
                return ActionResult(False, f"Could not find button: {button_text}")

            button_x, button_y = button_info["center"]

            click_result = self.desktop.click(button_x, button_y)
            if click_result.success:
                return ActionResult(True, f"Successfully clicked '{button_text}' button")
            else:
                return ActionResult(False, f"Failed to click button: {click_result.message}")

        except Exception as e:
            return ActionResult(False, f"Error clicking button '{button_text}': {e}")

    def fill_form(self, form_data: dict[str, str]) -> dict[str, ActionResult]:
        """
        Fill multiple form fields at once

        Args:
            form_data: Dictionary mapping field labels to values

        Returns:
            Dictionary mapping field labels to ActionResult objects

        Example:
            results = form_filler.fill_form({
                "Username": "john.doe",
                "Password": "secret123",
                "Email": "john@example.com"
            })
        """
        results = {}

        for label, value in form_data.items():
            # Refresh screenshot for each field to account for UI changes
            self.last_screenshot = None
            result = self.fill_field(label, value)
            results[label] = result

            if not result.success:
                print(f"Warning: Failed to fill '{label}': {result.message}")

        return results

    def get_form_fields(self, common_labels: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Detect form fields on current screen

        Args:
            common_labels: List of common field labels to look for

        Returns:
            List of detected form field information
        """
        if common_labels is None:
            common_labels = [
                "Username",
                "Email",
                "Password",
                "Name",
                "Address",
                "Phone",
                "Company",
                "Title",
                "Message",
                "Comment",
            ]

        detected_fields = []

        for label in common_labels:
            field_info = self.find_field_by_label(label, confidence_threshold=0.5)
            if field_info:
                detected_fields.append(field_info)

        return detected_fields

    def wait_for_element(
        self, text: str, timeout: float = 10.0, check_interval: float = 1.0
    ) -> dict[str, Any] | None:
        """
        Wait for an element to appear on screen

        Args:
            text: Text to wait for
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds

        Returns:
            Element information if found, None if timeout
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            # Force fresh screenshot
            self.last_screenshot = None
            element = self.find_field_by_label(text)

            if element:
                return element

            time.sleep(check_interval)

        return None
