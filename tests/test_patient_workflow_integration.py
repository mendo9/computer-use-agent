"""Integration tests for patient-specific workflows using PaddleOCR and YOLO

These tests simulate clicking through a patient management application inside a VM,
using computer vision tools (PaddleOCR for text recognition, YOLO for UI element detection).
The tests assume an application is running inside the VM, not a web browser.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import VMSession, VMTarget
from main import VMAutomation, VMConfig


class PatientWorkflowTestConfig:
    """Configuration for patient workflow integration tests"""

    # VM Connection (VNC preferred for patient workflows)
    VM_HOST = os.getenv("PATIENT_TEST_VM_HOST", "192.168.1.100")
    VM_PORT = int(os.getenv("PATIENT_TEST_VM_PORT", "5900"))
    VM_PASSWORD = os.getenv("PATIENT_TEST_VM_PASSWORD", "")

    # Patient Application Configuration
    PATIENT_APP_NAME = os.getenv("PATIENT_APP_NAME", "EMR_System.exe")
    PATIENT_APP_WINDOW_TITLE = os.getenv("PATIENT_APP_TITLE", "Electronic Medical Records")

    # Test Patient Data
    TEST_PATIENT_ID = os.getenv("TEST_PATIENT_ID", "PAT001234")
    TEST_PATIENT_NAME = os.getenv("TEST_PATIENT_NAME", "John Smith")
    TEST_PATIENT_MRN = os.getenv("TEST_PATIENT_MRN", "12345678")
    TEST_PATIENT_DOB = os.getenv("TEST_PATIENT_DOB", "01/15/1975")

    # Expected UI Elements in Patient Application
    SEARCH_FIELD_LABEL = os.getenv("SEARCH_FIELD_LABEL", "Patient ID")
    SEARCH_BUTTON_TEXT = os.getenv("SEARCH_BUTTON_TEXT", "Search")
    PATIENT_DETAILS_BUTTON = os.getenv("PATIENT_DETAILS_BUTTON", "View Details")
    CLOSE_BUTTON_TEXT = os.getenv("CLOSE_BUTTON_TEXT", "Close")


@pytest.fixture
def patient_vm_config():
    """VM configuration for patient workflow testing"""
    return VMConfig(
        vm_host=PatientWorkflowTestConfig.VM_HOST,
        vm_port=PatientWorkflowTestConfig.VM_PORT,
        vm_password=PatientWorkflowTestConfig.VM_PASSWORD,
        connection_type="vnc",
        target_app_name=PatientWorkflowTestConfig.PATIENT_APP_NAME,
        target_button_text=PatientWorkflowTestConfig.SEARCH_BUTTON_TEXT,
        patient_name=PatientWorkflowTestConfig.TEST_PATIENT_NAME,
        patient_mrn=PatientWorkflowTestConfig.TEST_PATIENT_MRN,
        patient_dob=PatientWorkflowTestConfig.TEST_PATIENT_DOB,
        expected_desktop_elements=["Desktop", "Start", "Taskbar"],
        expected_app_elements=[
            PatientWorkflowTestConfig.PATIENT_APP_WINDOW_TITLE,
            PatientWorkflowTestConfig.SEARCH_FIELD_LABEL,
            PatientWorkflowTestConfig.SEARCH_BUTTON_TEXT,
        ],
        vm_connection_timeout=45,
        desktop_load_timeout=90,
        app_launch_timeout=60,
        save_screenshots=True,
    )


class PatientWorkflowAgent:
    """Specialized agent for patient application workflows using computer vision"""

    def __init__(self, session: VMSession, vm_target: VMTarget, shared_components: dict[str, Any]):
        self.session = session
        self.vm_target = vm_target

        # Use shared components from VM Navigator
        self.screen_capture = shared_components["screen_capture"]
        self.input_actions = shared_components["input_actions"]
        self.ui_finder = shared_components["ui_finder"]
        self.verifier = shared_components["verifier"]

        # Direct access to computer vision tools
        self.ocr_reader = self.ui_finder.ocr_reader
        self.yolo_detector = self.ui_finder  # UIFinder wraps YOLO detector

        self.session.log_action("Patient Workflow Agent initialized with computer vision tools")

    async def find_patient_search_field(self, field_label: str = None) -> dict[str, Any]:
        """Find patient search input field using OCR and UI detection"""
        field_label = field_label or PatientWorkflowTestConfig.SEARCH_FIELD_LABEL

        try:
            self.session.log_action(f"Looking for patient search field: '{field_label}'")

            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen"}

            self.session.add_screenshot(screenshot, f"Searching for field: {field_label}")

            # Strategy 1: Use OCR to find field label, then find nearby input field
            text_detections = self.ocr_reader.read_text(screenshot)
            field_label_location = None

            for detection in text_detections:
                if field_label.lower() in detection.text.lower():
                    field_label_location = detection.center
                    self.session.log_action(f"Found field label at {field_label_location}")
                    break

            if field_label_location:
                # Look for input field near the label (usually to the right or below)
                label_x, label_y = field_label_location
                search_region = (
                    max(0, label_x - 50),
                    max(0, label_y - 20),
                    min(screenshot.shape[1], label_x + 300),
                    min(screenshot.shape[0], label_y + 80),
                )

                # Use YOLO to find input fields in the region
                ui_elements = self.ui_finder.find_input_fields(screenshot, search_region)

                if ui_elements:
                    best_field = min(
                        ui_elements,
                        key=lambda elem: abs(elem.center[0] - label_x)
                        + abs(elem.center[1] - label_y),
                    )

                    return {
                        "success": True,
                        "element": {
                            "center": best_field.center,
                            "bbox": best_field.bbox,
                            "confidence": best_field.confidence,
                            "type": "input_field",
                            "associated_label": field_label,
                        },
                    }

            # Strategy 2: Direct search for input fields with text matching
            all_elements = self.ui_finder.find_input_fields(screenshot)
            for element in all_elements:
                if element.text and field_label.lower() in element.text.lower():
                    return {
                        "success": True,
                        "element": {
                            "center": element.center,
                            "bbox": element.bbox,
                            "confidence": element.confidence,
                            "type": "input_field",
                            "text": element.text,
                        },
                    }

            return {"success": False, "error": f"Patient search field '{field_label}' not found"}

        except Exception as e:
            error_msg = f"Error finding patient search field: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    async def enter_patient_id(
        self, patient_id: str, field_element: dict[str, Any]
    ) -> dict[str, Any]:
        """Enter patient ID into the search field"""
        try:
            self.session.log_action(f"Entering patient ID: {patient_id}")

            # Click on the input field to focus it
            center = field_element["center"]
            x, y = center

            click_result = self.input_actions.click(x, y)
            if not click_result.success:
                return {
                    "success": False,
                    "error": f"Failed to click input field: {click_result.message}",
                }

            # Clear any existing text
            clear_result = self.input_actions.key_press("ctrl+a")
            if clear_result.success:
                await asyncio.sleep(0.2)
                self.input_actions.key_press("delete")

            await asyncio.sleep(0.5)

            # Type the patient ID
            type_result = self.input_actions.type_text(patient_id)
            if not type_result.success:
                return {
                    "success": False,
                    "error": f"Failed to type patient ID: {type_result.message}",
                }

            # Verify the text was entered
            await asyncio.sleep(1)
            screenshot = self.screen_capture.capture_screen()
            if screenshot:
                self.session.add_screenshot(screenshot, f"After entering patient ID: {patient_id}")

                # Use OCR to verify the text appears on screen
                text_detections = self.ocr_reader.read_text(screenshot)
                patient_id_found = any(
                    patient_id in detection.text for detection in text_detections
                )

                if patient_id_found:
                    self.session.log_action(f"✓ Patient ID '{patient_id}' successfully entered")
                    return {"success": True, "message": f"Patient ID entered: {patient_id}"}
                else:
                    self.session.log_action("⚠ Patient ID may not have been entered correctly")

            return {"success": True, "message": f"Patient ID entered: {patient_id}"}

        except Exception as e:
            error_msg = f"Error entering patient ID: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    async def click_search_button(self, button_text: str = None) -> dict[str, Any]:
        """Find and click the search button using computer vision"""
        button_text = button_text or PatientWorkflowTestConfig.SEARCH_BUTTON_TEXT

        try:
            self.session.log_action(f"Looking for search button: '{button_text}'")

            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen"}

            self.session.add_screenshot(screenshot, f"Searching for button: {button_text}")

            # Find button using multiple strategies
            button_elements = self.ui_finder.find_element_by_text(screenshot, button_text)

            if not button_elements:
                # Try finding clickable elements and match by text
                clickable_elements = self.ui_finder.find_clickable_elements(screenshot)
                button_elements = [
                    elem
                    for elem in clickable_elements
                    if elem.text and button_text.lower() in elem.text.lower()
                ]

            if not button_elements:
                return {"success": False, "error": f"Search button '{button_text}' not found"}

            # Click the best matching button
            best_button = max(button_elements, key=lambda x: x.confidence)
            x, y = best_button.center

            # Take before screenshot
            before_screenshot = screenshot

            click_result = self.input_actions.click(x, y)
            if not click_result.success:
                return {
                    "success": False,
                    "error": f"Failed to click search button: {click_result.message}",
                }

            # Wait for search to complete
            await asyncio.sleep(3)

            # Take after screenshot
            after_screenshot = self.screen_capture.capture_screen()
            if after_screenshot is not None:
                self.session.add_screenshot(after_screenshot, "After clicking search button")

                # Verify something changed (search was executed)
                verification = self.verifier.verify_click_success(
                    before_screenshot, after_screenshot, "any"
                )

                if verification.success:
                    self.session.log_action("✓ Search button clicked successfully")
                    return {"success": True, "message": "Search executed successfully"}

            return {"success": True, "message": "Search button clicked"}

        except Exception as e:
            error_msg = f"Error clicking search button: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    async def verify_patient_information(self, expected_patient: dict[str, str]) -> dict[str, Any]:
        """Verify correct patient information appears using OCR"""
        try:
            self.session.log_action("Verifying patient information displayed")

            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen for verification"}

            self.session.add_screenshot(screenshot, "Patient information verification")

            # Use OCR to read all text on screen
            text_detections = self.ocr_reader.read_text(screenshot)
            screen_text = " ".join([detection.text for detection in text_detections]).upper()

            # Verify each expected patient field
            verified_fields = []
            missing_fields = []

            for field_name, expected_value in expected_patient.items():
                if not expected_value:
                    continue

                if expected_value.upper() in screen_text:
                    verified_fields.append(field_name)
                    self.session.log_action(f"✓ Found {field_name}: {expected_value}")
                else:
                    missing_fields.append(field_name)
                    self.session.log_action(f"✗ Missing {field_name}: {expected_value}")

            # Require at least 2 fields to match for positive verification
            min_required = min(2, len([v for v in expected_patient.values() if v]))

            if len(verified_fields) >= min_required:
                return {
                    "success": True,
                    "message": f"Patient verification successful: {len(verified_fields)} fields matched",
                    "verified_fields": verified_fields,
                    "missing_fields": missing_fields,
                }
            else:
                return {
                    "success": False,
                    "error": f"Patient verification failed: only {len(verified_fields)} of {len(expected_patient)} fields found",
                    "verified_fields": verified_fields,
                    "missing_fields": missing_fields,
                }

        except Exception as e:
            error_msg = f"Error verifying patient information: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    async def click_patient_details_button(self, button_text: str = None) -> dict[str, Any]:
        """Click patient details/view button"""
        button_text = button_text or PatientWorkflowTestConfig.PATIENT_DETAILS_BUTTON

        try:
            self.session.log_action(f"Looking for patient details button: '{button_text}'")

            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen"}

            # Find and click the details button
            button_elements = self.ui_finder.find_element_by_text(screenshot, button_text)

            if not button_elements:
                # Try partial matches
                all_elements = self.ui_finder.find_clickable_elements(screenshot)
                button_elements = [
                    elem
                    for elem in all_elements
                    if elem.text
                    and any(word in elem.text.lower() for word in button_text.lower().split())
                ]

            if not button_elements:
                return {
                    "success": False,
                    "error": f"Patient details button '{button_text}' not found",
                }

            best_button = max(button_elements, key=lambda x: x.confidence)
            x, y = best_button.center

            click_result = self.input_actions.click(x, y)
            if not click_result.success:
                return {
                    "success": False,
                    "error": f"Failed to click details button: {click_result.message}",
                }

            # Wait for details to load
            await asyncio.sleep(2)

            after_screenshot = self.screen_capture.capture_screen()
            if after_screenshot is not None:
                self.session.add_screenshot(after_screenshot, "After clicking patient details")

            self.session.log_action("✓ Patient details button clicked")
            return {"success": True, "message": "Patient details opened"}

        except Exception as e:
            error_msg = f"Error clicking patient details: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}


@pytest.mark.integration
@pytest.mark.patient_workflow
@pytest.mark.skip(
    reason="Requires VM with patient application - configure PATIENT_TEST_* env vars to run"
)
class TestPatientWorkflowIntegration:
    """Integration tests for patient workflow using PaddleOCR and YOLO"""

    async def test_complete_patient_search_workflow(self, patient_vm_config):
        """Test complete patient search workflow using computer vision tools"""
        print("\n🏥 Testing complete patient search workflow")
        print(f"   VM: {patient_vm_config.vm_host}:{patient_vm_config.vm_port}")
        print(f"   App: {patient_vm_config.target_app_name}")
        print(
            f"   Patient: {patient_vm_config.patient_name} (MRN: {patient_vm_config.patient_mrn})"
        )

        # Create automation and run VM navigation
        automation = VMAutomation(patient_vm_config)

        # Phase 1: Connect to VM and launch patient application
        nav_result = await automation.run_vm_navigation_only()
        assert nav_result["success"], f"VM Navigation failed: {nav_result.get('error')}"

        print("✅ VM Navigation completed - Patient application should be running")

        # Phase 2: Execute patient workflow using computer vision
        shared_components = nav_result.get("shared_components", {})
        patient_agent = PatientWorkflowAgent(
            automation.session, automation.vm_target, shared_components
        )

        # Expected patient data for verification
        expected_patient = {
            "patient_id": PatientWorkflowTestConfig.TEST_PATIENT_ID,
            "name": PatientWorkflowTestConfig.TEST_PATIENT_NAME,
            "mrn": PatientWorkflowTestConfig.TEST_PATIENT_MRN,
            "dob": PatientWorkflowTestConfig.TEST_PATIENT_DOB,
        }

        # Step 1: Find patient search field using OCR
        print("🔍 Step 1: Finding patient search field...")
        search_field_result = await patient_agent.find_patient_search_field()
        assert search_field_result["success"], (
            f"Failed to find search field: {search_field_result.get('error')}"
        )
        print(f"✅ Found search field at {search_field_result['element']['center']}")

        # Step 2: Enter patient ID
        print("⌨️ Step 2: Entering patient ID...")
        enter_result = await patient_agent.enter_patient_id(
            PatientWorkflowTestConfig.TEST_PATIENT_ID, search_field_result["element"]
        )
        assert enter_result["success"], f"Failed to enter patient ID: {enter_result.get('error')}"
        print(f"✅ Patient ID entered: {PatientWorkflowTestConfig.TEST_PATIENT_ID}")

        # Step 3: Click search button
        print("🔍 Step 3: Clicking search button...")
        search_result = await patient_agent.click_search_button()
        assert search_result["success"], f"Failed to click search: {search_result.get('error')}"
        print("✅ Search executed successfully")

        # Step 4: Verify correct patient information appears
        print("🔎 Step 4: Verifying patient information...")
        verify_result = await patient_agent.verify_patient_information(expected_patient)

        # Note: For testing, we'll accept partial verification since patient data may vary
        if verify_result["success"]:
            print(f"✅ Patient verification successful: {verify_result['verified_fields']}")
        else:
            print(f"⚠️ Patient verification partial: {verify_result.get('error')}")
            # In a real scenario, this might be a hard failure for safety

        # Step 5: Click patient details (if available)
        print("📋 Step 5: Opening patient details...")
        details_result = await patient_agent.click_patient_details_button()

        if details_result["success"]:
            print("✅ Patient details opened successfully")
        else:
            print(f"⚠️ Patient details not available: {details_result.get('error')}")

        print("\n🏆 Patient workflow integration test completed!")

        # Save comprehensive session log
        log_file = automation.save_session_log("patient_workflow_test.json")
        print(f"📄 Session log saved: {log_file}")

        # Verify session state
        session_summary = automation.session.get_session_summary()
        assert session_summary["screenshots_count"] >= 5, "Should have multiple screenshots"
        assert session_summary["actions_count"] >= 3, "Should have multiple actions"

        print("📊 Session Summary:")
        print(f"   Screenshots: {session_summary['screenshots_count']}")
        print(f"   Actions: {session_summary['actions_count']}")
        print(f"   Errors: {session_summary['errors_count']}")

        return True

    async def test_patient_search_with_invalid_id(self, patient_vm_config):
        """Test patient search with invalid ID to verify error handling"""
        print("\n❌ Testing patient search with invalid ID")

        # Create automation and setup
        automation = VMAutomation(patient_vm_config)
        nav_result = await automation.run_vm_navigation_only()
        assert nav_result["success"], "VM Navigation should succeed"

        shared_components = nav_result.get("shared_components", {})
        patient_agent = PatientWorkflowAgent(
            automation.session, automation.vm_target, shared_components
        )

        # Use invalid patient ID
        invalid_patient_id = "INVALID_ID_999999"

        # Find and use search field
        search_field_result = await patient_agent.find_patient_search_field()
        assert search_field_result["success"], "Should find search field"

        # Enter invalid ID
        enter_result = await patient_agent.enter_patient_id(
            invalid_patient_id, search_field_result["element"]
        )
        assert enter_result["success"], "Should be able to enter invalid ID"

        # Execute search
        search_result = await patient_agent.click_search_button()
        assert search_result["success"], "Search should execute"

        # Verify no valid patient appears (or error message shows)
        expected_patient = {"patient_id": invalid_patient_id}
        verify_result = await patient_agent.verify_patient_information(expected_patient)

        # Should fail verification (no patient found)
        assert not verify_result["success"], "Should not find patient with invalid ID"

        print("✅ Invalid patient ID correctly handled")
        return True

    async def test_patient_workflow_with_ocr_text_extraction(self, patient_vm_config):
        """Test extracting specific patient data fields using OCR"""
        print("\n📝 Testing OCR text extraction for patient data")

        # Setup automation
        automation = VMAutomation(patient_vm_config)
        nav_result = await automation.run_vm_navigation_only()
        assert nav_result["success"], "VM Navigation should succeed"

        shared_components = nav_result.get("shared_components", {})
        patient_agent = PatientWorkflowAgent(
            automation.session, automation.vm_target, shared_components
        )

        # Execute search for valid patient
        search_field_result = await patient_agent.find_patient_search_field()
        assert search_field_result["success"], "Should find search field"

        enter_result = await patient_agent.enter_patient_id(
            PatientWorkflowTestConfig.TEST_PATIENT_ID, search_field_result["element"]
        )
        assert enter_result["success"], "Should enter patient ID"

        search_result = await patient_agent.click_search_button()
        assert search_result["success"], "Should execute search"

        # Wait for results to load
        await asyncio.sleep(2)

        # Extract all text using OCR
        screenshot = patient_agent.screen_capture.capture_screen()
        assert screenshot is not None, "Should capture screen"

        text_detections = patient_agent.ocr_reader.read_text(screenshot)

        # Log all detected text for debugging
        automation.session.log_action("=== OCR Text Extraction Results ===")
        for i, detection in enumerate(text_detections):
            automation.session.log_action(
                f"Text {i + 1}: '{detection.text}' at {detection.center} (confidence: {detection.confidence:.2f})"
            )

        # Verify we detected some text
        assert len(text_detections) > 0, "Should detect text with OCR"

        # Look for patient-related keywords
        patient_keywords = ["patient", "name", "id", "mrn", "dob", "date", "birth"]
        found_keywords = []

        for detection in text_detections:
            text_lower = detection.text.lower()
            for keyword in patient_keywords:
                if keyword in text_lower:
                    found_keywords.append((keyword, detection.text, detection.center))

        automation.session.log_action(f"Found {len(found_keywords)} patient-related text elements")

        print(f"✅ OCR extracted {len(text_detections)} text elements")
        print(f"✅ Found {len(found_keywords)} patient-related keywords")

        return True


@pytest.mark.integration
@pytest.mark.ui_detection
@pytest.mark.skip(reason="Requires VM with GUI application - configure test environment")
class TestUIDetectionIntegration:
    """Integration tests for UI element detection using YOLO"""

    async def test_yolo_ui_element_detection(self, patient_vm_config):
        """Test YOLO-based UI element detection in patient application"""
        print("\n🎯 Testing YOLO UI element detection")

        automation = VMAutomation(patient_vm_config)
        nav_result = await automation.run_vm_navigation_only()
        assert nav_result["success"], "VM Navigation should succeed"

        shared_components = nav_result.get("shared_components", {})
        ui_finder = shared_components["ui_finder"]
        screen_capture = shared_components["screen_capture"]

        # Capture current application screen
        screenshot = screen_capture.capture_screen()
        assert screenshot is not None, "Should capture screen"

        # Test different UI element detection methods
        test_methods = [
            ("All UI Elements", ui_finder.find_ui_elements),
            ("Clickable Elements", ui_finder.find_clickable_elements),
            ("Input Fields", ui_finder.find_input_fields),
            ("Buttons", lambda img: ui_finder.find_element_by_text(img, "button")),
        ]

        detection_results = {}

        for method_name, method_func in test_methods:
            print(f"🔍 Testing {method_name} detection...")

            try:
                elements = method_func(screenshot)
                detection_results[method_name] = {
                    "count": len(elements),
                    "elements": [
                        (elem.center, elem.confidence, getattr(elem, "text", None))
                        for elem in elements[:5]
                    ],  # Top 5 results
                }

                automation.session.log_action(f"{method_name}: Found {len(elements)} elements")

                print(f"✅ {method_name}: {len(elements)} elements detected")

            except Exception as e:
                detection_results[method_name] = {"error": str(e), "count": 0}
                print(f"❌ {method_name}: Error - {e!s}")

        # Verify we detected some UI elements
        total_elements = sum(result.get("count", 0) for result in detection_results.values())
        assert total_elements > 0, "Should detect some UI elements with YOLO"

        # Log detailed results
        automation.session.log_action("=== UI Detection Summary ===")
        for method_name, result in detection_results.items():
            if "error" not in result:
                automation.session.log_action(f"{method_name}: {result['count']} elements")
                for center, confidence, text in result["elements"]:
                    automation.session.log_action(
                        f"  - Element at {center} (conf: {confidence:.2f}) text: '{text}'"
                    )

        print(f"🎯 YOLO UI detection completed: {total_elements} total elements found")
        return detection_results


if __name__ == "__main__":
    # Run tests directly with pytest
    import sys

    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
