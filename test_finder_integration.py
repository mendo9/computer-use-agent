"""
Test the integration of improved OCR with the finder module.
"""

from pathlib import Path

from src.vision.finder import find_target_center
from src.vision.ocr_improved import add_text_mapping


def test_finder_with_ocr():
    """Test finder.py with improved OCR integration."""
    print("=" * 70)
    print("Testing Finder Integration with Improved OCR")
    print("=" * 70)

    # Test cases
    test_cases = [
        {
            "image": "trajectories/data/flowsheets_icon_header_screenshot.png",
            "query": "flowsheets_header",
            "expected_text": "Flowsheets",
        },
        {
            "image": "trajectories/data/all_flowsheets_header_screenshot.png",
            "query": "all_flowsheets",
            "expected_text": "All Flowsheets",
        },
    ]

    for test in test_cases:
        image_path = Path(test["image"])
        query = test["query"]
        expected_text = test["expected_text"]

        print(f"\n📁 Test: {image_path.name}")
        print(f"🔍 Query: '{query}' -> '{expected_text}'")

        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            continue

        # Read image as PNG bytes
        with open(image_path, "rb") as f:
            png_bytes = f.read()

        # Test the finder
        coords = find_target_center(png_bytes, query)

        if coords:
            print(f"✅ Found at coordinates: {coords}")
        else:
            print("❌ Not found")

            # Try adding a custom mapping if not in default map
            print(f"💡 Adding custom mapping: '{query}' -> '{expected_text}'")
            add_text_mapping(query, expected_text)

            # Retry with custom mapping
            coords = find_target_center(png_bytes, query)
            if coords:
                print(f"✅ Found with custom mapping at: {coords}")
            else:
                print("❌ Still not found even with custom mapping")

    print("\n" + "=" * 70)
    print("Integration Test Complete!")
    print("=" * 70)


def test_direct_ocr_improved():
    """Test the improved OCR directly."""
    from src.vision.ocr_improved import find_text_by_ocr_improved

    print("\n" + "=" * 70)
    print("Direct OCR Improved Test")
    print("=" * 70)

    image_path = Path("trajectories/data/all_flowsheets_header_screenshot.png")

    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return

    with open(image_path, "rb") as f:
        png_bytes = f.read()

    # Test different text patterns
    test_texts = ["All Flowsheets", "Select Patient Flowsheets", "My Favorites", "Patient"]

    for text in test_texts:
        print(f"\n🔍 Searching for: '{text}'")
        coords = find_text_by_ocr_improved(png_bytes, text)
        if coords:
            print(f"✅ Found at: {coords}")
        else:
            print("❌ Not found")


if __name__ == "__main__":
    # Test the integrated finder
    test_finder_with_ocr()

    # Test direct OCR
    test_direct_ocr_improved()
