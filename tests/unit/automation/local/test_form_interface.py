"""Unit tests for automation.local.form_interface module."""

import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from automation.core.types import ActionResult
from automation.local.form_interface import FormFiller


@dataclass
class MockOCRElement:
    """Mock OCR element for testing."""

    text: str
    center: tuple[int, int]
    bbox: tuple[int, int, int, int]
    confidence: float
    description: str = ""


class TestFormFiller:
    """Test cases for FormFiller class."""

    def test_init(self):
        """Test FormFiller initialization."""
        form_filler = FormFiller()

        assert form_filler.desktop is not None
        assert form_filler.last_screenshot is None
        assert form_filler.screenshot_cache_time == 0

    @patch("time.time")
    def test_get_current_screenshot_cache_hit(self, mock_time):
        """Test screenshot caching when cache is fresh."""
        form_filler = FormFiller()

        # Set up cache
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        form_filler.last_screenshot = mock_screenshot
        form_filler.screenshot_cache_time = 1000.0

        # Mock current time to be within cache window
        mock_time.return_value = 1000.5  # 0.5 seconds later, within 1.0s max_age

        # This should return cached screenshot without calling desktop.capture_screen
        result = form_filler._get_current_screenshot(max_age=1.0)

        assert np.array_equal(result, mock_screenshot)

    @patch("time.time")
    def test_get_current_screenshot_cache_miss(self, mock_time):
        """Test screenshot capture when cache is stale."""
        form_filler = FormFiller()

        # Set up stale cache
        old_screenshot = np.zeros((50, 50, 3), dtype=np.uint8)
        form_filler.last_screenshot = old_screenshot
        form_filler.screenshot_cache_time = 1000.0

        # Mock current time to be outside cache window
        mock_time.return_value = 1002.0  # 2 seconds later, outside 1.0s max_age

        # Mock desktop capture
        new_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        form_filler.desktop.capture_screen = Mock(return_value=(True, new_screenshot))

        result = form_filler._get_current_screenshot(max_age=1.0)

        assert np.array_equal(result, new_screenshot)
        assert np.array_equal(form_filler.last_screenshot, new_screenshot)
        assert form_filler.screenshot_cache_time == 1002.0

    def test_get_current_screenshot_capture_fails(self):
        """Test screenshot capture failure."""
        form_filler = FormFiller()

        # Mock desktop capture failure
        form_filler.desktop.capture_screen = Mock(return_value=(False, None))

        result = form_filler._get_current_screenshot()

        assert result is None

    def test_find_field_by_label_success(self):
        """Test successful field finding by label."""
        form_filler = FormFiller()

        # Mock screenshot
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        form_filler._get_current_screenshot = Mock(return_value=mock_screenshot)

        # Mock OCR results
        mock_element = MockOCRElement(
            text="Username",
            center=(100, 50),
            bbox=(50, 40, 150, 60),
            confidence=0.95,
            description="text field label",
        )

        with patch("vision.find_elements_by_text", return_value=[mock_element]):
            result = form_filler.find_field_by_label("Username")

        assert result is not None
        assert result["text"] == "Username"
        assert result["center"] == (100, 50)
        assert result["bbox"] == (50, 40, 150, 60)
        assert result["confidence"] == 0.95
        assert result["description"] == "text field label"

    def test_find_field_by_label_not_found(self):
        """Test field not found by label."""
        form_filler = FormFiller()

        # Mock screenshot
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        form_filler._get_current_screenshot = Mock(return_value=mock_screenshot)

        # Mock empty OCR results
        with patch("automation.local.form_interface.find_elements_by_text", return_value=[]):
            result = form_filler.find_field_by_label("NonexistentField")

        assert result is None

    def test_find_field_by_label_multiple_matches(self):
        """Test field finding with multiple matches (should return best)."""
        form_filler = FormFiller()

        # Mock screenshot
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        form_filler._get_current_screenshot = Mock(return_value=mock_screenshot)

        # Mock multiple OCR results with different confidence
        mock_elements = [
            MockOCRElement("Username", (100, 50), (50, 40, 150, 60), 0.85),
            MockOCRElement("Username", (200, 50), (150, 40, 250, 60), 0.95),  # Best match
            MockOCRElement("Username", (300, 50), (250, 40, 350, 60), 0.75),
        ]

        with patch("vision.find_elements_by_text", return_value=mock_elements):
            result = form_filler.find_field_by_label("Username")

        assert result is not None
        assert result["center"] == (200, 50)  # Should return the highest confidence match
        assert result["confidence"] == 0.95

    def test_find_input_field_near(self):
        """Test finding input field near a label."""
        form_filler = FormFiller()

        # Mock screenshot
        mock_screenshot = np.zeros((200, 200, 3), dtype=np.uint8)
        form_filler._get_current_screenshot = Mock(return_value=mock_screenshot)

        # Mock input field element
        mock_element = MockOCRElement(
            text="textfield",
            center=(150, 50),  # 50 pixels right of label
            bbox=(130, 40, 170, 60),
            confidence=0.8,
        )

        with patch("vision.find_elements_by_text", return_value=[mock_element]):
            result = form_filler.find_input_field_near((100, 50), search_radius=100)

        assert result is not None
        assert result["center"] == (150, 50)
        assert result["distance_from_label"] == 50.0

    def test_find_input_field_near_outside_radius(self):
        """Test finding input field outside search radius."""
        form_filler = FormFiller()

        # Mock screenshot
        mock_screenshot = np.zeros((300, 300, 3), dtype=np.uint8)
        form_filler._get_current_screenshot = Mock(return_value=mock_screenshot)

        # Mock input field element far from label
        mock_element = MockOCRElement(
            text="textfield",
            center=(250, 50),  # 150 pixels away
            bbox=(230, 40, 270, 60),
            confidence=0.8,
        )
        with patch(
            "automation.local.form_interface.find_elements_by_text", return_value=[mock_element]
        ):
            result = form_filler.find_input_field_near((100, 50), search_radius=100)

        assert result is None  # Should be None because it's outside the radius

    def test_fill_field_success_with_input_field(self):
        """Test successful field filling with detected input field."""
        form_filler = FormFiller()

        # Mock find_field_by_label
        form_filler.find_field_by_label = Mock(
            return_value={"text": "Username", "center": (100, 50), "confidence": 0.95}
        )

        # Mock find_input_field_near
        form_filler.find_input_field_near = Mock(
            return_value={"center": (150, 50), "confidence": 0.8}
        )

        # Mock desktop actions
        form_filler.desktop.click = Mock(return_value=ActionResult(True, "Clicked"))
        form_filler.desktop.key_press = Mock(return_value=ActionResult(True, "Key pressed"))
        form_filler.desktop.type_text = Mock(return_value=ActionResult(True, "Text typed"))

        result = form_filler.fill_field("Username", "john.doe")

        assert result.success is True
        assert "Successfully filled 'Username' with 'john.doe'" in result.message

        # Verify interactions
        form_filler.desktop.click.assert_called_once_with(150, 50)  # Click input field
        form_filler.desktop.key_press.assert_called_once_with("cmd+a")  # Select all
        form_filler.desktop.type_text.assert_called_once_with("john.doe")

    def test_fill_field_success_with_offset(self):
        """Test successful field filling using label offset (no input field found)."""
        form_filler = FormFiller()

        # Mock find_field_by_label
        form_filler.find_field_by_label = Mock(
            return_value={"text": "Password", "center": (100, 50), "confidence": 0.95}
        )

        # Mock find_input_field_near returns None
        form_filler.find_input_field_near = Mock(return_value=None)

        # Mock desktop actions
        form_filler.desktop.click = Mock(return_value=ActionResult(True, "Clicked"))
        form_filler.desktop.key_press = Mock(return_value=ActionResult(True, "Key pressed"))
        form_filler.desktop.type_text = Mock(return_value=ActionResult(True, "Text typed"))

        result = form_filler.fill_field("Password", "secret123", click_offset=(10, 30))

        assert result.success is True

        # Verify click at label + offset
        form_filler.desktop.click.assert_called_once_with(110, 80)  # (100+10, 50+30)

    def test_fill_field_label_not_found(self):
        """Test field filling when label is not found."""
        form_filler = FormFiller()

        # Mock find_field_by_label returns None
        form_filler.find_field_by_label = Mock(return_value=None)

        result = form_filler.fill_field("NonexistentField", "value")

        assert result.success is False
        assert "Could not find field with label: NonexistentField" in result.message

    def test_fill_field_click_fails(self):
        """Test field filling when click fails."""
        form_filler = FormFiller()

        # Mock find_field_by_label
        form_filler.find_field_by_label = Mock(
            return_value={"text": "Username", "center": (100, 50), "confidence": 0.95}
        )

        form_filler.find_input_field_near = Mock(return_value=None)

        # Mock click failure
        form_filler.desktop.click = Mock(return_value=ActionResult(False, "Click failed"))

        result = form_filler.fill_field("Username", "value")

        assert result.success is False
        assert "Failed to click field: Click failed" in result.message

    def test_fill_field_type_fails(self):
        """Test field filling when typing fails."""
        form_filler = FormFiller()

        # Mock successful label finding and clicking
        form_filler.find_field_by_label = Mock(
            return_value={"text": "Username", "center": (100, 50), "confidence": 0.95}
        )
        form_filler.find_input_field_near = Mock(return_value=None)
        form_filler.desktop.click = Mock(return_value=ActionResult(True, "Clicked"))
        form_filler.desktop.key_press = Mock(return_value=ActionResult(True, "Key pressed"))

        # Mock typing failure
        form_filler.desktop.type_text = Mock(return_value=ActionResult(False, "Type failed"))

        result = form_filler.fill_field("Username", "value")

        assert result.success is False
        assert "Failed to type text: Type failed" in result.message

    def test_click_button_success(self):
        """Test successful button clicking."""
        form_filler = FormFiller()

        # Mock find_field_by_label for button
        form_filler.find_field_by_label = Mock(
            return_value={"text": "Submit", "center": (200, 100), "confidence": 0.95}
        )

        # Mock desktop click
        form_filler.desktop.click = Mock(return_value=ActionResult(True, "Clicked"))

        result = form_filler.click_button("Submit")

        assert result.success is True
        assert "Successfully clicked 'Submit' button" in result.message
        form_filler.desktop.click.assert_called_once_with(200, 100)

    def test_click_button_not_found(self):
        """Test button clicking when button is not found."""
        form_filler = FormFiller()

        # Mock find_field_by_label returns None
        form_filler.find_field_by_label = Mock(return_value=None)

        result = form_filler.click_button("NonexistentButton")

        assert result.success is False
        assert "Could not find button: NonexistentButton" in result.message

    def test_fill_form_multiple_fields(self):
        """Test filling multiple form fields."""
        form_filler = FormFiller()

        # Mock individual field filling
        def mock_fill_field(label, value):
            if label == "Username" or label == "Password":
                return ActionResult(True, f"Filled {label}")
            else:
                return ActionResult(False, f"Failed to fill {label}")

        form_filler.fill_field = Mock(side_effect=mock_fill_field)

        form_data = {"Username": "john.doe", "Password": "secret123", "Email": "john@example.com"}

        results = form_filler.fill_form(form_data)

        assert len(results) == 3
        assert results["Username"].success is True
        assert results["Password"].success is True
        assert results["Email"].success is False

    def test_get_form_fields_default_labels(self):
        """Test getting form fields with default labels."""
        form_filler = FormFiller()

        # Mock find_field_by_label to return different results for different labels
        def mock_find_field(label, confidence_threshold=0.5):
            if label == "Username":
                return {"text": "Username", "center": (100, 50)}
            elif label == "Password":
                return {"text": "Password", "center": (100, 80)}
            return None

        form_filler.find_field_by_label = Mock(side_effect=mock_find_field)

        fields = form_filler.get_form_fields()

        # Should find Username and Password
        assert len(fields) == 2
        assert fields[0]["text"] == "Username"
        assert fields[1]["text"] == "Password"

    def test_get_form_fields_custom_labels(self):
        """Test getting form fields with custom labels."""
        form_filler = FormFiller()

        # Mock find_field_by_label
        def mock_find_field(label, confidence_threshold=0.5):
            if label == "CustomField":
                return {"text": "CustomField", "center": (100, 50)}
            return None

        form_filler.find_field_by_label = Mock(side_effect=mock_find_field)

        fields = form_filler.get_form_fields(["CustomField", "AnotherField"])

        assert len(fields) == 1
        assert fields[0]["text"] == "CustomField"

    @patch("time.time")
    @patch("time.sleep")
    def test_wait_for_element_found(self, mock_sleep, mock_time):
        """Test waiting for element that is found."""
        form_filler = FormFiller()

        # Mock time progression
        mock_time.side_effect = [0, 0.5, 1.0]  # Start, first check, element found

        # Mock find_field_by_label to return None first, then element
        def mock_find_field(text):
            if mock_time.call_count > 2:  # After second time call
                return {"text": "Submit", "center": (100, 50)}
            return None

        form_filler.find_field_by_label = Mock(side_effect=mock_find_field)

        result = form_filler.wait_for_element("Submit", timeout=5.0, check_interval=0.5)

        assert result is not None
        assert result["text"] == "Submit"
        mock_sleep.assert_called_with(0.5)

    @patch("time.time")
    @patch("time.sleep")
    def test_wait_for_element_timeout(self, mock_sleep, mock_time):
        """Test waiting for element that times out."""
        form_filler = FormFiller()

        # Mock time progression to exceed timeout
        mock_time.side_effect = [0, 1, 2, 3, 4, 5, 6]  # Exceeds 5 second timeout

        # Mock find_field_by_label to always return None
        form_filler.find_field_by_label = Mock(return_value=None)

        result = form_filler.wait_for_element("Submit", timeout=5.0, check_interval=1.0)

        assert result is None

    def test_screenshot_cache_invalidation(self):
        """Test that screenshot cache is properly invalidated."""
        form_filler = FormFiller()

        # Set initial cache
        form_filler.last_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        form_filler.screenshot_cache_time = 1000.0

        # fill_form should invalidate cache for each field
        form_filler.fill_field = Mock(return_value=ActionResult(True, "Success"))

        form_data = {"Field1": "Value1", "Field2": "Value2"}
        form_filler.fill_form(form_data)

        # Cache should have been cleared twice (once per field)
        assert form_filler.last_screenshot is None


class TestFormFillerErrorHandling:
    """Test error handling in FormFiller."""

    def test_find_field_by_label_exception(self):
        """Test exception handling in find_field_by_label."""
        form_filler = FormFiller()

        # Mock screenshot
        form_filler._get_current_screenshot = Mock(return_value=np.zeros((100, 100, 3)))

        # Mock find_elements_by_text to raise exception
        with patch(
            "automation.local.form_interface.find_elements_by_text",
            side_effect=Exception("OCR error"),
        ):
            result = form_filler.find_field_by_label("Username")

        assert result is None

    def test_find_input_field_near_exception(self):
        """Test exception handling in find_input_field_near."""
        form_filler = FormFiller()

        # Mock screenshot
        form_filler._get_current_screenshot = Mock(return_value=np.zeros((100, 100, 3)))

        # Mock find_elements_by_text to raise exception
        with patch(
            "automation.local.form_interface.find_elements_by_text",
            side_effect=Exception("OCR error"),
        ):
            result = form_filler.find_input_field_near((100, 50))

        assert result is None

    def test_fill_field_exception(self):
        """Test exception handling in fill_field."""
        form_filler = FormFiller()

        # Mock find_field_by_label to raise exception
        form_filler.find_field_by_label = Mock(side_effect=Exception("Test error"))

        result = form_filler.fill_field("Username", "value")

        assert result.success is False
        assert "Error filling field 'Username': Test error" in result.message

    def test_click_button_exception(self):
        """Test exception handling in click_button."""
        form_filler = FormFiller()

        # Mock find_field_by_label to raise exception
        form_filler.find_field_by_label = Mock(side_effect=Exception("Test error"))

        result = form_filler.click_button("Submit")

        assert result.success is False
        assert "Error clicking button 'Submit': Test error" in result.message
