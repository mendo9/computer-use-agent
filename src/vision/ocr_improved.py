"""
Improved OCR text detection with character confusion handling.
"""

from typing import Optional, Tuple, Dict, List

import cv2
import easyocr
import numpy as np

# Initialize EasyOCR instance (lazy loading)
_easyocr_reader = None


def get_easyocr_reader():
    """Get or initialize EasyOCR reader."""
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(["en"], gpu=False)
    return _easyocr_reader


def normalize_ocr_text(text: str) -> str:
    """Normalize OCR text to handle common character confusions.

    Args:
        text: Raw OCR text

    Returns:
        Normalized text with common OCR errors corrected
    """
    # Common OCR character substitutions
    replacements = [
        ("II", "ll"),  # Double I to double l
        ("AII", "All"),  # Common "All" misread
        ("OAII", "All"),  # Another variant
        ("OAI", "All"),  # Another variant
        ("Al1", "All"),  # Number 1 instead of l
        ("A11", "All"),  # Double 1 instead of ll
        ("|", "l"),  # Pipe instead of l
        ("0", "O"),  # Zero instead of O in certain contexts
    ]

    normalized = text
    for old, new in replacements:
        normalized = normalized.replace(old, new)

    return normalized


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity score between two strings.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    # Simple character overlap ratio
    set1 = set(text1.lower())
    set2 = set(text2.lower())

    if not set1 and not set2:
        return 1.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    if union == 0:
        return 0.0

    return intersection / union


def find_text_by_ocr_improved(png_bytes: bytes, query: str) -> Optional[Tuple[int, int]]:
    """Find text in image using improved OCR with character confusion handling.

    Args:
        png_bytes: Screenshot as PNG bytes
        target_text: Text to find

    Returns:
        (x, y) center coordinates as integers, or None if not found
    """
    target_text = TEXT_MAP.get(query, query)

    try:
        # Convert PNG bytes to OpenCV image
        nparr = np.frombuffer(png_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return None

        # Preprocess image (convert to grayscale and sharpen)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sharpened = cv2.filter2D(gray, -1, np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]))

        # Get EasyOCR reader
        reader = get_easyocr_reader()

        # Run OCR
        print(f"🔍 Running improved OCR for '{target_text}'...")
        results = reader.readtext(sharpened)

        if not results:
            print("📝 No text detected")
            return None

        # Find best match
        best_match = find_best_match(results, target_text)

        if best_match:
            # Calculate center coordinates
            bbox = best_match["bbox"]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))

            print(
                f"✅ Found '{best_match['text']}' -> '{best_match['normalized']}' "
                f"(confidence: {best_match['confidence']:.2f}) at ({center_x}, {center_y})"
            )

            return (center_x, center_y)

        print(f"❌ Text '{target_text}' not found")
        return None

    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None


def find_best_match(ocr_results: List, target_text: str) -> Optional[Dict]:
    """Find the best match for target text in OCR results.

    Args:
        ocr_results: List of OCR detection results
        target_text: Text to find

    Returns:
        Best matching result or None if no good match found
    """
    target_lower = target_text.lower()
    target_words = target_lower.split()

    matches = []

    for bbox, text, confidence in ocr_results:
        # Original text check
        text_lower = text.lower()

        # Normalized text check
        normalized = normalize_ocr_text(text)
        normalized_lower = normalized.lower()

        match_score = 0.0
        match_type = None

        # Check for exact match
        if target_lower == text_lower or target_lower == normalized_lower:
            match_score = 1.0
            match_type = "exact"
        # Check for substring match
        elif target_lower in text_lower or target_lower in normalized_lower:
            match_score = 0.9
            match_type = "substring"
        # Check if all target words are present
        elif all(word in text_lower or word in normalized_lower for word in target_words):
            match_score = 0.8
            match_type = "all_words"
        # Check for high similarity
        else:
            similarity = max(
                calculate_similarity(text, target_text),
                calculate_similarity(normalized, target_text),
            )
            if similarity >= 0.7:
                match_score = similarity
                match_type = "fuzzy"

        if match_score > 0:
            matches.append(
                {
                    "text": text,
                    "normalized": normalized,
                    "bbox": bbox,
                    "confidence": confidence,
                    "match_type": match_type,
                    "match_score": match_score,
                }
            )

    if not matches:
        return None

    # Sort by match score and confidence
    matches.sort(key=lambda x: (x["match_score"], x["confidence"]), reverse=True)

    # Return best match if it's good enough
    best = matches[0]
    if best["match_score"] >= 0.7:  # Minimum threshold
        return best

    return None


# Maintain compatibility with existing TEXT_MAP
TEXT_MAP = {
    # Google News mappings
    "google_news_tech_button": "Technology",
    "google_news_virtual_reality_button": "Virtual Reality",
    "google_news_sign_in_button": "Sign in",
    "google_news_next_button": "Next",
    "google_news_language_dropdown": "English (United States)",
    "google_news_language_dropdown_arrow": "▼",
    "google_news_italian_dropdown": "Italiano",
    # Medical system mappings
    "flowsheets_header": "Flowsheets",
    "all_flowsheets": "All Flowsheets",
    "patient_flowsheets": "Patient Flowsheets",
    "my_favorites": "My Favorites",
}


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
