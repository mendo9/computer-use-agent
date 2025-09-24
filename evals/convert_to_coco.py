# scripts/convert_to_coco.py
from __future__ import annotations

import argparse
import os

from evals.utils import image_size, load_json, save_json, to_xywh


def normalize_items(raw: dict) -> list[dict]:
    """
    Returns a flat list of dicts:
      { 'screenshot', 'type', 'name', 'bbox', 'text'? }
    Supports:
      A) { items: [ { screenshot, elements: [ { ... } ] } ] }
      B) { items: [ { screenshot, type, name, bbox, text? } ] }
    """
    items = raw.get("items")
    if not isinstance(items, list):
        raise ValueError("Expected top-level {'items': [...]} in annotation.json")
    flat: list[dict] = []
    for it in items:
        if "elements" in it and isinstance(it["elements"], list):
            shot = it.get("screenshot")
            if not shot:
                raise ValueError("Per-image item missing 'screenshot'")
            for e in it["elements"]:
                rec = {
                    "screenshot": shot,
                    "type": e.get("type", "template"),
                    "name": e.get("name") or e.get("label") or "unknown",
                    "bbox": e.get("bbox"),
                    "text": e.get("text"),
                }
                if rec["bbox"] is None:
                    raise ValueError(f"Element missing bbox for {rec}")
                flat.append(rec)
        else:
            shot = it.get("screenshot")
            if not shot or "bbox" not in it:
                raise ValueError("Flat item must have 'screenshot' and 'bbox'")
            rec = {
                "screenshot": shot,
                "type": it.get("type", "template"),
                "name": it.get("name") or it.get("label") or "unknown",
                "bbox": it["bbox"],
                "text": it.get("text"),
            }
            flat.append(rec)
    return flat


def build_coco(flat: list[dict]) -> dict:
    img_map: dict[str, int] = {}
    images, categories, annotations = [], [], []
    cat_map: dict[str, int] = {}

    next_img_id = next_cat_id = next_ann_id = 1

    for rec in flat:
        shot = rec["screenshot"]
        if shot not in img_map:
            if not os.path.exists(shot):
                raise FileNotFoundError(f"Image not found: {shot}")
            w, h = image_size(shot)
            img_map[shot] = next_img_id
            images.append({"id": next_img_id, "file_name": shot, "width": w, "height": h})
            next_img_id += 1

        name = rec["name"]
        if name not in cat_map:
            cat_map[name] = next_cat_id
            categories.append({"id": next_cat_id, "name": name})
            next_cat_id += 1

        img_id = img_map[shot]
        iw = next(i["width"] for i in images if i["id"] == img_id)
        ih = next(i["height"] for i in images if i["id"] == img_id)

        xywh = to_xywh(rec["bbox"], img_w=iw, img_h=ih)

        ann = {
            "id": next_ann_id,
            "image_id": img_id,
            "category_id": cat_map[name],
            "bbox": xywh,
            "area": float(xywh[2] * xywh[3]),
            "iscrowd": 0,
        }
        if rec.get("text") is not None:
            ann["text"] = rec["text"]

        # Optional: preserve quadrilateral as segmentation if input was a quad
        b = rec["bbox"]
        if (
            isinstance(b, (list, tuple))
            and len(b) == 4
            and all(isinstance(pt, (list, tuple)) and len(pt) == 2 for pt in b)
        ):
            flat_poly = [c for pt in b for c in pt]
            ann["segmentation"] = [flat_poly]

        annotations.append(ann)
        next_ann_id += 1

    return {"images": images, "annotations": annotations, "categories": categories}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="annotation.json", help="Flexible annotation JSON")
    ap.add_argument("--out", dest="out", default="annotation.coco.json", help="COCO output")
    args = ap.parse_args()

    raw = load_json(args.inp)
    flat = normalize_items(raw)
    coco = build_coco(flat)
    save_json(args.out, coco)
    print(f"✅ Wrote COCO file: {args.out}")
    print(
        f"  images: {len(coco['images'])}, anns: {len(coco['annotations'])}, cats: {len(coco['categories'])}"
    )


if __name__ == "__main__":
    main()
