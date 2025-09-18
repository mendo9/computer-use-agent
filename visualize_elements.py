#!/usr/bin/env python3
"""
Simple script to visualize detected UI elements on a screenshot.
Usage: python visualize_elements.py <screenshot_path> [element1] [element2] ...
"""

import sys
from pathlib import Path

import cv2

from src.vision.finder import TEMPLATE_MAP, find_target_center


def visualize_elements(screenshot_path: str, elements: list = None) -> None:
    """Visualize detected elements on screenshot."""

    if not Path(screenshot_path).exists():
        print(f"❌ Screenshot not found: {screenshot_path}")
        return

    # Load image
    image = cv2.imread(screenshot_path)
    if image is None:
        print(f"❌ Could not load image: {screenshot_path}")
        return

    # Convert to PNG bytes for finder
    _, buffer = cv2.imencode(".png", image)
    png_bytes = buffer.tobytes()

    # Default elements if none provided
    if not elements:
        elements = [
            "google_news_sign_in_button",
            "google_news_next_button",
            "google_news_tech_button",
            "google_news_email_text",
        ]

    print(f"📸 Analyzing screenshot: {screenshot_path}")
    print(f"🔍 Looking for elements: {elements}")
    print("-" * 50)

    # Create result image
    result_image = image.copy()
    found_elements = []

    # Colors for different elements
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    for i, element in enumerate(elements):
        center = find_target_center(png_bytes, element)
        color = colors[i % len(colors)]

        if center:
            print(f"✅ {element}: ({center[0]}, {center[1]})")
            found_elements.append((element, center, color))

            # Draw circle at center
            cv2.circle(result_image, center, 8, color, -1)
            cv2.circle(result_image, center, 12, color, 2)

            # Add label
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2

            # Position label above the point
            text_x = center[0] - 50
            text_y = center[1] - 20

            # Ensure text stays within image bounds
            text_x = max(10, min(text_x, image.shape[1] - 200))
            text_y = max(30, text_y)

            # Draw background for text
            label = f"{element}: {center}"
            (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, thickness)
            cv2.rectangle(
                result_image,
                (text_x - 5, text_y - text_height - 5),
                (text_x + text_width + 5, text_y + 5),
                (0, 0, 0),
                -1,
            )

            # Draw text
            cv2.putText(result_image, label, (text_x, text_y), font, font_scale, color, thickness)

        else:
            print(f"❌ {element}: Not found")

    # Save result
    output_path = f"elements_{Path(screenshot_path).stem}.png"
    cv2.imwrite(output_path, result_image)

    print("-" * 50)
    print(f"📊 Found {len(found_elements)} out of {len(elements)} elements")
    print(f"💾 Result saved to: {output_path}")

    return found_elements


def main():
    if len(sys.argv) < 2:
        print("Usage: python visualize_elements.py <screenshot_path> [element1] [element2] ...")
        print(f"Available elements: {list(TEMPLATE_MAP.keys())}")
        return

    screenshot_path = sys.argv[1]
    elements = sys.argv[2:] if len(sys.argv) > 2 else None

    visualize_elements(screenshot_path, elements)


if __name__ == "__main__":
    main()
