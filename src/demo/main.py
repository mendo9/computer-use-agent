"""
Tiny usage example (pseudo-code). Replace `YourBackendConnection`/`YourController`
with your actual VNC/RDP adapters that satisfy the Protocols.
"""

from ocr.actions.primitives import click_element
from ocr.actions.verify import page_changed
from ocr.adapters.input import Input
from ocr.adapters.screen import Screen
from ocr.runtime.context import Session
from ocr.runtime.runner import Step, StepRunner
from ocr.ui.model import merge_detections_and_text
from ocr.ui.selectors import by_text
from ocr.vision.detector import YOLODetector
from ocr.vision.ocr import OCRReader


# --- inject your backends here ---
class YourBackendConnection:
    def connect(self): ...
    def disconnect(self): ...
    def capture(self):
        # return an ndarray-like RGB image
        raise NotImplementedError

    def is_connected(self):
        return True


class YourController:
    def move(self, x, y): ...
    def click(self, x, y, button="left"): ...
    def double_click(self, x, y, button="left"): ...
    def type_text(self, text): ...
    def key(self, *keys): ...
    def scroll(self, dy): ...


def main():
    screen = Screen(YourBackendConnection())
    inp = Input(YourController())
    det = YOLODetector()  # wire your onnxruntime model
    ocr = OCRReader()  # wire your PaddleOCR engine

    sess = Session(screen=screen, input=inp, detector=det, ocr=ocr)
    runner = StepRunner(sess)

    def click_submit(session: Session):
        frame_before = session.screen.capture()
        dets = session.detector.detect(frame_before)
        tbs = session.ocr.read(frame_before)
        elements = merge_detections_and_text(dets, tbs)
        submit = by_text("Submit").match(elements)
        if not submit:
            session.record("Submit not found")
            return
        click_element(session.input, submit[0])
        frame_after = session.screen.capture()
        if page_changed(session.screen, frame_before, frame_after):
            session.record("Click succeeded (page changed)")
        else:
            session.record("Click uncertain (no change)")

    runner.execute(
        [
            Step("Connect", lambda s: s.screen.connect()),
            Step("Click Submit", click_submit),
            Step("Disconnect", lambda s: s.screen.disconnect()),
        ]
    )


if __name__ == "__main__":
    main()
