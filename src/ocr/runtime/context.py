from __future__ import annotations

from dataclasses import dataclass, field

from ocr.adapters.input import Input
from ocr.adapters.screen import Screen
from ocr.vision.detector import YOLODetector
from ocr.vision.ocr import OCRReader


@dataclass
class LogEntry:
    message: str


@dataclass
class Session:
    screen: Screen
    input: Input
    detector: YOLODetector
    ocr: OCRReader
    log: list[LogEntry] = field(default_factory=list)

    def record(self, msg: str) -> None:
        self.log.append(LogEntry(msg))
