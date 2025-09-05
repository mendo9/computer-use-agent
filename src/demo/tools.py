"""
Expose scaffolding as OpenAI Agents SDK tools.
"""

from __future__ import annotations

import json

from agents import RunContextWrapper, function_tool
from typing_extensions import TypedDict

from ocr.actions.primitives import scroll_down
from ocr.actions.primitives import type_text as act_type
from ocr.actions.verify import expect_text, page_changed
from ocr.runtime.context import Session
from ocr.ui.model import merge_detections_and_text


class FindTextArgs(TypedDict):
    query: str


class ClickTextArgs(TypedDict):
    query: str


class TypeTextArgs(TypedDict):
    value: str
    anchor_text: str | None


class ScrollArgs(TypedDict):
    pixels: int


@function_tool
def list_ui(ctx: RunContextWrapper[Session]) -> str:
    """List merged UI elements (OCR + detector) on the current screen as JSON."""
    s = ctx.context
    frame = s.screen.capture()
    dets = s.detector.detect(frame)
    tbs = s.ocr.read(frame)
    elems = merge_detections_and_text(dets, tbs)
    out = [
        {
            "bbox": e.bbox,
            "center": e.center,
            "text": e.text,
            "label": e.label,
            "score": e.score,
            "source": e.source,
        }
        for e in elems
    ]
    return json.dumps(out)


@function_tool
def find_text(ctx: RunContextWrapper[Session], args: FindTextArgs) -> str:
    """Find all OCR text boxes that include the query. Args: query: text to search for."""
    s = ctx.context
    frame = s.screen.capture()
    boxes = s.ocr.find(frame, args["query"])
    out = [{"bbox": b.bbox, "text": b.text, "score": b.score} for b in boxes]
    return json.dumps(out)


@function_tool
def click_text(ctx: RunContextWrapper[Session], args: ClickTextArgs) -> str:
    """Click the first UI element whose OCR text contains the query. Args: query."""
    s = ctx.context
    before = s.screen.capture()
    tbs = s.ocr.find(before, args["query"])
    if not tbs:
        return json.dumps({"ok": False, "reason": "text_not_found"})
    # Click the center of first match
    x1, y1, x2, y2 = tbs[0].bbox
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    s.input.move(cx, cy)
    s.input.click(cx, cy)
    after = s.screen.capture()
    changed = page_changed(s.screen, before, after)
    return json.dumps({"ok": True, "clicked": {"x": cx, "y": cy}, "page_changed": changed})


@function_tool
def type_text(ctx: RunContextWrapper[Session], args: TypeTextArgs) -> str:
    """Type text. If anchor_text is provided, click it first to focus the field, then type value.
    Args:
      value: the string to type
      anchor_text: optional text to click before typing
    """
    s = ctx.context
    if args.get("anchor_text"):
        before = s.screen.capture()
        tbs = s.ocr.find(before, args["anchor_text"] or "")
        if tbs:
            x1, y1, x2, y2 = tbs[0].bbox
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            s.input.move(cx, cy)
            s.input.click(cx, cy)
    act_type(s.input, args["value"])
    # Best-effort verification: see the text somewhere on screen
    frame = s.screen.capture()
    ok = expect_text(s.ocr, frame, args["value"][:12]) if args["value"] else True
    return json.dumps({"ok": bool(ok)})


@function_tool
def scroll(ctx: RunContextWrapper[Session], args: ScrollArgs) -> str:
    """Scroll down a number of pixels. Args: pixels"""
    s = ctx.context
    scroll_down(s.input, int(args["pixels"]))
    return json.dumps({"ok": True})
