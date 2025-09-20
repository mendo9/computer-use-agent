"""
Test OCR detection for "All Flowsheets" text in dialog screenshot.
"""

import cv2
import easyocr
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


def preprocess_image(image):
    """Preprocess image to improve OCR accuracy."""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply different preprocessing techniques
    processed_images = {
        "original": image,
        "grayscale": gray,
        "threshold": cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        "adaptive_threshold": cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        ),
        "denoised": cv2.fastNlMeansDenoising(gray, None, 10, 7, 21),
        "sharpened": cv2.filter2D(gray, -1, np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])),
    }

    return processed_images


def test_easyocr_with_preprocessing(image_path, target_text):
    """Test EasyOCR with different preprocessing techniques."""
    print("=" * 70)
    print(f"Testing EasyOCR with preprocessing for '{target_text}'")
    print("=" * 70)

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Failed to load image: {image_path}")
        return

    print(f"\n📁 Image: {image_path}")
    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]} pixels")
    print(f"🎯 Target text: '{target_text}'")

    # Initialize EasyOCR
    print("\n🚀 Initializing EasyOCR...")
    reader = easyocr.Reader(["en"], gpu=False)

    # Get preprocessed versions
    processed_images = preprocess_image(image)

    results_by_method = {}

    # Test each preprocessing method
    for method_name, processed_img in processed_images.items():
        print(f"\n📚 Testing with {method_name} preprocessing...")

        try:
            # Run OCR
            if len(processed_img.shape) == 2:  # Grayscale
                results = reader.readtext(processed_img)
            else:  # Color
                results = reader.readtext(processed_img)

            found_matches = []
            all_texts = []

            # Search for target text
            for bbox, text, confidence in results:
                all_texts.append(text)

                # Check for exact match or partial match
                if target_text.lower() in text.lower() or text.lower() in target_text.lower():
                    found_matches.append(
                        {
                            "text": text,
                            "bbox": bbox,
                            "confidence": confidence,
                            "match_type": "exact"
                            if text.lower() == target_text.lower()
                            else "partial",
                        }
                    )

                # Also check for split text (e.g., "All" and "Flowsheets" separately)
                elif any(word.lower() in text.lower() for word in target_text.split()):
                    found_matches.append(
                        {"text": text, "bbox": bbox, "confidence": confidence, "match_type": "word"}
                    )

            results_by_method[method_name] = {
                "matches": found_matches,
                "all_texts": all_texts,
                "total_detected": len(results),
            }

            # Print results
            if found_matches:
                print(f"  ✅ Found {len(found_matches)} match(es):")
                for match in found_matches:
                    print(
                        f"    - '{match['text']}' ({match['match_type']} match, conf: {match['confidence']:.2%})"
                    )
            else:
                print("  ❌ No matches found")
                print(f"  📝 Detected texts: {', '.join(all_texts[:10])}")
                if len(all_texts) > 10:
                    print(f"      ... and {len(all_texts) - 10} more")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results_by_method[method_name] = {"matches": [], "all_texts": [], "total_detected": 0}

    # Create visualization
    visualize_preprocessing_results(image, processed_images, results_by_method, target_text)

    # Find best method
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    best_method = None
    best_confidence = 0

    for method, data in results_by_method.items():
        if data["matches"]:
            max_conf = max(m["confidence"] for m in data["matches"])
            print(f"\n{method}: {len(data['matches'])} matches, best confidence: {max_conf:.2%}")
            if max_conf > best_confidence:
                best_confidence = max_conf
                best_method = method
        else:
            print(f"\n{method}: No matches found (detected {data['total_detected']} text regions)")

    if best_method:
        print(f"\n🏆 Best method: {best_method} with {best_confidence:.2%} confidence")
    else:
        print(f"\n❌ Text '{target_text}' not found with any preprocessing method")
        print("\n💡 Suggestions:")
        print("  1. Try cropping the image to focus on the text area")
        print("  2. Increase image resolution if possible")
        print("  3. Adjust threshold values for better contrast")
        print("  4. Check if text is rendered as an image or icon")


def visualize_preprocessing_results(original_image, processed_images, results, target_text):
    """Visualize OCR results for different preprocessing methods."""
    n_methods = len(processed_images)
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()

    fig.suptitle(f'EasyOCR Preprocessing Comparison - Target: "{target_text}"', fontsize=16)

    for idx, (method_name, processed_img) in enumerate(processed_images.items()):
        ax = axes[idx]

        # Display image
        if len(processed_img.shape) == 2:  # Grayscale
            ax.imshow(processed_img, cmap="gray")
        else:  # Color
            ax.imshow(cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB))

        # Add title with results
        matches = results[method_name]["matches"]
        if matches:
            title = f"{method_name}\n✅ Found: {len(matches)} match(es)"
            title_color = "green"

            # Draw bounding boxes for matches
            for match in matches:
                if len(match["bbox"]) >= 4:
                    # Convert bbox to matplotlib coordinates
                    bbox_points = match["bbox"]
                    polygon = patches.Polygon(
                        bbox_points, linewidth=2, edgecolor="lime", facecolor="none"
                    )
                    ax.add_patch(polygon)

                    # Add text label
                    x_coords = [p[0] for p in bbox_points]
                    y_coords = [p[1] for p in bbox_points]
                    center_x = np.mean(x_coords)
                    center_y = np.mean(y_coords)

                    ax.plot(center_x, center_y, "go", markersize=8)
        else:
            title = f"{method_name}\n❌ Not found"
            title_color = "red"

        ax.set_title(title, color=title_color, fontsize=12)
        ax.axis("off")

    plt.tight_layout()
    save_path = (
        "/Users/work/Workspaces/computer-use-agent/all_flowsheets_preprocessing_comparison.png"
    )
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"\n💾 Visualization saved to: {save_path}")
    plt.show()


def main():
    """Run the test."""
    image_path = "/Users/work/Workspaces/computer-use-agent/trajectories/data/all_flowsheets_header_screenshot.png"
    target_text = "All Flowsheets"

    test_easyocr_with_preprocessing(image_path, target_text)


if __name__ == "__main__":
    main()
