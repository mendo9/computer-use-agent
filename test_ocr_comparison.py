"""
Comprehensive OCR comparison: PaddleOCR vs EasyOCR vs Tesseract
Tests detection of "Flowsheets" text and visualizes results.
"""

import cv2
import numpy as np
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Test image configuration
IMAGE_PATH = "/Users/work/Workspaces/computer-use-agent/trajectories/data/flowsheets_icon_header_screenshot.png"
TARGET_TEXT = "Flowsheets"

def test_paddleocr(image):
    """Test PaddleOCR."""
    try:
        from paddleocr import PaddleOCR
        print("\n📚 Testing PaddleOCR...")

        start = time.time()
        ocr = PaddleOCR(use_angle_cls=False, lang='en', use_gpu=False, show_log=False)
        results = ocr.ocr(image, cls=False)
        elapsed = time.time() - start

        found_result = None
        if results and results[0]:
            for line in results[0]:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]

                if TARGET_TEXT.lower() in text.lower():
                    found_result = {
                        'text': text,
                        'bbox': bbox,
                        'confidence': confidence,
                        'time': elapsed
                    }
                    break

        if found_result:
            print(f"  ✅ Found: '{found_result['text']}' (conf: {found_result['confidence']:.2%})")
            print(f"  ⏱️  Time: {elapsed:.2f}s")
        else:
            print(f"  ❌ Not found (searched {len(results[0]) if results and results[0] else 0} regions)")
            print(f"  ⏱️  Time: {elapsed:.2f}s")

        return found_result
    except Exception as e:
        print(f"  ❌ PaddleOCR failed: {e}")
        return None


def test_easyocr(image):
    """Test EasyOCR."""
    try:
        import easyocr
        print("\n📚 Testing EasyOCR...")

        start = time.time()
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(image)
        elapsed = time.time() - start

        found_result = None
        for bbox, text, confidence in results:
            if TARGET_TEXT.lower() in text.lower():
                found_result = {
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence,
                    'time': elapsed
                }
                break

        if found_result:
            print(f"  ✅ Found: '{found_result['text']}' (conf: {found_result['confidence']:.2%})")
            print(f"  ⏱️  Time: {elapsed:.2f}s")
        else:
            print(f"  ❌ Not found (searched {len(results)} regions)")
            print(f"  ⏱️  Time: {elapsed:.2f}s")

        return found_result
    except Exception as e:
        print(f"  ❌ EasyOCR failed: {e}")
        return None


def test_tesseract(image):
    """Test Tesseract OCR."""
    try:
        import pytesseract
        print("\n📚 Testing Tesseract...")

        start = time.time()
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Get data with bounding boxes
        data = pytesseract.image_to_data(rgb_image, output_type=pytesseract.Output.DICT)
        elapsed = time.time() - start

        found_result = None
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text and TARGET_TEXT.lower() in text.lower():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                confidence = data['conf'][i] / 100.0

                bbox = [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]

                found_result = {
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence,
                    'time': elapsed
                }
                break

        if found_result:
            print(f"  ✅ Found: '{found_result['text']}' (conf: {found_result['confidence']:.2%})")
            print(f"  ⏱️  Time: {elapsed:.2f}s")
        else:
            print(f"  ❌ Not found (searched {sum(1 for t in data['text'] if t.strip())} text regions)")
            print(f"  ⏱️  Time: {elapsed:.2f}s")

        return found_result
    except Exception as e:
        print(f"  ❌ Tesseract failed: {e}")
        return None


def visualize_results(image, results):
    """Create visualization comparing all OCR results."""
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Count successful results
    n_results = sum(1 for r in results.values() if r is not None)
    if n_results == 0:
        print("\n❌ No OCR library found the text")
        return

    # Create subplots
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(f'OCR Comparison: Finding "{TARGET_TEXT}"', fontsize=16)

    libraries = ['PaddleOCR', 'EasyOCR', 'Tesseract']

    for idx, (lib, ax) in enumerate(zip(libraries, axes)):
        ax.imshow(image_rgb)
        ax.set_title(lib)
        ax.axis('off')

        result = results.get(lib)
        if result:
            # Calculate center
            bbox = result['bbox']
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            center_x = int(np.mean(x_coords))
            center_y = int(np.mean(y_coords))

            # Draw green dot
            circle = patches.Circle((center_x, center_y), radius=15, color='lime', linewidth=3, fill=True)
            ax.add_patch(circle)

            # Draw bounding box
            polygon = patches.Polygon(bbox, linewidth=2, edgecolor='lime', facecolor='none')
            ax.add_patch(polygon)

            # Add info text
            info_text = f"✅ Found\n'{result['text']}'\nConf: {result['confidence']:.1%}\nTime: {result['time']:.1f}s"
            ax.text(10, image.shape[0] - 10, info_text,
                   fontsize=10, color='white', weight='bold',
                   va='bottom', ha='left',
                   bbox={'boxstyle': 'round,pad=0.5', 'facecolor': 'green', 'alpha': 0.7})
        else:
            # Not found
            ax.text(image.shape[1]/2, image.shape[0]/2, '❌ NOT FOUND',
                   fontsize=20, color='red', weight='bold',
                   ha='center', va='center',
                   bbox={'boxstyle': 'round,pad=0.5', 'facecolor': 'white', 'alpha': 0.8})

    plt.tight_layout()

    # Save result
    save_path = "/Users/work/Workspaces/computer-use-agent/ocr_comparison_results.png"
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n💾 Comparison saved to: {save_path}")
    plt.show()


def main():
    """Run comprehensive OCR comparison."""
    print("=" * 70)
    print("OCR Library Comparison Test")
    print(f"Target text: '{TARGET_TEXT}'")
    print("=" * 70)

    # Load image
    print(f"\n📁 Loading image: {IMAGE_PATH}")
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        print("❌ Failed to load image")
        return

    print(f"📐 Image size: {image.shape[1]}x{image.shape[0]} pixels")

    # Test each OCR library
    results = {}

    # Test PaddleOCR
    results['PaddleOCR'] = test_paddleocr(image)

    # Test EasyOCR
    results['EasyOCR'] = test_easyocr(image)

    # Test Tesseract
    results['Tesseract'] = test_tesseract(image)

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)

    best_library = None
    best_confidence = 0
    fastest_library = None
    fastest_time = float('inf')

    for lib, result in results.items():
        if result:
            print(f"\n{lib}:")
            print(f"  Text: '{result['text']}'")
            print(f"  Confidence: {result['confidence']:.1%}")
            print(f"  Time: {result['time']:.2f}s")

            if result['confidence'] > best_confidence:
                best_confidence = result['confidence']
                best_library = lib

            if result['time'] < fastest_time:
                fastest_time = result['time']
                fastest_library = lib
        else:
            print(f"\n{lib}: Failed or not found")

    if best_library:
        print(f"\n🏆 Best accuracy: {best_library} ({best_confidence:.1%})")
        print(f"⚡ Fastest: {fastest_library} ({fastest_time:.2f}s)")

    # Visualize results
    print("\n📊 Creating visualization...")
    visualize_results(image, results)

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()