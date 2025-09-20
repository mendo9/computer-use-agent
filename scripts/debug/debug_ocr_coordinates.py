"""
Debug OCR coordinate accuracy by testing different strategies.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path so we can import from src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.vision.finder import find_target_advanced
from src.vision.ocr import TEXT_MAP


async def debug_ocr_coordinates(screenshot_path: str, query: str):
    """Debug OCR coordinate accuracy with different strategies."""

    # Check if screenshot exists
    if not Path(screenshot_path).exists():
        print(f"❌ Screenshot not found: {screenshot_path}")
        return

    # Read the screenshot
    with open(screenshot_path, "rb") as f:
        png_bytes = f.read()

    print(f"🔍 Testing OCR coordinate accuracy for '{query}'")
    print(f"📸 Using screenshot: {screenshot_path}\n")

    # Test different strategies with debug enabled
    strategies: list[dict[str, str | None]] = [
        {"region": None, "prefer": "highest_confidence", "label": "Default (highest confidence)"},
        {"region": None, "prefer": "leftmost", "label": "Leftmost"},
        {
            "region": "left",
            "prefer": "highest_confidence",
            "label": "Left region, highest confidence",
        },
        {"region": "left", "prefer": "leftmost", "label": "Left region, leftmost"},
        {"region": None, "prefer": "topmost", "label": "Topmost"},
        {"region": None, "prefer": "largest", "label": "Largest area"},
    ]

    for i, strategy in enumerate(strategies, 1):
        label = strategy["label"]
        region = strategy["region"]
        prefer = strategy["prefer"] or "highest_confidence"

        print(f"📋 Strategy {i}: {label}")
        print("=" * 50)

        coords = find_target_advanced(
            png_bytes,
            query,
            region=region,
            prefer=prefer,
            debug=True,  # Enable detailed debugging
        )

        if coords:
            print(f"✅ Final result: {coords}")
        else:
            print("❌ No match found")

        print("\n" + "=" * 60 + "\n")


def main():
    """Main function to run OCR coordinate debugging."""

    print("OCR Coordinate Accuracy Debugger")

    # Parse command line arguments
    if len(sys.argv) < 3:
        print("\nUsage: python debug_ocr_coordinates.py <screenshot_path> <query>")
        print("  <screenshot_path>: Path to the screenshot image")
        print("  <query>: OCR query to test (must be in TEXT_MAP)")
        print(f"\nAvailable OCR queries: {list(TEXT_MAP.keys())}")
        print("\nExample:")
        print(
            "  python debug_ocr_coordinates.py trajectories/data/osh_heart_screenshot.png osh_heart_failure_header"
        )
        return

    screenshot_path = sys.argv[1]
    query = sys.argv[2]

    # Validate query
    if query not in TEXT_MAP:
        print(f"❌ Invalid query '{query}'. Must be one of: {list(TEXT_MAP.keys())}")
        return

    print(f"\nUsing screenshot: {screenshot_path}")
    print(f"Testing query: {query} -> '{TEXT_MAP[query]}'")

    # Run the async debugging function
    asyncio.run(debug_ocr_coordinates(screenshot_path, query))
    print("\nDone!")


if __name__ == "__main__":
    main()
