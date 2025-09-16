"""
UI element finder using template matching.
"""

from pathlib import Path

import cv2
import numpy as np

from src.vision.template_detector import detect_ui_elements
from src.vision.template_manager import TemplateManager, TemplateRequest, TemplateStrategy

TEMPLATES_PATH = Path(__file__).parent  # src/vision/
TEMPLATE_MAP = {
    "safari": ("safari_icon", "macos_dock"),
    "safari_icon": ("safari_icon", "macos_dock"),
    "notes": ("notes_icon", "macos_dock"),
    "notepad": ("notes_icon", "macos_dock"),
}
# can use 0.4 if enable_multiscale is FALSE
CONFIDENCE_THRESHOLD = 0.8


def find_target_center(png_bytes: bytes, query: str) -> tuple[int, int] | None:
    """
    Find UI element center coordinates in screenshot.

    Args:
        png_bytes: Screenshot as PNG bytes
        query: Element name (e.g., "safari", "notes")

    Returns:
        (x, y) center coordinates as integers, or None if not found
    """
    coords = _find_by_template_matching(png_bytes, query)
    if coords:
        return coords

    return None


def _find_by_template_matching(png_bytes: bytes, query: str) -> tuple[int, int] | None:
    """Find element using advanced template matching system."""

    # Convert PNG bytes to OpenCV image
    nparr = np.frombuffer(png_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    try:
        template_manager = TemplateManager(library_path=TEMPLATES_PATH)

        # Map query to template info
        template_name, category = _get_template_info(query)

        # Create template request
        template_request = TemplateRequest(
            strategy=TemplateStrategy.LIBRARY,
            data={"id": template_name, "category": category},
            name=template_name,
        )

        # Resolve template
        template_sources = template_manager.resolve_templates(template_request)

        detections = detect_ui_elements(
            image=image,
            template_sources=template_sources,
            confidence_threshold=CONFIDENCE_THRESHOLD,
            method="auto",
            enable_multiscale=True,
            enable_rotation=False,
            max_detections=3,  # Get multiple detections to choose from
        )

        # Return the best overall match
        if detections:
            return detections[0].center

    except Exception:
        pass

    return None


def _get_template_info(query: str) -> tuple[str, str]:
    """Get template name and category for a query."""

    template_info = TEMPLATE_MAP.get(query.lower())
    if template_info:
        return template_info
    # Default to common category for unknown queries
    return query, "common"
