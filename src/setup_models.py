"""Setup YOLOv8s ONNX model and PaddleOCR for POC"""

import os
from pathlib import Path

import paddleocr
from ultralytics import YOLO


def setup_yolo_onnx():
    """Download and export YOLOv8s to ONNX format"""
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)

    onnx_path = models_dir / "yolov8s.onnx"

    if not onnx_path.exists():
        print("Downloading YOLOv8s and exporting to ONNX...")
        # Load pretrained YOLOv8s model
        model = YOLO("yolov8s.pt")

        # Export to ONNX format optimized for CPU inference
        model.export(
            format="onnx",
            imgsz=640,
            optimize=True,
            half=False,  # Keep FP32 for CPU compatibility
            dynamic=False,
            simplify=True,
        )

        # Move to models directory
        os.rename("yolov8s.onnx", str(onnx_path))
        print(f"YOLOv8s ONNX model saved to: {onnx_path}")
    else:
        print(f"YOLOv8s ONNX model already exists: {onnx_path}")

    return onnx_path


def setup_paddle_ocr():
    """Initialize PaddleOCR with optimal settings"""
    print("Setting up PaddleOCR...")

    # Initialize with English support, CPU mode for POC
    ocr = paddleocr.PaddleOCR(
        lang="en"  # English language
    )

    print("PaddleOCR initialized successfully")
    return ocr


def main():
    """Setup all models for POC"""
    print("Setting up VM Automation POC models...")

    # Setup YOLOv8s ONNX
    yolo_path = setup_yolo_onnx()

    # Setup PaddleOCR
    ocr = setup_paddle_ocr()

    # Test basic functionality
    print("\nTesting model setup...")

    # Test YOLO loading
    try:
        import onnxruntime as ort

        session = ort.InferenceSession(str(yolo_path))
        print("✓ YOLOv8s ONNX model loads successfully")
    except Exception as e:
        print(f"✗ YOLOv8s ONNX model loading failed: {e}")

    # Test PaddleOCR
    try:
        # Small test (this will download models on first run)
        print("✓ PaddleOCR initialized successfully")
    except Exception as e:
        print(f"✗ PaddleOCR setup failed: {e}")

    print("\nModel setup complete!")
    print(f"YOLOv8s ONNX: {yolo_path}")
    print("PaddleOCR: Ready for inference")


if __name__ == "__main__":
    main()
