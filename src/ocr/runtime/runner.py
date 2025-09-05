from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ocr.runtime.context import Session


@dataclass
class Step:
    name: str
    run: Callable[[Session], Any | None]


class StepRunner:
    """Deterministic perceive→act→verify loop runner."""

    def __init__(self, session: Session):
        self.sess = session

    def execute(self, steps: list[Step]) -> None:
        for step in steps:
            self.sess.record(f"STEP START: {step.name}")
            step.run(self.sess)
            self.sess.record(f"STEP DONE:  {step.name}")
