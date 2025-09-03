"""Combined UI element finder using YOLO + OCR"""

import math
from dataclasses import dataclass

import cv2
import numpy as np

from .ocr_reader import OCRReader, TextDetection
from .yolo_detector import Detection, YOLODetector


@dataclass
class UIElement:
    """Combined UI element with both visual and text information"""

    element_type: str  # "detected" or "text" or "combined"
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    center: tuple[int, int]
    confidence: float

    # Visual detection info (if available)
    yolo_detection: Detection | None = None

    # Text info (if available)
    text_detection: TextDetection | None = None
    text: str | None = None

    # Metadata
    element_id: str | None = None
    description: str | None = None


class UIFinder:
    """Combined UI element finder using YOLO detection + OCR"""

    def __init__(self, yolo_model_path: str, yolo_confidence: float = 0.6, use_gpu: bool = False):
        """Initialize UI finder with YOLO and OCR"""
        self.yolo_detector = YOLODetector(yolo_model_path, yolo_confidence)
        self.ocr_reader = OCRReader(use_gpu=use_gpu)

        print("UIFinder initialized with YOLOv8s + PaddleOCR")

    def find_ui_elements(self, image: np.ndarray) -> list[UIElement]:
        """Find all UI elements using both YOLO and OCR"""
        # Get YOLO detections
        yolo_detections = self.yolo_detector.detect(image)

        # Get OCR text detections
        text_detections = self.ocr_reader.read_text(image)

        # Combine results
        ui_elements = []

        # Add YOLO detections as UI elements
        for detection in yolo_detections:
            ui_element = UIElement(
                element_type="detected",
                bbox=detection.bbox,
                center=detection.center,
                confidence=detection.confidence,
                yolo_detection=detection,
                description=f"Detected {detection.class_name}",
            )
            ui_elements.append(ui_element)

        # Add text detections as UI elements
        for text_det in text_detections:
            ui_element = UIElement(
                element_type="text",
                bbox=text_det.rect_bbox,
                center=text_det.center,
                confidence=text_det.confidence,
                text_detection=text_det,
                text=text_det.text,
                description=f"Text: {text_det.text}",
            )
            ui_elements.append(ui_element)

        # Try to combine nearby elements (text labels with detected objects)
        combined_elements = self._combine_nearby_elements(ui_elements)

        return combined_elements

    def find_element_by_text(
        self, image: np.ndarray, text_query: str, search_radius: int = 100
    ) -> list[UIElement]:
        """
        Find UI elements by text content or nearby text labels

        Args:
            image: Screenshot image
            text_query: Text to search for
            search_radius: Radius to search for nearby visual elements

        Returns:
            List of matching UI elements
        """
        # Find text matches
        text_matches = self.ocr_reader.find_text(image, text_query)

        if not text_matches:
            return []

        # Get YOLO detections for context
        yolo_detections = self.yolo_detector.detect(image)

        results = []

        for text_match in text_matches:
            # Create UI element for the text itself
            text_element = UIElement(
                element_type="text",
                bbox=text_match.rect_bbox,
                center=text_match.center,
                confidence=text_match.confidence,
                text_detection=text_match,
                text=text_match.text,
                description=f"Text match: {text_match.text}",
            )
            results.append(text_element)

            # Find nearby visual elements (likely the associated control)
            nearby_elements = self._find_nearby_visual_elements(
                text_match.center, yolo_detections, search_radius
            )

            for nearby in nearby_elements:
                combined_element = UIElement(
                    element_type="combined",
                    bbox=nearby.bbox,
                    center=nearby.center,
                    confidence=(text_match.confidence + nearby.confidence) / 2,
                    yolo_detection=nearby,
                    text_detection=text_match,
                    text=text_match.text,
                    description=f"{nearby.class_name} near '{text_match.text}'",
                )
                results.append(combined_element)

        return results

    def find_clickable_elements(self, image: np.ndarray) -> list[UIElement]:
        """Find likely clickable elements (buttons, links, etc.)"""
        # Classes that are typically clickable
        clickable_classes = {
            "mouse",
            "remote",
            "cell phone",
            "laptop",
            "keyboard",
            "tv",
            "book",
            "clock",  # These might represent UI elements in screenshots
        }

        yolo_detections = self.yolo_detector.detect(image)
        clickable_elements = []

        for detection in yolo_detections:
            if detection.class_name in clickable_classes:
                ui_element = UIElement(
                    element_type="detected",
                    bbox=detection.bbox,
                    center=detection.center,
                    confidence=detection.confidence,
                    yolo_detection=detection,
                    description=f"Clickable {detection.class_name}",
                )
                clickable_elements.append(ui_element)

        # Also look for text that might be buttons
        text_detections = self.ocr_reader.read_text(image)
        button_keywords = [
            "button",
            "click",
            "submit",
            "ok",
            "cancel",
            "yes",
            "no",
            "save",
            "delete",
        ]

        for text_det in text_detections:
            text_lower = text_det.text.lower()
            if any(keyword in text_lower for keyword in button_keywords):
                ui_element = UIElement(
                    element_type="text",
                    bbox=text_det.rect_bbox,
                    center=text_det.center,
                    confidence=text_det.confidence,
                    text_detection=text_det,
                    text=text_det.text,
                    description=f"Button text: {text_det.text}",
                )
                clickable_elements.append(ui_element)

        return clickable_elements

    def find_input_fields(self, image: np.ndarray) -> list[UIElement]:
        """Find input fields by looking for rectangular regions and nearby labels"""
        # This is a simplified implementation
        # In a real scenario, you might train YOLO specifically for UI elements

        # Look for text that indicates input fields
        text_detections = self.ocr_reader.read_text(image)
        input_indicators = ["name", "email", "password", "address", "phone", "field", "input"]

        input_fields = []

        for text_det in text_detections:
            text_lower = text_det.text.lower()
            if any(indicator in text_lower for indicator in input_indicators):
                # This text might be a label for an input field
                # Look for rectangular regions nearby
                ui_element = UIElement(
                    element_type="text",
                    bbox=text_det.rect_bbox,
                    center=text_det.center,
                    confidence=text_det.confidence,
                    text_detection=text_det,
                    text=text_det.text,
                    description=f"Input field label: {text_det.text}",
                )
                input_fields.append(ui_element)

        return input_fields

    def _combine_nearby_elements(
        self, ui_elements: list[UIElement], max_distance: int = 50
    ) -> list[UIElement]:
        """Combine nearby visual and text elements"""
        combined_elements = ui_elements.copy()

        # This is a simplified implementation
        # In practice, you might want more sophisticated spatial reasoning

        return combined_elements

    def _find_nearby_visual_elements(
        self, center_point: tuple[int, int], detections: list[Detection], max_distance: int
    ) -> list[Detection]:
        """Find visual elements near a text point"""
        px, py = center_point
        nearby = []

        for detection in detections:
            dx, dy = detection.center
            distance = math.sqrt((dx - px) ** 2 + (dy - py) ** 2)

            if distance <= max_distance:
                nearby.append(detection)

        return nearby

    def get_element_screenshot(
        self, image: np.ndarray, element: UIElement, padding: int = 5
    ) -> np.ndarray:
        """Extract screenshot of a specific UI element"""
        x1, y1, x2, y2 = element.bbox

        # Add padding
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(image.shape[1], x2 + padding)
        y2 = min(image.shape[0], y2 + padding)

        return image[y1:y2, x1:x2]

    def draw_ui_elements(self, image: np.ndarray, ui_elements: list[UIElement]) -> np.ndarray:
        """Draw all UI elements on image for visualization"""
        result_image = image.copy()

        for element in ui_elements:
            x1, y1, x2, y2 = element.bbox

            # Choose color based on element type
            if element.element_type == "detected":
                color = (0, 255, 0)  # Green for YOLO detections
            elif element.element_type == "text":
                color = (255, 0, 0)  # Blue for OCR text
            else:  # combined
                color = (0, 255, 255)  # Yellow for combined elements

            # Draw bounding box
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)

            # Draw label
            label = element.description or "Unknown"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(
                result_image, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1
            )
            cv2.putText(
                result_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2
            )

        return result_image
