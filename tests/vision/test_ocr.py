"""Unit tests for OCR text detection functionality."""

from unittest.mock import MagicMock, patch

import cv2
import numpy as np

from src.vision.ocr import (
    TEXT_MAP,
    _text_similarity,
    add_text_mapping,
    find_text_by_ocr,
    get_text_mappings,
)


class TestTextSimilarity:
    """Test text similarity matching function."""

    def test_exact_match(self):
        """Test exact text matching."""
        assert _text_similarity("technology", "technology") is True
        assert _text_similarity("sign in", "sign in") is True

    def test_case_insensitive_match(self):
        """Test case insensitive matching."""
        assert _text_similarity("Technology", "technology") is True
        assert _text_similarity("SIGN IN", "sign in") is True

    def test_partial_match(self):
        """Test partial text matching."""
        assert _text_similarity("Technology Button", "technology") is True
        assert _text_similarity("Click Sign in", "sign in") is True

    def test_fuzzy_word_match(self):
        """Test fuzzy word matching."""
        assert _text_similarity("Virtual Reality", "virtual reality") is True
        assert _text_similarity("Virtual Reality News", "virtual reality") is True
        assert _text_similarity("VR Reality", "virtual reality") is True

    def test_no_match(self):
        """Test cases where text should not match."""
        assert _text_similarity("technology", "science") is False
        assert _text_similarity("sign out", "sign in") is False
        assert _text_similarity("completely different", "technology") is False

    def test_whitespace_normalization(self):
        """Test whitespace handling."""
        assert _text_similarity("  technology  ", "technology") is True
        assert _text_similarity("sign   in", "sign in") is True


class TestTextMapping:
    """Test text mapping functionality."""

    def test_add_text_mapping(self):
        """Test adding new text mappings."""
        original_map = get_text_mappings()

        add_text_mapping("test_button", "Test Button")

        mappings = get_text_mappings()
        assert "test_button" in mappings
        assert mappings["test_button"] == "Test Button"

        # Cleanup - restore original mappings
        TEXT_MAP.clear()
        TEXT_MAP.update(original_map)

    def test_get_text_mappings_returns_copy(self):
        """Test that get_text_mappings returns a copy."""
        mappings = get_text_mappings()
        original_size = len(mappings)

        # Modify the returned dict
        mappings["new_key"] = "new_value"

        # Original should be unchanged
        assert len(get_text_mappings()) == original_size
        assert "new_key" not in get_text_mappings()


class TestFindTextByOCR:
    """Test OCR text detection functionality."""

    def create_test_image(self, text: str = "Technology") -> bytes:
        """Create a test image with text and return as PNG bytes."""
        # Create a white background image
        img = np.ones((100, 300, 3), dtype=np.uint8) * 255

        # Add text in black
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        color = (0, 0, 0)  # Black
        thickness = 2

        # Get text size to center it
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (img.shape[1] - text_size[0]) // 2
        text_y = (img.shape[0] + text_size[1]) // 2

        cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness)

        # Convert to PNG bytes
        _, png_bytes = cv2.imencode(".png", img)
        return png_bytes.tobytes()

    def test_query_not_in_text_map(self):
        """Test OCR with query not in TEXT_MAP."""
        png_bytes = self.create_test_image()
        result = find_text_by_ocr(png_bytes, "unknown_query")
        assert result is None

    @patch("src.vision.ocr.PaddleOCR")
    def test_ocr_initialization(self, mock_paddle_ocr):
        """Test OCR instance initialization."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance

        # Mock successful OCR result
        mock_result = MagicMock()
        mock_result.rec_texts = ["Technology"]
        mock_result.rec_scores = [0.95]
        mock_result.rec_polys = [np.array([[10, 10], [100, 10], [100, 30], [10, 30]])]
        mock_ocr_instance.predict.return_value = [mock_result]

        png_bytes = self.create_test_image("Technology")
        result = find_text_by_ocr(png_bytes, "google_news_tech_button")

        # Verify OCR was initialized correctly
        mock_paddle_ocr.assert_called_once_with(use_textline_orientation=True, lang="en")
        assert result is not None

    @patch("src.vision.ocr.PaddleOCR")
    def test_successful_text_detection(self, mock_paddle_ocr):
        """Test successful OCR text detection."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance

        # Mock successful OCR result
        mock_result = MagicMock()
        mock_result.rec_texts = ["Technology"]
        mock_result.rec_scores = [0.95]
        mock_result.rec_polys = [np.array([[10, 10], [100, 10], [100, 30], [10, 30]])]
        mock_ocr_instance.predict.return_value = [mock_result]

        png_bytes = self.create_test_image("Technology")
        result = find_text_by_ocr(png_bytes, "google_news_tech_button")

        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    @patch("src.vision.ocr.PaddleOCR")
    def test_low_confidence_text_ignored(self, mock_paddle_ocr):
        """Test that low confidence text is ignored."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance

        # Mock low confidence OCR result
        mock_result = MagicMock()
        mock_result.rec_texts = ["Technology"]
        mock_result.rec_scores = [0.5]  # Below 0.7 threshold
        mock_result.rec_polys = [np.array([[10, 10], [100, 10], [100, 30], [10, 30]])]
        mock_ocr_instance.predict.return_value = [mock_result]

        png_bytes = self.create_test_image("Technology")
        result = find_text_by_ocr(png_bytes, "google_news_tech_button")

        assert result is None

    @patch("src.vision.ocr.PaddleOCR")
    def test_no_matching_text(self, mock_paddle_ocr):
        """Test when OCR finds text but it doesn't match target."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance

        # Mock OCR result with different text
        mock_result = MagicMock()
        mock_result.rec_texts = ["Different Text"]
        mock_result.rec_scores = [0.95]
        mock_result.rec_polys = [np.array([[10, 10], [100, 10], [100, 30], [10, 30]])]
        mock_ocr_instance.predict.return_value = [mock_result]

        png_bytes = self.create_test_image("Different Text")
        result = find_text_by_ocr(png_bytes, "google_news_tech_button")

        assert result is None

    @patch("src.vision.ocr.PaddleOCR")
    def test_ocr_exception_handling(self, mock_paddle_ocr):
        """Test OCR exception handling."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance
        mock_ocr_instance.predict.side_effect = Exception("OCR Error")

        png_bytes = self.create_test_image()
        result = find_text_by_ocr(png_bytes, "google_news_tech_button")

        assert result is None

    @patch("src.vision.ocr.PaddleOCR")
    def test_empty_ocr_results(self, mock_paddle_ocr):
        """Test handling of empty OCR results."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance
        mock_ocr_instance.predict.return_value = []

        png_bytes = self.create_test_image()
        result = find_text_by_ocr(png_bytes, "google_news_tech_button")

        assert result is None

    @patch("src.vision.ocr.PaddleOCR")
    def test_invalid_image_data(self, mock_paddle_ocr):
        """Test handling of invalid image data."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance

        # Invalid PNG bytes
        invalid_bytes = b"invalid image data"
        result = find_text_by_ocr(invalid_bytes, "google_news_tech_button")

        assert result is None

    @patch("src.vision.ocr.PaddleOCR")
    def test_multiple_text_detections(self, mock_paddle_ocr):
        """Test handling multiple text detections."""
        mock_ocr_instance = MagicMock()
        mock_paddle_ocr.return_value = mock_ocr_instance

        # Mock multiple OCR results, first one doesn't match, second one does
        mock_result = MagicMock()
        mock_result.rec_texts = ["Other Text", "Technology"]
        mock_result.rec_scores = [0.8, 0.95]
        mock_result.rec_polys = [
            np.array([[10, 10], [80, 10], [80, 30], [10, 30]]),
            np.array([[90, 10], [180, 10], [180, 30], [90, 30]]),
        ]
        mock_ocr_instance.predict.return_value = [mock_result]

        png_bytes = self.create_test_image("Technology")
        result = find_text_by_ocr(png_bytes, "google_news_tech_button")

        assert result is not None
        # Should return center coordinates of the matching text (Technology)
        assert result == (135, 20)  # Center of second polygon

    def test_center_coordinate_calculation(self):
        """Test center coordinate calculation from polygon."""
        # This is tested implicitly in other tests, but we can verify the math
        # For polygon [[10, 10], [100, 10], [100, 30], [10, 30]]
        # Center should be ((10+100+100+10)/4, (10+10+30+30)/4) = (55, 20)
        poly = np.array([[10, 10], [100, 10], [100, 30], [10, 30]])
        center_x = int(np.mean(poly[:, 0]))
        center_y = int(np.mean(poly[:, 1]))

        assert center_x == 55
        assert center_y == 20


class TestTextMapDefaults:
    """Test default TEXT_MAP contents."""

    def test_default_text_mappings_exist(self):
        """Test that expected default mappings exist."""
        mappings = get_text_mappings()

        expected_mappings = {
            "google_news_tech_button": "Technology",
            "google_news_virtual_reality_button": "Virtual Reality",
            "google_news_sign_in_button": "Sign in",
            "google_news_next_button": "Next",
        }

        for key, value in expected_mappings.items():
            assert key in mappings
            assert mappings[key] == value
