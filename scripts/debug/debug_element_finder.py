#!/usr/bin/env python3
"""
Debug script to visualize detected UI elements with their coordinates.
Shows screenshot with bounding boxes and coordinates of found elements.
"""

import sys
from pathlib import Path

import cv2
import numpy as np

# Add project root to Python path so we can import from src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.vision.finder import TEMPLATE_MAP, find_target_center


def draw_detection_results(
    image: np.ndarray, detections: list, title: str = "Detections"
) -> np.ndarray:
    """Draw bounding boxes and coordinates on the image."""
    result_image = image.copy()

    for _, detection in enumerate(detections):
        # Get detection info
        center = detection.center
        bbox = detection.bbox if hasattr(detection, "bbox") else None
        confidence = detection.confidence if hasattr(detection, "confidence") else 0.0

        # Draw center point
        cv2.circle(result_image, center, 5, (0, 255, 0), -1)

        # Draw bounding box if available
        if bbox:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Add text with coordinates and confidence
        text = f"({center[0]}, {center[1]}) conf:{confidence:.2f}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 1

        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

        # Draw background rectangle
        text_x = center[0] + 10
        text_y = center[1] - 10
        cv2.rectangle(
            result_image,
            (text_x - 2, text_y - text_height - 2),
            (text_x + text_width + 2, text_y + baseline + 2),
            (0, 0, 0),
            -1,
        )

        # Draw text
        cv2.putText(
            result_image, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness
        )

    return result_image


def test_element_detection(
    screenshot_path: str, elements_to_find: list[str], region: str
) -> dict[str, tuple[int, int] | None]:
    """Test element detection and save visualization."""

    # Load screenshot
    if not Path(screenshot_path).exists():
        print(f"Screenshot not found: {screenshot_path}")
        return {}

    # Read image
    image = cv2.imread(screenshot_path)
    if image is None:
        print(f"Could not load image: {screenshot_path}")
        return {}

    print(f"Testing element detection on: {screenshot_path}")
    print(f"Image size: {image.shape[1]}x{image.shape[0]}")
    print(f"Elements to find: {elements_to_find}")
    print("-" * 50)

    # Convert to PNG bytes for finder function
    _, buffer = cv2.imencode(".png", image)
    png_bytes = buffer.tobytes()

    results: dict[str, tuple[int, int] | None] = {}
    all_detections = []

    for element in elements_to_find:
        print(f"\nSearching for: {element}")

        # Find center using existing finder
        center = find_target_center(png_bytes, element)
        # center = (245, 405)
        # center = find_target_advanced(png_bytes, element, prefer="topmost")

        if center:
            print(f"  ✓ Found at: {center}")
            results[element] = center

            # Create a mock detection object for visualization
            class MockDetection:
                def __init__(self, center, confidence=0.0):
                    self.center = center
                    self.confidence = confidence

            all_detections.append(MockDetection(center))
        else:
            print("  ✗ Not found")
            results[element] = None

    # Draw all detections on image
    if all_detections:
        result_image = draw_detection_results(image, all_detections, "Element Detection Results")

        # Save result
        output_path = (
            f"{Path(screenshot_path).parent}/debug_finder_{Path(screenshot_path).stem}.png"
        )
        cv2.imwrite(output_path, result_image)
        print(f"\n✓ Results saved to: {output_path}")
    else:
        print("\n✗ No elements found to visualize")

    return results


def main():
    """Main function to run element detection debugging."""

    print("UI Element Detection Debugger")

    # Parse command line arguments
    if len(sys.argv) < 4:
        print("\nUsage: python debug_element_finder.py <screenshot_path> <elements>")
        print("  <elements>: space-separated list of elements to test or individual arguments")
        print(f"Available elements: {list(TEMPLATE_MAP.keys())}")
        return

    screenshot_path = sys.argv[1]

    # Handle both individual arguments and space-separated string
    # Single argument with space-separated elements (from launch.json) or multiple arguments (command line)
    elements = sys.argv[2].split() if len(sys.argv) == 3 else sys.argv[2:]
    region = sys.argv[3]

    print(f"\nUsing screenshot: {screenshot_path}")
    print(f"Elements to test: {elements}")

    results = test_element_detection(screenshot_path, elements, region)
    if results:
        print(
            f"\nSummary: Found {len([v for v in results.values() if v is not None])}/{len(results)} elements"
        )
    print("\nDone!")


if __name__ == "__main__":
    main()
