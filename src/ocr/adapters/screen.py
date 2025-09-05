from dataclasses import dataclass
from typing import Any, Protocol

# Optional ndarray type (we don't enforce numpy dependency in the stub)
try:
    Frame = "np.ndarray"
except Exception:  # pragma: no cover
    Frame = Any  # fallback


class Connection(Protocol):
    """Minimal protocol the underlying backend (VNC/RDP/etc.) should implement."""

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def capture(self) -> Any: ...  # returns ndarray-like RGB image
    def is_connected(self) -> bool: ...


@dataclass
class Screen:
    """Protocol-agnostic screen adapter."""

    backend: Connection
    size: tuple[int, int] | None = None  # (width, height)

    def connect(self) -> None:
        self.backend.connect()

    def disconnect(self) -> None:
        try:
            self.backend.disconnect()
        except Exception:
            pass

    def capture(self) -> Any:
        """Grab a full-frame RGB image from the backend."""
        frame = self.backend.capture()
        return frame

    def crop(self, frame: Any, bbox: tuple[int, int, int, int]) -> Any:
        """Crop [x1,y1,x2,y2] from a frame. Requires numpy-like slicing."""
        x1, y1, x2, y2 = bbox
        try:
            return frame[y1:y2, x1:x2]  # type: ignore[index]
        except Exception:
            raise RuntimeError("crop() requires ndarray-like frames")

    def phash(self, frame: Any) -> str:
        """Very simple perceptual hash placeholder (override with robust impl)."""
        try:
            import numpy as _np  # type: ignore

            small = _np.mean(_np.asarray(frame), axis=2) if frame.ndim == 3 else _np.asarray(frame)
            small = small[::16, ::16]  # crude downsample
            bits = (small > small.mean()).astype(int).flatten()
            return "".join(map(str, bits.tolist()))
        except Exception:
            # Fallback non-perceptual
            return str(hash(bytes(memoryview(frame))))  # may fail if not contiguous
