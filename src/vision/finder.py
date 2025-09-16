"""
UI element finder using template matching with OmniParser fallback.
"""

import asyncio
import base64
from pathlib import Path

import cv2
import numpy as np

try:
    from src.config import OPENAI_MODEL
    from src.vision.omniparser_fork import OmniparserConfig

    OMNIPARSER_AVAILABLE = True
except ImportError:
    OMNIPARSER_AVAILABLE = False

# Constants
BASE_TEMPLATE_PATH = Path(__file__).parent / "templates"
CONFIDENCE_THRESHOLD = 0.65

# Template mapping: query -> (template_name, category)
TEMPLATE_MAP = {
    "safari": ("safari_icon", "macos_dock"),
    "safari_icon": ("safari_icon", "macos_dock"),
    "notes": ("notes_icon", "macos_dock"),
    "notepad": ("notes_icon", "macos_dock"),
}


def find_target_center(
    png_bytes: bytes, query: str, screen_width: int | None = None, screen_height: int | None = None
) -> tuple[int, int] | None:
    """
    Find UI element center coordinates in screenshot.

    Args:
        png_bytes: Screenshot as PNG bytes
        query: Element name (e.g., "safari", "notes")
        screen_width: Screen width in pixels (for OmniParser fallback)
        screen_height: Screen height in pixels (for OmniParser fallback)

    Returns:
        (x, y) center coordinates as integers, or None if not found
    """
    # Try template matching first
    coords = find_by_template_matching(png_bytes, query)
    if coords:
        return coords

    # Fall back to OmniParser
    return find_by_omniparser(png_bytes, query, screen_width, screen_height)


def find_by_template_matching(png_bytes: bytes, query: str) -> tuple[int, int] | None:
    """Find element using template matching."""
    # Convert image
    image = _png_bytes_to_image(png_bytes)
    if image is None:
        return None

    # Get template info
    template_name, category = _get_template_info(query)

    # Load template
    template = _load_template(template_name, category)
    if template is None:
        return None

    # Perform matching
    return _perform_template_matching(image, template)


def find_by_omniparser(
    png_bytes: bytes, query: str, screen_width: int | None, screen_height: int | None
) -> tuple[int, int] | None:
    """Find element using OmniParser as fallback."""
    if not OMNIPARSER_AVAILABLE or not screen_width or not screen_height:
        return None

    try:
        # Convert to base64
        png_base64 = base64.b64encode(png_bytes).decode("utf-8")
        omniparser = OmniparserConfig()

        # Handle async context properly
        try:
            asyncio.get_running_loop()
            # Event loop running - use thread pool
            import concurrent.futures

            def run_omniparser():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        omniparser.predict_click(
                            model=OPENAI_MODEL, image_b64=png_base64, instruction=query
                        )
                    )
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_omniparser)
                coords = future.result(timeout=30)

        except RuntimeError:
            # No event loop - use asyncio.run
            coords = asyncio.run(
                omniparser.predict_click(
                    model=OPENAI_MODEL, image_b64=png_base64, instruction=query
                )
            )

        if coords:
            return _normalize_to_pixel_coords(coords, screen_width, screen_height)

    except Exception:
        pass

    return None


def _perform_template_matching(image: np.ndarray, template: np.ndarray) -> tuple[int, int] | None:
    """Perform template matching and return center coordinates."""
    try:
        # Convert to grayscale for better matching
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Get best matching result (includes confidence checking)
        best_result = _find_best_template_match(img_gray, template_gray)
        if best_result is None:
            return None

        _, _, max_loc = best_result

        # Calculate center coordinates
        h, w = template_gray.shape
        top_left = max_loc
        center_x = int(top_left[0] + w // 2)
        center_y = int(top_left[1] + h // 2)

        return (center_x, center_y)
    except Exception:
        return None


def _png_bytes_to_image(png_bytes: bytes) -> np.ndarray | None:
    """Convert PNG bytes to OpenCV image."""
    try:
        nparr = np.frombuffer(png_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return image
    except Exception:
        return None


def _get_template_info(query: str) -> tuple[str, str]:
    """Get template name and category for a query."""
    template_info = TEMPLATE_MAP.get(query.lower())
    if template_info:
        return template_info
    # Default to common category for unknown queries
    return query, "common"


def _load_template(template_name: str, category: str) -> np.ndarray | None:
    """Load template image from file."""
    try:
        template_path = BASE_TEMPLATE_PATH / category / f"{template_name}.png"
        template = cv2.imread(str(template_path))
        return template
    except Exception:
        return None


def _normalize_to_pixel_coords(
    normalized_coords: tuple[float, float], screen_width: int, screen_height: int
) -> tuple[int, int]:
    """Convert normalized coordinates (0-1) to pixel coordinates."""
    x, y = normalized_coords
    pixel_x = int(x * screen_width)
    pixel_y = int(y * screen_height)
    return (pixel_x, pixel_y)


def _find_best_template_match(
    image: np.ndarray, template: np.ndarray
) -> tuple[int, float, tuple[int, int]] | None:
    """
    Find the best template matching result by testing different OpenCV methods
    and applying confidence thresholds. Returns the best match that meets
    the confidence requirement.

    Returns:
        tuple[method, max_val, max_loc] if a good match is found, None otherwise
    """
    # Test methods in order of preference for UI elements
    available_methods = [
        cv2.TM_CCORR_NORMED,  # Often best for UI elements with brightness variations
        cv2.TM_CCOEFF_NORMED,  # Good general purpose method
        cv2.TM_SQDIFF_NORMED,  # Alternative method (inverted scoring)
    ]

    best_method = cv2.TM_CCORR_NORMED  # Default fallback
    best_confidence = 0.0
    best_max_val = 0.0
    best_max_loc: tuple[int, int] = (0, 0)

    for method in available_methods:
        try:
            result = cv2.matchTemplate(image, template, method)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            # Calculate confidence and check threshold (handle SQDIFF methods differently)
            # For SQDIFF methods, lower values are better matches; for others, higher values are better
            confidence = 1.0 - max_val if method == cv2.TM_SQDIFF_NORMED else max_val

            # Skip results below confidence threshold
            if confidence < CONFIDENCE_THRESHOLD:
                continue

            # Keep track of best method and results
            if confidence > best_confidence:
                best_confidence = confidence
                best_method = method
                best_max_val = max_val
                best_max_loc = (max_loc[0], max_loc[1])

            # If we found a very good match, use it immediately
            if confidence > 0.8:  # Higher threshold for early exit
                return method, max_val, (max_loc[0], max_loc[1])

        except Exception:
            continue  # Skip methods that fail

    # Return best result found (only if it meets confidence threshold)
    if best_confidence >= CONFIDENCE_THRESHOLD:
        return best_method, best_max_val, (best_max_loc[0], best_max_loc[1])

    return None
