from dataclasses import dataclass

from ocr.vision.detector import Detection
from ocr.vision.ocr import TextBox


@dataclass
class UIElement:
    bbox: tuple[int, int, int, int]
    center: tuple[int, int]
    text: str | None = None
    label: str | None = None
    score: float = 0.0
    source: str = "unknown"  # "ocr" | "yolo" | "merged"


def merge_detections_and_text(dets: list[Detection], tbs: list[TextBox]) -> list[UIElement]:
    """Naive fusion by proximity (center-to-center)."""
    elems: list[UIElement] = []
    for d in dets:
        x1, y1, x2, y2 = d.bbox
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        elems.append(
            UIElement(bbox=d.bbox, center=(cx, cy), label=d.label, score=d.score, source="yolo")
        )
    for t in tbs:
        x1, y1, x2, y2 = t.bbox
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        elems.append(
            UIElement(bbox=t.bbox, center=(cx, cy), text=t.text, score=t.score, source="ocr")
        )
    return elems
