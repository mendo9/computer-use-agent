from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ocr.ui.model import UIElement

Predicate = Callable[[UIElement, list[UIElement]], bool]


@dataclass
class Selector:
    tests: list[Predicate]

    def match(self, elements: list[UIElement]) -> list[UIElement]:
        out = []
        for e in elements:
            if all(t(e, elements) for t in self.tests):
                out.append(e)
        return out


def by_text(query: str, case_insensitive: bool = True) -> Selector:
    q = query.lower() if case_insensitive else query

    def _t(e: UIElement, _all: list[UIElement]) -> bool:
        t = e.text or ""
        t = t.lower() if case_insensitive else t
        return q in t if q else False

    return Selector([_t])


def by_label(label: str) -> Selector:
    def _t(e: UIElement, _all: list[UIElement]) -> bool:
        return (e.label or "") == label

    return Selector([_t])


def _dist(a: tuple[int, int], b: tuple[int, int]) -> float:
    dx, dy = a[0] - b[0], a[1] - b[1]
    return (dx * dx + dy * dy) ** 0.5


def near(anchor: Selector, radius: int = 60) -> Selector:
    def _t(e: UIElement, all_elems: list[UIElement]) -> bool:
        anchors = anchor.match(all_elems)
        return any(_dist(e.center, a.center) <= radius for a in anchors)

    return Selector([_t])


def below(anchor: Selector, max_px: int | None = None) -> Selector:
    def _t(e: UIElement, all_elems: list[UIElement]) -> bool:
        anchors = anchor.match(all_elems)
        if not anchors:
            return False
        return any(
            (e.center[1] > a.center[1])
            and (max_px is None or (e.center[1] - a.center[1]) <= max_px)
            for a in anchors
        )

    return Selector([_t])


def right_of(anchor: Selector, max_px: int | None = None) -> Selector:
    def _t(e: UIElement, all_elems: list[UIElement]) -> bool:
        anchors = anchor.match(all_elems)
        if not anchors:
            return False
        return any(
            (e.center[0] > a.center[0])
            and (max_px is None or (e.center[0] - a.center[0]) <= max_px)
            for a in anchors
        )

    return Selector([_t])
