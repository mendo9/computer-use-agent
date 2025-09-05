from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class Detection:
    bbox: tuple[int, int, int, int]  # x1,y1,x2,y2
    label: str
    score: float


class YOLODetector:
    """
    ONNX YOLOv8-style detector.
    - Expects an ONNX model with (1,3,H,W) input and standard YOLOv8 output.
    - Uses letterbox resize to model size (default 640).
    """

    def __init__(
        self,
        onnx_path: str | None = None,
        class_names: list[str] | None = None,
        input_size: int = 640,
    ):
        self.onnx_path = onnx_path or os.getenv("YOLO_ONNX_PATH", "")
        self.class_names = class_names or []
        self.input_size = input_size
        self._session = None
        self._try_load()

    def _try_load(self) -> None:
        if not self.onnx_path or not os.path.exists(self.onnx_path):
            return
        try:
            import onnxruntime as ort  # type: ignore

            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            self._session = ort.InferenceSession(self.onnx_path, providers=providers)
        except Exception as e:
            # Defer failure to inference call, but keep message for debugging
            self._load_error = str(e)

    def _letterbox(self, img, new_size=640, color=(114, 114, 114)):
        import cv2
        import numpy as np

        h, w = img.shape[:2]
        scale = min(new_size / h, new_size / w)
        nh, nw = int(round(h * scale)), int(round(w * scale))
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((new_size, new_size, 3), color, dtype=img.dtype)
        top = (new_size - nh) // 2
        left = (new_size - nw) // 2
        canvas[top : top + nh, left : left + nw] = resized
        return canvas, scale, left, top

    def detect(
        self, frame: Any, conf_threshold: float = 0.25, iou_threshold: float = 0.45
    ) -> list[Detection]:
        """
        Return a list of Detection(bbox,label,score).
        Falls back to [] if onnxruntime or model is missing.
        """
        if self._session is None:
            return []

        import cv2
        import numpy as np

        img = frame
        if img is None:
            return []

        # letterbox
        inp, scale, dx, dy = self._letterbox(img, self.input_size)
        x = cv2.cvtColor(inp, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        x = np.transpose(x, (2, 0, 1))[None, ...]  # (1,3,H,W)

        input_name = self._session.get_inputs()[0].name
        outputs = self._session.run(None, {input_name: x})

        # YOLOv8 ONNX common format: (batch, num, 85) or (1, num, 84+)
        preds = outputs[0]
        if preds.ndim == 3:
            preds = preds[0]
        # preds: (num, 85) => [x,y,w,h, conf, cls_scores...]
        boxes, scores, cls_ids = self._postprocess(preds, conf_threshold, iou_threshold)

        dets: list[Detection] = []
        for (cx, cy, w, h), score, cls_id in zip(boxes, scores, cls_ids, strict=False):
            # undo letterbox
            x1 = int((cx - w / 2) - dx)
            y1 = int((cy - h / 2) - dy)
            x2 = int((cx + w / 2) - dx)
            y2 = int((cy + h / 2) - dy)
            # scale back to original
            x1 = int(x1 / scale)
            y1 = int(y1 / scale)
            x2 = int(x2 / scale)
            y2 = int(y2 / scale)
            label = (
                self.class_names[int(cls_id)]
                if self.class_names and 0 <= int(cls_id) < len(self.class_names)
                else str(int(cls_id))
            )
            dets.append(
                Detection(
                    bbox=(max(0, x1), max(0, y1), max(0, x2), max(0, y2)),
                    label=label,
                    score=float(score),
                )
            )
        return dets

    def _postprocess(self, preds, conf_thres: float, iou_thres: float):
        import numpy as np

        # If preds already separated, handle; else assume [cx,cy,w,h, conf, *cls]
        if preds.shape[1] < 6:
            return [], [], []

        boxes = preds[:, :4]
        obj = preds[:, 4:5]
        cls = preds[:, 5:]
        cls_ids = np.argmax(cls, axis=1)
        cls_scores = cls[np.arange(len(cls_ids)), cls_ids]
        scores = obj.squeeze() * cls_scores
        mask = scores >= conf_thres
        boxes = boxes[mask]
        scores = scores[mask]
        cls_ids = cls_ids[mask]

        # NMS on xywh boxes after converting to xyxy
        if len(boxes) == 0:
            return [], [], []

        cxcywh = boxes
        xyxy = cxcywh.copy()
        xyxy[:, 0] = cxcywh[:, 0] - cxcywh[:, 2] / 2
        xyxy[:, 1] = cxcywh[:, 1] - cxcywh[:, 3] / 2
        xyxy[:, 2] = cxcywh[:, 0] + cxcywh[:, 2] / 2
        xyxy[:, 3] = cxcywh[:, 1] + cxcywh[:, 3] / 2

        keep = self._nms(xyxy, scores, iou_thres)
        return cxcywh[keep], scores[keep], cls_ids[keep]

    def _nms(self, boxes, scores, iou_thres):
        idxs = scores.argsort()[::-1]
        keep = []
        while len(idxs) > 0:
            i = idxs[0]
            keep.append(i)
            if len(idxs) == 1:
                break
            ious = self._iou(boxes[i], boxes[idxs[1:]])
            idxs = idxs[1:][ious < iou_thres]
        return keep

    def _iou(self, box, boxes):
        import numpy as np

        x1 = np.maximum(box[0], boxes[:, 0])
        y1 = np.maximum(box[1], boxes[:, 1])
        x2 = np.minimum(box[2], boxes[:, 2])
        y2 = np.minimum(box[3], boxes[:, 3])
        inter = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
        area1 = (box[2] - box[0]) * (box[3] - box[1])
        area2 = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        union = area1 + area2 - inter + 1e-6
        return inter / union
