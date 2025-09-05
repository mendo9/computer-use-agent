"""
Unified vision system with superior OCR and YOLO implementations.

This module provides advanced computer vision capabilities including:
- YOLOv8s-ONNX object detection with UI-specific optimizations
- PaddleOCR text recognition with spatial reasoning
- Combined UI element finder with intelligent spatial combination
- Rich data structures with full context information
"""

# Superior implementations - use these for all new code
from ocr.vision.detector import Detection, YOLODetector
from ocr.vision.finder import UIElement, UIFinder
from ocr.vision.ocr import OCRReader, TextDetection

__all__ = [
    # Object Detection
    "YOLODetector",
    "Detection",
    # Text Recognition
    "OCRReader",
    "TextDetection",
    # Combined UI Finding
    "UIFinder",
    "UIElement",
]
