#!/usr/bin/env python3
"""
Debug script to visualize detected UI elements with their coordinates.
Shows screenshot with bounding boxes and coordinates of found elements.
"""

import asyncio
from pathlib import Path

import cv2
import numpy as np

from src.vision.finder import TEMPLATE_MAP, find_target_center


def draw_detection_results(
    image: np.ndarray, detections: list, title: str = "Detections"
) -> np.ndarray:
    """Draw bounding boxes and coordinates on the image."""
    result_image = image.copy()

    for i, detection in enumerate(detections):
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


def test_element_detection(screenshot_path: str, elements_to_find: list[str]) -> None:
    """Test element detection and save visualization."""

    # Load screenshot
    if not Path(screenshot_path).exists():
        print(f"Screenshot not found: {screenshot_path}")
        return

    # Read image
    image = cv2.imread(screenshot_path)
    if image is None:
        print(f"Could not load image: {screenshot_path}")
        return

    print(f"Testing element detection on: {screenshot_path}")
    print(f"Image size: {image.shape[1]}x{image.shape[0]}")
    print(f"Elements to find: {elements_to_find}")
    print("-" * 50)

    # Convert to PNG bytes for finder function
    _, buffer = cv2.imencode(".png", image)
    png_bytes = buffer.tobytes()

    results = {}
    all_detections = []

    for element in elements_to_find:
        print(f"\nSearching for: {element}")

        # Find center using existing finder
        center = find_target_center(png_bytes, element)

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
        output_path = f"debug_detection_results_{Path(screenshot_path).stem}.png"
        cv2.imwrite(output_path, result_image)
        print(f"\n✓ Results saved to: {output_path}")
    else:
        print("\n✗ No elements found to visualize")

    return results


async def take_and_analyze_screenshot(elements_to_find: list[str]) -> None:
    """Take a new screenshot and analyze it."""
    try:
        # Try to import Windows backend
        from src.backends.windows_computer import WindowsComputer

        # Create Windows computer instance
        computer = WindowsComputer()

        # Take screenshot
        print("Taking screenshot...")
        screenshot_bytes = await computer.screenshot_bytes()

        # Save screenshot
        screenshot_path = "current_screenshot.png"
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)
        print(f"Screenshot saved: {screenshot_path}")

        # Analyze the screenshot
        test_element_detection(screenshot_path, elements_to_find)

    except ImportError:
        print("Windows backend not available. Please provide a screenshot file path instead.")
    except Exception as e:
        print(f"Error taking screenshot: {e}")


def main():
    """Main function to run element detection debugging."""

    print("UI Element Detection Debugger")
    print("=" * 40)

    # Available elements from TEMPLATE_MAP
    available_elements = list(TEMPLATE_MAP.keys())
    print(f"\nAvailable elements: {available_elements}")

    # Default elements to test (you can modify this)
    elements_to_test = [
        "google_news_email_text",
        "google_news_next_button",
        "google_news_tech_button",
        "google_news_sign_in_button",
    ]

    # Check if screenshot file is provided as argument
    import sys

    if len(sys.argv) > 1:
        screenshot_path = sys.argv[1]
        print(f"\nUsing provided screenshot: {screenshot_path}")
        test_element_detection(screenshot_path, elements_to_test)
    else:
        print("\nNo screenshot provided. Attempting to take new screenshot...")
        asyncio.run(take_and_analyze_screenshot(elements_to_test))

    print("\nDone!")


if __name__ == "__main__":
    main()
