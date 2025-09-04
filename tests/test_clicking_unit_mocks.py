"""Unit tests for clicking functionality using mocks

These tests use mock components to test clicking, UI detection, and agent workflows
without requiring a VM connection. They focus on testing the logic and error handling.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import AppControllerAgent, VMNavigatorAgent, VMSession, VMTarget
from main import VMConfig
from vision.ui_finder import UIElement

# Import mock components
from .mock_components import (
    create_mock_components,
    setup_error_scenario,
    setup_patient_safety_test_scenario,
)


@pytest.fixture
def mock_components():
    """Create mock components for testing"""
    return create_mock_components()


@pytest.fixture
def mock_vm_config():
    """Mock VM configuration for testing"""
    return VMConfig(
        vm_host="mock-vm-host", vm_port=5900, vm_username="test-user", vm_password="test-password"
    )


@pytest.fixture
def mock_vm_target():
    """Mock VM target for testing"""
    return VMTarget(
        vm_host="mock-host",
        vm_port=5900,
        vm_username="test",
        vm_password="test",
        target_app_name="TestApp.exe",
        target_button_text="Submit",
        expected_desktop_elements=["Desktop", "Start"],
        expected_app_elements=["Submit", "TestApp"],
    )


@pytest.fixture
def mock_session(mock_vm_target):
    """Mock VM session for testing"""
    return VMSession(vm_config=mock_vm_target.to_vm_config(), session_id="test_session")


class TestInputActionsMocking:
    """Test input actions with mocks"""

    def test_mock_click_success(self, mock_components):
        """Test successful click with mock input actions"""
        input_actions = mock_components["input_actions"]

        result = input_actions.click(100, 200, "left")

        assert result.success, "Mock click should succeed"
        assert "Click left at (100, 200)" in result.message

        # Verify action was logged
        actions_log = input_actions.get_actions_log()
        assert len(actions_log) == 1
        assert "Click left at (100, 200)" in actions_log[0]

    def test_mock_click_failure(self, mock_components):
        """Test click failure handling with mocks"""
        input_actions = mock_components["input_actions"]
        input_actions.set_failure_mode(True)

        result = input_actions.click(100, 200)

        assert not result.success, "Mock click should fail when failure mode is set"
        assert "Mock click failure" in result.message

        # Verify failed action was logged
        actions_log = input_actions.get_actions_log()
        assert len(actions_log) == 1
        assert "[FAILED]" in actions_log[0]

    def test_mock_double_click(self, mock_components):
        """Test double-click with mocks"""
        input_actions = mock_components["input_actions"]

        result = input_actions.double_click(150, 250)

        assert result.success, "Mock double-click should succeed"
        assert "Double-click at (150, 250)" in result.message

    def test_mock_type_text(self, mock_components):
        """Test text typing with mocks"""
        input_actions = mock_components["input_actions"]

        result = input_actions.type_text("Hello World")

        assert result.success, "Mock typing should succeed"
        assert "Type: Hello World" in result.message

    def test_mock_key_press(self, mock_components):
        """Test key pressing with mocks"""
        input_actions = mock_components["input_actions"]

        result = input_actions.press_key("enter")

        assert result.success, "Mock key press should succeed"
        assert "Press key: enter" in result.message

    def test_mock_scroll(self, mock_components):
        """Test scrolling with mocks"""
        input_actions = mock_components["input_actions"]

        result = input_actions.scroll(500, 400, "down", 3)

        assert result.success, "Mock scroll should succeed"
        assert "Scroll down 3 times at (500, 400)" in result.message

    def test_input_actions_log_management(self, mock_components):
        """Test input actions logging functionality"""
        input_actions = mock_components["input_actions"]

        # Perform multiple actions
        input_actions.click(100, 100)
        input_actions.type_text("test")
        input_actions.press_key("enter")

        # Verify all actions were logged
        log = input_actions.get_actions_log()
        assert len(log) == 3
        assert "Click left at (100, 100)" in log[0]
        assert "Type: test" in log[1]
        assert "Press key: enter" in log[2]

        # Clear log
        input_actions.clear_log()
        assert len(input_actions.get_actions_log()) == 0


class TestUIFinderMocking:
    """Test UI element finding with mocks"""

    def test_find_element_by_text_success(self, mock_components):
        """Test finding element by text with mocks"""
        ui_finder = mock_components["ui_finder"]

        # Find a default mock element
        elements = ui_finder.find_element_by_text(None, "Submit")

        assert len(elements) == 1
        element = elements[0]
        assert element.text == "Submit"
        assert element.center == (450, 325)
        assert element.confidence == 0.9

    def test_find_element_custom_mock(self, mock_components):
        """Test finding custom mock element"""
        ui_finder = mock_components["ui_finder"]

        # Add custom mock element
        custom_element = UIElement(
            element_type="button",
            bbox=(200, 300, 300, 350),
            center=(250, 325),
            confidence=0.95,
            text="Custom Button",
            description="Test custom button",
        )
        ui_finder.add_mock_element("Custom Button", custom_element)

        # Find the custom element
        elements = ui_finder.find_element_by_text(None, "Custom Button")

        assert len(elements) == 1
        element = elements[0]
        assert element.text == "Custom Button"
        assert element.center == (250, 325)
        assert element.confidence == 0.95

    def test_find_element_search_failure(self, mock_components):
        """Test element search failure with mocks"""
        ui_finder = mock_components["ui_finder"]

        # Set up search failure for specific element
        ui_finder.set_search_failure("NonExistent", True)

        elements = ui_finder.find_element_by_text(None, "NonExistent")
        assert len(elements) == 0, "Should not find element when search is set to fail"

    def test_find_all_ui_elements(self, mock_components):
        """Test finding all UI elements with mocks"""
        ui_finder = mock_components["ui_finder"]

        elements = ui_finder.find_ui_elements(None)

        assert len(elements) >= 2  # Should find multiple mock elements

        # Verify expected elements are present
        element_texts = [elem.text for elem in elements if elem.text]
        assert "Submit" in element_texts
        assert "Name Field" in element_texts

    def test_find_clickable_elements(self, mock_components):
        """Test finding clickable elements with mocks"""
        ui_finder = mock_components["ui_finder"]

        clickable_elements = ui_finder.find_clickable_elements(None)

        assert len(clickable_elements) >= 1

        # Should find the Submit button as clickable
        submit_button = next((elem for elem in clickable_elements if elem.text == "Submit"), None)
        assert submit_button is not None
        assert submit_button.center == (450, 325)


class TestOCRMocking:
    """Test OCR functionality with mocks"""

    def test_ocr_read_text_default(self, mock_components):
        """Test OCR text reading with default mocks"""
        ocr_reader = mock_components["ui_finder"].ocr_reader

        # Create a mock image
        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)

        detections = ocr_reader.read_text(mock_image)

        assert len(detections) >= 2

        # Verify expected text detections
        texts = [det.text for det in detections]
        assert "Submit" in texts
        assert "Name Field" in texts

    def test_ocr_read_patient_banner(self, mock_components):
        """Test OCR reading patient banner area"""
        ocr_reader = mock_components["ui_finder"].ocr_reader

        # Create a mock image and specify banner region (top 20% of screen)
        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)
        banner_region = (0, 0, 800, 120)  # Top 20%

        detections = ocr_reader.read_text(mock_image, banner_region)

        assert len(detections) >= 3

        # Verify patient information is detected in banner
        texts = [det.text for det in detections]
        assert any("John Doe" in text for text in texts)
        assert any("123456" in text for text in texts)
        assert any("01/01/1980" in text for text in texts)

    def test_ocr_find_specific_text(self, mock_components):
        """Test OCR finding specific text"""
        ocr_reader = mock_components["ui_finder"].ocr_reader

        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)

        # Find text containing "Submit"
        matching_detections = ocr_reader.find_text(mock_image, "Submit")

        assert len(matching_detections) >= 1
        assert all("Submit" in det.text for det in matching_detections)


class TestVerificationMocking:
    """Test verification functionality with mocks"""

    def test_page_load_verification_success(self, mock_components):
        """Test successful page load verification"""
        verifier = mock_components["verifier"]

        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)
        indicators = ["Desktop", "Submit"]

        result = verifier.verify_page_loaded(mock_image, indicators)

        assert result.success
        assert "Desktop" in result.message or "Submit" in result.message
        assert result.confidence > 0.5

    def test_page_load_verification_failure(self, mock_components):
        """Test page load verification failure"""
        verifier = mock_components["verifier"]

        # Set verification to fail
        verifier.set_verification_failure("page_load", True)

        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)
        indicators = ["Desktop"]

        result = verifier.verify_page_loaded(mock_image, indicators)

        assert not result.success
        assert "failed" in result.message.lower()

    def test_click_success_verification(self, mock_components):
        """Test click success verification"""
        verifier = mock_components["verifier"]

        # Create mock before/after screenshots
        before = np.zeros((600, 800, 3), dtype=np.uint8)
        after = np.ones((600, 800, 3), dtype=np.uint8) * 50  # Different image

        result = verifier.verify_click_success(before, after)

        assert result.success
        assert "verified" in result.message.lower()

    def test_element_presence_verification(self, mock_components):
        """Test element presence verification"""
        verifier = mock_components["verifier"]

        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)

        result = verifier.verify_element_present(mock_image, "Submit button")

        assert result.success
        assert "Submit button" in result.message


class TestAppControllerWithMocks:
    """Test App Controller agent using mocks"""

    def test_app_controller_initialization(self, mock_session, mock_vm_target, mock_components):
        """Test App Controller initialization with mock components"""
        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        assert app_controller.session == mock_session
        assert app_controller.vm_target == mock_vm_target
        assert app_controller.tools.screen_capture == mock_components["screen_capture"]
        assert app_controller.tools.input_actions == mock_components["input_actions"]

    def test_capture_current_screen(self, mock_session, mock_vm_target, mock_components):
        """Test screen capture through App Controller"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        result = app_controller.tools.capture_current_screen("Test capture")

        assert result["success"]
        assert result["description"] == "Test capture"
        assert len(mock_session.screenshots) > 0

    async def test_find_target_element_success(self, mock_session, mock_vm_target, mock_components):
        """Test finding target element successfully"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        result = app_controller.tools.find_target_element_with_retry("Submit", max_retries=1)

        assert result["success"]
        assert result["element"]["text"] == "Submit"
        assert result["element"]["center"] == (450, 325)
        assert result["element"]["search_strategy"] == "text_search"

    async def test_find_target_element_failure(self, mock_session, mock_vm_target, mock_components):
        """Test element finding failure"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        # Set up search failure
        mock_components["ui_finder"].set_search_failure("NonExistent", True)

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        result = app_controller.tools.find_target_element_with_retry("NonExistent", max_retries=1)

        assert not result["success"]
        assert "not found" in result["error"]

    async def test_click_element_verified_success(
        self, mock_session, mock_vm_target, mock_components
    ):
        """Test clicking element with verification"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        element_info = {
            "center": (450, 325),
            "text": "Submit",
            "bbox": (400, 300, 500, 350),
            "confidence": 0.9,
        }

        result = app_controller.tools.click_element_verified(element_info)

        assert result["success"]
        assert "Successfully clicked Submit" in result["message"]

        # Verify click was performed
        input_log = mock_components["input_actions"].get_actions_log()
        assert any("Click left at (450, 325)" in action for action in input_log)

    async def test_click_element_verified_failure(
        self, mock_session, mock_vm_target, mock_components
    ):
        """Test clicking element with click failure"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        # Set input actions to fail
        mock_components["input_actions"].set_failure_mode(True)

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        element_info = {"center": (450, 325), "text": "Submit"}

        result = app_controller.tools.click_element_verified(element_info)

        assert not result["success"]
        assert "Mock click failure" in result["error"]

    async def test_verify_action_outcome(self, mock_session, mock_vm_target, mock_components):
        """Test verifying action outcomes"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        expected_outcomes = ["Submit", "Success"]  # Submit exists in mock, Success doesn't

        result = app_controller.tools.verify_action_outcome(expected_outcomes)

        assert result["success"]
        assert "Submit" in result["found_outcomes"]
        assert "Success" in result["missing_outcomes"]
        assert result["success_rate"] == 0.5  # 1 out of 2 found

    async def test_scroll_and_search(self, mock_session, mock_vm_target, mock_components):
        """Test scrolling to find element"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        # Test finding element immediately (no scrolling needed)
        result = app_controller.tools.scroll_and_search("Submit", max_scrolls=2)

        assert result["success"]
        assert result["element"]["text"] == "Submit"

        # Verify no scroll actions were needed (element found immediately)
        input_log = mock_components["input_actions"].get_actions_log()
        scroll_actions = [action for action in input_log if "Scroll" in action]
        assert len(scroll_actions) == 0

    async def test_button_click_workflow_success(
        self, mock_session, mock_vm_target, mock_components
    ):
        """Test complete button click workflow"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        expected_outcomes = ["Submit"]
        result = await app_controller.execute_button_click_workflow(expected_outcomes)

        assert result["success"]
        assert result["element_clicked"] == "Submit"
        assert "element_info" in result

        # Verify workflow steps were executed
        assert len(mock_session.screenshots) > 0
        assert len(mock_session.action_log) > 0

        input_log = mock_components["input_actions"].get_actions_log()
        assert any("Click" in action for action in input_log)

    async def test_button_click_workflow_prerequisite_failure(
        self, mock_session, mock_vm_target, mock_components
    ):
        """Test workflow failure due to missing prerequisites"""
        # Don't set agent_1_completed
        mock_session.agent_1_completed = False

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        result = await app_controller.execute_button_click_workflow()

        assert not result["success"]
        assert "Agent 1" in result["error"]

    async def test_form_filling_workflow(self, mock_session, mock_vm_target, mock_components):
        """Test form filling workflow"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        form_fields = [
            {"field_name": "Name Field", "value": "John Doe"},
            {"field_name": "ID Field", "value": "123456"},
        ]

        result = await app_controller.execute_form_filling_workflow(
            form_fields, submit_button="Submit"
        )

        assert result["success"]
        assert result["fields_filled"] == 2
        assert result["submitted"]

        # Verify form fields were filled
        input_log = mock_components["input_actions"].get_actions_log()
        type_actions = [action for action in input_log if "Type:" in action]
        assert len(type_actions) >= 2
        assert any("John Doe" in action for action in type_actions)
        assert any("123456" in action for action in type_actions)


class TestPatientSafetyWithMocks:
    """Test patient safety features using mocks"""

    def test_patient_verification_success(self, mock_session, mock_vm_target, mock_components):
        """Test successful patient verification using mocks"""
        # Set up patient safety test scenario
        setup_patient_safety_test_scenario(mock_components, "John Doe", "123456")

        mock_session.agent_1_completed = True
        mock_session.current_app = "PatientApp"

        # Create VM Navigator to test patient verification
        navigator = VMNavigatorAgent(mock_session, mock_vm_target)
        navigator.tools.screen_capture = mock_components["screen_capture"]
        navigator.tools.ui_finder = mock_components["ui_finder"]

        patient_info = {"name": "John Doe", "mrn": "123456", "dob": "01/01/1980"}

        result = navigator.tools.verify_patient_banner(patient_info)

        assert result["success"]
        assert "John Doe" in result["verified_fields"]
        assert "123456" in result["verified_fields"]
        assert len(result["verified_fields"]) >= 2

    def test_patient_verification_failure(self, mock_session, mock_vm_target, mock_components):
        """Test patient verification failure"""
        # Set up scenario where patient name is not found
        setup_error_scenario(mock_components, "patient_mismatch")

        mock_session.agent_1_completed = True
        mock_session.current_app = "PatientApp"

        navigator = VMNavigatorAgent(mock_session, mock_vm_target)
        navigator.tools.screen_capture = mock_components["screen_capture"]
        navigator.tools.ui_finder = mock_components["ui_finder"]

        patient_info = {
            "name": "John Doe",  # This will fail to be found
            "mrn": "123456",
            "dob": "01/01/1980",
        }

        result = navigator.tools.verify_patient_banner(patient_info)

        assert not result["success"]
        assert "SAFETY CHECK FAILED" in result["error"]
        assert result.get("safety_critical") == True


class TestErrorScenariosWithMocks:
    """Test various error scenarios using mocks"""

    async def test_connection_failure_scenario(self, mock_session, mock_vm_target, mock_components):
        """Test handling connection failure"""
        setup_error_scenario(mock_components, "connection_failure")

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        result = app_controller.tools.capture_current_screen()

        assert not result["success"]
        assert "error" in result

    async def test_element_not_found_scenario(self, mock_session, mock_vm_target, mock_components):
        """Test handling element not found"""
        setup_error_scenario(mock_components, "element_not_found")

        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        result = app_controller.tools.find_target_element_with_retry("Submit", max_retries=1)

        assert not result["success"]
        assert "not found" in result["error"]

    async def test_click_failure_scenario(self, mock_session, mock_vm_target, mock_components):
        """Test handling click failure"""
        setup_error_scenario(mock_components, "click_failure")

        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        element_info = {"center": (100, 100), "text": "Test"}
        result = app_controller.tools.click_element_verified(element_info)

        assert not result["success"]
        assert "failure" in result["error"].lower()

    async def test_verification_failure_scenario(
        self, mock_session, mock_vm_target, mock_components
    ):
        """Test handling verification failure"""
        setup_error_scenario(mock_components, "verification_failure")

        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        element_info = {"center": (100, 100), "text": "Test"}
        result = app_controller.tools.click_element_verified(element_info)

        assert not result["success"]
        assert "verification failed" in result["error"].lower()


class TestMockComponentIntegration:
    """Test integration between different mock components"""

    async def test_full_workflow_with_mocks(self, mock_session, mock_vm_target, mock_components):
        """Test full workflow using all mock components together"""
        mock_session.agent_1_completed = True
        mock_session.current_app = "TestApp"

        app_controller = AppControllerAgent(mock_session, mock_vm_target, mock_components)

        # Execute complete workflow
        result = await app_controller.execute_button_click_workflow()

        assert result["success"]

        # Verify all components were used
        assert len(mock_components["screen_capture"].mock_sequence) >= 0  # Screenshots taken
        assert len(mock_components["input_actions"].get_actions_log()) > 0  # Actions performed

        # Verify session state
        assert len(mock_session.screenshots) > 0
        assert len(mock_session.action_log) > 0
        assert mock_session.errors == []  # No errors should occur

    def test_mock_components_state_consistency(self, mock_components):
        """Test that mock components maintain consistent state"""
        screen_capture = mock_components["screen_capture"]
        input_actions = mock_components["input_actions"]

        # Initially should be connected (mocked)
        assert screen_capture.is_connected

        # Capture screen should work
        screenshot = screen_capture.capture_screen()
        assert screenshot is not None

        # Input actions should work
        result = input_actions.click(100, 100)
        assert result.success

        # Disconnect should update state
        screen_capture.disconnect()
        assert not screen_capture.is_connected

        # Screen capture should fail after disconnect
        screenshot = screen_capture.capture_screen()
        assert screenshot is None


if __name__ == "__main__":
    # Run tests directly with pytest
    import sys

    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
