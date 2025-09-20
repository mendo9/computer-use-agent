"""
Advanced OCR text detection with multiple libraries comparison.
"""

import time

import cv2
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np

try:
    from paddleocr import PaddleOCR

    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False
    print("PaddleOCR not available")

try:
    import easyocr

    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("EasyOCR not available")

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Tesseract not available")


class OCRResult:
    """Container for OCR detection results."""

    def __init__(self, text: str, bbox: list[tuple[int, int]], confidence: float, library: str):
        self.text = text
        self.bbox = bbox  # List of corner points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        self.confidence = confidence
        self.library = library
        self.center = self._calculate_center()

    def _calculate_center(self) -> tuple[int, int]:
        """Calculate center point of the bounding box."""
        if not self.bbox:
            return (0, 0)
        x_coords = [point[0] for point in self.bbox]
        y_coords = [point[1] for point in self.bbox]
        return (int(np.mean(x_coords)), int(np.mean(y_coords)))

    def __repr__(self):
        return f"OCRResult(text='{self.text}', confidence={self.confidence:.2f}, library={self.library}, center={self.center})"


class MultiOCR:
    """Multi-library OCR for text detection comparison."""

    def __init__(self):
        self.paddle_ocr = None
        self.easyocr_reader = None
        self._init_ocr_engines()

    def _init_ocr_engines(self):
        """Initialize available OCR engines."""
        if PADDLE_AVAILABLE:
            try:
                self.paddle_ocr = PaddleOCR(use_textline_orientation=True, lang="en")
                print("✅ PaddleOCR initialized")
            except Exception as e:
                print(f"❌ Failed to initialize PaddleOCR: {e}")

        if EASYOCR_AVAILABLE:
            try:
                self.easyocr_reader = easyocr.Reader(["en"], gpu=False)
                print("✅ EasyOCR initialized")
            except Exception as e:
                print(f"❌ Failed to initialize EasyOCR: {e}")

    def detect_with_paddle(self, image: np.ndarray) -> list[OCRResult]:
        """Detect text using PaddleOCR."""
        results = []
        if not self.paddle_ocr:
            return results

        try:
            start = time.time()
            ocr_results = self.paddle_ocr.predict(image, use_textline_orientation=True)
            elapsed = time.time() - start
            print(f"⏱️ PaddleOCR took {elapsed:.2f}s")

            if ocr_results and ocr_results[0]:
                for line in ocr_results[0]:
                    bbox = line[0]
                    text = line[1][0]
                    confidence = line[1][1]

                    # Convert bbox to list of tuples
                    bbox_points = [(int(point[0]), int(point[1])) for point in bbox]

                    results.append(
                        OCRResult(
                            text=text, bbox=bbox_points, confidence=confidence, library="PaddleOCR"
                        )
                    )
                    print(f"  📝 PaddleOCR: '{text}' (conf: {confidence:.2f})")
        except Exception as e:
            print(f"❌ PaddleOCR error: {e}")

        return results

    def detect_with_easyocr(self, image: np.ndarray) -> list[OCRResult]:
        """Detect text using EasyOCR."""
        results = []
        if not self.easyocr_reader:
            return results

        try:
            start = time.time()
            ocr_results = self.easyocr_reader.readtext(image)
            elapsed = time.time() - start
            print(f"⏱️ EasyOCR took {elapsed:.2f}s")

            for bbox, text, confidence in ocr_results:
                # Convert bbox to list of tuples
                if len(bbox) == 4:
                    bbox_points = [(int(point[0]), int(point[1])) for point in bbox]
                else:
                    # Handle different bbox formats
                    bbox_points = bbox

                results.append(
                    OCRResult(text=text, bbox=bbox_points, confidence=confidence, library="EasyOCR")
                )
                print(f"  📝 EasyOCR: '{text}' (conf: {confidence:.2f})")
        except Exception as e:
            print(f"❌ EasyOCR error: {e}")

        return results

    def detect_with_tesseract(self, image: np.ndarray) -> list[OCRResult]:
        """Detect text using Tesseract OCR."""
        results = []
        if not TESSERACT_AVAILABLE:
            return results

        try:
            start = time.time()
            # Convert to RGB if needed
            if len(image.shape) == 2:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Get detailed data including bounding boxes
            data = pytesseract.image_to_data(rgb_image, output_type=pytesseract.Output.DICT)
            elapsed = time.time() - start
            print(f"⏱️ Tesseract took {elapsed:.2f}s")

            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                if text:  # Only process non-empty text
                    x, y, w, h = (
                        data["left"][i],
                        data["top"][i],
                        data["width"][i],
                        data["height"][i],
                    )
                    confidence = data["conf"][i] / 100.0  # Convert to 0-1 range

                    # Create bbox as four corner points
                    bbox_points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

                    if confidence > 0:  # Tesseract returns -1 for low confidence
                        results.append(
                            OCRResult(
                                text=text,
                                bbox=bbox_points,
                                confidence=confidence,
                                library="Tesseract",
                            )
                        )
                        print(f"  📝 Tesseract: '{text}' (conf: {confidence:.2f})")
        except Exception as e:
            print(f"❌ Tesseract error: {e}")

        return results

    def detect_all(self, image: np.ndarray) -> dict[str, list[OCRResult]]:
        """Run all available OCR engines and return results."""
        all_results = {}

        print("\n🔍 Running OCR detection with all available libraries...")

        if PADDLE_AVAILABLE:
            print("\n📚 PaddleOCR:")
            all_results["PaddleOCR"] = self.detect_with_paddle(image)

        if EASYOCR_AVAILABLE:
            print("\n📚 EasyOCR:")
            all_results["EasyOCR"] = self.detect_with_easyocr(image)

        if TESSERACT_AVAILABLE:
            print("\n📚 Tesseract:")
            all_results["Tesseract"] = self.detect_with_tesseract(image)

        return all_results

    def find_text(self, image: np.ndarray, target_text: str) -> dict[str, OCRResult | None]:
        """Find specific text using all OCR engines."""
        all_results = self.detect_all(image)
        found_results = {}

        target_lower = target_text.lower()

        print(f"\n🎯 Searching for text: '{target_text}'")

        for library, results in all_results.items():
            found = None
            for result in results:
                if target_lower in result.text.lower():
                    if found is None or result.confidence > found.confidence:
                        found = result

            found_results[library] = found
            if found:
                print(
                    f"  ✅ {library}: Found '{found.text}' at {found.center} (conf: {found.confidence:.2f})"
                )
            else:
                print(f"  ❌ {library}: Not found")

        return found_results

    def visualize_results(self, image_path: str, target_text: str, save_path: str | None = None):
        """Visualize OCR results with green dots on found text."""
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            print(f"❌ Failed to read image: {image_path}")
            return

        # Find text
        found_results = self.find_text(image, target_text)

        # Create figure with subplots for each library
        n_libraries = len(found_results)
        if n_libraries == 0:
            print("❌ No OCR libraries available")
            return

        fig, axes = plt.subplots(1, n_libraries, figsize=(6 * n_libraries, 8))
        if n_libraries == 1:
            axes = [axes]

        # Convert BGR to RGB for matplotlib
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        for idx, (library, result) in enumerate(found_results.items()):
            ax = axes[idx]
            ax.imshow(image_rgb)
            ax.set_title(f"{library}\n{target_text} {'Found ✅' if result else 'Not Found ❌'}")
            ax.axis("off")

            if result:
                # Draw green dot at center
                circle = patches.Circle(
                    result.center, radius=10, color="lime", linewidth=3, fill=True
                )
                ax.add_patch(circle)

                # Draw bounding box
                if len(result.bbox) >= 4:
                    # Create polygon from bbox points
                    polygon = patches.Polygon(
                        result.bbox, linewidth=2, edgecolor="lime", facecolor="none"
                    )
                    ax.add_patch(polygon)

                # Add text annotation
                ax.annotate(
                    f"{result.text}\n({result.confidence:.2f})",
                    xy=result.center,
                    xytext=(result.center[0], result.center[1] - 30),
                    fontsize=10,
                    color="lime",
                    weight="bold",
                    ha="center",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="black", alpha=0.7),
                    arrowprops=dict(arrowstyle="->", color="lime", lw=2),
                )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=100, bbox_inches="tight")
            print(f"✅ Visualization saved to: {save_path}")

        plt.show()

        return found_results


def main():
    """Test the multi-OCR system with the flowsheets screenshot."""
    print("=" * 60)
    print("Multi-OCR Text Detection Test")
    print("=" * 60)

    # Initialize multi-OCR system
    ocr = MultiOCR()

    # Test with the flowsheets screenshot
    image_path = "/Users/work/Workspaces/computer-use-agent/trajectories/data/all_flowsheets_header_screenshot.png"
    target_text = "All Flowsheets"

    print(f"\n📁 Image: {image_path}")
    print(f"🔍 Target text: '{target_text}'")

    # Visualize results
    save_path = "/Users/work/Workspaces/computer-use-agent/ocr_comparison_results.png"
    results = ocr.visualize_results(image_path, target_text, save_path)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    best_result = None
    best_library = None

    for library, result in results.items():
        if result:
            if best_result is None or result.confidence > best_result.confidence:
                best_result = result
                best_library = library

    if best_result:
        print(f"\n🏆 Best match: {best_library}")
        print(f"   Text: '{best_result.text}'")
        print(f"   Confidence: {best_result.confidence:.2%}")
        print(f"   Location: {best_result.center}")
    else:
        print("\n❌ Text not found by any OCR library")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
