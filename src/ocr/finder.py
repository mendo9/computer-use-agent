"""Combined YOLO+OCR Search and Analysis Functions

Combines YOLO detection and PaddleOCR to provide intelligent UI element finding
and screen analysis capabilities.
"""

import math
from dataclasses import dataclass

import numpy as np

from .detector import Detection, detect_ui_elements
from .reader import TextResult, extract_text


@dataclass
class UIElement:
    """Combined UI element with visual and text information"""

    element_type: str  # "visual", "text", "combined"
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    center: tuple[int, int]
    confidence: float
    area: int

    # Visual detection info (if available)
    visual_detection: Detection | None = None

    # Text info (if available)
    text_detection: TextResult | None = None
    text: str | None = None

    # Metadata
    description: str | None = None


@dataclass
class ScreenAnalysis:
    """Complete screen analysis result"""

    ui_elements: list[UIElement]
    text_elements: list[UIElement]
    visual_elements: list[UIElement]
    clickable_elements: list[UIElement]

    summary: dict
    query: str


def find_elements_by_text(
    image: np.ndarray,
    text_query: str,
    confidence_threshold: float = 0.6,
    search_radius: int = 100,
    case_sensitive: bool = False,
) -> list[UIElement]:
    """
    Find UI elements that contain or are near specific text

    Args:
        image: Input image
        text_query: Text to search for
        confidence_threshold: Minimum confidence for detections
        search_radius: Radius to search for nearby visual elements
        case_sensitive: Whether text search is case sensitive

    Returns:
        List of UIElement objects that match the text query

    Example:
        # Find all Submit buttons
        submit_elements = find_elements_by_text(image, "Submit")

        # Find username input fields
        username_fields = find_elements_by_text(image, "username", case_sensitive=False)
    """
    # Get text detections
    text_results = extract_text(image, confidence_threshold=confidence_threshold)

    # Find matching text
    query = text_query.strip()
    if not case_sensitive:
        query = query.lower()

    matching_text = []
    for text_result in text_results:
        detected_text = text_result.text.strip()
        if not case_sensitive:
            detected_text = detected_text.lower()

        if query in detected_text:
            matching_text.append(text_result)

    if not matching_text:
        return []

    # Get visual detections
    visual_detections = detect_ui_elements(image, confidence_threshold=confidence_threshold)

    elements = []

    for text_result in matching_text:
        # Create text element
        text_element = UIElement(
            element_type="text",
            bbox=text_result.rect_bbox,
            center=text_result.center,
            confidence=text_result.confidence,
            area=text_result.area,
            text_detection=text_result,
            text=text_result.text,
            description=f"Text: '{text_result.text}'",
        )

        # Look for nearby visual elements
        nearby_visual = None
        min_distance = float("inf")

        for visual_det in visual_detections:
            distance = _calculate_distance(text_result.center, visual_det.center)
            if distance <= search_radius and distance < min_distance:
                min_distance = distance
                nearby_visual = visual_det

        if nearby_visual:
            # Create combined element
            combined_bbox = _merge_bboxes(text_result.rect_bbox, nearby_visual.bbox)
            combined_center = (
                (text_result.center[0] + nearby_visual.center[0]) // 2,
                (text_result.center[1] + nearby_visual.center[1]) // 2,
            )
            combined_area = (combined_bbox[2] - combined_bbox[0]) * (
                combined_bbox[3] - combined_bbox[1]
            )

            combined_element = UIElement(
                element_type="combined",
                bbox=combined_bbox,
                center=combined_center,
                confidence=(text_result.confidence + nearby_visual.confidence) / 2,
                area=combined_area,
                visual_detection=nearby_visual,
                text_detection=text_result,
                text=text_result.text,
                description=f"{nearby_visual.class_name}: '{text_result.text}'",
            )
            elements.append(combined_element)
        else:
            elements.append(text_element)

    return elements


def find_clickable_elements(
    image: np.ndarray, confidence_threshold: float = 0.6
) -> list[UIElement]:
    """
    Find elements that are likely to be clickable

    Args:
        image: Input image
        confidence_threshold: Minimum confidence for detections

    Returns:
        List of potentially clickable UIElement objects

    Example:
        clickable = find_clickable_elements(image)
        for element in clickable:
            print(f"Clickable: {element.description} at {element.center}")
    """
    # Get all elements
    all_elements = _get_all_ui_elements(image, confidence_threshold)

    clickable_elements = []

    # Define clickable indicators
    clickable_visual_classes = {"laptop", "mouse", "remote", "keyboard", "cell phone", "book"}

    clickable_text_terms = {
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
        "menu",
        "settings",
    }

    for element in all_elements:
        is_clickable = False

        # Check visual indicators
        if element.visual_detection:
            if element.visual_detection.class_name.lower() in clickable_visual_classes:
                is_clickable = True

        # Check text indicators
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


def analyze_screen_content(
    image: np.ndarray, query: str, confidence_threshold: float = 0.6
) -> ScreenAnalysis:
    """
    Comprehensive screen analysis with natural language query

    Args:
        image: Input image to analyze
        query: Natural language description of what to analyze
        confidence_threshold: Minimum confidence for detections

    Returns:
        ScreenAnalysis object with comprehensive results

    Example:
        analysis = analyze_screen_content(image, "Find all buttons and input fields")
        print(f"Found {len(analysis.clickable_elements)} clickable elements")
        print(f"Total UI elements: {analysis.summary['total_elements']}")
    """
    # Get all UI elements
    all_elements = _get_all_ui_elements(image, confidence_threshold)

    # Separate by type
    visual_elements = [e for e in all_elements if e.element_type in ["visual", "combined"]]
    text_elements = [e for e in all_elements if e.element_type in ["text", "combined"]]
    clickable_elements = find_clickable_elements(image, confidence_threshold)

    # Create summary
    summary = {
        "total_elements": len(all_elements),
        "visual_elements": len(visual_elements),
        "text_elements": len(text_elements),
        "clickable_elements": len(clickable_elements),
        "unique_text_content": len(set(e.text for e in text_elements if e.text)),
        "visual_classes": list(
            set(e.visual_detection.class_name for e in visual_elements if e.visual_detection)
        ),
    }

    return ScreenAnalysis(
        ui_elements=all_elements,
        text_elements=text_elements,
        visual_elements=visual_elements,
        clickable_elements=clickable_elements,
        summary=summary,
        query=query,
    )


def _get_all_ui_elements(image: np.ndarray, confidence_threshold: float) -> list[UIElement]:
    """Get all UI elements combining YOLO and OCR results"""
    # Get detections
    visual_detections = detect_ui_elements(image, confidence_threshold=confidence_threshold)
    text_results = extract_text(image, confidence_threshold=confidence_threshold)

    elements = []

    # Add visual elements
    for detection in visual_detections:
        element = UIElement(
            element_type="visual",
            bbox=detection.bbox,
            center=detection.center,
            confidence=detection.confidence,
            area=detection.area,
            visual_detection=detection,
            description=f"{detection.class_name} ({detection.confidence:.2f})",
        )
        elements.append(element)

    # Add text elements
    for text_result in text_results:
        element = UIElement(
            element_type="text",
            bbox=text_result.rect_bbox,
            center=text_result.center,
            confidence=text_result.confidence,
            area=text_result.area,
            text_detection=text_result,
            text=text_result.text,
            description=f"Text: '{text_result.text}' ({text_result.confidence:.2f})",
        )
        elements.append(element)

    # Merge nearby elements (optional enhancement)
    combined_elements = _combine_nearby_elements(elements, proximity_threshold=50)

    return combined_elements


def _combine_nearby_elements(
    elements: list[UIElement], proximity_threshold: int = 50
) -> list[UIElement]:
    """Combine nearby visual and text elements"""
    visual_elements = [e for e in elements if e.element_type == "visual"]
    text_elements = [e for e in elements if e.element_type == "text"]
    combined_elements = []

    used_text_indices = set()

    for visual_elem in visual_elements:
        # Find nearby text elements
        nearby_texts = []
        for i, text_elem in enumerate(text_elements):
            if i in used_text_indices:
                continue

            distance = _calculate_distance(visual_elem.center, text_elem.center)
            if distance <= proximity_threshold:
                nearby_texts.append((i, text_elem, distance))

        if nearby_texts:
            # Sort by distance and take closest
            nearby_texts.sort(key=lambda x: x[2])
            text_idx, closest_text, _ = nearby_texts[0]
            used_text_indices.add(text_idx)

            # Create combined element
            combined_bbox = _merge_bboxes(visual_elem.bbox, closest_text.bbox)
            combined_center = (
                (visual_elem.center[0] + closest_text.center[0]) // 2,
                (visual_elem.center[1] + closest_text.center[1]) // 2,
            )
            combined_area = (combined_bbox[2] - combined_bbox[0]) * (
                combined_bbox[3] - combined_bbox[1]
            )

            combined_element = UIElement(
                element_type="combined",
                bbox=combined_bbox,
                center=combined_center,
                confidence=(visual_elem.confidence + closest_text.confidence) / 2,
                area=combined_area,
                visual_detection=visual_elem.visual_detection,
                text_detection=closest_text.text_detection,
                text=closest_text.text,
                description=f"{visual_elem.visual_detection.class_name}: '{closest_text.text}'",
            )
            combined_elements.append(combined_element)
        else:
            # Keep visual element as-is
            combined_elements.append(visual_elem)

    # Add remaining text elements
    for i, text_elem in enumerate(text_elements):
        if i not in used_text_indices:
            combined_elements.append(text_elem)

    return combined_elements


def _calculate_distance(point1: tuple[int, int], point2: tuple[int, int]) -> float:
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def _merge_bboxes(
    bbox1: tuple[int, int, int, int], bbox2: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    """Merge two bounding boxes"""
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    merged_x1 = min(x1_1, x1_2)
    merged_y1 = min(y1_1, y1_2)
    merged_x2 = max(x2_1, x2_2)
    merged_y2 = max(y2_1, y2_2)

    return (merged_x1, merged_y1, merged_x2, merged_y2)


def find_elements_near_point(
    image: np.ndarray, point: tuple[int, int], radius: int = 50, confidence_threshold: float = 0.6
) -> list[UIElement]:
    """
    Find UI elements near a specific point

    Args:
        image: Input image
        point: Center point (x, y)
        radius: Search radius in pixels
        confidence_threshold: Minimum confidence

    Returns:
        List of nearby UIElement objects sorted by distance
    """
    all_elements = _get_all_ui_elements(image, confidence_threshold)
    nearby_elements = []

    px, py = point

    for element in all_elements:
        ex, ey = element.center
        distance = ((ex - px) ** 2 + (ey - py) ** 2) ** 0.5

        if distance <= radius:
            # Add distance for sorting
            element.distance = distance  # type: ignore
            nearby_elements.append(element)

    # Sort by distance
    nearby_elements.sort(key=lambda x: getattr(x, "distance", float("inf")))

    return nearby_elements
