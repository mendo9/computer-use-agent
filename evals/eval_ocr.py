# scripts/eval_ocr.py
from __future__ import annotations

import argparse
import json
import os
import pathlib

from jiwer import cer, wer

try:
    from torchmetrics.text import CharErrorRate, WordErrorRate

    TM_OK = True
except Exception:
    TM_OK = False

from evals.utils import draw_overlay, ensure_dir, load_json, save_json, to_xywh

# your repo function
from src.vision.ocr import find_text_by_ocr


def is_ocr_ann(ann: dict) -> bool:
    return "text" in ann and isinstance(ann["text"], str)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", default="annotation.coco.json")
    ap.add_argument("--out_dir", default="eval_out/ocr")
    ap.add_argument("--overlay", action="store_true")
    ap.add_argument("--confidence_threshold", type=float, default=0.0)
    args = ap.parse_args()

    ensure_dir(args.out_dir)
    overlay_dir = os.path.join(args.out_dir, "overlays")
    ensure_dir(overlay_dir)

    gt = load_json(args.gt)
    id_to_name = {c["id"]: c["name"] for c in gt["categories"]}

    gt_by_image: dict[int, list[dict]] = {}
    for ann in gt["annotations"]:
        gt_by_image.setdefault(ann["image_id"], []).append(ann)

    gt_texts_all: list[str] = []
    pred_texts_all: list[str] = []
    per_item = []

    for im in gt["images"]:
        img_id = im["id"]
        img_path = im["file_name"]
        W, H = im["width"], im["height"]
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        gt_boxes, pred_boxes = [], []

        for ann in gt_by_image.get(img_id, []):
            if not is_ocr_ann(ann):
                continue
            cid = ann["category_id"]
            cat_name = id_to_name[cid]
            gt_text = ann["text"]

            # GT overlay (use bbox if present)
            if "bbox" in ann and isinstance(ann["bbox"], list):
                gt_xywh = to_xywh(ann["bbox"], img_w=W, img_h=H)
                gt_boxes.append((tuple(map(int, gt_xywh)), gt_text))
            else:
                gt_boxes.append(((0, 0, 0, 0), gt_text))

            # Predict via your OCR
            pred = find_text_by_ocr(img_bytes, gt_text)
            pred_text, pred_score, pred_xywh = "", None, None
            if isinstance(pred, dict):
                pred_text = pred.get("text", "") or ""
                pred_score = pred.get("score", None)
                pb = pred.get("bbox", None)
                if pb is not None:
                    pred_xywh = to_xywh(pb, img_w=W, img_h=H)
            elif isinstance(pred, str):
                pred_text = pred

            if pred_score is not None and pred_score < args.confidence_threshold:
                pred_text = ""  # filtered

            gt_texts_all.append(gt_text)
            pred_texts_all.append(pred_text)

            if pred_xywh:
                pred_boxes.append((tuple(map(int, pred_xywh)), pred_text, float(pred_score or 0.0)))

            per_item.append(
                {
                    "image_id": img_id,
                    "category_id": cid,
                    "category_name": cat_name,
                    "gt_text": gt_text,
                    "pred_text": pred_text,
                    "score": pred_score,
                }
            )

        if args.overlay and (gt_boxes or pred_boxes):
            base = pathlib.Path(img_path).stem
            draw_overlay(img_path, gt_boxes, pred_boxes, os.path.join(overlay_dir, f"{base}.png"))

    # Metrics (jiwer + optional torchmetrics)
    wer_value = wer(gt_texts_all, pred_texts_all) if gt_texts_all else 0.0
    cer_value = cer(gt_texts_all, pred_texts_all) if gt_texts_all else 0.0
    tm_cer = tm_wer = None
    if TM_OK and gt_texts_all:
        try:
            tm_cer = float(CharErrorRate()(pred_texts_all, gt_texts_all))
            tm_wer = float(WordErrorRate()(pred_texts_all, gt_texts_all))
        except Exception:
            tm_cer = tm_wer = None

    summary = {
        "samples": len(gt_texts_all),
        "jiwer": {"CER": cer_value, "WER": wer_value},
        "torchmetrics": {"CER": tm_cer, "WER": tm_wer},
    }
    print("\nOCR metrics:")
    print(json.dumps(summary, indent=2))

    save_json(os.path.join(args.out_dir, "metrics_ocr.json"), summary)
    save_json(os.path.join(args.out_dir, "per_item_ocr.json"), per_item)


if __name__ == "__main__":
    main()
