from dataclasses import dataclass

# Using superior unified vision implementations
from ocr.vision.detector import Detection
from ocr.vision.ocr import TextDetection


@dataclass
class UIElement:
    bbox: tuple[int, int, int, int]
    center: tuple[int, int]
    text: str | None = None
    label: str | None = None
    score: float = 0.0
    source: str = "unknown"  # "ocr" | "yolo" | "merged"


def merge_detections_and_text(dets: list[Detection], text_detections: list[TextDetection]) -> list[UIElement]:
    """Fusion by proximity (center-to-center) using superior data structures."""
    elems: list[UIElement] = []
    
    # Add YOLO detections
    for d in dets:
        elems.append(
            UIElement(
                bbox=d.bbox, 
                center=d.center,  # VM Detection already has center
                label=d.class_name,  # VM Detection uses class_name not label
                score=d.confidence,  # VM Detection uses confidence not score
                source="yolo"
            )
        )
    
    # Add text detections
    for t in text_detections:
        elems.append(
            UIElement(
                bbox=t.rect_bbox,  # TextDetection has rect_bbox for rectangular bounds
                center=t.center,   # TextDetection already has center
                text=t.text, 
                score=t.confidence,  # TextDetection uses confidence not score
                source="ocr"
            )
        )
    
    return elems
