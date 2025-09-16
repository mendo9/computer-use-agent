"""Template Matching UI Element Detection

Comprehensive template matching implementation for finding custom UI elements.
Uses OpenCV's template matching with multi-scale and rotation support.
Supports single and multi-template detection strategies.
"""

from dataclasses import dataclass

import cv2
import numpy as np

from src.vision.template_manager import (
    TemplateManager,
    TemplateSource,
    TemplateStrategy,
    get_template_manager,
)


@dataclass
class Detection:
    """Template matching detection result"""

    template_name: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    center: tuple[int, int]
    area: int
    scale: float = 1.0
    angle: float = 0.0
    method: str = "TM_CCOEFF_NORMED"

    # Enhanced multi-template fields
    template_source: TemplateSource | None = None
    template_match_method: str = "single"
    template_confidence: float = 1.0


class TemplateMatchingMethods:
    """Available OpenCV template matching methods"""

    TM_CCOEFF = cv2.TM_CCOEFF
    TM_CCOEFF_NORMED = cv2.TM_CCOEFF_NORMED
    TM_CCORR = cv2.TM_CCORR
    TM_CCORR_NORMED = cv2.TM_CCORR_NORMED
    TM_SQDIFF = cv2.TM_SQDIFF
    TM_SQDIFF_NORMED = cv2.TM_SQDIFF_NORMED

    @classmethod
    def get_method_by_name(cls, method_name: str) -> int:
        """Get OpenCV method constant by name"""
        method_map = {
            "TM_CCOEFF": cls.TM_CCOEFF,
            "TM_CCOEFF_NORMED": cls.TM_CCOEFF_NORMED,
            "TM_CCORR": cls.TM_CCORR,
            "TM_CCORR_NORMED": cls.TM_CCORR_NORMED,
            "TM_SQDIFF": cls.TM_SQDIFF,
            "TM_SQDIFF_NORMED": cls.TM_SQDIFF_NORMED,
        }
        return method_map.get(method_name, cls.TM_CCOEFF_NORMED)


def detect_ui_elements(
    image: np.ndarray,
    template_sources: TemplateSource | list[TemplateSource] | np.ndarray,
    template_name: str = "template",
    confidence_threshold: float = 0.8,
    method: str = "auto",
    max_detections: int = 100,
    enable_multiscale: bool = True,
    scale_range: tuple[float, float] = (0.5, 2.0),
    scale_steps: int = 20,
    enable_rotation: bool = False,
    rotation_range: tuple[float, float] = (-30, 30),
    rotation_steps: int = 13,
    nms_threshold: float = 0.3,
    template_manager: TemplateManager | None = None,
) -> list[Detection]:
    """
    Detect UI elements using template matching with advanced features

    Args:
        image: Input image as numpy array (BGR format from cv2)
        template_sources: Template source(s) - TemplateSource, list of TemplateSource, or np.ndarray for backward compatibility
        template_name: Name identifier for the template (used if template_sources is np.ndarray)
        confidence_threshold: Minimum confidence for detections (0.0-1.0)
        method: Template matching method ("auto", "TM_CCOEFF_NORMED", "TM_SQDIFF_NORMED", etc.)
        max_detections: Maximum number of detections to return
        enable_multiscale: Enable multi-scale template matching
        scale_range: Range of scales to test (min_scale, max_scale)
        scale_steps: Number of scale steps to test
        enable_rotation: Enable rotation-invariant template matching
        rotation_range: Range of rotations in degrees (min_angle, max_angle)
        rotation_steps: Number of rotation steps to test
        nms_threshold: Non-maximum suppression threshold
        template_manager: Optional template manager instance

    Returns:
        List of Detection objects sorted by confidence

    Example:
        # Multi-template detection
        template_manager = get_template_manager()
        template_sources = template_manager.resolve_templates([
            TemplateRequest(strategy=TemplateStrategy.LIBRARY, data={"id": "submit_button"}),
            TemplateRequest(strategy=TemplateStrategy.BASE64, data=base64_template)
        ])
        detections = detect_ui_elements(image, template_sources)

        # Single template (backward compatibility)
        template = cv2.imread("button_template.png")
        detections = detect_ui_elements(image, template, "login_button")
    """
    if image is None:
        return []

    # Normalize template_sources to list of TemplateSource objects
    if template_manager is None:
        template_manager = get_template_manager()

    template_sources_list = _normalize_template_sources(
        template_sources, template_name, template_manager
    )

    if not template_sources_list:
        return []

    # Convert image to grayscale for better template matching
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Detect with multiple templates if needed
    if len(template_sources_list) == 1:
        detections = _detect_single_template(
            image_gray,
            template_sources_list[0],
            method,
            confidence_threshold,
            enable_multiscale,
            scale_range,
            scale_steps,
            enable_rotation,
            rotation_range,
            rotation_steps,
        )
    else:
        detections = _detect_multi_template(
            image_gray,
            template_sources_list,
            method,
            confidence_threshold,
            enable_multiscale,
            scale_range,
            scale_steps,
            enable_rotation,
            rotation_range,
            rotation_steps,
        )

    # Apply Cross-Template Non-Maximum Suppression
    detections = _apply_cross_template_nms(detections, nms_threshold)

    # Sort by confidence and limit results
    detections.sort(key=lambda x: x.confidence, reverse=True)
    return detections[:max_detections]


def _select_best_method(image: np.ndarray, template: np.ndarray) -> str:
    """
    Automatically select the best template matching method based on image characteristics

    Returns:
        Best method name for the given image and template
    """
    # For UI element detection, TM_CCOEFF_NORMED is generally the best choice
    # as it's most robust to lighting variations and provides reliable results

    # Calculate some basic image statistics to inform method selection
    template_std = np.std(template.astype(np.float32))
    image_std = np.std(image.astype(np.float32))

    # If template has very low variance (e.g., solid color), use SQDIFF
    if template_std < 10:
        return "TM_SQDIFF_NORMED"

    # If there's a big difference in image vs template variance, use CCOEFF
    # which handles lighting differences better
    if abs(image_std - template_std) > 20:
        return "TM_CCOEFF_NORMED"

    # Default to the most robust method based on research
    return "TM_CCOEFF_NORMED"


def _basic_template_matching(
    image: np.ndarray,
    template: np.ndarray,
    template_name: str,
    method: int,
    confidence_threshold: float,
) -> list[Detection]:
    """Basic template matching without scaling or rotation"""
    result = cv2.matchTemplate(image, template, method)
    return _process_match_result(
        result, template, template_name, method, confidence_threshold, scale=1.0, angle=0.0
    )


def _advanced_template_matching(
    image: np.ndarray,
    template: np.ndarray,
    template_name: str,
    method: int,
    confidence_threshold: float,
    enable_multiscale: bool,
    scale_range: tuple[float, float],
    scale_steps: int,
    enable_rotation: bool,
    rotation_range: tuple[float, float],
    rotation_steps: int,
) -> list[Detection]:
    """Advanced template matching with scaling and rotation"""
    detections = []

    # Generate scale factors
    scales = [1.0]  # Always include original scale
    if enable_multiscale:
        min_scale, max_scale = scale_range
        scales = np.linspace(min_scale, max_scale, scale_steps)

    # Generate rotation angles
    angles = [0.0]  # Always include no rotation
    if enable_rotation:
        min_angle, max_angle = rotation_range
        angles = np.linspace(min_angle, max_angle, rotation_steps)

    for scale in scales:
        for angle in angles:
            # Transform template
            transformed_template = _transform_template(template, scale, angle)
            if transformed_template is None:
                continue

            # Perform template matching
            result = cv2.matchTemplate(image, transformed_template, method)

            # Process results and add to detections
            scale_detections = _process_match_result(
                result,
                transformed_template,
                template_name,
                method,
                confidence_threshold,
                scale,
                angle,
            )
            detections.extend(scale_detections)

    return detections


def _process_match_result(
    result: np.ndarray,
    template: np.ndarray,
    template_name: str,
    method: int,
    confidence_threshold: float,
    scale: float,
    angle: float,
) -> list[Detection]:
    """Process template matching result and create Detection objects"""
    # Handle different method types for thresholding
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        # For SQDIFF methods, lower values are better matches
        locations = np.where(result <= (1.0 - confidence_threshold))
        confidences = 1.0 - result[locations]
    else:
        # For other methods, higher values are better matches
        locations = np.where(result >= confidence_threshold)
        confidences = result[locations]

    detections = []
    template_h, template_w = template.shape[:2]

    for pt, conf in zip(zip(*locations[::-1], strict=False), confidences, strict=False):
        x1, y1 = pt
        x2, y2 = x1 + template_w, y1 + template_h
        center = (x1 + template_w // 2, y1 + template_h // 2)
        area = template_w * template_h

        detection = Detection(
            template_name=template_name,
            confidence=float(conf),
            bbox=(x1, y1, x2, y2),
            center=center,
            area=area,
            scale=scale,
            angle=angle,
            method=_get_method_name(method),
        )
        detections.append(detection)

    return detections


def _transform_template(template: np.ndarray, scale: float, angle: float) -> np.ndarray | None:
    """Transform template with scaling and rotation"""
    h, w = template.shape[:2]

    # Scale template
    if scale != 1.0:
        new_w, new_h = int(w * scale), int(h * scale)
        if new_w < 1 or new_h < 1:
            return None
        template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        h, w = new_h, new_w

    # Rotate template
    if angle != 0.0:
        # Calculate rotation matrix
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        # Calculate new dimensions to contain rotated image
        cos_a, sin_a = abs(rotation_matrix[0, 0]), abs(rotation_matrix[0, 1])
        new_w = int((h * sin_a) + (w * cos_a))
        new_h = int((h * cos_a) + (w * sin_a))

        # Adjust the rotation matrix to account for translation
        rotation_matrix[0, 2] += (new_w / 2) - center[0]
        rotation_matrix[1, 2] += (new_h / 2) - center[1]

        # Apply rotation
        template = cv2.warpAffine(
            template,
            rotation_matrix,
            (new_w, new_h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0),
        )

    return template


def _calculate_iou(box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]) -> float:
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


def _get_method_name(method: int) -> str:
    """Get method name from OpenCV constant"""
    method_names = {
        cv2.TM_CCOEFF: "TM_CCOEFF",
        cv2.TM_CCOEFF_NORMED: "TM_CCOEFF_NORMED",
        cv2.TM_CCORR: "TM_CCORR",
        cv2.TM_CCORR_NORMED: "TM_CCORR_NORMED",
        cv2.TM_SQDIFF: "TM_SQDIFF",
        cv2.TM_SQDIFF_NORMED: "TM_SQDIFF_NORMED",
    }
    return method_names.get(method, "UNKNOWN")


def _normalize_template_sources(
    template_sources: TemplateSource | list[TemplateSource] | np.ndarray,
    template_name: str,
    template_manager: TemplateManager,
) -> list[TemplateSource]:
    """Normalize template_sources parameter to list of TemplateSource objects"""
    if isinstance(template_sources, TemplateSource):
        return [template_sources]

    elif isinstance(template_sources, list):
        # Check if it's a list of TemplateSource objects
        if template_sources and all(isinstance(ts, TemplateSource) for ts in template_sources):
            return template_sources
        elif not template_sources:
            return []
        else:
            raise ValueError(
                f"List contains non-TemplateSource objects: {[type(ts) for ts in template_sources]}"
            )

    elif isinstance(template_sources, np.ndarray):
        # Backward compatibility: create TemplateSource from numpy array
        template_source = TemplateSource(
            strategy=TemplateStrategy.BASE64,
            template=template_sources,
            metadata={
                "name": template_name,
                "source": "numpy_array",
                "size": template_sources.shape,
            },
        )
        return [template_source]

    else:
        raise ValueError(f"Unsupported template_sources type: {type(template_sources)}")


def _detect_single_template(
    image_gray: np.ndarray,
    template_source: TemplateSource,
    method: str,
    confidence_threshold: float,
    enable_multiscale: bool,
    scale_range: tuple[float, float],
    scale_steps: int,
    enable_rotation: bool,
    rotation_range: tuple[float, float],
    rotation_steps: int,
) -> list[Detection]:
    """Detect using single template"""
    template = template_source.template
    template_name = template_source.metadata.get("name", "template")

    # Convert template to grayscale
    template_gray = (
        cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(template.shape) == 3 else template
    )

    # Auto-select best method or use specified method
    if method == "auto":
        method = _select_best_method(image_gray, template_gray)

    # Get OpenCV method constant
    cv_method = TemplateMatchingMethods.get_method_by_name(method)

    if enable_multiscale or enable_rotation:
        detections = _advanced_template_matching(
            image_gray,
            template_gray,
            template_name,
            cv_method,
            confidence_threshold,
            enable_multiscale,
            scale_range,
            scale_steps,
            enable_rotation,
            rotation_range,
            rotation_steps,
        )
    else:
        detections = _basic_template_matching(
            image_gray, template_gray, template_name, cv_method, confidence_threshold
        )

    # Add template source info to detections
    for detection in detections:
        detection.template_source = template_source
        detection.template_match_method = "single"
        detection.template_confidence = template_source.confidence_weight

    return detections


def _detect_multi_template(
    image_gray: np.ndarray,
    template_sources: list[TemplateSource],
    method: str,
    confidence_threshold: float,
    enable_multiscale: bool,
    scale_range: tuple[float, float],
    scale_steps: int,
    enable_rotation: bool,
    rotation_range: tuple[float, float],
    rotation_steps: int,
) -> list[Detection]:
    """Detect using multiple templates"""
    all_detections = []

    for template_source in template_sources:
        # Get detections for this template
        template_detections = _detect_single_template(
            image_gray,
            template_source,
            method,
            confidence_threshold * template_source.confidence_weight,  # Weight the threshold
            enable_multiscale,
            scale_range,
            scale_steps,
            enable_rotation,
            rotation_range,
            rotation_steps,
        )

        # Apply template confidence weighting
        for detection in template_detections:
            detection.confidence *= template_source.confidence_weight
            detection.template_match_method = "multi"

        all_detections.extend(template_detections)

    return all_detections


def _apply_cross_template_nms(detections: list[Detection], iou_threshold: float) -> list[Detection]:
    """Apply Non-Maximum Suppression across multiple templates"""
    if not detections:
        return detections

    # Sort by confidence
    detections.sort(key=lambda x: x.confidence, reverse=True)

    filtered_detections = []

    for detection in detections:
        # Check if this detection overlaps significantly with any kept detection
        keep = True
        for kept_detection in filtered_detections:
            if _calculate_iou(detection.bbox, kept_detection.bbox) > iou_threshold:
                keep = False
                break

        if keep:
            filtered_detections.append(detection)

    return filtered_detections


def draw_detections(image: np.ndarray, detections: list[Detection]) -> np.ndarray:
    """
    Draw detection bounding boxes on image

    Args:
        image: Input image
        detections: List of detections to draw

    Returns:
        Image with drawn bounding boxes
    """
    result_image = image.copy()

    for detection in detections:
        x1, y1, x2, y2 = detection.bbox

        # Draw bounding box
        cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw center point
        cv2.circle(result_image, detection.center, 3, (0, 0, 255), -1)

        # Create label with template name, confidence, scale, and angle
        label = f"{detection.template_name}: {detection.confidence:.2f}"
        if detection.scale != 1.0:
            label += f" s:{detection.scale:.2f}"
        if detection.angle != 0.0:
            label += f" a:{detection.angle:.1f}°"

        # Draw label background
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        cv2.rectangle(
            result_image,
            (x1, y1 - label_size[1] - 10),
            (x1 + label_size[0], y1),
            (0, 255, 0),
            -1,
        )

        # Draw label text
        cv2.putText(result_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    return result_image
