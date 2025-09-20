#!/usr/bin/env python3
"""
Debug script to test OCR text detection with visualization.
Shows screenshot with detected text locations and coordinates.
"""

import sys
from pathlib import Path

import cv2
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

# Add project root to Python path so we can import from src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.vision.ocr import find_text_by_ocr


def visualize_ocr_detection(
    image_path: str, target_texts: list[str]
) -> dict[str, tuple[int, int] | None]:
    """Test OCR detection and create visualization."""

    # Load image
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return {}

    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        return {}

    print(f"📁 Testing OCR detection on: {image_path}")
    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]}")
    print(f"🎯 Target texts: {target_texts}")
    print("-" * 70)

    # Convert to PNG bytes for OCR function
    _, buffer = cv2.imencode(".png", image)
    png_bytes = buffer.tobytes()

    results = {}
    detections = []

    # Test each target text
    for target_text in target_texts:
        print(f"\n🔍 Searching for: '{target_text}'")

        # Use production OCR function for coordinates and bbox
        result = find_text_by_ocr(png_bytes, target_text, return_bbox=True)

        if result[0]:  # coords found
            coords, bbox = result
            print(f"  ✅ Found at: {coords}")
            results[target_text] = coords
            detections.append({"text": target_text, "coords": coords, "bbox": bbox})
        else:
            print("  ❌ Not found")
            results[target_text] = None

    # Create visualization
    if detections:
        print("\n📊 Creating visualization...")
        create_visualization(image, detections, image_path, target_texts)
    else:
        print("\n❌ No text found to visualize")

    return results


def create_visualization(
    image: np.ndarray, detections: list, image_path: str, target_texts: list[str]
):
    """Create and save visualization of OCR results."""

    # Convert BGR to RGB for matplotlib
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.imshow(image_rgb)
    ax.set_title(
        f"OCR Detection Results - {len(detections)}/{len(target_texts)} found", fontsize=16
    )
    ax.axis("off")

    # Draw detections
    colors = ["lime", "red", "yellow", "cyan", "magenta", "orange"]

    for i, detection in enumerate(detections):
        coords = detection["coords"]
        text = detection["text"]
        color = colors[i % len(colors)]

        # Draw exact bounding box if available
        bbox = detection.get("bbox")
        if bbox:
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            width = max_x - min_x
            height = max_y - min_y

            # Draw exact bounding box
            rect = patches.Rectangle(
                (min_x, min_y),
                width,
                height,
                linewidth=3,
                edgecolor=color,
                facecolor="none",
                alpha=0.8,
            )
            ax.add_patch(rect)

        # Draw small center dot
        circle = patches.Circle(coords, radius=5, color=color, linewidth=2, fill=True, alpha=0.9)
        ax.add_patch(circle)

        # Add text annotation with background
        ax.annotate(
            f"'{text}'\n({coords[0]}, {coords[1]})",
            xy=coords,
            xytext=(coords[0], coords[1] - 50),
            fontsize=12,
            color=color,
            weight="bold",
            ha="center",
            bbox={
                "boxstyle": "round,pad=0.5",
                "facecolor": "black",
                "edgecolor": color,
                "alpha": 0.8,
            },
            arrowprops={"arrowstyle": "->", "color": color, "lw": 2},
        )

    # Save result
    output_path = f"{Path(image_path).parent}/debug_ocr_{Path(image_path).stem}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"💾 Visualization saved to: {output_path}")

    plt.show()


def main():
    """Main function to run OCR detection debugging."""

    print("OCR Detection Debugger")
    print("=" * 70)

    # Parse command line arguments
    if len(sys.argv) < 3:
        print("\nUsage: python test_easyocr.py <screenshot_path> <texts_to_find>")
        print("  <texts_to_find>: space-separated text strings to search for")
        print("\nExample:")
        print('  python test_easyocr.py screenshot.png "All Flowsheets" "Patient" "My Favorites"')
        return

    image_path = sys.argv[1]

    # Handle both individual arguments and space-separated string
    target_texts = sys.argv[2:] if len(sys.argv) > 3 else sys.argv[2].split()

    print(f"\n📁 Screenshot: {image_path}")
    print(f"🎯 Target texts: {target_texts}")

    # Run OCR detection test
    results = visualize_ocr_detection(image_path, target_texts)

    # Print summary
    if results:
        found_count = len([v for v in results.values() if v is not None])
        total_count = len(results)
        print(f"\n📋 Summary: Found {found_count}/{total_count} text strings")

        for text, coords in results.items():
            status = f"✅ {coords}" if coords else "❌ Not found"
            print(f"  '{text}': {status}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
