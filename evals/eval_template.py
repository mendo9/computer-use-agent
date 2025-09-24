# scripts/eval_template.py
from __future__ import annotations

import argparse
import json
import os
import pathlib

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

from evals.utils import (
    clip_xywh,
    cxcywh_to_xywh,
    draw_overlay,
    ensure_dir,
    load_json,
    save_json,
    template_wh,
)

# your repo function
from src.vision.finder import find_target_center


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", default="annotation.coco.json")
    ap.add_argument("--out_dir", default="eval_out/template")
    ap.add_argument("--overlay", action="store_true")
    ap.add_argument("--default_template_wh", type=int, nargs=2, metavar=("W", "H"))
    args = ap.parse_args()

    ensure_dir(args.out_dir)
    overlay_dir = os.path.join(args.out_dir, "overlays")
    ensure_dir(overlay_dir)

    gt = load_json(args.gt)
    id_to_name = {c["id"]: c["name"] for c in gt["categories"]}

    gt_by_image: dict[int, list[dict]] = {}
    for ann in gt["annotations"]:
        gt_by_image.setdefault(ann["image_id"], []).append(ann)

    predictions = []

    for im in gt["images"]:
        img_id = im["id"]
        img_path = im["file_name"]
        W, H = im["width"], im["height"]
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        gt_boxes, pred_boxes = [], []

        for ann in gt_by_image.get(img_id, []):
            cid = ann["category_id"]
            cat_name = id_to_name[cid]
            # template detection only: require template file or default WH
            twh = template_wh(cat_name) or (
                tuple(args.default_template_wh) if args.default_template_wh else None
            )
            if twh is None:
                continue  # treat as OCR category; skip here

            # GT overlay
            gt_xywh = ann["bbox"]
            gt_boxes.append((tuple(map(int, gt_xywh)), cat_name))

            # predict
            center = find_target_center(img_bytes, cat_name)
            if center is None:
                continue
            cx, cy = center
            pred_xywh = clip_xywh(cxcywh_to_xywh(cx, cy, twh[0], twh[1]), W, H)

            predictions.append(
                {"image_id": img_id, "category_id": cid, "bbox": pred_xywh, "score": 1.0}
            )
            pred_boxes.append((tuple(map(int, pred_xywh)), cat_name, 1.0))

        if args.overlay and (gt_boxes or pred_boxes):
            base = pathlib.Path(img_path).stem
            draw_overlay(img_path, gt_boxes, pred_boxes, os.path.join(overlay_dir, f"{base}.png"))

    # Save predictions
    pred_path = os.path.join(args.out_dir, "predictions.json")
    save_json(pred_path, predictions)

    # COCO eval
    coco_gt = COCO(args.gt)
    coco_dt = coco_gt.loadRes(pred_path) if predictions else coco_gt.loadRes([])
    coco_eval = COCOeval(coco_gt, coco_dt, "bbox")
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()

    summary = {
        "AP": coco_eval.stats[0],
        "AP50": coco_eval.stats[1],
        "AP75": coco_eval.stats[2],
        "AR": coco_eval.stats[8],
    }
    save_json(os.path.join(args.out_dir, "metrics_template.json"), summary)
    print("\nTemplate metrics:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
