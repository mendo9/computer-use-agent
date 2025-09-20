"""
OCR-based text detection for UI elements.
"""

import re

import cv2
import numpy as np
from paddleocr import PaddleOCR

# Import improved OCR as fallback
try:
    from src.vision.ocr_improved import find_text_by_ocr_improved, add_text_mapping as add_text_mapping_improved
except ImportError:
    find_text_by_ocr_improved = None
    add_text_mapping_improved = None

# Initialize OCR instance (lazy loading)
_ocr_instance: PaddleOCR | None = None

# Text mapping for OCR fallback - maps query to expected text
TEXT_MAP = {
    "close_button": "Close",
    "login_button": "Login",
}


def find_text_by_ocr(png_bytes: bytes, query: str, region: str = "full") -> tuple[int, int] | None:
    """Find element using OCR text detection in a specific region.

    Args:
        png_bytes: Screenshot as PNG bytes
        query: Element query name (must be in TEXT_MAP)
        region: Region to search ('top', 'left', 'middle', 'right')

    Returns:
        (x, y) center coordinates as integers, or None if not found
    """
    global _ocr_instance

    if query not in TEXT_MAP:
        return None

    try:
        # Initialize OCR instance if needed (lazy loading)
        if _ocr_instance is None:
            _ocr_instance = PaddleOCR(
                use_textline_orientation=False,  # Disable rotation detection for speed
                lang="en",
            )

        # Convert PNG bytes to OpenCV image
        nparr = np.frombuffer(png_bytes, np.uint8)
        full_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if full_image is None:
            return None

        # Crop image to specified region with overlap
        image, region_offset = _crop_to_region(full_image, region)

        if image is None:
            return None

        # Run OCR on the image with timeout handling
        print(f"🔍 Running OCR on image size: {image.shape}")
        try:
            ocr_results = _ocr_instance.predict(image)
            print(f"🔍 OCR returned {len(ocr_results) if ocr_results else 0} results")
        except Exception as e:
            print(f"❌ OCR prediction failed: {e}")
            return None

        if not ocr_results:
            return None

        # Get the target text to find
        target_text = TEXT_MAP[query].lower()

        # Parse the PaddleOCR format (works with both dict and object formats)
        for result in ocr_results:
            # Handle both dictionary and object attribute access
            texts = getattr(result, "rec_texts", None) or result.get("rec_texts", [])
            scores = getattr(result, "rec_scores", None) or result.get("rec_scores", [])
            polys = getattr(result, "rec_polys", None) or result.get("rec_polys", [])

            if texts and scores and polys:
                for text, score, poly in zip(texts, scores, polys, strict=False):
                    # Check if detected text matches target (case insensitive, partial match)
                    if score > 0.7 and _text_similarity(text.lower(), target_text):
                        # Convert polygon to center coordinates
                        # poly is a numpy array with shape (4, 2) representing the four corners
                        x_coords = poly[:, 0]
                        y_coords = poly[:, 1]

                        # Standard center calculation (revert to working version)
                        center_x = int(np.mean(x_coords))
                        center_y = int(np.mean(y_coords))

                        # Adjust coordinates back to full image coordinates
                        final_x = center_x + region_offset[0]
                        final_y = center_y + region_offset[1]

                        print(
                            f"📝 OCR found '{text}' (confidence: {score:.2f}) at region ({center_x}, {center_y}) -> full ({final_x}, {final_y})"
                        )
                        return (final_x, final_y)

        print(f"📝 OCR didn't find text '{target_text}' in image")
        return None

    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None


def _crop_to_region(image: np.ndarray, region: str) -> tuple[np.ndarray | None, tuple[int, int]]:
    """Crop image to specified region with overlap.

    Args:
        image: Full screenshot image
        region: Region to crop ('top', 'left', 'middle', 'right')

    Returns:
        (cropped_image, (offset_x, offset_y)) or (None, (0, 0)) if invalid
    """
    h, w = image.shape[:2]
    overlap = 50  # pixels of overlap between regions

    if region == "top":
        # Top half with bottom overlap
        y1, y2 = 0, h // 2 + overlap
        x1, x2 = 0, w
    elif region == "left":
        # Left half with right overlap (unbiased 50/50 split)
        y1, y2 = 0, h
        x1, x2 = 0, w // 2 + overlap
    elif region == "middle":
        # Center 50% with equal side overlaps
        y1, y2 = 0, h
        x1, x2 = w // 4, 3 * w // 4
    elif region == "right":
        # Right half with left overlap (unbiased 50/50 split)
        y1, y2 = 0, h
        x1, x2 = w // 2 - overlap, w
    else:
        return None, (0, 0)

    # Ensure bounds are valid
    y1, y2 = max(0, y1), min(h, y2)
    x1, x2 = max(0, x1), min(w, x2)

    cropped = image[y1:y2, x1:x2]
    return cropped, (x1, y1)


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
        # Single word - check for partial match
        return any(target in word or word in target for word in detected_words)

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
