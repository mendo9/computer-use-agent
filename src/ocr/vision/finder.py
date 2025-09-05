"""Combined UI element finder using YOLO + OCR"""

import math
from dataclasses import dataclass

import numpy as np

from ocr.vision.detector import Detection, YOLODetector
from ocr.vision.ocr import OCRReader, TextDetection


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

        # Create UI elements from detections
        elements = []

        # Add YOLO detections as visual elements
        for detection in yolo_detections:
            element = UIElement(
                element_type="detected",
                bbox=detection.bbox,
                center=detection.center,
                confidence=detection.confidence,
                yolo_detection=detection,
                description=f"{detection.class_name} ({detection.confidence:.2f})",
            )
            elements.append(element)

        # Add text detections as text elements
        for text_det in text_detections:
            element = UIElement(
                element_type="text",
                bbox=text_det.rect_bbox,
                center=text_det.center,
                confidence=text_det.confidence,
                text_detection=text_det,
                text=text_det.text,
                description=f"Text: '{text_det.text}' ({text_det.confidence:.2f})",
            )
            elements.append(element)

        # Merge nearby visual and text elements
        combined_elements = self._combine_nearby_elements(elements, proximity_threshold=50)

        return combined_elements

    def _combine_nearby_elements(
        self, elements: list[UIElement], proximity_threshold: int = 50
    ) -> list[UIElement]:
        """Combine nearby visual and text elements into combined elements"""
        visual_elements = [e for e in elements if e.element_type == "detected"]
        text_elements = [e for e in elements if e.element_type == "text"]
        combined_elements = []

        used_text_indices = set()

        for visual_elem in visual_elements:
            # Find nearby text elements
            nearby_texts = []
            for i, text_elem in enumerate(text_elements):
                if i in used_text_indices:
                    continue

                distance = self._calculate_distance(visual_elem.center, text_elem.center)
                if distance <= proximity_threshold:
                    nearby_texts.append((i, text_elem, distance))

            if nearby_texts:
                # Sort by distance and take the closest
                nearby_texts.sort(key=lambda x: x[2])
                text_idx, closest_text, _ = nearby_texts[0]
                used_text_indices.add(text_idx)

                # Create combined element
                combined_bbox = self._merge_bboxes(visual_elem.bbox, closest_text.bbox)
                combined_center = (
                    (visual_elem.center[0] + closest_text.center[0]) // 2,
                    (visual_elem.center[1] + closest_text.center[1]) // 2,
                )

                combined_element = UIElement(
                    element_type="combined",
                    bbox=combined_bbox,
                    center=combined_center,
                    confidence=(visual_elem.confidence + closest_text.confidence) / 2,
                    yolo_detection=visual_elem.yolo_detection,
                    text_detection=closest_text.text_detection,
                    text=closest_text.text,
                    description=f"{visual_elem.yolo_detection.class_name}: '{closest_text.text}'",
                )
                combined_elements.append(combined_element)
            else:
                # Keep visual element as-is
                combined_elements.append(visual_elem)

        # Add remaining text elements that weren't combined
        for i, text_elem in enumerate(text_elements):
            if i not in used_text_indices:
                combined_elements.append(text_elem)

        return combined_elements

    def _calculate_distance(self, point1: tuple[int, int], point2: tuple[int, int]) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def _merge_bboxes(
        self, bbox1: tuple[int, int, int, int], bbox2: tuple[int, int, int, int]
    ) -> tuple[int, int, int, int]:
        """Merge two bounding boxes into one containing both"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2

        merged_x1 = min(x1_1, x1_2)
        merged_y1 = min(y1_1, y1_2)
        merged_x2 = max(x2_1, x2_2)
        merged_y2 = max(y2_1, y2_2)

        return (merged_x1, merged_y1, merged_x2, merged_y2)

    def find_element_by_text(
        self,
        image: np.ndarray,
        text_query: str,
        search_radius: int = 100,
        confidence_threshold: float = 0.5,
    ) -> list[UIElement]:
        """Find UI elements that contain or are near specific text"""
        text_detections = self.ocr_reader.find_text(
            image, text_query, threshold=confidence_threshold
        )

        if not text_detections:
            return []

        # Also get visual elements to see if any are near the found text
        visual_detections = self.yolo_detector.detect(image)
        elements = []

        for text_det in text_detections:
            # Create text element
            text_element = UIElement(
                element_type="text",
                bbox=text_det.rect_bbox,
                center=text_det.center,
                confidence=text_det.confidence,
                text_detection=text_det,
                text=text_det.text,
                description=f"Text: '{text_det.text}'",
            )

            # Look for nearby visual elements
            nearby_visual = None
            min_distance = float("inf")

            for visual_det in visual_detections:
                distance = self._calculate_distance(text_det.center, visual_det.center)
                if distance <= search_radius and distance < min_distance:
                    min_distance = distance
                    nearby_visual = visual_det

            if nearby_visual:
                # Create combined element
                combined_bbox = self._merge_bboxes(text_det.rect_bbox, nearby_visual.bbox)
                combined_element = UIElement(
                    element_type="combined",
                    bbox=combined_bbox,
                    center=text_det.center,
                    confidence=(text_det.confidence + nearby_visual.confidence) / 2,
                    yolo_detection=nearby_visual,
                    text_detection=text_det,
                    text=text_det.text,
                    description=f"{nearby_visual.class_name}: '{text_det.text}'",
                )
                elements.append(combined_element)
            else:
                elements.append(text_element)

        return elements

    def find_clickable_elements(self, image: np.ndarray) -> list[UIElement]:
        """Find elements that are likely to be clickable (buttons, links, etc.)"""
        # Get all UI elements
        all_elements = self.find_ui_elements(image)

        clickable_elements = []
        clickable_visual_classes = [
            "person",
            "car",
            "truck",
            "bottle",
            "cup",
            "fork",
            "knife",
            "spoon",
            "bowl",
            "chair",
            "couch",
            "bed",
            "dining table",
            "toilet",
            "tv",
            "laptop",
            "mouse",
            "remote",
            "keyboard",
            "cell phone",
            "book",
            "clock",
        ]

        clickable_text_terms = [
            "button",
            "click",
            "submit",
            "ok",
            "cancel",
            "close",
            "save",
            "open",
            "login",
            "sign",
            "next",
            "back",
        ]

        for element in all_elements:
            is_clickable = False

            # Check if visual detection suggests clickable element
            if element.yolo_detection:
                if element.yolo_detection.class_name.lower() in clickable_visual_classes:
                    is_clickable = True

            # Check if text suggests clickable element
            if element.text:
                text_lower = element.text.lower()
                if any(term in text_lower for term in clickable_text_terms):
                    is_clickable = True

                # Short text often indicates buttons/links
                if len(element.text.split()) <= 3 and len(element.text) <= 20:
                    is_clickable = True

            if is_clickable:
                clickable_elements.append(element)

        return clickable_elements

    def find_input_fields(self, image: np.ndarray) -> list[UIElement]:
        """Find elements that appear to be input fields"""
        # This is a simplified implementation
        # In practice, you'd look for rectangular regions with text inside
        # or use more sophisticated computer vision techniques

        text_detections = self.ocr_reader.read_text(image)
        input_fields = []

        for text_det in text_detections:
            # Look for common input field indicators
            text_lower = text_det.text.lower()
            input_indicators = [
                "enter",
                "input",
                "search",
                "type",
                "username",
                "password",
                "email",
                "name",
                "address",
            ]

            if any(indicator in text_lower for indicator in input_indicators):
                field_element = UIElement(
                    element_type="input_field",
                    bbox=text_det.rect_bbox,
                    center=text_det.center,
                    confidence=text_det.confidence,
                    text_detection=text_det,
                    text=text_det.text,
                    description=f"Input field: '{text_det.text}'",
                )
                input_fields.append(field_element)

        return input_fields
