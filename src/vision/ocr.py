"""
Improved OCR text detection with character confusion handling.
"""

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
    """Calculate similarity score between two strings using multiple metrics.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0

    text1_clean = text1.lower().strip()
    text2_clean = text2.lower().strip()

    if text1_clean == text2_clean:
        return 1.0

    # 1. Word-level Jaccard similarity (more meaningful for text)
    words1 = set(text1_clean.split())
    words2 = set(text2_clean.split())

    if words1 and words2:
        word_intersection = len(words1 & words2)
        word_union = len(words1 | words2)
        word_similarity = word_intersection / word_union if word_union > 0 else 0.0
    else:
        word_similarity = 0.0

    # 2. Character-level Jaccard similarity (fallback for short text)
    chars1 = set(text1_clean)
    chars2 = set(text2_clean)

    if chars1 and chars2:
        char_intersection = len(chars1 & chars2)
        char_union = len(chars1 | chars2)
        char_similarity = char_intersection / char_union if char_union > 0 else 0.0
    else:
        char_similarity = 0.0

    # 3. Length penalty - penalize very different lengths
    len1, len2 = len(text1_clean), len(text2_clean)
    max_len = max(len1, len2)
    min_len = min(len1, len2)
    length_ratio = min_len / max_len if max_len > 0 else 1.0

    # For very different lengths, apply strong penalty
    if length_ratio < 0.5:
        length_penalty = 0.5
    elif length_ratio < 0.7:
        length_penalty = 0.7
    else:
        length_penalty = 1.0

    # 4. Simple edit distance for strings with similar lengths (optimized)
    edit_similarity = 0.0
    # Only compute expensive edit distance for reasonable candidates
    if (
        abs(len1 - len2) <= max(len1, len2) * 0.3
        and max(len1, len2) <= 50  # Limit to shorter strings
        and (word_similarity > 0.3 or char_similarity > 0.5)
    ):  # Only if somewhat promising
        edit_distance = _levenshtein_distance(text1_clean, text2_clean)
        max_possible_distance = max(len1, len2)
        if max_possible_distance > 0:
            edit_similarity = 1.0 - (edit_distance / max_possible_distance)

    # Combine metrics with weights
    # Prioritize word-level similarity, but fall back to character-level for short text
    if len(words1) >= 2 and len(words2) >= 2:
        # Multi-word text: prioritize word similarity
        final_similarity = 0.7 * word_similarity + 0.2 * char_similarity + 0.1 * edit_similarity
    else:
        # Short text: balance character and edit distance
        final_similarity = 0.5 * char_similarity + 0.5 * edit_similarity

    # Apply length penalty
    final_similarity *= length_penalty

    return min(1.0, max(0.0, final_similarity))


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    # Create matrix
    rows = len(s1) + 1
    cols = len(s2) + 1
    matrix = [[0] * cols for _ in range(rows)]

    # Initialize first row and column
    for i in range(rows):
        matrix[i][0] = i
    for j in range(cols):
        matrix[0][j] = j

    # Fill matrix
    for i in range(1, rows):
        for j in range(1, cols):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1

            matrix[i][j] = min(
                matrix[i - 1][j] + 1,  # deletion
                matrix[i][j - 1] + 1,  # insertion
                matrix[i - 1][j - 1] + cost,  # substitution
            )

    return matrix[rows - 1][cols - 1]


def find_text_by_ocr(png_bytes: bytes, query: str, return_bbox: bool = False):
    """Find text in image using OCR with character confusion handling.

    Args:
        png_bytes: Screenshot as PNG bytes
        query: Text to find
        return_bbox: If True, return (coords, bbox), otherwise just coords

    Returns:
        If return_bbox=False: (x, y) center coordinates as integers, or None if not found
        If return_bbox=True: ((x, y), bbox) tuple, or (None, None) if not found
    """
    target_text = TEXT_MAP.get(query, query)

    try:
        # Convert PNG bytes to OpenCV image
        nparr = np.frombuffer(png_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return None

        # Try multiple preprocessing methods for better text detection (especially underlined text)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        preprocessing_methods = [
            (
                "sharpened",
                cv2.filter2D(gray, -1, np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])),
            ),
            (
                "bilateral_filtered",
                cv2.bilateralFilter(gray, 9, 75, 75),
            ),  # Better for underlined text
        ]

        # Get EasyOCR reader
        reader = get_easyocr_reader()

        print(f"🔍 Running improved OCR for '{target_text}'...")

        best_overall_match = None
        best_overall_score = 0

        # Try each preprocessing method
        for method_name, processed_image in preprocessing_methods:
            results = reader.readtext(processed_image)

            if not results:
                continue

            best_match = find_best_match(results, target_text)

            if best_match and best_match["match_score"] > best_overall_score:
                best_overall_match = best_match
                best_overall_score = best_match["match_score"]
                best_overall_match["preprocessing_method"] = method_name

        # Use the best match found across all methods
        best_match = best_overall_match

        if best_match:
            # Calculate center coordinates
            bbox = best_match["bbox"]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))

            method = best_match.get("preprocessing_method", "unknown")
            print(
                f"✅ Found '{best_match['text']}' -> '{best_match['normalized']}' "
                f"(confidence: {best_match['confidence']:.2f}) at ({center_x}, {center_y}) using {method} preprocessing"
            )

            if return_bbox:
                return ((center_x, center_y), bbox)
            else:
                return (center_x, center_y)

        print(f"❌ Text '{target_text}' not found")
        if return_bbox:
            return (None, None)
        else:
            return None

    except Exception as e:
        print(f"❌ OCR error: {e}")
        if return_bbox:
            return (None, None)
        else:
            return None


def find_best_match(ocr_results: list, target_text: str) -> dict | None:
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
}
