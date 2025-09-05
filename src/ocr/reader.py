"""Pure PaddleOCR Text Extraction Functions

Standalone PaddleOCR-based text recognition with no external dependencies.
"""

from dataclasses import dataclass

import cv2
import numpy as np
import paddleocr


@dataclass
class TextResult:
    """Text recognition result"""

    text: str
    confidence: float
    bbox: list[tuple[int, int]]  # 4 corner points
    rect_bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    center: tuple[int, int]
    area: int


def extract_text(
    image: np.ndarray,
    language: str = "en",
    confidence_threshold: float = 0.5,
    max_results: int = 100,
) -> list[TextResult]:
    """
    Extract text from entire image using PaddleOCR

    Args:
        image: Input image as numpy array (BGR format from cv2)
        language: Language code for OCR ('en', 'ch', 'fr', etc.)
        confidence_threshold: Minimum confidence for text results (0.0-1.0)
        max_results: Maximum number of text results to return

    Returns:
        List of TextResult objects sorted by confidence

    Example:
        image = cv2.imread("screenshot.png")
        text_results = extract_text(image, confidence_threshold=0.7)
        for result in text_results:
            print(f"Found text: '{result.text}' at {result.center}")
    """
    # Initialize PaddleOCR with new API
    ocr = paddleocr.PaddleOCR(use_textline_orientation=True, lang=language)

    # Run OCR using new predict method
    try:
        results = ocr.predict(image)

        if not results:
            return []

        text_results = []

        # Process each page result (usually just one for single image)
        for page_result in results:
            if not page_result:
                continue

            # Extract text data from OCRResult object
            rec_texts = page_result.get("rec_texts", [])
            rec_scores = page_result.get("rec_scores", [])
            rec_polys = page_result.get("rec_polys", [])

            # Process each detected text
            for i, (text, confidence, bbox_points) in enumerate(
                zip(rec_texts, rec_scores, rec_polys, strict=False)
            ):
                if confidence < confidence_threshold:
                    continue

                # Convert bbox points to integer coordinates
                bbox_points = [(int(x), int(y)) for x, y in bbox_points]

                # Calculate rectangular bounding box
                x_coords = [point[0] for point in bbox_points]
                y_coords = [point[1] for point in bbox_points]

                x1, y1 = min(x_coords), min(y_coords)
                x2, y2 = max(x_coords), max(y_coords)

                # Calculate center and area
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                area = (x2 - x1) * (y2 - y1)

                text_result = TextResult(
                    text=text.strip(),
                    confidence=confidence,
                    bbox=bbox_points,
                    rect_bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y),
                    area=area,
                )

                text_results.append(text_result)

        # Sort by confidence and limit results
        text_results.sort(key=lambda x: x.confidence, reverse=True)
        return text_results[:max_results]

    except Exception as e:
        print(f"OCR error: {e}")
        return []


def extract_text_from_region(
    image: np.ndarray,
    region: tuple[int, int, int, int],
    language: str = "en",
    confidence_threshold: float = 0.5,
) -> list[TextResult]:
    """
    Extract text from specific region of image

    Args:
        image: Input image as numpy array
        region: Region coordinates (x1, y1, x2, y2) to crop
        language: Language code for OCR
        confidence_threshold: Minimum confidence for results

    Returns:
        List of TextResult objects with coordinates adjusted to full image

    Example:
        # Extract text from top-left 300x200 region
        region_text = extract_text_from_region(image, (0, 0, 300, 200))
    """
    x1, y1, x2, y2 = region

    # Crop region
    cropped_image = image[y1:y2, x1:x2]

    # Extract text from cropped region
    text_results = extract_text(cropped_image, language, confidence_threshold)

    # Adjust coordinates to full image
    adjusted_results = []
    for result in text_results:
        # Adjust bbox points
        adjusted_bbox = [(x + x1, y + y1) for x, y in result.bbox]

        # Adjust rect_bbox
        rx1, ry1, rx2, ry2 = result.rect_bbox
        adjusted_rect_bbox = (rx1 + x1, ry1 + y1, rx2 + x1, ry2 + y1)

        # Adjust center
        adjusted_center = (result.center[0] + x1, result.center[1] + y1)

        adjusted_result = TextResult(
            text=result.text,
            confidence=result.confidence,
            bbox=adjusted_bbox,
            rect_bbox=adjusted_rect_bbox,
            center=adjusted_center,
            area=result.area,
        )

        adjusted_results.append(adjusted_result)

    return adjusted_results


def find_text_by_content(
    image: np.ndarray,
    target_text: str,
    language: str = "en",
    similarity_threshold: float = 0.8,
    case_sensitive: bool = False,
) -> list[TextResult]:
    """
    Find specific text content in image

    Args:
        image: Input image
        target_text: Text to search for
        language: Language for OCR
        similarity_threshold: Minimum similarity for matches (0-1)
        case_sensitive: Whether to match case exactly

    Returns:
        List of matching TextResult objects

    Example:
        # Find all occurrences of "Submit" button
        submit_buttons = find_text_by_content(image, "Submit", similarity_threshold=0.9)
    """
    # Extract all text
    all_text = extract_text(image, language)
    matches = []

    # Prepare target text for comparison
    target = target_text.strip()
    if not case_sensitive:
        target = target.lower()

    for text_result in all_text:
        detected = text_result.text.strip()
        if not case_sensitive:
            detected = detected.lower()

        # Simple substring matching
        if target in detected or detected in target:
            matches.append(text_result)

    return matches


def get_text_near_point(
    image: np.ndarray, point: tuple[int, int], radius: int = 50, language: str = "en"
) -> list[TextResult]:
    """
    Get text near a specific point

    Args:
        image: Input image
        point: Center point (x, y)
        radius: Search radius in pixels
        language: Language for OCR

    Returns:
        List of nearby TextResult objects sorted by distance
    """
    # Extract all text
    all_text = extract_text(image, language)
    nearby_text = []

    px, py = point

    for text_result in all_text:
        tx, ty = text_result.center
        distance = ((tx - px) ** 2 + (ty - py) ** 2) ** 0.5

        if distance <= radius:
            # Add distance info for sorting
            text_result_with_distance = text_result
            text_result_with_distance.distance = distance  # type: ignore
            nearby_text.append(text_result_with_distance)

    # Sort by distance
    nearby_text.sort(key=lambda x: getattr(x, "distance", float("inf")))

    return nearby_text


def draw_text_results(image: np.ndarray, text_results: list[TextResult]) -> np.ndarray:
    """
    Draw text detection results on image

    Args:
        image: Input image
        text_results: List of text results to draw

    Returns:
        Image with drawn text bounding boxes and labels
    """
    result_image = image.copy()

    for text_result in text_results:
        # Draw bounding box
        bbox_points = np.array(text_result.bbox, dtype=np.int32)
        cv2.polylines(result_image, [bbox_points], True, (255, 0, 0), 2)

        # Draw text label
        x1, y1, x2, y2 = text_result.rect_bbox
        label = f"{text_result.text} ({text_result.confidence:.2f})"

        # Background for text
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(
            result_image,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0], y1),
            (255, 0, 0),
            -1,
        )

        # Text
        cv2.putText(
            result_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

    return result_image
