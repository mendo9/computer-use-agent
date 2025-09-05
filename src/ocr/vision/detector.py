"""YOLOv8s-ONNX inference for UI element detection"""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


@dataclass
class Detection:
    """UI element detection result"""

    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    center: tuple[int, int]
    id: str | None = None


class YOLODetector:
    """YOLOv8s-ONNX detector for UI elements"""

    # COCO classes relevant for UI and screen automation
    # Focused on objects commonly found in screen/desktop environments
    UI_CLASSES = {
        0: "person",  # For user avatars, profile pictures
        62: "tv",  # For monitors, displays
        63: "laptop",  # For device detection
        64: "mouse",  # For peripheral detection
        65: "remote",  # For control devices
        66: "keyboard",  # For input device detection
        67: "cell phone",  # For mobile device detection
        73: "book",  # For document/reading interfaces
        74: "clock",  # For time displays, widgets
        76: "scissors",  # For cut/edit tools in UI
    }

    # Full COCO class set (kept for completeness but filtered for UI relevance)
    FULL_COCO_CLASSES = {
        0: "person",
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        4: "airplane",
        5: "bus",
        6: "train",
        7: "truck",
        8: "boat",
        9: "traffic light",
        10: "fire hydrant",
        11: "stop sign",
        12: "parking meter",
        13: "bench",
        14: "bird",
        15: "cat",
        16: "dog",
        17: "horse",
        18: "sheep",
        19: "cow",
        20: "elephant",
        21: "bear",
        22: "zebra",
        23: "giraffe",
        24: "backpack",
        25: "umbrella",
        26: "handbag",
        27: "tie",
        28: "suitcase",
        29: "frisbee",
        30: "skis",
        31: "snowboard",
        32: "sports ball",
        33: "kite",
        34: "baseball bat",
        35: "baseball glove",
        36: "skateboard",
        37: "surfboard",
        38: "tennis racket",
        39: "bottle",
        40: "wine glass",
        41: "cup",
        42: "fork",
        43: "knife",
        44: "spoon",
        45: "bowl",
        46: "banana",
        47: "apple",
        48: "sandwich",
        49: "orange",
        50: "broccoli",
        51: "carrot",
        52: "hot dog",
        53: "pizza",
        54: "donut",
        55: "cake",
        56: "chair",
        57: "couch",
        58: "potted plant",
        59: "bed",
        60: "dining table",
        61: "toilet",
        62: "tv",
        63: "laptop",
        64: "mouse",
        65: "remote",
        66: "keyboard",
        67: "cell phone",
        68: "microwave",
        69: "oven",
        70: "toaster",
        71: "sink",
        72: "refrigerator",
        73: "book",
        74: "clock",
        75: "vase",
        76: "scissors",
        77: "teddy bear",
        78: "hair drier",
        79: "toothbrush",
    }

    def __init__(
        self, model_path: str, confidence_threshold: float = 0.6, use_ui_focused: bool = True
    ):
        """
        Initialize YOLOv8s-ONNX detector

        Args:
            model_path: Path to ONNX model file
            confidence_threshold: Minimum confidence for detections
            use_ui_focused: If True, filter to UI-relevant classes only
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.use_ui_focused = use_ui_focused

        # Choose class set based on focus preference
        self.active_classes = self.UI_CLASSES if use_ui_focused else self.FULL_COCO_CLASSES

        # Initialize ONNX Runtime session
        self.session = ort.InferenceSession(str(self.model_path))

        # Get model input details
        self.input_name = self.session.get_inputs()[0].name
        self.input_shape = self.session.get_inputs()[0].shape
        self.input_height, self.input_width = self.input_shape[2], self.input_shape[3]

        class_mode = "UI-focused" if use_ui_focused else "full COCO"
        print(f"YOLOv8s ONNX loaded: {self.model_path}")
        print(f"Input shape: {self.input_shape}")
        print(f"Detection mode: {class_mode} ({len(self.active_classes)} classes)")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for YOLO inference"""
        # Resize and normalize
        resized = cv2.resize(image, (self.input_width, self.input_height))

        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1] and convert to float32
        normalized = rgb.astype(np.float32) / 255.0

        # Transpose to CHW format and add batch dimension
        input_tensor = normalized.transpose(2, 0, 1)[np.newaxis, ...]

        return input_tensor

    def postprocess(self, outputs: np.ndarray, original_shape: tuple[int, int]) -> list[Detection]:
        """Postprocess YOLO outputs to detections"""
        predictions = outputs[0]  # Shape: [1, 84, 8400] for YOLOv8s

        # Transpose to [8400, 84]
        predictions = predictions.transpose(0, 2, 1)[0]

        detections = []
        orig_h, orig_w = original_shape

        for pred in predictions:
            # Extract box coordinates and confidence
            x_center, y_center, width, height = pred[0:4]
            confidence = pred[4]
            class_scores = pred[5:]

            if confidence < self.confidence_threshold:
                continue

            # Get class with highest score
            class_id = np.argmax(class_scores)
            class_confidence = class_scores[class_id] * confidence

            if class_confidence < self.confidence_threshold:
                continue

            # Skip classes not in our active set (for UI-focused mode)
            if class_id not in self.active_classes:
                continue

            # Convert to original image coordinates
            x_center *= orig_w / self.input_width
            y_center *= orig_h / self.input_height
            width *= orig_w / self.input_width
            height *= orig_h / self.input_height

            # Convert to bbox format
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)

            # Ensure bbox is within image bounds
            x1 = max(0, min(x1, orig_w))
            y1 = max(0, min(y1, orig_h))
            x2 = max(0, min(x2, orig_w))
            y2 = max(0, min(y2, orig_h))

            detection = Detection(
                class_name=self.active_classes.get(class_id, f"class_{class_id}"),
                confidence=float(class_confidence),
                bbox=(x1, y1, x2, y2),
                center=(int(x_center), int(y_center)),
            )

            detections.append(detection)

        # Apply Non-Maximum Suppression
        detections = self._apply_nms(detections, iou_threshold=0.5)

        return detections

    def _apply_nms(self, detections: list[Detection], iou_threshold: float) -> list[Detection]:
        """Apply Non-Maximum Suppression"""
        if not detections:
            return detections

        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)

        filtered_detections = []

        for detection in detections:
            # Check if this detection overlaps significantly with any kept detection
            keep = True
            for kept_detection in filtered_detections:
                if self._calculate_iou(detection.bbox, kept_detection.bbox) > iou_threshold:
                    keep = False
                    break

            if keep:
                filtered_detections.append(detection)

        return filtered_detections

    def _calculate_iou(
        self, box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]
    ) -> float:
        """Calculate Intersection over Union"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2

        # Calculate intersection area
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)

        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0

        intersection_area = (x2_i - x1_i) * (y2_i - y1_i)

        # Calculate union area
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = area1 + area2 - intersection_area

        return intersection_area / union_area if union_area > 0 else 0.0

    def detect(self, image: np.ndarray) -> list[Detection]:
        """Detect UI elements in image"""
        original_shape = image.shape[:2]  # (height, width)

        # Preprocess
        input_tensor = self.preprocess(image)

        # Run inference
        outputs = self.session.run(None, {self.input_name: input_tensor})

        # Postprocess
        detections = self.postprocess(outputs, original_shape)

        return detections

    def draw_detections(self, image: np.ndarray, detections: list[Detection]) -> np.ndarray:
        """Draw bounding boxes and labels on image"""
        result_image = image.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection.bbox

            # Draw bounding box
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw label
            label = f"{detection.class_name}: {detection.confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(
                result_image,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                (0, 255, 0),
                -1,
            )
            cv2.putText(
                result_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2
            )

        return result_image
