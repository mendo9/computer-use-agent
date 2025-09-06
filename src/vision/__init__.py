"""Pure Computer Vision Functions for Generic Use

This module provides clean, standalone computer vision functions using:
- YOLO for UI element detection
- PaddleOCR for text recognition
- Combined search and analysis capabilities

No dependencies on connections, sessions, workflows, or adapters.
Perfect for MCP servers and LLM function calling.

Example usage:
    import cv2
    from vision import detect_ui_elements, extract_text, find_elements_by_text

    image = cv2.imread("screenshot.png")
    elements = detect_ui_elements(image)
    text_results = extract_text(image)
    buttons = find_elements_by_text(image, "Submit")
"""

from .detector import Detection, detect_ui_elements
from .finder import (
    ScreenAnalysis,
    UIElement,
    analyze_screen_content,
    find_clickable_elements,
    find_elements_by_text,
)
from .reader import TextResult, extract_text, extract_text_from_region
from .setup_models import download_models, get_model_paths, setup_models
from .verification import (
    VerificationResult,
    compare_screenshots,
    create_diff_visualization,
    verify_click_success,
    verify_element_present,
    verify_page_loaded,
    verify_text_input,
    wait_for_element,
)

__version__ = "1.0.0"

__all__ = [
    # Detection functions
    "detect_ui_elements",
    "Detection",
    # Text extraction functions
    "extract_text",
    "extract_text_from_region",
    "TextResult",
    # Combined search functions
    "find_elements_by_text",
    "find_clickable_elements",
    "analyze_screen_content",
    "UIElement",
    "ScreenAnalysis",
    # Verification functions
    "verify_click_success",
    "verify_text_input",
    "verify_element_present",
    "verify_page_loaded",
    "wait_for_element",
    "compare_screenshots",
    "create_diff_visualization",
    "VerificationResult",
    # Model management
    "setup_models",
    "download_models",
    "get_model_paths",
]
