"""Action verification and validation tools"""

import time
from dataclasses import dataclass

import cv2
import numpy as np

from src.vm.vision.ocr_reader import OCRReader
from src.vm.vision.ui_finder import UIElement, UIFinder


@dataclass
class VerificationResult:
    """Result of an action verification"""

    success: bool
    message: str
    confidence: float
    screenshot: np.ndarray | None = None
    found_elements: list[UIElement] | None = None


class ActionVerifier:
    """Verify that actions were successful"""

    def __init__(self, ui_finder: UIFinder, ocr_reader: OCRReader):
        """
        Initialize action verifier

        Args:
            ui_finder: UI finder instance
            ocr_reader: OCR reader instance
        """
        self.ui_finder = ui_finder
        self.ocr_reader = ocr_reader

    def verify_click_success(
        self,
        before_screenshot: np.ndarray,
        after_screenshot: np.ndarray,
        expected_change: str = "any",
    ) -> VerificationResult:
        """
        Verify that a click action was successful

        Args:
            before_screenshot: Screenshot before click
            after_screenshot: Screenshot after click
            expected_change: Type of change expected ("any", "dialog", "page_change", etc.)

        Returns:
            VerificationResult
        """
        # Calculate difference between screenshots
        diff = cv2.absdiff(before_screenshot, after_screenshot)
        change_percentage = np.mean(diff > 10) * 100  # Pixels that changed significantly

        if change_percentage < 1.0:
            return VerificationResult(
                success=False,
                message=f"No significant screen change detected ({change_percentage:.1f}%)",
                confidence=0.1,
                screenshot=after_screenshot,
            )

        # Look for specific changes based on expected_change
        if expected_change == "dialog":
            # Look for new dialog boxes or windows
            elements_before = self.ui_finder.find_ui_elements(before_screenshot)
            elements_after = self.ui_finder.find_ui_elements(after_screenshot)

            new_elements = len(elements_after) - len(elements_before)
            if new_elements > 0:
                return VerificationResult(
                    success=True,
                    message=f"Dialog appeared - {new_elements} new UI elements detected",
                    confidence=0.8,
                    screenshot=after_screenshot,
                    found_elements=elements_after,
                )

        # General success based on screen change
        confidence = min(change_percentage / 10.0, 1.0)  # Scale to 0-1

        return VerificationResult(
            success=True,
            message=f"Screen changed ({change_percentage:.1f}% of pixels)",
            confidence=confidence,
            screenshot=after_screenshot,
        )

    def verify_text_input(
        self, screenshot: np.ndarray, input_region: tuple[int, int, int, int], expected_text: str
    ) -> VerificationResult:
        """
        Verify that text was correctly entered in an input field

        Args:
            screenshot: Screenshot after text input
            input_region: Region of the input field (x1, y1, x2, y2)
            expected_text: Text that should be present

        Returns:
            VerificationResult
        """
        # Read text from the input region
        detected_text = self.ocr_reader.read_field_value(screenshot, input_region)

        if detected_text is None:
            return VerificationResult(
                success=False,
                message="No text detected in input field",
                confidence=0.1,
                screenshot=screenshot,
            )

        # Simple text matching (could be improved with fuzzy matching)
        detected_clean = detected_text.strip().lower()
        expected_clean = expected_text.strip().lower()

        if expected_clean in detected_clean or detected_clean in expected_clean:
            confidence = 0.9 if detected_clean == expected_clean else 0.7
            return VerificationResult(
                success=True,
                message=f"Text verified: '{detected_text}' matches expected '{expected_text}'",
                confidence=confidence,
                screenshot=screenshot,
            )

        return VerificationResult(
            success=False,
            message=f"Text mismatch: found '{detected_text}', expected '{expected_text}'",
            confidence=0.2,
            screenshot=screenshot,
        )

    def verify_element_present(
        self, screenshot: np.ndarray, element_description: str
    ) -> VerificationResult:
        """
        Verify that a specific UI element is present

        Args:
            screenshot: Current screenshot
            element_description: Description of element to find

        Returns:
            VerificationResult
        """
        # Try to find element by text
        matching_elements = self.ui_finder.find_element_by_text(screenshot, element_description)

        if matching_elements:
            return VerificationResult(
                success=True,
                message=f"Element found: {element_description}",
                confidence=max(elem.confidence for elem in matching_elements),
                screenshot=screenshot,
                found_elements=matching_elements,
            )

        # Try to find clickable elements if text search failed
        clickable_elements = self.ui_finder.find_clickable_elements(screenshot)

        # Simple keyword matching
        keywords = element_description.lower().split()
        for element in clickable_elements:
            if element.text and any(keyword in element.text.lower() for keyword in keywords):
                return VerificationResult(
                    success=True,
                    message=f"Element found by keyword match: {element.text}",
                    confidence=element.confidence,
                    screenshot=screenshot,
                    found_elements=[element],
                )

        return VerificationResult(
            success=False,
            message=f"Element not found: {element_description}",
            confidence=0.1,
            screenshot=screenshot,
        )

    def verify_page_loaded(
        self, screenshot: np.ndarray, expected_indicators: list[str], timeout: int = 5
    ) -> VerificationResult:
        """
        Verify that a page/application has loaded completely

        Args:
            screenshot: Current screenshot
            expected_indicators: List of text/elements that should be present
            timeout: Not used in this implementation (for compatibility)

        Returns:
            VerificationResult
        """
        found_indicators = []
        total_confidence = 0

        for indicator in expected_indicators:
            elements = self.ui_finder.find_element_by_text(screenshot, indicator)
            if elements:
                found_indicators.append(indicator)
                total_confidence += max(elem.confidence for elem in elements)

        if not found_indicators:
            return VerificationResult(
                success=False,
                message=f"Page load verification failed - none of {expected_indicators} found",
                confidence=0.1,
                screenshot=screenshot,
            )

        success_rate = len(found_indicators) / len(expected_indicators)
        avg_confidence = total_confidence / len(found_indicators)

        return VerificationResult(
            success=success_rate >= 0.5,  # At least half the indicators should be present
            message=f"Page loaded - found {len(found_indicators)}/{len(expected_indicators)} indicators: {found_indicators}",
            confidence=avg_confidence * success_rate,
            screenshot=screenshot,
        )

    def wait_for_element(
        self, capture_func, element_description: str, max_attempts: int = 10, delay: float = 1.0
    ) -> VerificationResult:
        """
        Wait for a specific element to appear

        Args:
            capture_func: Function to capture current screenshot
            element_description: Description of element to wait for
            max_attempts: Maximum number of attempts
            delay: Delay between attempts in seconds

        Returns:
            VerificationResult
        """
        for attempt in range(max_attempts):
            screenshot = capture_func()
            if screenshot is None:
                continue

            result = self.verify_element_present(screenshot, element_description)
            if result.success:
                result.message += f" (found after {attempt + 1} attempts)"
                return result

            if attempt < max_attempts - 1:  # Don't sleep on last attempt
                time.sleep(delay)

        return VerificationResult(
            success=False,
            message=f"Element '{element_description}' not found after {max_attempts} attempts",
            confidence=0.1,
        )

    def compare_screenshots(self, screen1: np.ndarray, screen2: np.ndarray) -> dict[str, float]:
        """
        Compare two screenshots and return similarity metrics

        Args:
            screen1: First screenshot
            screen2: Second screenshot

        Returns:
            Dictionary with similarity metrics
        """
        if screen1.shape != screen2.shape:
            return {"similarity": 0.0, "mse": float("inf"), "change_percentage": 100.0}

        # Mean Squared Error
        mse = np.mean((screen1.astype(float) - screen2.astype(float)) ** 2)

        # Change percentage
        diff = cv2.absdiff(screen1, screen2)
        change_percentage = np.mean(diff > 10) * 100

        # Similarity score (inverse of normalized MSE)
        max_possible_mse = 255**2
        similarity = 1.0 - (mse / max_possible_mse)

        return {"similarity": similarity, "mse": mse, "change_percentage": change_percentage}

    def create_diff_visualization(self, screen1: np.ndarray, screen2: np.ndarray) -> np.ndarray:
        """
        Create a visualization showing differences between two screenshots

        Args:
            screen1: First screenshot
            screen2: Second screenshot

        Returns:
            Difference visualization image
        """
        if screen1.shape != screen2.shape:
            return np.zeros_like(screen1)

        # Create difference image
        diff = cv2.absdiff(screen1, screen2)

        # Threshold to highlight significant changes
        thresh = cv2.threshold(cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY), 10, 255, cv2.THRESH_BINARY)[
            1
        ]

        # Create colored difference visualization
        diff_colored = diff.copy()
        diff_colored[thresh > 0] = [0, 0, 255]  # Highlight changes in red

        return diff_colored
