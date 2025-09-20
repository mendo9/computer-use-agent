"""
Simple OCR test that finds "Flowsheets" and prints coordinates.
"""

import cv2
import numpy as np
from paddleocr import PaddleOCR


def test_paddleocr():
    """Test PaddleOCR on the flowsheets screenshot."""
    print("=" * 60)
    print("PaddleOCR Test for 'Flowsheets' Text Detection")
    print("=" * 60)

    # Initialize PaddleOCR
    print("\n🚀 Initializing PaddleOCR (this may take a minute on first run)...")
    ocr = PaddleOCR(use_angle_cls=False, lang="en", use_gpu=False, show_log=False)

    # Load image
    image_path = "/Users/work/Workspaces/computer-use-agent/trajectories/data/flowsheets_icon_header_screenshot.png"
    print(f"\n📁 Loading image: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        print("❌ Failed to load image")
        return

    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]}")

    # Run OCR
    print("\n🔍 Running OCR detection (this may take a moment)...")
    results = ocr.predict(image, use_textline_orientation=False)

    # Find "Flowsheets" text
    target_text = "Flowsheets"
    found = False

    print(f"\n🎯 Searching for '{target_text}' in detected text...")
    print("-" * 60)

    if results and results[0]:
        print(f"\n📝 Found {len(results[0])} text regions:\n")
        for idx, line in enumerate(results[0], 1):
            bbox = line[0]
            text = line[1][0]
            confidence = line[1][1]

            # Calculate center of bounding box
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))

            print(f"{idx:3}. Text: '{text}'")
            print(f"     Confidence: {confidence:.2%}")
            print(f"     Location: ({center_x}, {center_y})")

            # Check if this is our target text
            if target_text.lower() in text.lower():
                print("     >>> ✅ MATCH FOUND! <<<")
                found = True

                # Save result image with annotation
                result_image = image.copy()
                # Draw green circle at center
                cv2.circle(result_image, (center_x, center_y), 15, (0, 255, 0), -1)
                # Draw bounding box
                pts = np.array(bbox, np.int32)
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(result_image, [pts], True, (0, 255, 0), 3)
                # Add text label
                cv2.putText(
                    result_image,
                    f"'{text}' FOUND",
                    (center_x - 50, center_y - 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                # Save the result
                save_path = "/Users/work/Workspaces/computer-use-agent/paddleocr_result_marked.png"
                cv2.imwrite(save_path, result_image)
                print(f"     💾 Result saved to: {save_path}")
            print()

    print("-" * 60)

    if found:
        print(f"\n✅ SUCCESS! Found '{target_text}' in the image")
    else:
        print(f"\n❌ '{target_text}' not found in the image")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_paddleocr()
