"""
Improved OCR test with character confusion handling for "All Flowsheets".
"""

import cv2
import easyocr
import numpy as np


def normalize_ocr_text(text):
    """Normalize OCR text to handle common character confusions."""
    # Common OCR character substitutions
    replacements = [
        ("II", "ll"),  # Double I to double l
        ("AII", "All"),  # Common "All" misread
        ("OAII", "All"),  # Another variant
        ("Al1", "All"),  # Number 1 instead of l
        ("A11", "All"),  # Double 1 instead of ll
        ("/", ""),  # Remove slashes that might interfere
        ("f", "/"),  # f might be read instead of /
    ]

    normalized = text
    for old, new in replacements:
        normalized = normalized.replace(old, new)

    return normalized


def find_text_with_normalization(ocr_results, target_text):
    """Find target text accounting for OCR errors."""
    target_lower = target_text.lower()
    target_words = target_lower.split()

    matches = []

    for bbox, text, confidence in ocr_results:
        # Original text check
        text_lower = text.lower()

        # Normalized text check
        normalized = normalize_ocr_text(text)
        normalized_lower = normalized.lower()

        # Check for exact match
        if target_lower == text_lower or target_lower == normalized_lower:
            matches.append(
                {
                    "text": text,
                    "normalized": normalized,
                    "bbox": bbox,
                    "confidence": confidence,
                    "match_type": "exact",
                    "match_score": 1.0,
                }
            )
        # Check for substring match
        elif target_lower in text_lower or target_lower in normalized_lower:
            matches.append(
                {
                    "text": text,
                    "normalized": normalized,
                    "bbox": bbox,
                    "confidence": confidence,
                    "match_type": "substring",
                    "match_score": 0.9,
                }
            )
        # Check if all target words are present
        elif all(word in text_lower or word in normalized_lower for word in target_words):
            matches.append(
                {
                    "text": text,
                    "normalized": normalized,
                    "bbox": bbox,
                    "confidence": confidence,
                    "match_type": "all_words",
                    "match_score": 0.8,
                }
            )
        # Check for fuzzy match with common OCR errors
        elif is_fuzzy_match(text, target_text) or is_fuzzy_match(normalized, target_text):
            matches.append(
                {
                    "text": text,
                    "normalized": normalized,
                    "bbox": bbox,
                    "confidence": confidence,
                    "match_type": "fuzzy",
                    "match_score": calculate_similarity(normalized, target_text),
                }
            )

    # Sort by match score and confidence
    matches.sort(key=lambda x: (x["match_score"], x["confidence"]), reverse=True)
    return matches


def is_fuzzy_match(text1, text2, threshold=0.7):
    """Check if two texts are similar enough considering OCR errors."""
    # Simple character-based similarity
    text1_lower = text1.lower()
    text2_lower = text2.lower()

    # Check Levenshtein-like similarity
    similarity = calculate_similarity(text1_lower, text2_lower)
    return similarity >= threshold


def calculate_similarity(text1, text2):
    """Calculate similarity score between two strings."""
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


def test_improved_ocr(image_path, target_text):
    """Test OCR with improved text matching."""
    print("=" * 70)
    print(f"Improved OCR Test for '{target_text}'")
    print("=" * 70)

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return

    print(f"\n📁 Image: {image_path}")
    print(f"🎯 Target text: '{target_text}'")

    # Initialize EasyOCR
    print("\n🚀 Initializing EasyOCR...")
    reader = easyocr.Reader(["en"], gpu=False)

    # Preprocess image (sharpen for better results)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sharpened = cv2.filter2D(gray, -1, np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]))

    # Run OCR
    print("\n🔍 Running OCR detection...")
    results = reader.readtext(sharpened)

    print(f"\n📝 Detected {len(results)} text regions:")
    for i, (bbox, text, conf) in enumerate(results[:20], 1):
        normalized = normalize_ocr_text(text)
        if text != normalized:
            print(f"  {i:2}. '{text}' -> '{normalized}' (conf: {conf:.2%})")
        else:
            print(f"  {i:2}. '{text}' (conf: {conf:.2%})")

    if len(results) > 20:
        print(f"  ... and {len(results) - 20} more")

    # Find matches with improved matching
    print(f"\n🎯 Searching for '{target_text}'...")
    matches = find_text_with_normalization(results, target_text)

    if matches:
        print(f"\n✅ Found {len(matches)} potential match(es):")
        for i, match in enumerate(matches[:5], 1):
            print(f"\n  Match {i}:")
            print(f"    Original: '{match['text']}'")
            if match["text"] != match["normalized"]:
                print(f"    Normalized: '{match['normalized']}'")
            print(f"    Match type: {match['match_type']}")
            print(f"    Confidence: {match['confidence']:.2%}")
            print(f"    Match score: {match['match_score']:.2f}")

            # Calculate center
            bbox = match["bbox"]
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))
            print(f"    Location: ({center_x}, {center_y})")

        # Save visualization
        visualize_match(image, matches[0], target_text)
    else:
        print(f"\n❌ No matches found for '{target_text}'")
        print("\n💡 Try adjusting the normalization rules or preprocessing parameters")


def visualize_match(image, match, target_text):
    """Create visualization of the best match."""
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt

    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.imshow(image_rgb)
    ax.set_title(f"OCR Detection: '{target_text}' -> '{match['normalized']}'", fontsize=14)
    ax.axis("off")

    # Draw bounding box
    bbox = match["bbox"]
    polygon = patches.Polygon(bbox, linewidth=3, edgecolor="lime", facecolor="none")
    ax.add_patch(polygon)

    # Draw center dot
    x_coords = [p[0] for p in bbox]
    y_coords = [p[1] for p in bbox]
    center_x = int(np.mean(x_coords))
    center_y = int(np.mean(y_coords))

    circle = patches.Circle((center_x, center_y), radius=10, color="lime", fill=True)
    ax.add_patch(circle)

    # Add annotation
    info = f"Detected: '{match['text']}'"
    if match["text"] != match["normalized"]:
        info += f"\nNormalized: '{match['normalized']}'"
    info += f"\nConfidence: {match['confidence']:.1%}"

    ax.text(
        10,
        image.shape[0] - 10,
        info,
        fontsize=12,
        color="white",
        weight="bold",
        va="bottom",
        ha="left",
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "green", "alpha": 0.8},
    )

    # Save
    save_path = "/Users/work/Workspaces/computer-use-agent/all_flowsheets_ocr_match.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n💾 Visualization saved to: {save_path}")
    plt.show()


def main():
    """Run the improved OCR test."""
    image_path = "/Users/work/Workspaces/computer-use-agent/trajectories/data/osh_heart_header_screenshot.png"
    target_text = "OSH Heart Failure"

    test_improved_ocr(image_path, target_text)

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
