"""
Test the production-ready improved OCR module.
"""

from pathlib import Path

from src.vision.ocr_improved import TEXT_MAP, add_text_mapping, find_text_by_ocr_improved


def test_production_ocr():
    """Test the production OCR module with real images."""
    print("=" * 70)
    print("Production OCR Module Test")
    print("=" * 70)

    # Show current text mappings
    print("\n📚 Current TEXT_MAP entries:")
    for query, text in TEXT_MAP.items():
        print(f"  '{query}' -> '{text}'")

    # Test cases
    test_cases = [
        {
            "image": "trajectories/data/flowsheets_icon_header_screenshot.png",
            "text": "Flowsheets",
            "expected": True,
        },
        {
            "image": "trajectories/data/all_flowsheets_header_screenshot.png",
            "text": "All Flowsheets",
            "expected": True,
        },
        {
            "image": "trajectories/data/all_flowsheets_header_screenshot.png",
            "text": "Patient",
            "expected": True,
        },
        {
            "image": "trajectories/data/all_flowsheets_header_screenshot.png",
            "text": "My Favorites",
            "expected": True,
        },
        {
            "image": "trajectories/data/flowsheets_icon_header_screenshot.png",
            "text": "Vital Signs",
            "expected": True,  # This is in the image
        },
    ]

    success_count = 0
    total_count = len(test_cases)

    for i, test in enumerate(test_cases, 1):
        image_path = Path(test["image"])
        target_text = test["text"]
        expected = test["expected"]

        print(f"\n{'=' * 50}")
        print(f"Test {i}/{total_count}: '{target_text}'")
        print(f"Image: {image_path.name}")

        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            continue

        # Read image as PNG bytes
        with open(image_path, "rb") as f:
            png_bytes = f.read()

        # Test the OCR
        coords = find_text_by_ocr_improved(png_bytes, target_text)

        if coords:
            print(f"✅ Result: Found at {coords}")
            if expected:
                success_count += 1
        else:
            print("❌ Result: Not found")
            if not expected:
                success_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Success rate: {success_count}/{total_count} ({success_count / total_count * 100:.1f}%)")

    # Test adding custom mapping
    print("\n📝 Testing custom text mapping...")
    custom_query = "custom_button"
    custom_text = "Custom Button Text"

    print(f"Adding mapping: '{custom_query}' -> '{custom_text}'")
    add_text_mapping(custom_query, custom_text)

    if custom_query in TEXT_MAP and TEXT_MAP[custom_query] == custom_text:
        print("✅ Custom mapping added successfully")
    else:
        print("❌ Failed to add custom mapping")

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_production_ocr()
