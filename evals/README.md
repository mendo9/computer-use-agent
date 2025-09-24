# Vision Evaluation Framework

This directory provides evaluation tooling for the **template matching** (OpenCV) and **OCR** (EasyOCR/PaddleOCR) components of the vision pipeline.

It allows you to:

* Convert a simple `annotation.json` into **COCO format**
* Evaluate **template matching** with [pycocotools](https://github.com/cocodataset/cocoapi) (IoU / mAP)
* Evaluate **OCR** with [jiwer](https://github.com/jitsi/jiwer) and [torchmetrics](https://torchmetrics.readthedocs.io/) (CER / WER)
* Generate **visual overlays** comparing ground truth vs predictions
* Save structured **JSON reports** for CI/CD or regression tracking

---

## Requirements

* Python 3.10+
* Dependencies:

  ```bash
  uv add pycocotools jiwer torchmetrics opencv-python pillow
  ```

> `pycocotools` may require build tools on Linux. Prebuilt wheels are usually available on macOS/Windows.
> `torchmetrics` works without torch for text metrics, but some environments may require `torch`.

---

## File Structure

* `eval/annotation.json` — flexible input format you maintain or export
* `eval/convert_to_coco.py` — convert `annotation.json` to `annotation.coco.json`
* `eval/eval_template.py` — evaluate template matching (IoU / mAP)
* `eval/eval_ocr.py` — evaluate OCR (CER / WER)
* `eval/utils.py` — shared helpers for overlays, bbox conversion, etc.

Your repo already provides:

* `src/vision/finder.py` — template matching (`find_target_center(...)`)
* `src/vision/ocr.py` — OCR (`find_text_by_ocr(...)`)
* `src/vision/templates/` — template images (`safari_icon.png`, etc.)

---

## Annotation Format

Example `annotation.json` (input to converter):

```json
{
  "items": [
    {
      "screenshot": "trajectories/data/screenshot1.png",
      "elements": [
        {
          "type": "template",
          "name": "safari_icon",
          "bbox": [100, 150, 50, 50]
        },
        {
          "type": "text",
          "name": "sign_in_label",
          "bbox": [300, 500, 380, 520],
          "text": "Sign in"
        }
      ]
    },
    {
      "screenshot": "trajectories/data/screenshot2.png",
      "elements": [
        {
          "type": "text",
          "name": "headline_label",
          "bbox": [[50, 60], [220, 60], [220, 92], [50, 92]],
          "text": "Top Stories"
        }
      ]
    }
  ]
}
```

Supported `bbox` formats:

* `[x, y, w, h]` — xywh
* `[x1, y1, x2, y2]` — corners
* `[[x1,y1],[x2,y2],[x3,y3],[x4,y4]]` — quad (EasyOCR style)

---

## End-to-End Usage

### 1. Convert to COCO

```bash
uv run python scripts/convert_to_coco.py --in annotation.json --out annotation.coco.json
```

Produces:

* `annotation.coco.json` with `images[]`, `annotations[]`, `categories[]`

### 2. Template Evaluation

```bash
uv run python scripts/eval_template.py --gt annotation.coco.json --overlay
```

Outputs:

* `eval/out/template/predictions.json` (COCO predictions)
* `eval/out/template/metrics_template.json` (AP, AP50, AP75, AR)
* `eval/out/template/overlays/*.png` (green = GT, red = predictions)

### 3. OCR Evaluation

```bash
uv run python scripts/eval_ocr.py --gt annotation.coco.json --overlay
```

Outputs:

* `eval/out/ocr/metrics_ocr.json` (CER / WER metrics)
* `eval/out/ocr/per_item_ocr.json` (per-sample details)
* `eval/out/ocr/overlays/*.png`

---

## Metrics

**Template (COCOeval)**

* `AP` = mean Average Precision @ IoU \[.5:.95]
* `AP50` = AP @ IoU ≥ 0.5
* `AP75` = AP @ IoU ≥ 0.75
* `AR` = Average Recall

**OCR (jiwer / torchmetrics)**

* `CER` = Character Error Rate (lower is better)
* `WER` = Word Error Rate (lower is better)

---

## CI/CD Integration (optional)

You can enforce quality gates by checking JSON metrics:

```bash
python - <<'PY'
import json, sys
tmpl=json.load(open('eval_out/template/metrics_template.json'))
ocr=json.load(open('eval_out/ocr/metrics_ocr.json'))
ok = True
if tmpl["AP50"] < 0.80: ok=False
if ocr["jiwer"]["CER"] > 0.10: ok=False
sys.exit(0 if ok else 1)
PY
```

---

## Summary

* Maintain `annotation.json` with screenshots, elements, bboxes, and OCR text.
* Convert → `annotation.coco.json`.
* Run **template** eval for IoU/mAP.
* Run **OCR** eval for CER/WER.
* Inspect overlays and JSON reports.
* Integrate into CI/CD with metric gates.


# Example `annotation.coco.json`

This file is produced automatically by `scripts/convert_to_coco.py`. It is the COCO-standard format derived from your simpler `annotation.json`.

It contains three main sections:

* **images**: metadata for each screenshot
* **annotations**: bounding boxes and labels for elements in the screenshots
* **categories**: unique list of template/text classes

---

## Example

```json
{
  "images": [
    {
      "id": 1,
      "file_name": "trajectories/data/screenshot1.png",
      "width": 1024,
      "height": 768
    },
    {
      "id": 2,
      "file_name": "trajectories/data/screenshot2.png",
      "width": 800,
      "height": 600
    }
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "bbox": [100, 150, 50, 50],
      "area": 2500,
      "iscrowd": 0
    },
    {
      "id": 2,
      "image_id": 1,
      "category_id": 2,
      "bbox": [300, 500, 80, 20],
      "area": 1600,
      "iscrowd": 0,
      "text": "Sign in"
    },
    {
      "id": 3,
      "image_id": 2,
      "category_id": 3,
      "bbox": [50, 60, 170, 32],
      "area": 5440,
      "iscrowd": 0,
      "text": "Top Stories",
      "segmentation": [[50, 60, 220, 60, 220, 92, 50, 92]]
    }
  ],
  "categories": [
    {"id": 1, "name": "safari_icon"},
    {"id": 2, "name": "sign_in_label"},
    {"id": 3, "name": "headline_label"}
  ]
}
```

---

## Notes

* All `bbox` entries are normalized to `[x, y, width, height]`.
* Image sizes (`width`, `height`) are extracted automatically from the screenshots.
* OCR annotations preserve the `text` field (ground truth text).
* EasyOCR-style quads are stored in `segmentation` for fidelity, while the bounding box is the tight axis-aligned rectangle.
* `category_id` values link back to entries in `categories`.
* `image_id` values link back to entries in `images`.

This format is directly consumable by [pycocotools](https://github.com/cocodataset/cocoapi) for evaluation.

---

## How it fits together (diagram)

```mermaid
flowchart LR
  A[annotation.json
(flexible input)] --> B[convert_to_coco.py]
  B --> C[annotation.coco.json
(COCO ground truth)]
  C --> D[eval_template.py
(OpenCV templates)]
  C --> E[eval_ocr.py
(OCR text)]
  D --> F[predictions.json
(COCO results)]
  D --> G[metrics_template.json
(AP / AP50 / AP75 / AR)]
  D --> H[overlays/*.png
(GT vs Pred boxes)]
  E --> I[metrics_ocr.json
(CER / WER)]
  E --> J[per_item_ocr.json
(per-sample text)]
  E --> K[overlays/*.png
(GT vs Pred text)]
```

---

## How predictions are compared to ground truth

### Template matching (detection)

* **Ground truth:** `annotation.coco.json` with `images`, `annotations` (GT bboxes), `categories`.
* **Predictions:** `eval_out/template/predictions.json` produced by `eval_template.py` (one JSON list of detections with `image_id`, `category_id`, `bbox` in `[x,y,w,h]`, and `score`).
* **Comparer:** [`pycocotools` COCOeval](https://github.com/cocodataset/cocoapi). The script loads GT and predictions, then computes:

  * IoU matching between predicted and GT boxes
  * **AP / AP50 / AP75 / AR**
* **Outputs:**

  * Console summary (printed by `COCOeval.summarize()`)
  * `eval_out/template/metrics_template.json` with key stats
  * `eval_out/template/overlays/*.png` highlighting GT (green) and predictions (red)

Example console (truncated):

```
Average Precision  (AP) @[ IoU=0.50:0.95 ] = 0.421
Average Precision  (AP) @[ IoU=0.50      ] = 0.850
Average Recall     (AR) @[ IoU=0.50:0.95 ] = 0.580
```

Example `eval_out/template/metrics_template.json`:

```json
{
  "AP": 0.421,
  "AP50": 0.850,
  "AP75": 0.372,
  "AR": 0.580
}
```

### OCR (text recognition)

* **Ground truth:** `annotation.coco.json` annotations for OCR include a `text` field (expected string) and a `bbox` (optional, used for overlays).
* **Predictions:** `eval_ocr.py` calls your OCR function and collects predicted strings (and predicted boxes/scores if available).
* **Comparer:**

  * **CER/WER** via [`jiwer`](https://github.com/jitsi/jiwer) (always)
  * **CER/WER** via [`torchmetrics.text`](https://torchmetrics.readthedocs.io/) (optional)
* **Outputs:**

  * Console JSON summary with counts and error rates
  * `eval_out/ocr/metrics_ocr.json` (aggregate CER/WER)
  * `eval_out/ocr/per_item_ocr.json` (per-sample GT vs Pred text/score)
  * `eval_out/ocr/overlays/*.png` showing GT vs Pred text regions

Example `eval_out/ocr/metrics_ocr.json`:

```json
{
  "samples": 23,
  "jiwer": {"CER": 0.06, "WER": 0.11},
  "torchmetrics": {"CER": 0.06, "WER": 0.10}
}
```

---

## File examples

### Example `annotation.coco.json`

A minimal snippet is reproduced here; a full example is also included as a separate doc in this workspace.

```json
{
  "images": [
    {"id": 1, "file_name": "trajectories/data/screenshot1.png", "width": 1024, "height": 768}
  ],
  "annotations": [
    {"id": 1, "image_id": 1, "category_id": 1, "bbox": [100,150,50,50], "area": 2500, "iscrowd": 0},
    {"id": 2, "image_id": 1, "category_id": 2, "bbox": [300,500,80,20],  "area": 1600, "iscrowd": 0, "text": "Sign in"}
  ],
  "categories": [
    {"id": 1, "name": "safari_icon"},
    {"id": 2, "name": "sign_in_label"}
  ]
}
```

### Example `predictions.json`

This is generated by `eval_template.py` and fed into COCOeval.

```json
[
  {"image_id": 1, "category_id": 1, "bbox": [98,148,52,52],  "score": 0.92},
  {"image_id": 1, "category_id": 2, "bbox": [305,498,78,22], "score": 0.87}
]
```

---

## Tips

* Make your **category names** match your template keys (e.g., `safari_icon` ↔ `src/vision/templates/safari_icon.png`).
* For template eval, if your function only returns a **center**, the script infers a bbox using the template’s width/height from disk (or `--default_template_wh`).
* EasyOCR **quads** are accepted in input and converted to tight axis-aligned boxes for COCO; the original quad can be preserved in `segmentation`.
* Add CI gates by checking `AP50` and `CER` in the saved JSON metric files.
