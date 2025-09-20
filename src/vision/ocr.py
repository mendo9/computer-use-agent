"""
OCR-based text detection for UI elements.
"""

import re

import cv2
import numpy as np
from paddleocr import PaddleOCR

# Initialize OCR instance
_ocr_instance = PaddleOCR(use_textline_orientation=True, lang="en")

# Text mapping for OCR fallback - maps query to expected text
TEXT_MAP = {
    "all_flowsheets_button": "All Flowsheets",
    "osh_heart_failure_header": "OSH Heart Failure",
    "flowsheets_header": "Flowsheets",
    "close_button": "Close",
    "chart_header": "CHART",
    "login_button": "Login",
    "patient_chart_header": "Patient Charts",
    "patient_id_field": "Patient ID",
    "search_button": "Search",
    "select_button": "Select",
}


def _point_in_region(x: int, y: int, region: str, width: int, height: int) -> bool:
    """Check if a point is in the specified region.

    Args:
        x, y: Point coordinates
        region: Region name ("top", "bottom", "left", "right", "center")
        width, height: Image dimensions

    Returns:
        True if point is in the specified region
    """
    if region == "top":
        return y < height // 2
    elif region == "bottom":
        return y >= height // 2
    elif region == "left":
        return x < width // 2
    elif region == "right":
        return x >= width // 2
    elif region == "center":
        return width // 3 <= x <= 2 * width // 3 and height // 3 <= y <= 2 * height // 3
    else:
        return True  # Unknown region, accept all points


def _search_full_image_with_region(
    ocr_results, target_text: str, region: str, image_width: int, image_height: int, debug: bool
) -> tuple[int, int] | None:
    """Search full-image OCR results with region filtering."""
    if debug:
        print(f"📝 Using full-image OCR with region filter: {region}")

    for result in ocr_results:
        texts = getattr(result, "rec_texts", None) or result.get("rec_texts", [])
        scores = getattr(result, "rec_scores", None) or result.get("rec_scores", [])
        polys = getattr(result, "rec_polys", None) or result.get("rec_polys", [])

        if texts and scores and polys:
            for text, score, poly in zip(texts, scores, polys, strict=False):
                if score > 0.7 and _text_similarity(text.lower(), target_text):
                    x_coords = poly[:, 0]
                    y_coords = poly[:, 1]
                    center_x = int(np.mean(x_coords))
                    center_y = int(np.mean(y_coords))

                    print(f"📝 Full-image OCR found '{text}' at ({center_x}, {center_y})")

                    if debug:
                        print(f"  🔍 '{text}' polygon: {poly.tolist()}")

                    if _point_in_region(center_x, center_y, region, image_width, image_height):
                        return (center_x, center_y)
                    else:
                        print(f"📝 '{text}' filtered out due to region '{region}'")

    print(f"📝 No matches found in region '{region}'")
    return None


def _search_regions(image: np.ndarray, target_text: str, debug: bool = False) -> list[dict]:
    """Search strategic regions and collect all matches."""
    height, width = image.shape[:2]
    all_matches = []

    # Strategic regions: main content first, then comprehensive coverage
    margin = 50
    mid_x, mid_y = width // 2, height // 2

    regions = [
        # High priority - likely locations
        ("main_content", (width // 4, height // 6, 3 * width // 4, 2 * height // 3), 1),
        ("center", (width // 3, height // 3, 2 * width // 3, 2 * height // 3), 2),
        ("top_center", (width // 4, 0, 3 * width // 4, height // 2), 2),
        # Comprehensive coverage - overlapping quadrants
        ("top_left", (0, 0, mid_x + margin, mid_y + margin), 3),
        ("top_right", (mid_x - margin, 0, width, mid_y + margin), 3),
        ("bottom_left", (0, mid_y - margin, mid_x + margin, height), 4),
        ("bottom_right", (mid_x - margin, mid_y - margin, width, height), 4),
    ]

    if debug:
        print(f"🔍 Searching {len(regions)} regions...")

    for name, bounds, priority in regions:
        left, top, right, bottom = bounds

        # Ensure bounds are valid
        left = max(0, min(left, width - 1))
        right = max(left + 1, min(right, width))
        top = max(0, min(top, height - 1))
        bottom = max(top + 1, min(bottom, height))

        # Crop and run OCR on region
        cropped = image[top:bottom, left:right]

        if debug:
            print(f"  📐 Searching {name}: ({left}, {top}) to ({right}, {bottom})")

        try:
            ocr_results = _ocr_instance.predict(cropped)
            if not ocr_results:
                continue

            for result in ocr_results:
                texts = getattr(result, "rec_texts", None) or result.get("rec_texts", [])
                scores = getattr(result, "rec_scores", None) or result.get("rec_scores", [])
                polys = getattr(result, "rec_polys", None) or result.get("rec_polys", [])

                if texts and scores and polys:
                    for text, score, poly in zip(texts, scores, polys, strict=False):
                        if score > 0.7 and _text_similarity(text.lower(), target_text):
                            # Convert crop coordinates to full image coordinates
                            crop_center_x = int(np.mean(poly[:, 0]))
                            crop_center_y = int(np.mean(poly[:, 1]))
                            full_center_x = left + crop_center_x
                            full_center_y = top + crop_center_y

                            all_matches.append(
                                {
                                    "text": text,
                                    "score": score,
                                    "center": (full_center_x, full_center_y),
                                    "source": f"{name} region",
                                    "priority": priority,
                                }
                            )

                            if debug:
                                print(f"  ✅ Found '{text}' -> ({full_center_x}, {full_center_y})")

        except Exception as e:
            if debug:
                print(f"  ❌ Error in {name}: {e}")

    if debug:
        print(f"📊 Total matches: {len(all_matches)}")

    return all_matches


def _select_best_match(matches: list[dict], debug: bool = False) -> dict:
    """Select the best match from region search results.

    Simple selection criteria: prefer high-priority regions, then high confidence.
    """
    if len(matches) == 1:
        return matches[0]

    if debug:
        print(f"🔍 Selecting best match from {len(matches)} candidates:")
        for i, match in enumerate(matches, 1):
            print(
                f"  {i}. '{match['text']}' at {match['center']} | score: {match['score']:.3f} | {match['source']}"
            )

    # Simple selection: priority region first, then highest confidence
    best_match = min(matches, key=lambda m: (m.get("priority", 4), -m["score"]))

    if debug:
        print(f"📍 Selected '{best_match['text']}' from {best_match['source']}")

    return best_match


def find_text_by_ocr(
    png_bytes: bytes,
    query: str,
    region: str | None = None,
    prefer: str = "highest_confidence",
    debug: bool = False,
) -> tuple[int, int] | None:
    """Find element using OCR text detection.

    Args:
        png_bytes: Screenshot as PNG bytes
        query: Element query name (must be in TEXT_MAP)
        region: Optional region filter ("top", "bottom", "left", "right", "center")
        prefer: Selection strategy when multiple matches ("highest_confidence", "largest", "smallest", "topmost", "bottommost", "leftmost", "rightmost")
        debug: Enable detailed coordinate debugging output

    Returns:
        (x, y) center coordinates as integers, or None if not found
    """
    if query not in TEXT_MAP:
        return None

    try:
        # Convert PNG bytes to OpenCV image
        nparr = np.frombuffer(png_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return None

        # Run OCR on the image
        ocr_results = _ocr_instance.predict(image)

        if not ocr_results:
            return None

        # Get the target text to find
        target_text = TEXT_MAP[query].lower()
        target_words = target_text.split()

        # Get image dimensions for region filtering (if needed)
        image_height, image_width = image.shape[:2]

        # Region-based OCR by default (more accurate), full-image if region filter specified
        if region:
            # Full-image OCR with region filtering
            return _search_full_image_with_region(
                ocr_results, target_text, region, image_width, image_height, debug
            )
        else:
            # Region-based OCR (default - more accurate)
            all_matches = _search_regions(image, target_text, debug)
            if not all_matches:
                print(f"📝 OCR didn't find text '{target_text}' in any region")
                return None

            best_match = _select_best_match(all_matches, debug)
            print(
                f"📝 Selected '{best_match['text']}' from {best_match['source']} (confidence: {best_match['score']:.2f}) at {best_match['center']}"
            )
            return best_match["center"]

    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None


def _text_similarity(detected: str, target: str) -> bool:
    """Check if detected text is similar enough to target text.

    Args:
        detected: Text detected by OCR (lowercase)
        target: Target text to match (lowercase)

    Returns:
        True if texts are similar enough
    """
    # Remove extra whitespace and normalize
    detected = re.sub(r"\s+", " ", detected.strip())
    target = re.sub(r"\s+", " ", target.strip())

    # Exact match
    if detected == target:
        return True

    # Partial match - target contained in detected
    if target in detected:
        return True

    # Fuzzy match - check if most words match
    detected_words = detected.split()
    target_words = target.split()

    if len(target_words) == 1:
        # Single word - require exact match to avoid false positives like "flowsheet" matching "flowsheets"
        return any(word.lower() == target.lower() for word in detected_words)

    # Multi-word - check if most words are present
    matches = sum(
        1
        for word in target_words
        if any(word in dword or dword in word for dword in detected_words)
    )
    return matches >= len(target_words) * 0.7  # At least 70% of words match


def add_text_mapping(query: str, text: str) -> None:
    """Add a new text mapping for OCR detection.

    Args:
        query: Query name (e.g., "my_button")
        text: Expected text to find (e.g., "Click Me")
    """
    TEXT_MAP[query] = text


def get_text_mappings() -> dict[str, str]:
    """Get all current text mappings.

    Returns:
        Dictionary of query -> text mappings
    """
    return TEXT_MAP.copy()
