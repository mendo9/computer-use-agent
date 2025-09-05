from __future__ import annotations

from ocr.adapters.input import Input
from ocr.ui.model import UIElement


def click_element(inp: Input, element: UIElement, button: str = "left") -> None:
    x, y = element.center
    inp.move(x, y)
    inp.click(x, y, button=button)


def type_text(inp: Input, text: str) -> None:
    inp.type_text(text)


def scroll_down(inp: Input, pixels: int = 400) -> None:
    # Convention: positive dy scrolls down
    inp.scroll(+abs(pixels))
