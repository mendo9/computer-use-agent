"""
Unit tests for vision finder module.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np
import pytest

from src.vision.finder import (
    CONFIDENCE_THRESHOLD,
    TEMPLATE_MAP,
    TEMPLATES_PATH,
    _find_by_template_matching,
    _get_template_info,
    find_target_center,
)


class TestPngBytesToImage:
    """Tests for PNG bytes to image conversion (handled by cv2.imdecode)."""

    def test_valid_png_bytes_conversion(self):
        """Test converting valid PNG bytes to image using cv2.imdecode."""
        # Create a simple test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[40:60, 40:60] = [255, 255, 255]  # White square

        # Encode to PNG bytes
        _, buffer = cv2.imencode(".png", test_image)
        png_bytes = buffer.tobytes()

        # Test cv2 decoding (this is what finder.py uses)
        nparr = np.frombuffer(png_bytes, np.uint8)
        result = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        assert result is not None
        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)

    def test_invalid_png_bytes_handling(self):
        """Test handling invalid PNG bytes with cv2.imdecode."""
        invalid_bytes = b"not a png"
        nparr = np.frombuffer(invalid_bytes, np.uint8)
        result = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        assert result is None


class TestGetTemplateInfo:
    """Tests for _get_template_info function."""

    def test_mapped_query(self):
        """Test getting info for mapped queries."""
        name, category = _get_template_info("safari")
        assert name == "safari_icon"
        assert category == "macos_dock"

    def test_case_insensitive(self):
        """Test case insensitive mapping."""
        name, category = _get_template_info("SAFARI")
        assert name == "safari_icon"
        assert category == "macos_dock"

    def test_unmapped_query(self):
        """Test getting info for unmapped queries."""
        name, category = _get_template_info("unknown_app")
        assert name == "unknown_app"
        assert category == "common"

    def test_empty_query(self):
        """Test handling empty query."""
        name, category = _get_template_info("")
        assert name == ""
        assert category == "common"


class TestFindByTemplateMatching:
    """Tests for _find_by_template_matching function."""

    @patch("src.vision.finder.detect_ui_elements")
    @patch("src.vision.finder.TemplateManager")
    @patch("cv2.imdecode")
    def test_successful_find(self, mock_imdecode, mock_template_manager, mock_detect_ui_elements):
        """Test successful element finding with new template system."""
        # Setup mocks
        mock_image = np.ones((100, 100, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image

        mock_manager_instance = Mock()
        mock_template_manager.return_value = mock_manager_instance
        mock_manager_instance.resolve_templates.return_value = [Mock()]

        # Mock detection result
        mock_detection = Mock()
        mock_detection.center = (100, 150)
        mock_detect_ui_elements.return_value = [mock_detection]

        result = _find_by_template_matching(b"fake_png", "safari")

        assert result == (100, 150)
        mock_imdecode.assert_called_once()
        mock_template_manager.assert_called_once()
        mock_detect_ui_elements.assert_called_once()

    @patch("cv2.imdecode")
    def test_invalid_image(self, mock_imdecode):
        """Test handling invalid image decode."""
        mock_imdecode.return_value = None

        result = _find_by_template_matching(b"invalid", "safari")
        assert result is None

    @patch("src.vision.finder.detect_ui_elements")
    @patch("src.vision.finder.TemplateManager")
    @patch("cv2.imdecode")
    def test_no_detections(self, mock_imdecode, mock_template_manager, mock_detect_ui_elements):
        """Test handling when no detections are found."""
        mock_image = np.ones((100, 100, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image

        mock_manager_instance = Mock()
        mock_template_manager.return_value = mock_manager_instance
        mock_manager_instance.resolve_templates.return_value = [Mock()]

        # No detections found
        mock_detect_ui_elements.return_value = []

        result = _find_by_template_matching(b"fake_png", "missing")
        assert result is None

    @patch("src.vision.finder.TemplateManager")
    @patch("cv2.imdecode")
    def test_exception_handling(self, mock_imdecode, mock_template_manager):
        """Test exception handling in template matching."""
        mock_image = np.ones((100, 100, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image

        # Mock template manager to raise exception
        mock_template_manager.side_effect = Exception("Template error")

        result = _find_by_template_matching(b"fake_png", "test")
        assert result is None


class TestFindTargetCenter:
    """Tests for main find_target_center function."""

    @patch("src.vision.finder._find_by_template_matching")
    def test_template_matching_success(self, mock_template_matching):
        """Test when template matching succeeds."""
        mock_template_matching.return_value = (100, 200)

        result = find_target_center(b"fake_png", "safari")

        assert result == (100, 200)
        mock_template_matching.assert_called_once_with(b"fake_png", "safari")

    @patch("src.vision.finder.find_text_by_ocr")
    @patch("src.vision.finder._find_by_template_matching")
    def test_template_matching_fails_ocr_fallback(self, mock_template_matching, mock_ocr):
        """Test when template matching fails but OCR succeeds."""
        mock_template_matching.return_value = None
        mock_ocr.return_value = (150, 200)

        result = find_target_center(b"fake_png", "google_news_tech_button")

        assert result == (150, 200)
        mock_template_matching.assert_called_once_with(b"fake_png", "google_news_tech_button")
        mock_ocr.assert_called_once_with(b"fake_png", "google_news_tech_button")

    @patch("src.vision.finder.find_text_by_ocr")
    @patch("src.vision.finder._find_by_template_matching")
    def test_template_matching_fails_no_ocr_mapping(self, mock_template_matching, mock_ocr):
        """Test when template matching fails and no OCR mapping exists."""
        mock_template_matching.return_value = None

        result = find_target_center(b"fake_png", "nonexistent")

        assert result is None
        mock_template_matching.assert_called_once_with(b"fake_png", "nonexistent")
        mock_ocr.assert_not_called()

    @patch("src.vision.finder.find_text_by_ocr")
    @patch("src.vision.finder._find_by_template_matching")
    def test_template_matching_fails_ocr_fails(self, mock_template_matching, mock_ocr):
        """Test when both template matching and OCR fail."""
        mock_template_matching.return_value = None
        mock_ocr.return_value = None

        result = find_target_center(b"fake_png", "google_news_tech_button")

        assert result is None
        mock_template_matching.assert_called_once_with(b"fake_png", "google_news_tech_button")
        mock_ocr.assert_called_once_with(b"fake_png", "google_news_tech_button")


class TestConstants:
    """Tests for module constants."""

    def test_templates_path(self):
        """Test TEMPLATES_PATH is correct."""
        assert isinstance(TEMPLATES_PATH, Path)
        assert "vision" in str(TEMPLATES_PATH)
        assert TEMPLATES_PATH.name == "vision"

    def test_template_map(self):
        """Test TEMPLATE_MAP structure."""
        assert isinstance(TEMPLATE_MAP, dict)
        assert "safari" in TEMPLATE_MAP
        assert isinstance(TEMPLATE_MAP["safari"], tuple)
        assert len(TEMPLATE_MAP["safari"]) == 2

    def test_google_news_template_mappings(self):
        """Test Google News template mappings are present."""
        google_news_mappings = {
            "google_news_email_text": ("email_text", "google_news"),
            "google_news_italian_dropdown": ("italian_drp_dwn", "google_news"),
            "google_news_language_dropdown": ("language_drp_dwn", "google_news"),
            "google_news_next_button": ("next_btn", "google_news"),
            "google_news_tech_button": ("technology_btn", "google_news"),
            "google_news_virtual_reality_button": ("virtual_reality_btn", "google_news"),
            "google_news_sign_in_button": ("sign_in_btn", "google_news"),
        }

        for query, expected_mapping in google_news_mappings.items():
            assert query in TEMPLATE_MAP
            assert TEMPLATE_MAP[query] == expected_mapping

    def test_confidence_threshold(self):
        """Test CONFIDENCE_THRESHOLD is reasonable."""
        assert isinstance(CONFIDENCE_THRESHOLD, (int, float))
        assert 0.0 <= CONFIDENCE_THRESHOLD <= 1.0


# Integration tests
class TestIntegration:
    """Integration tests with real images."""

    @pytest.fixture
    def sample_png_bytes(self):
        """Create sample PNG bytes for testing."""
        # Create a simple test image
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[25:75, 25:75] = [100, 150, 200]  # Colored square

        # Encode to PNG
        _, buffer = cv2.imencode(".png", image)
        return buffer.tobytes()

    def test_png_bytes_decode_integration(self, sample_png_bytes):
        """Test PNG bytes decoding integration with cv2."""
        nparr = np.frombuffer(sample_png_bytes, np.uint8)
        result = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        assert result is not None
        assert result.shape == (100, 100, 3)
        # Check the colored square is present
        assert not np.array_equal(result[50, 50], [0, 0, 0])

    @patch("src.vision.finder.detect_ui_elements")
    @patch("src.vision.finder.TemplateManager")
    def test_template_matching_integration(
        self, mock_template_manager, mock_detect_ui_elements, sample_png_bytes
    ):
        """Test template matching integration with new system."""
        # Setup mocks
        mock_manager_instance = Mock()
        mock_template_manager.return_value = mock_manager_instance
        mock_manager_instance.resolve_templates.return_value = [Mock()]

        # Mock a successful detection
        mock_detection = Mock()
        mock_detection.center = (50, 50)
        mock_detect_ui_elements.return_value = [mock_detection]

        # This should find the colored square in our test image
        result = _find_by_template_matching(sample_png_bytes, "test_element")

        assert result == (50, 50)
        mock_template_manager.assert_called_once()
        mock_detect_ui_elements.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
