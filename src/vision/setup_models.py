"""Model Setup and Management Functions

Downloads and manages YOLO and PaddleOCR models for computer vision tasks.
"""

import os
from pathlib import Path

import paddleocr
from ultralytics import YOLO


def get_model_paths() -> dict[str, str]:
    """
    Get paths to model files

    Returns:
        Dictionary with model paths

    Example:
        paths = get_model_paths()
        yolo_path = paths['yolo_onnx']
    """
    models_dir = Path(__file__).parent / "models"

    return {
        "models_dir": str(models_dir),
        "yolo_onnx": str(models_dir / "yolov8s.onnx"),
        "yolo_pt": str(models_dir / "yolov8s.pt"),
    }


def download_models() -> dict[str, str]:
    """
    Download and setup all required models

    Returns:
        Dictionary with downloaded model paths

    Example:
        paths = download_models()
        print(f"Models ready at: {paths}")
    """
    print("🔍 Setting up computer vision models...")

    # Setup YOLO
    yolo_path = setup_yolo_model()

    # Setup PaddleOCR
    setup_paddle_ocr()

    paths = get_model_paths()

    print("✅ All models ready!")
    return paths


def setup_models() -> dict[str, str]:
    """Alias for download_models() for backward compatibility"""
    return download_models()


def setup_yolo_model() -> str:
    """
    Download and convert YOLOv8s to ONNX format

    Returns:
        Path to ONNX model file
    """
    models_dir = Path(__file__).parent / "models"
    models_dir.mkdir(exist_ok=True)

    onnx_path = models_dir / "yolov8s.onnx"
    pt_path = models_dir / "yolov8s.pt"

    if onnx_path.exists():
        print(f"✅ YOLOv8s ONNX already exists: {onnx_path}")
        return str(onnx_path)

    print("📥 Downloading YOLOv8s and converting to ONNX...")

    try:
        # Load pretrained YOLOv8s model (will download if not present)
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
        if os.path.exists("yolov8s.onnx"):
            os.rename("yolov8s.onnx", str(onnx_path))
        if os.path.exists("yolov8s.pt"):
            os.rename("yolov8s.pt", str(pt_path))

        print(f"✅ YOLOv8s ONNX saved to: {onnx_path}")

    except Exception as e:
        print(f"❌ YOLOv8s setup failed: {e}")
        raise

    return str(onnx_path)


def setup_paddle_ocr() -> bool:
    """
    Initialize PaddleOCR (downloads models on first use)

    Returns:
        True if successful
    """
    print("📥 Setting up PaddleOCR...")

    try:
        # Initialize PaddleOCR - this will download models on first use
        ocr = paddleocr.PaddleOCR(use_textline_orientation=True, lang="en")

        print("✅ PaddleOCR initialized successfully")
        return True

    except Exception as e:
        print(f"❌ PaddleOCR setup failed: {e}")
        raise


def verify_models() -> dict[str, bool]:
    """
    Verify that all models are properly installed

    Returns:
        Dictionary with verification status for each model
    """
    print("🔍 Verifying model installations...")

    results = {"yolo_onnx": False, "paddle_ocr": False}

    # Check YOLO ONNX
    try:
        import onnxruntime as ort

        paths = get_model_paths()

        if os.path.exists(paths["yolo_onnx"]):
            session = ort.InferenceSession(paths["yolo_onnx"])
            results["yolo_onnx"] = True
            print("✅ YOLOv8s ONNX model verified")
        else:
            print("❌ YOLOv8s ONNX model not found")

    except Exception as e:
        print(f"❌ YOLOv8s ONNX verification failed: {e}")

    # Check PaddleOCR
    try:
        ocr = paddleocr.PaddleOCR(use_textline_orientation=True, lang="en")
        results["paddle_ocr"] = True
        print("✅ PaddleOCR verified")

    except Exception as e:
        print(f"❌ PaddleOCR verification failed: {e}")

    return results


def cleanup_temp_files():
    """Clean up temporary files from model downloads"""
    temp_files = ["yolov8s.pt", "yolov8s.onnx"]

    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"🧹 Cleaned up {temp_file}")


if __name__ == "__main__":
    # Run setup when called directly
    print("Computer Vision Model Setup")
    print("=" * 40)

    try:
        paths = download_models()
        print("\n📋 Model Summary:")
        for name, path in paths.items():
            print(f"  {name}: {path}")

        print("\n🔍 Verification:")
        verification = verify_models()
        for model, status in verification.items():
            status_icon = "✅" if status else "❌"
            print(f"  {model}: {status_icon}")

        cleanup_temp_files()

        if all(verification.values()):
            print("\n🎉 All models ready for computer vision tasks!")
        else:
            print("\n⚠️  Some models failed verification. Check errors above.")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        cleanup_temp_files()
