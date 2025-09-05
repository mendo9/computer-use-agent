# Re-export UIElement from the comprehensive vision finder module
# Legacy compatibility - use UIFinder.find_ui_elements() instead
from ocr.vision.detector import Detection
from ocr.vision.finder import UIElement
from ocr.vision.ocr import TextDetection


def merge_detections_and_text(
    dets: list[Detection], text_detections: list[TextDetection]
) -> list[UIElement]:
    """
    DEPRECATED: Use UIFinder.find_ui_elements() instead.
    Legacy function for compatibility - will be removed in future versions.
    """
    import warnings

    warnings.warn(
        "merge_detections_and_text is deprecated. Use UIFinder.find_ui_elements() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    elems: list[UIElement] = []

    # Add YOLO detections as detected elements
    for d in dets:
        elems.append(
            UIElement(
                element_type="detected",
                bbox=d.bbox,
                center=d.center,
                confidence=d.confidence,
                yolo_detection=d,
                description=f"{d.class_name} ({d.confidence:.2f})",
            )
        )

    # Add text detections as text elements
    for t in text_detections:
        elems.append(
            UIElement(
                element_type="text",
                bbox=t.rect_bbox,
                center=t.center,
                confidence=t.confidence,
                text_detection=t,
                text=t.text,
                description=f"Text: '{t.text}' ({t.confidence:.2f})",
            )
        )

    return elems
