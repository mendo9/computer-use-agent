"""
Minimal, pluggable grounding: turn a query/label into (x,y) from the last screenshot.
You can replace with your real PaddleOCR/OpenCV pipeline.
"""


def find_target_center(png_bytes: bytes, query: str) -> tuple[int, int] | None:
    """Find the center coordinates of a target element in a screenshot.

    Args:
        png_bytes: Screenshot image data as PNG bytes
        query: Text or label to search for in the image

    Returns:
        Tuple of (x, y) coordinates if found, None otherwise
    """
    # TODO: real OCR/template matching here.
    # For now, returns None (so the agent falls back to OmniParser if enabled).
    return None
