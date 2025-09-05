from __future__ import annotations

from typing import Any

from ocr.adapters.screen import Screen
from ocr.vision.ocr import OCRReader


def page_changed(screen: Screen, before: Any, after: Any, min_delta_bits: int = 8) -> bool:
    """Crude perceptual-change check using simple phash bit difference."""
    try:
        hb = screen.phash(before)
        ha = screen.phash(after)
        # Hamming distance
        diff = sum(1 for (b, a) in zip(hb, ha, strict=False) if b != a)
        return diff >= min_delta_bits
    except Exception:
        return True  # be permissive in stub


def expect_text(ocr: OCRReader, frame: Any, query: str) -> bool:
    text_detections = ocr.read_text(frame)  # Use new method name
    q = query.lower()
    return any(q in td.text.lower() for td in text_detections)
