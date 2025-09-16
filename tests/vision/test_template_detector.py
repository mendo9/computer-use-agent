"""
Unit tests for template detection module.
"""

from unittest.mock import Mock, patch

import cv2
import numpy as np
import pytest

from src.vision.template_detector import (
    Detection,
    TemplateMatchingMethods,
    _advanced_template_matching,
    _apply_cross_template_nms,
    _basic_template_matching,
    _calculate_iou,
    _get_method_name,
    _normalize_template_sources,
    _select_best_method,
    _transform_template,
    detect_ui_elements,
    draw_detections,
)
from src.vision.template_manager import TemplateSource, TemplateStrategy


class TestDetection:
    """Tests for Detection dataclass."""

    def test_detection_creation(self):
        """Test Detection object creation with required fields."""
        detection = Detection(
            template_name="test",
            confidence=0.85,
            bbox=(10, 20, 30, 40),
            center=(20, 30),
            area=400,
        )

        assert detection.template_name == "test"
        assert detection.confidence == 0.85
        assert detection.bbox == (10, 20, 30, 40)
        assert detection.center == (20, 30)
        assert detection.area == 400
        assert detection.scale == 1.0  # default
        assert detection.angle == 0.0  # default

    def test_detection_with_optional_fields(self):
        """Test Detection with optional fields."""
        template_source = Mock()
        detection = Detection(
            template_name="test",
            confidence=0.85,
            bbox=(10, 20, 30, 40),
            center=(20, 30),
            area=400,
            scale=1.5,
            angle=15.0,
            template_source=template_source,
            template_match_method="multi",
        )

        assert detection.scale == 1.5
        assert detection.angle == 15.0
        assert detection.template_source == template_source
        assert detection.template_match_method == "multi"


class TestTemplateMatchingMethods:
    """Tests for TemplateMatchingMethods class."""

    def test_get_method_by_name_valid(self):
        """Test getting valid method constants."""
        assert (
            TemplateMatchingMethods.get_method_by_name("TM_CCOEFF_NORMED") == cv2.TM_CCOEFF_NORMED
        )
        assert TemplateMatchingMethods.get_method_by_name("TM_SQDIFF") == cv2.TM_SQDIFF

    def test_get_method_by_name_invalid(self):
        """Test getting method with invalid name returns default."""
        result = TemplateMatchingMethods.get_method_by_name("INVALID_METHOD")
        assert result == cv2.TM_CCOEFF_NORMED

    def test_all_methods_exist(self):
        """Test all method constants are accessible."""
        assert hasattr(TemplateMatchingMethods, "TM_CCOEFF")
        assert hasattr(TemplateMatchingMethods, "TM_CCOEFF_NORMED")
        assert hasattr(TemplateMatchingMethods, "TM_SQDIFF_NORMED")


class TestSelectBestMethod:
    """Tests for _select_best_method function."""

    def test_low_variance_template(self):
        """Test method selection for low variance template."""
        image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        template = np.full((20, 20), 128, dtype=np.uint8)  # Solid color, low variance

        method = _select_best_method(image, template)
        assert method == "TM_SQDIFF_NORMED"

    def test_high_variance_difference(self):
        """Test method selection for high variance difference."""
        image = np.random.randint(0, 10, (100, 100), dtype=np.uint8)  # Low variance
        template = np.random.randint(0, 255, (20, 20), dtype=np.uint8)  # High variance

        method = _select_best_method(image, template)
        assert method == "TM_CCOEFF_NORMED"

    def test_default_method(self):
        """Test default method selection."""
        image = np.random.randint(100, 150, (100, 100), dtype=np.uint8)
        template = np.random.randint(100, 150, (20, 20), dtype=np.uint8)

        method = _select_best_method(image, template)
        assert method == "TM_CCOEFF_NORMED"


class TestBasicTemplateMatching:
    """Tests for _basic_template_matching function."""

    @patch("cv2.matchTemplate")
    def test_basic_matching_success(self, mock_match):
        """Test basic template matching with matches above threshold."""
        # Mock matchTemplate result with high confidence match
        mock_result = np.array([[0.9, 0.7], [0.6, 0.85]])
        mock_match.return_value = mock_result

        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((20, 20), dtype=np.uint8)

        detections = _basic_template_matching(image, template, "test", cv2.TM_CCOEFF_NORMED, 0.8)

        assert len(detections) == 2  # Two matches above threshold
        assert all(d.confidence >= 0.8 for d in detections)
        assert all(d.template_name == "test" for d in detections)

    @patch("cv2.matchTemplate")
    def test_basic_matching_no_matches(self, mock_match):
        """Test basic template matching with no matches above threshold."""
        mock_result = np.array([[0.5, 0.6], [0.4, 0.7]])  # All below 0.8 threshold
        mock_match.return_value = mock_result

        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((20, 20), dtype=np.uint8)

        detections = _basic_template_matching(image, template, "test", cv2.TM_CCOEFF_NORMED, 0.8)

        assert len(detections) == 0

    @patch("cv2.matchTemplate")
    def test_sqdiff_method_handling(self, mock_match):
        """Test SQDIFF method with inverted threshold logic."""
        mock_result = np.array([[0.1, 0.3], [0.25, 0.05]])  # Low values = good matches for SQDIFF
        mock_match.return_value = mock_result

        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((20, 20), dtype=np.uint8)

        detections = _basic_template_matching(image, template, "test", cv2.TM_SQDIFF_NORMED, 0.8)

        # Should find matches where result <= (1.0 - 0.8) = 0.2
        assert len(detections) == 2
        # Confidence should be inverted: 1.0 - original_value
        assert any(d.confidence > 0.9 for d in detections)  # 1.0 - 0.05 = 0.95


class TestAdvancedTemplateMatching:
    """Tests for _advanced_template_matching function."""

    @patch("src.vision.template_detector._transform_template")
    @patch("cv2.matchTemplate")
    def test_multiscale_matching(self, mock_match, mock_transform):
        """Test multi-scale template matching."""
        mock_result = np.array([[0.9]])
        mock_match.return_value = mock_result
        mock_transform.side_effect = lambda t, s, a: np.ones(
            (int(20 * s), int(20 * s)), dtype=np.uint8
        )

        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((20, 20), dtype=np.uint8)

        detections = _advanced_template_matching(
            image,
            template,
            "test",
            cv2.TM_CCOEFF_NORMED,
            0.8,
            enable_multiscale=True,
            scale_range=(0.8, 1.2),
            scale_steps=3,
            enable_rotation=False,
            rotation_range=(-10, 10),
            rotation_steps=3,
        )

        # Should have detections for each scale (3 scales)
        assert len(detections) >= 3
        assert mock_transform.call_count >= 3

    @patch("src.vision.template_detector._transform_template")
    @patch("cv2.matchTemplate")
    def test_rotation_matching(self, mock_match, mock_transform):
        """Test rotation-invariant template matching."""
        mock_result = np.array([[0.9]])
        mock_match.return_value = mock_result
        mock_transform.side_effect = lambda t, s, a: np.ones(
            (25, 25), dtype=np.uint8
        )  # Slightly larger after rotation

        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((20, 20), dtype=np.uint8)

        detections = _advanced_template_matching(
            image,
            template,
            "test",
            cv2.TM_CCOEFF_NORMED,
            0.8,
            enable_multiscale=False,
            scale_range=(1.0, 1.0),
            scale_steps=1,
            enable_rotation=True,
            rotation_range=(-15, 15),
            rotation_steps=4,
        )

        # Should have detections for each rotation angle (4 angles)
        assert len(detections) >= 4

    @patch("src.vision.template_detector._transform_template")
    def test_invalid_transform_handling(self, mock_transform):
        """Test handling of invalid template transforms."""
        mock_transform.return_value = None  # Simulate failed transform

        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((20, 20), dtype=np.uint8)

        detections = _advanced_template_matching(
            image,
            template,
            "test",
            cv2.TM_CCOEFF_NORMED,
            0.8,
            enable_multiscale=True,
            scale_range=(0.1, 0.2),
            scale_steps=2,  # Very small scales
            enable_rotation=False,
            rotation_range=(0, 0),
            rotation_steps=1,
        )

        assert len(detections) == 0  # No valid transforms


class TestTransformTemplate:
    """Tests for _transform_template function."""

    def test_no_transform(self):
        """Test template with no scaling or rotation."""
        template = np.ones((20, 30), dtype=np.uint8)
        result = _transform_template(template, 1.0, 0.0)

        assert np.array_equal(result, template)
        assert result.shape == (20, 30)

    def test_scaling_only(self):
        """Test template scaling."""
        template = np.ones((20, 20), dtype=np.uint8)
        result = _transform_template(template, 2.0, 0.0)

        assert result is not None
        assert result.shape == (40, 40)

    def test_invalid_scaling(self):
        """Test handling of invalid scaling."""
        template = np.ones((20, 20), dtype=np.uint8)
        result = _transform_template(template, 0.01, 0.0)  # Too small

        assert result is None

    def test_rotation_only(self):
        """Test template rotation."""
        template = np.ones((20, 20), dtype=np.uint8)
        result = _transform_template(template, 1.0, 45.0)

        assert result is not None
        # Rotated template should be larger due to bounding box
        assert result.shape[0] > 20 or result.shape[1] > 20

    def test_combined_transform(self):
        """Test combined scaling and rotation."""
        template = np.ones((20, 20), dtype=np.uint8)
        result = _transform_template(template, 1.5, 30.0)

        assert result is not None
        assert result.shape != (20, 20)


class TestCalculateIOU:
    """Tests for _calculate_iou function."""

    def test_no_overlap(self):
        """Test boxes with no overlap."""
        box1 = (0, 0, 10, 10)
        box2 = (20, 20, 30, 30)
        iou = _calculate_iou(box1, box2)
        assert iou == 0.0

    def test_complete_overlap(self):
        """Test identical boxes."""
        box1 = (10, 10, 20, 20)
        box2 = (10, 10, 20, 20)
        iou = _calculate_iou(box1, box2)
        assert iou == 1.0

    def test_partial_overlap(self):
        """Test boxes with partial overlap."""
        box1 = (0, 0, 20, 20)  # Area: 400
        box2 = (10, 10, 30, 30)  # Area: 400, Intersection: 100
        iou = _calculate_iou(box1, box2)
        # Union = 400 + 400 - 100 = 700, IoU = 100/700 ≈ 0.143
        assert abs(iou - (100 / 700)) < 0.001

    def test_contained_box(self):
        """Test one box contained in another."""
        box1 = (5, 5, 15, 15)  # Area: 100
        box2 = (0, 0, 20, 20)  # Area: 400
        iou = _calculate_iou(box1, box2)
        # Intersection = 100, Union = 400, IoU = 100/400 = 0.25
        assert abs(iou - 0.25) < 0.001


class TestGetMethodName:
    """Tests for _get_method_name function."""

    def test_known_methods(self):
        """Test getting names for known methods."""
        assert _get_method_name(cv2.TM_CCOEFF_NORMED) == "TM_CCOEFF_NORMED"
        assert _get_method_name(cv2.TM_SQDIFF) == "TM_SQDIFF"

    def test_unknown_method(self):
        """Test handling unknown method."""
        assert _get_method_name(999) == "UNKNOWN"


class TestNormalizeTemplateSources:
    """Tests for _normalize_template_sources function."""

    def test_single_template_source(self):
        """Test normalizing single TemplateSource."""
        template = np.ones((20, 20), dtype=np.uint8)
        source = TemplateSource(TemplateStrategy.BASE64, template)
        mock_manager = Mock()

        result = _normalize_template_sources(source, "test", mock_manager)
        assert len(result) == 1
        assert result[0] == source

    def test_list_template_sources(self):
        """Test normalizing list of TemplateSource objects."""
        template1 = np.ones((20, 20), dtype=np.uint8)
        template2 = np.ones((30, 30), dtype=np.uint8)
        sources = [
            TemplateSource(TemplateStrategy.BASE64, template1),
            TemplateSource(TemplateStrategy.LIBRARY, template2),
        ]
        mock_manager = Mock()

        result = _normalize_template_sources(sources, "test", mock_manager)
        assert len(result) == 2
        assert result == sources

    def test_numpy_array_backward_compatibility(self):
        """Test backward compatibility with numpy array."""
        template = np.ones((20, 20), dtype=np.uint8)
        mock_manager = Mock()

        result = _normalize_template_sources(template, "test_name", mock_manager)
        assert len(result) == 1
        assert result[0].strategy == TemplateStrategy.BASE64
        assert np.array_equal(result[0].template, template)
        assert result[0].metadata["name"] == "test_name"

    def test_invalid_list_contents(self):
        """Test error handling for invalid list contents."""
        invalid_list = ["not_a_template_source", 123]
        mock_manager = Mock()

        with pytest.raises(ValueError, match="List contains non-TemplateSource objects"):
            _normalize_template_sources(invalid_list, "test", mock_manager)

    def test_unsupported_type(self):
        """Test error handling for unsupported types."""
        mock_manager = Mock()

        with pytest.raises(ValueError, match="Unsupported template_sources type"):
            _normalize_template_sources("invalid_type", "test", mock_manager)


class TestApplyCrossTemplateNMS:
    """Tests for _apply_cross_template_nms function."""

    def test_empty_detections(self):
        """Test NMS with empty detection list."""
        result = _apply_cross_template_nms([], 0.5)
        assert result == []

    def test_no_overlap_detections(self):
        """Test NMS with non-overlapping detections."""
        detections = [
            Detection("test1", 0.9, (0, 0, 10, 10), (5, 5), 100),
            Detection("test2", 0.8, (20, 20, 30, 30), (25, 25), 100),
        ]

        result = _apply_cross_template_nms(detections, 0.3)
        assert len(result) == 2  # Both should be kept

    def test_overlapping_detections(self):
        """Test NMS with overlapping detections."""
        detections = [
            Detection("test1", 0.9, (0, 0, 20, 20), (10, 10), 400),  # High confidence
            Detection("test2", 0.7, (5, 5, 25, 25), (15, 15), 400),  # Lower confidence, overlaps
        ]

        result = _apply_cross_template_nms(detections, 0.2)  # Low threshold = strict NMS
        assert len(result) == 1  # Only highest confidence should remain
        assert result[0].template_name == "test1"

    def test_confidence_sorting(self):
        """Test that detections are sorted by confidence."""
        detections = [
            Detection("low", 0.6, (0, 0, 10, 10), (5, 5), 100),
            Detection("high", 0.9, (20, 20, 30, 30), (25, 25), 100),
            Detection("medium", 0.75, (40, 40, 50, 50), (45, 45), 100),
        ]

        result = _apply_cross_template_nms(detections, 0.1)  # No overlap expected
        assert len(result) == 3
        # Should be sorted by confidence descending
        confidences = [d.confidence for d in result]
        assert confidences == sorted(confidences, reverse=True)


class TestDetectUIElements:
    """Tests for main detect_ui_elements function."""

    def test_empty_image(self):
        """Test handling of None image."""
        result = detect_ui_elements(None, [])
        assert result == []

    @patch("src.vision.template_detector.get_template_manager")
    @patch("src.vision.template_detector._normalize_template_sources")
    def test_no_templates(self, mock_normalize, mock_get_manager):
        """Test handling when no templates are provided."""
        mock_normalize.return_value = []
        mock_get_manager.return_value = Mock()

        image = np.ones((100, 100, 3), dtype=np.uint8)
        result = detect_ui_elements(image, [])

        assert result == []

    @patch("src.vision.template_detector._detect_single_template")
    @patch("src.vision.template_detector._normalize_template_sources")
    @patch("src.vision.template_detector.get_template_manager")
    def test_single_template_detection(self, mock_get_manager, mock_normalize, mock_detect_single):
        """Test detection with single template."""
        # Mock setup
        template = np.ones((20, 20), dtype=np.uint8)
        template_source = TemplateSource(TemplateStrategy.BASE64, template)
        mock_normalize.return_value = [template_source]
        mock_get_manager.return_value = Mock()

        mock_detection = Detection("test", 0.9, (10, 10, 30, 30), (20, 20), 400)
        mock_detect_single.return_value = [mock_detection]

        image = np.ones((100, 100, 3), dtype=np.uint8)
        result = detect_ui_elements(image, template_source)

        assert len(result) == 1
        assert result[0] == mock_detection
        mock_detect_single.assert_called_once()

    @patch("src.vision.template_detector._detect_multi_template")
    @patch("src.vision.template_detector._normalize_template_sources")
    @patch("src.vision.template_detector.get_template_manager")
    def test_multi_template_detection(self, mock_get_manager, mock_normalize, mock_detect_multi):
        """Test detection with multiple templates."""
        # Mock setup
        template1 = np.ones((20, 20), dtype=np.uint8)
        template2 = np.ones((30, 30), dtype=np.uint8)
        sources = [
            TemplateSource(TemplateStrategy.BASE64, template1),
            TemplateSource(TemplateStrategy.BASE64, template2),
        ]
        mock_normalize.return_value = sources
        mock_get_manager.return_value = Mock()

        mock_detections = [
            Detection("test1", 0.9, (10, 10, 30, 30), (20, 20), 400),
            Detection("test2", 0.8, (50, 50, 80, 80), (65, 65), 900),
        ]
        mock_detect_multi.return_value = mock_detections

        image = np.ones((100, 100, 3), dtype=np.uint8)
        result = detect_ui_elements(image, sources)

        assert len(result) == 2
        mock_detect_multi.assert_called_once()

    @patch("src.vision.template_detector._detect_single_template")
    @patch("src.vision.template_detector._normalize_template_sources")
    @patch("src.vision.template_detector.get_template_manager")
    def test_max_detections_limit(self, mock_get_manager, mock_normalize, mock_detect_single):
        """Test that max_detections parameter limits results."""
        template = np.ones((20, 20), dtype=np.uint8)
        template_source = TemplateSource(TemplateStrategy.BASE64, template)
        mock_normalize.return_value = [template_source]
        mock_get_manager.return_value = Mock()

        # Return more detections than max_detections limit
        mock_detections = [
            Detection(
                f"test{i}",
                0.9 - i * 0.1,
                (i * 10, i * 10, (i + 1) * 10, (i + 1) * 10),
                (i * 10 + 5, i * 10 + 5),
                100,
            )
            for i in range(5)
        ]
        mock_detect_single.return_value = mock_detections

        image = np.ones((100, 100, 3), dtype=np.uint8)
        result = detect_ui_elements(image, template_source, max_detections=3)

        assert len(result) == 3
        # Should return the highest confidence detections
        assert all(result[i].confidence >= result[i + 1].confidence for i in range(len(result) - 1))


class TestDrawDetections:
    """Tests for draw_detections function."""

    def test_empty_detections(self):
        """Test drawing with no detections."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        result = draw_detections(image, [])

        # Should return copy of original image
        assert result.shape == image.shape
        assert not np.array_equal(result, image)  # Should be a copy

    @patch("cv2.rectangle")
    @patch("cv2.circle")
    @patch("cv2.putText")
    @patch("cv2.getTextSize")
    def test_draw_single_detection(
        self, mock_get_text_size, mock_put_text, mock_circle, mock_rectangle
    ):
        """Test drawing single detection."""
        mock_get_text_size.return_value = ((100, 20), 0)  # (width, height), baseline

        image = np.zeros((200, 200, 3), dtype=np.uint8)
        detection = Detection(
            "test_button", 0.85, (10, 20, 50, 60), (30, 40), 1600, scale=1.2, angle=15.0
        )

        result = draw_detections(image, [detection])

        # Verify OpenCV functions were called
        mock_rectangle.assert_called()  # Bounding box and label background
        mock_circle.assert_called_once()  # Center point
        mock_put_text.assert_called_once()  # Label text

        # Check that label includes name, confidence, scale, and angle
        label_call = mock_put_text.call_args[0][1]  # Second argument is the text
        assert "test_button" in label_call
        assert "0.85" in label_call
        assert "1.20" in label_call
        assert "15.0" in label_call

    def test_draw_multiple_detections(self):
        """Test drawing multiple detections."""
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        detections = [
            Detection("button1", 0.9, (10, 10, 30, 30), (20, 20), 400),
            Detection("button2", 0.8, (50, 50, 70, 70), (60, 60), 400),
        ]

        result = draw_detections(image, detections)

        # Should return modified image
        assert result.shape == image.shape
        # Image should be modified (not equal to original black image)
        assert not np.array_equal(result, image)


if __name__ == "__main__":
    pytest.main([__file__])
