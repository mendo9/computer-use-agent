from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TextBox:
    bbox: tuple[int, int, int, int]  # x1,y1,x2,y2
    text: str
    score: float


class OCRReader:
    """
    PaddleOCR wrapper.
    - Lazily creates PaddleOCR engine on first use.
    - Reads all text boxes; simple filter for `find`.
    """

    def __init__(self, lang: str = "en", det_db_box_thresh: float = 0.6):
        self.lang = lang
        self.det_db_box_thresh = det_db_box_thresh
        self._engine = None
        self._load_error: str | None = None

    def _ensure_engine(self):
        if self._engine is not None or self._load_error is not None:
            return
        try:
            from paddleocr import PaddleOCR  # type: ignore

            # Use server model for better quality; adjust as needed
            self._engine = PaddleOCR(
                use_angle_cls=True,
                lang=self.lang,
                det_db_box_thresh=self.det_db_box_thresh,
                show_log=False,
            )
        except Exception as e:
            self._load_error = str(e)

    def read(self, frame: Any) -> list[TextBox]:
        self._ensure_engine()
        if self._engine is None:
            return []
        # PaddleOCR expects BGR numpy array or image path
        try:
            result = self._engine.ocr(frame, rec=True, cls=True)
        except Exception:
            return []
        boxes: list[TextBox] = []
        # result is a list per image; we pass a single frame, so take index 0
        if not result or not isinstance(result, list):
            return boxes
        lines = result[0]
        for line in lines or []:
            # line: [ [[x1,y1],...,[x4,y4]], (text, score) ]
            poly, (text, score) = line
            x_coords = [int(p[0]) for p in poly]
            y_coords = [int(p[1]) for p in poly]
            x1, y1, x2, y2 = min(x_coords), min(y_coords), max(x_coords), max(y_coords)
            boxes.append(TextBox((x1, y1, x2, y2), text, float(score)))
        return boxes

    def find(self, frame: Any, query: str, fuzzy: float = 0.9) -> list[TextBox]:
        q = (query or "").strip().lower()
        out = []
        for tb in self.read(frame):
            if q and q in tb.text.lower():
                out.append(tb)
        return out
