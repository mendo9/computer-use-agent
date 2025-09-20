"""
Quick OCR test with visualization for finding "Flowsheets" in the screenshot.
"""

import cv2
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from paddleocr import PaddleOCR


def test_paddleocr():
    """Test PaddleOCR on the flowsheets screenshot."""
    print("=" * 60)
    print("PaddleOCR Test for 'Flowsheets' Text Detection")
    print("=" * 60)

    # Initialize PaddleOCR
    print("\n🚀 Initializing PaddleOCR...")
    ocr = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False, show_log=False)

    # Load image
    image_path = "/Users/work/Workspaces/computer-use-agent/trajectories/data/flowsheets_icon_header_screenshot.png"
    print(f"\n📁 Loading image: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        print("❌ Failed to load image")
        return

    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]}")

    # Run OCR
    print("\n🔍 Running OCR detection...")
    results = ocr.ocr(image, cls=True)

    # Find "Flowsheets" text
    target_text = "Flowsheets"
    found_text = None
    found_bbox = None

    print(f"\n🎯 Searching for '{target_text}' in detected text...")

    if results and results[0]:
        print(f"📝 Found {len(results[0])} text regions:")
        for idx, line in enumerate(results[0]):
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]

            print(f"  {idx + 1}. '{text}' (confidence: {confidence:.2f})")

            # Check if this is our target text
            if target_text.lower() in text.lower():
                found_text = text
                found_bbox = bbox
                print("     ✅ MATCH FOUND!")

    # Visualize results
    print("\n📊 Creating visualization...")

    # Convert BGR to RGB for matplotlib
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.imshow(image_rgb)
    ax.set_title(f"PaddleOCR Detection - Target: '{target_text}'", fontsize=16)
    ax.axis("off")

    if found_text and found_bbox:
        # Calculate center of bounding box
        x_coords = [point[0] for point in found_bbox]
        y_coords = [point[1] for point in found_bbox]
        center_x = int(np.mean(x_coords))
        center_y = int(np.mean(y_coords))

        print(f"\n✅ SUCCESS! Found '{found_text}' at ({center_x}, {center_y})")

        # Draw green dot at center
        circle = patches.Circle(
            (center_x, center_y), radius=15, color="lime", linewidth=4, fill=True
        )
        ax.add_patch(circle)

        # Draw bounding box
        polygon = patches.Polygon(found_bbox, linewidth=3, edgecolor="lime", facecolor="none")
        ax.add_patch(polygon)

        # Add text annotation
        ax.text(
            center_x,
            center_y - 40,
            f"'{found_text}' FOUND HERE",
            fontsize=14,
            color="lime",
            weight="bold",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="black", edgecolor="lime", alpha=0.8),
        )

        # Draw arrow pointing to the text
        ax.annotate(
            "",
            xy=(center_x, center_y),
            xytext=(center_x, center_y - 35),
            arrowprops=dict(arrowstyle="->", color="lime", lw=3),
        )
    else:
        print(f"\n❌ Text '{target_text}' not found")
        ax.text(
            image.shape[1] / 2,
            50,
            f"'{target_text}' NOT FOUND",
            fontsize=16,
            color="red",
            weight="bold",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="yellow", alpha=0.8),
        )

    # Save and show
    save_path = "/Users/work/Workspaces/computer-use-agent/paddleocr_flowsheets_result.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n💾 Result saved to: {save_path}")

    plt.show()

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_paddleocr()
