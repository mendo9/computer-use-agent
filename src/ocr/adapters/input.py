from dataclasses import dataclass
from typing import Protocol


class Controller(Protocol):
    """Backend must implement basic input primitives in screen coords."""

    def move(self, x: int, y: int) -> None: ...
    def click(self, x: int, y: int, button: str = "left") -> None: ...
    def double_click(self, x: int, y: int, button: str = "left") -> None: ...
    def type_text(self, text: str) -> None: ...
    def key(self, *keys: str) -> None: ...
    def scroll(self, dy: int) -> None: ...


@dataclass
class Input:
    backend: Controller

    def move(self, x: int, y: int) -> None:
        self.backend.move(x, y)

    def click(self, x: int, y: int, button: str = "left") -> None:
        self.backend.click(x, y, button)

    def double_click(self, x: int, y: int, button: str = "left") -> None:
        self.backend.double_click(x, y, button)

    def type_text(self, text: str) -> None:
        self.backend.type_text(text)

    def hotkey(self, *keys: str) -> None:
        self.backend.key(*keys)

    def scroll(self, dy: int) -> None:
        self.backend.scroll(dy)
