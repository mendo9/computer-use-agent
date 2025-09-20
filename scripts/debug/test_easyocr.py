"""
EasyOCR test for finding "Flowsheets" text in image.
"""

import cv2
import easyocr
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


def test_easyocr():
    """Test EasyOCR on the flowsheets screenshot."""
    print("=" * 60)
    print("EasyOCR Test for 'Flowsheets' Text Detection")
    print("=" * 60)

    # Initialize EasyOCR
    print("\n🚀 Initializing EasyOCR...")
    reader = easyocr.Reader(["en"], gpu=False)

    # Load image
    image_path = "/Users/work/Workspaces/computer-use-agent/trajectories/data/all_flowsheets_header_screenshot.png"
    print(f"\n📁 Loading image: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        print("❌ Failed to load image")
        return

    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]}")

    # Run OCR
    print("\n🔍 Running EasyOCR detection...")
    results = reader.readtext(image)

    # Find "Flowsheets" text
    # target_text = "All Flowsheets"
    target_text = "Patient"
    found_text = None
    found_bbox = None
    found_confidence = 0

    print(f"\n🎯 Searching for '{target_text}' in detected text...")
    print("-" * 60)

    if results:
        print(f"\n📝 Found {len(results)} text regions:\n")
        for idx, (bbox, text, confidence) in enumerate(results, 1):
            # Calculate center of bounding box
            if len(bbox) >= 4:
                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
            else:
                continue

            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))

            print(f"{idx:3}. Text: '{text}'")
            print(f"     Confidence: {confidence:.2%}")
            print(f"     Location: ({center_x}, {center_y})")

            # Check if this is our target text
            if target_text.lower() in text.lower():
                print("     >>> ✅ MATCH FOUND! <<<")
                found_text = text
                found_bbox = bbox
                found_confidence = confidence
            print()

    print("-" * 60)

    # Create visualization
    if found_text:
        print(f"\n✅ SUCCESS! Found '{found_text}' with {found_confidence:.2%} confidence")

        # Convert BGR to RGB for matplotlib
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        ax.imshow(image_rgb)
        ax.set_title(f"EasyOCR Detection - Found: '{found_text}'", fontsize=16)
        ax.axis("off")

        # Calculate center
        x_coords = [point[0] for point in found_bbox]
        y_coords = [point[1] for point in found_bbox]
        center_x = int(np.mean(x_coords))
        center_y = int(np.mean(y_coords))

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
            bbox={
                "boxstyle": "round,pad=0.5",
                "facecolor": "black",
                "edgecolor": "lime",
                "alpha": 0.8,
            },
        )

        # Save the result
        save_path = (
            f"/Users/work/Workspaces/computer-use-agent/easyocr_result_{target_text.lower()}.png"
        )
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"💾 Visualization saved to: {save_path}")

        plt.show()
    else:
        print(f"\n❌ '{target_text}' not found in the image")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_easyocr()
