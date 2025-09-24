# evaluation/utils.py
from __future__ import annotations

import json
import os
import pathlib

import cv2
from PIL import Image, ImageDraw, ImageFont


# ---------- I/O & FS ----------
def ensure_dir(p: str | pathlib.Path) -> None:
    pathlib.Path(p).mkdir(parents=True, exist_ok=True)


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, obj: dict | list) -> None:
    ensure_dir(pathlib.Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def image_size(path: str) -> tuple[int, int]:
    with Image.open(path) as im:
        return im.width, im.height


# ---------- BBox helpers ----------
def x1y1x2y2_to_xywh(x1, y1, x2, y2):
    x = float(min(x1, x2))
    y = float(min(y1, y2))
    w = float(abs(x2 - x1))
    h = float(abs(y2 - y1))
    return [x, y, w, h]


def quad_to_xywh(quad):
    # quad: [[x,y], [x,y], [x,y], [x,y]]
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    x_min, x_max = float(min(xs)), float(max(xs))
    y_min, y_max = float(min(ys)), float(max(ys))
    return [x_min, y_min, x_max - x_min, y_max - y_min]


def cxcywh_to_xywh(cx, cy, w, h):
    return [float(cx - w / 2), float(cy - h / 2), float(w), float(h)]


def clip_xywh(xywh, img_w, img_h):
    x, y, w, h = xywh
    x = max(0.0, min(x, img_w))
    y = max(0.0, min(y, img_h))
    w = max(0.0, min(w, img_w - x))
    h = max(0.0, min(h, img_h - y))
    return [x, y, w, h]


def to_xywh(b, img_w: int | None = None, img_h: int | None = None):
    """
    Accepts:
      - [x, y, w, h]
      - [x1, y1, x2, y2]
      - [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]  (EasyOCR quad)
    Returns [x, y, w, h]; clips if img_w/img_h provided.
    """
    # Quad?
    if (
        isinstance(b, (list, tuple))
        and len(b) == 4
        and all(isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in b)
    ):
        xywh = quad_to_xywh(b)
    # 4 scalars
    elif (
        isinstance(b, (list, tuple)) and len(b) == 4 and all(isinstance(v, (int, float)) for v in b)
    ):
        x0, y0, a, d = b
        if a > x0 and d > y0:
            xywh = x1y1x2y2_to_xywh(x0, y0, a, d)  # corners
        else:
            xywh = [float(x0), float(y0), float(a), float(d)]  # already xywh
    else:
        raise ValueError(f"Unsupported bbox format: {b}")

    if img_w is not None and img_h is not None:
        xywh = clip_xywh(xywh, img_w, img_h)
    return xywh


# ---------- Template helpers ----------
def template_wh(template_name: str) -> tuple[int, int] | None:
    """
    Try to infer template size from repository paths.
    Adjust candidates if your structure differs.
    """
    candidates = [
        f"src/vision/templates/{template_name}.png",
        f"src/vision/templates/{template_name}.jpg",
        f"src/vision/templates/{template_name}/{template_name}.png",
    ]
    for p in candidates:
        if os.path.exists(p):
            img = cv2.imread(p)
            if img is not None:
                h, w = img.shape[:2]
                return (w, h)
    return None


# ---------- Visual overlays ----------
def draw_overlay(
    img_path: str,
    gt_boxes: list[tuple[tuple[int, int, int, int], str | None]],
    pred_boxes: list[tuple[tuple[int, int, int, int], str | None, float]],
    out_path: str,
) -> None:
    """
    Draw GT (green) and predictions (red) with optional labels/confidence.
    gt_boxes: [((x,y,w,h), label), ...]
    pred_boxes: [((x,y,w,h), label, score), ...]
    """
    im = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default()

    for (x, y, w, h), label in gt_boxes:
        draw.rectangle([x, y, x + w, y + h], outline=(0, 200, 0), width=2)
        if label:
            draw.text((x, y - 12), f"GT: {label}", fill=(0, 200, 0), font=font)

    for (x, y, w, h), label, score in pred_boxes:
        draw.rectangle([x, y, x + w, y + h], outline=(220, 0, 0), width=2)
        tag = "Pred"
        if label:
            tag += f": {label}"
        if score is not None:
            tag += f" ({score:.2f})"
        draw.text((x, y + h + 4), tag, fill=(220, 0, 0), font=font)

    ensure_dir(pathlib.Path(out_path).parent)
    im.save(out_path)
