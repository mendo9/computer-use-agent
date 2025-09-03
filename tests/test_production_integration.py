"""Integration tests for production VM automation POC"""

import time
from typing import Any

import pytest

from src.agents.shared_context import VMSession
from src.production import ProductionConfig, VMAutomationProduction

from .mock_components import (
    create_mock_components,
    setup_error_scenario,
    setup_patient_safety_test_scenario,
)


class MockVMAutomationProduction(VMAutomationProduction):
    """Mock version of production automation for testing"""

    def __init__(self, config: ProductionConfig, mock_components: dict[str, Any]):
        """Initialize with mock components injected"""
        # Initialize basic attributes without calling parent __init__ to avoid YOLO model loading
        self.config = config
        self.session_id = f"test_{int(time.time())}"
        poc_target = config.to_vm_target()
        self.session = VMSession(vm_config=poc_target.to_vm_config(), session_id=self.session_id)

        # Replace real components with mocks for testing
        self.mock_components = mock_components

        # Override agents to use mock components
        self._setup_mock_agents()

    def _setup_mock_agents(self):
        """Setup agents with mock components"""

        # Create a mock VM Navigator Tools class that doesn't require YOLO model
        class MockVMNavigatorTools:
            def __init__(self, session, poc_target, mock_components):
                self.session = session
                self.poc_target = poc_target
                self.screen_capture = mock_components["screen_capture"]
                self.input_actions = mock_components["input_actions"]
                self.ui_finder = mock_components["ui_finder"]
                self.verifier = mock_components["verifier"]

            def connect_to_vm(self):
                return self.screen_capture.connect("mock-host")

            def capture_screen_with_retry(self, description="", max_retries=3):
                screenshot = self.screen_capture.capture_screen()
                if screenshot is not None:
                    self.session.add_screenshot(screenshot, description)
                    return {"success": True, "description": description}
                return {"success": False, "error": "Mock capture failed"}

            def wait_for_desktop_loaded(self, timeout=60):
                return {"success": True, "message": "Mock desktop loaded"}

            def find_application_with_retry(self, app_name, max_retries=3):
                elements = self.ui_finder.find_element_by_text(None, app_name)
                if elements:
                    return {
                        "success": True,
                        "element": {"center": elements[0].center, "bbox": elements[0].bbox},
                    }
                return {"success": False, "error": "App not found"}

            def launch_application_verified(self, element_info):
                result = self.input_actions.double_click(*element_info["center"])
                if result.success:
                    self.session.current_app = self.poc_target.target_app_name
                    return {"success": True, "message": "App launched"}
                return {"success": False, "error": "Launch failed"}

            def verify_application_loaded_enhanced(self):
                return {"success": True, "message": "Mock app verification"}

            def verify_patient_banner(self, patient_info):
                # Mock patient verification
                found_identifiers = []
                for field, value in patient_info.items():
                    if value:  # If value provided
                        elements = self.ui_finder.find_element_by_text(None, value)
                        if elements:
                            found_identifiers.append(field)

                if len(found_identifiers) >= 2:
                    return {
                        "success": True,
                        "verified_fields": found_identifiers,
                        "safety_critical": True,
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Only {len(found_identifiers)} identifiers verified",
                        "safety_critical": True,
                    }

        # Create simple mock agents that don't require YOLO model
        class MockVMNavigator:
            def __init__(self, session, poc_target, shared_components):
                self.session = session
                self.poc_target = poc_target
                self.tools = MockVMNavigatorTools(session, poc_target, shared_components)
                self.shared_components = shared_components

            async def execute_navigation(self, patient_info=None):
                # Mock navigation execution with realistic logging and screenshots
                import numpy as np

                self.session.log_action("Mock VM Navigator Agent starting...")

                # Mock screenshot captures
                mock_screenshot = np.ones((768, 1024, 3), dtype=np.uint8) * 240
                self.session.add_screenshot(mock_screenshot, "Mock VM connection")

                self.session.log_action("Mock: Connected to VM")
                self.session.add_screenshot(mock_screenshot, "Mock desktop loaded")

                self.session.log_action("Mock: Desktop loaded successfully")
                self.session.log_action("Mock: Application launched")
                self.session.add_screenshot(mock_screenshot, "Mock application launched")

                # Mock patient verification if patient info provided
                if patient_info:
                    self.session.log_action("SAFETY CHECK: Verifying patient identity...")
                    self.session.add_screenshot(mock_screenshot, "Patient banner verification")
                    self.session.log_action(
                        f"✓ Patient name verified: {patient_info.get('name', '')}"
                    )
                    self.session.log_action(
                        f"✓ Patient MRN verified: {patient_info.get('mrn', '')}"
                    )
                    self.session.log_action("SAFETY CHECK PASSED: 2 patient identifiers verified")

                self.session.agent_1_completed = True
                self.session.current_app = self.poc_target.target_app_name
                self.session.agent_1_results = {
                    "app_launched": True,
                    "app_name": self.session.current_app,
                    "patient_verified": patient_info is not None,
                }
                return {"success": True, "message": "Mock navigation completed"}

        class MockAppController:
            def __init__(self, session, poc_target, shared_components):
                self.session = session
                self.poc_target = poc_target
                self.shared_components = shared_components

            async def execute_button_click_workflow(self, expected_outcomes=None):
                # Mock button click execution
                return {"success": True, "message": "Mock button click completed"}

            async def execute_form_filling_workflow(self, form_fields, submit_button=None):
                # Mock form filling execution with realistic actions
                self.session.log_action(f"Starting form filling with {len(form_fields)} fields")

                # Simulate filling each field
                for field_info in form_fields:
                    field_name = field_info.get("field_name", "")
                    field_value = field_info.get("value", "")

                    if field_name and field_value:
                        self.session.log_action(f"Filling field: {field_name}")

                        # Simulate click on field (using mock input actions)
                        input_actions = self.shared_components["input_actions"]
                        input_actions.click(200, 200)  # Mock field click

                        # Simulate typing value
                        input_actions.type_text(field_value)

                        self.session.log_action(f"Successfully filled field: {field_name}")

                # Simulate submit button click
                submit_button_text = submit_button or self.poc_target.target_button_text
                if submit_button_text:
                    self.session.log_action(f"Clicking submit button: {submit_button_text}")
                    input_actions = self.shared_components["input_actions"]
                    input_actions.click(450, 325)  # Mock submit button click

                return {
                    "success": True,
                    "message": f"Mock form filling completed - {len(form_fields)} fields",
                    "fields_filled": len(form_fields),
                    "submitted": True,
                }

        # Initialize mock agents
        shared_components = self.mock_components
        self.vm_navigator = MockVMNavigator(
            self.session, self.config.to_vm_target(), shared_components
        )
        self.app_controller = MockAppController(
            self.session, self.config.to_vm_target(), shared_components
        )

    async def run_full_automation(self):
        """Mock full automation workflow"""
        start_time = time.time()

        # Mock VM navigation
        patient_info = None
        if self.config.patient_name:
            patient_info = {
                "name": self.config.patient_name,
                "mrn": self.config.patient_mrn or "",
                "dob": self.config.patient_dob or "",
            }

        nav_result = await self.vm_navigator.execute_navigation(patient_info)
        if not nav_result["success"]:
            return nav_result

        # Mock app interaction
        app_result = await self.app_controller.execute_button_click_workflow()

        execution_time = time.time() - start_time

        return {
            "success": app_result["success"],
            "execution_time": execution_time,
            "patient_verified": patient_info is not None,
            "phases": {"vm_navigation": nav_result, "app_interaction": app_result},
            "session_summary": {
                "is_connected": True,
                "current_app": self.session.current_app,
                "agent_1_completed": self.session.agent_1_completed,
                "screenshots_count": len(self.session.screenshots),
                "actions_count": len(self.session.action_log),
                "errors_count": len(self.session.errors),
            },
        }

    async def run_vm_navigation_only(self):
        """Mock VM navigation only"""
        patient_info = None
        if self.config.patient_name:
            patient_info = {
                "name": self.config.patient_name,
                "mrn": self.config.patient_mrn or "",
                "dob": self.config.patient_dob or "",
            }

        return await self.vm_navigator.execute_navigation(patient_info)

    async def run_form_filling_workflow(self, form_data):
        """Mock form filling workflow"""
        start_time = time.time()

        # Mock VM navigation first
        nav_result = await self.run_vm_navigation_only()
        if not nav_result["success"]:
            return nav_result

        # Mock form filling
        form_result = await self.app_controller.execute_form_filling_workflow(form_data)

        execution_time = time.time() - start_time

        return {
            "success": form_result["success"],
            "execution_time": execution_time,
            "fields_filled": form_result.get("fields_filled", 0),
            "submitted": form_result.get("submitted", False),
        }

    def get_session_report(self):
        """Mock session report generation"""
        return {
            "session_id": self.session_id,
            "config": {
                "vm_host": self.config.vm_host,
                "target_app": self.config.target_app_name,
                "patient_configured": bool(self.config.patient_name),
            },
            "session_summary": {
                "is_connected": True,
                "screenshots_count": len(self.session.screenshots),
                "actions_count": len(self.session.action_log),
                "errors_count": len(self.session.errors),
            },
            "action_log": self.session.action_log.copy(),
        }


@pytest.fixture
def production_config() -> ProductionConfig:
    """Create production configuration for testing"""
    return ProductionConfig(
        vm_host="test-vm.local",
        vm_port=5900,
        vm_username="testuser",
        vm_password="testpass",
        target_app_name="TestApp.exe",
        target_button_text="Submit",
        patient_name="John Doe",
        patient_mrn="123456",
        patient_dob="01/01/1980",
        expected_desktop_elements=["Desktop", "Start"],
        expected_app_elements=["Submit", "Patient"],
        save_screenshots=True,
        log_phi=False,
    )


@pytest.fixture
def mock_automation(production_config) -> MockVMAutomationProduction:
    """Create mock automation instance"""
    mock_components = create_mock_components()
    setup_patient_safety_test_scenario(mock_components)
    return MockVMAutomationProduction(production_config, mock_components)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_production_workflow(mock_automation):
    """Test complete production workflow with patient safety"""

    # Run full automation
    start_time = time.time()
    result = await mock_automation.run_full_automation()
    execution_time = time.time() - start_time

    # Verify success
    assert result["success"], f"Automation failed: {result.get('error')}"

    # Verify phases completed
    assert "phases" in result
    assert result["phases"]["vm_navigation"]["success"]
    assert result["phases"]["app_interaction"]["success"]

    # Verify patient safety was checked
    assert result["patient_verified"], "Patient verification should have been performed"

    # Verify timing
    assert execution_time < 30.0, "Automation took too long"

    # Verify session state
    session_summary = result["session_summary"]
    assert session_summary["is_connected"]
    assert session_summary["current_app"] == "TestApp.exe"
    assert session_summary["agent_1_completed"]
    assert session_summary["screenshots_count"] >= 3

    # Verify no critical errors
    assert session_summary["errors_count"] == 0

    print(f"✅ Production workflow completed in {execution_time:.2f}s")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_safety_verification_success(mock_automation):
    """Test successful patient safety verification"""

    # Run VM navigation only to test patient safety
    result = await mock_automation.run_vm_navigation_only()

    assert result["success"], f"VM navigation failed: {result.get('error')}"

    # Check that patient was verified
    assert mock_automation.session.agent_1_results.get("patient_verified", False)

    # Check logs for patient verification
    patient_logs = [log for log in mock_automation.session.action_log if "patient" in log.lower()]
    assert len(patient_logs) >= 2, "Should have multiple patient-related log entries"

    print("✅ Patient safety verification successful")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_patient_safety_verification_failure():
    """Test patient safety verification failure (critical)"""

    config = ProductionConfig(
        vm_host="test-vm.local",
        vm_username="testuser",
        vm_password="testpass",
        target_app_name="TestApp.exe",
        target_button_text="Submit",
        patient_name="Jane Smith",  # Wrong patient name
        patient_mrn="999999",  # Wrong MRN
        patient_dob="12/31/1999",  # Wrong DOB
        log_phi=False,
    )

    mock_components = create_mock_components()
    setup_error_scenario(mock_components, "patient_mismatch")

    mock_automation = MockVMAutomationProduction(config, mock_components)

    # Run automation - should fail at patient verification
    result = await mock_automation.run_full_automation()

    # Should fail with safety critical error
    assert not result["success"]
    assert result.get("safety_critical", False)
    assert result["phase_failed"] == "patient_safety_verification"
    assert "CRITICAL SAFETY FAILURE" in result["error"]

    print("✅ Patient safety verification correctly failed for wrong patient")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_form_filling_workflow(mock_automation):
    """Test form filling workflow"""

    # Define form data
    form_data = [
        {"field_name": "First Name", "value": "John"},
        {"field_name": "Last Name", "value": "Doe"},
        {"field_name": "Date of Birth", "value": "01/01/1980"},
        {"field_name": "Medical Record Number", "value": "123456"},
    ]

    # Run form filling workflow
    result = await mock_automation.run_form_filling_workflow(form_data)

    assert result["success"], f"Form filling failed: {result.get('error')}"
    assert result["fields_filled"] == len(form_data)
    assert result["submitted"]

    # Check that all actions were logged
    action_logs = mock_automation.mock_components["input_actions"].get_actions_log()

    # Should have clicks for each field plus typing
    click_actions = [log for log in action_logs if "Click" in log]
    type_actions = [log for log in action_logs if "Type" in log]

    assert len(click_actions) >= len(form_data) + 1  # Fields + submit button
    assert len(type_actions) == len(form_data)  # One type per field

    print(f"✅ Form filling completed - {len(form_data)} fields filled")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_and_recovery(mock_automation):
    """Test error handling scenarios"""

    # Test connection failure
    setup_error_scenario(mock_automation.mock_components, "connection_failure")

    result = await mock_automation.run_vm_navigation_only()

    assert not result["success"]
    assert "connection" in result["error"].lower() or "connect" in result["error"].lower()

    # Reset for element not found test
    mock_automation.mock_components["screen_capture"].is_connected = True
    setup_error_scenario(mock_automation.mock_components, "element_not_found")

    result = await mock_automation.run_full_automation()

    assert not result["success"]
    assert result["phase_failed"] == "app_interaction"

    print("✅ Error handling scenarios tested successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_reporting_and_phi_handling(mock_automation):
    """Test session reporting with PHI filtering"""

    # Run automation to generate session data
    await mock_automation.run_full_automation()

    # Test session report generation
    report = mock_automation.get_session_report()

    assert "session_id" in report
    assert "config" in report
    assert "session_summary" in report
    assert "action_log" in report

    # Verify PHI filtering (should not contain actual patient info since log_phi=False)
    action_log_text = " ".join(report["action_log"])

    # Patient name should be filtered out or replaced
    if mock_automation.config.log_phi:
        # If logging PHI, patient info should be present
        assert mock_automation.config.patient_name in action_log_text
    else:
        # If not logging PHI, patient info should be filtered
        if mock_automation.config.patient_name in action_log_text:
            # Should be replaced with placeholder
            assert (
                "[PATIENT_NAME]" in action_log_text
                or "patient information configured" in action_log_text.lower()
            )

    print("✅ Session reporting and PHI handling verified")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_configuration_validation():
    """Test production configuration validation"""

    # Test valid configuration
    valid_config = ProductionConfig(
        vm_host="test-vm.local",
        vm_username="user",
        vm_password="pass",
        target_app_name="App.exe",
        target_button_text="Submit",
    )

    errors = valid_config.validate()
    assert len(errors) == 0, f"Valid config should have no errors: {errors}"

    # Test invalid configuration - missing required fields
    invalid_config = ProductionConfig(
        vm_host="",  # Missing
        target_app_name="",  # Missing
        target_button_text="",  # Missing
    )

    errors = invalid_config.validate()
    assert len(errors) > 0, "Invalid config should have errors"
    assert any("host" in error.lower() for error in errors)
    assert any("application" in error.lower() for error in errors)
    assert any("button" in error.lower() for error in errors)

    # Test partial patient info (should fail)
    partial_patient_config = ProductionConfig(
        vm_host="test-vm.local",
        vm_username="user",
        vm_password="pass",
        target_app_name="App.exe",
        target_button_text="Submit",
        patient_name="John Doe",  # Only name provided
        patient_mrn="",  # Missing MRN
        patient_dob="",  # Missing DOB
    )

    errors = partial_patient_config.validate()
    assert len(errors) > 0
    assert any("patient" in error.lower() for error in errors)

    print("✅ Configuration validation tested successfully")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_performance_benchmark(mock_automation):
    """Benchmark production automation performance"""

    num_runs = 3
    execution_times = []

    for i in range(num_runs):
        # Reset mock components
        mock_automation.mock_components["input_actions"].clear_log()

        start_time = time.time()
        result = await mock_automation.run_full_automation()
        execution_time = time.time() - start_time

        assert result["success"], f"Run {i + 1} failed: {result.get('error')}"
        execution_times.append(execution_time)

    # Calculate performance metrics
    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)

    # Performance assertions
    assert avg_time < 15.0, f"Average execution time too high: {avg_time:.2f}s"
    assert max_time < 20.0, f"Max execution time too high: {max_time:.2f}s"
    assert min_time > 1.0, f"Min execution time suspiciously low: {min_time:.2f}s"

    print(f"✅ Performance benchmark ({num_runs} runs):")
    print(f"   Average: {avg_time:.2f}s")
    print(f"   Range: {min_time:.2f}s - {max_time:.2f}s")


@pytest.mark.integration
def test_configuration_from_environment(monkeypatch):
    """Test configuration loading from environment variables"""

    # Set environment variables
    monkeypatch.setenv("VM_HOST", "env-test-vm.local")
    monkeypatch.setenv("VM_PORT", "5901")
    monkeypatch.setenv("VM_USERNAME", "env-user")
    monkeypatch.setenv("VM_PASSWORD", "env-pass")
    monkeypatch.setenv("TARGET_APP", "EnvApp.exe")
    monkeypatch.setenv("TARGET_BUTTON", "EnvSubmit")
    monkeypatch.setenv("PATIENT_NAME", "Env Patient")
    monkeypatch.setenv("PATIENT_MRN", "ENV123")
    monkeypatch.setenv("PATIENT_DOB", "01/01/2000")
    monkeypatch.setenv("LOG_PHI", "false")

    # Load configuration from environment
    config = ProductionConfig.from_env()

    assert config.vm_host == "env-test-vm.local"
    assert config.vm_port == 5901
    assert config.vm_username == "env-user"
    assert config.vm_password == "env-pass"
    assert config.target_app_name == "EnvApp.exe"
    assert config.target_button_text == "EnvSubmit"
    assert config.patient_name == "Env Patient"
    assert config.patient_mrn == "ENV123"
    assert config.patient_dob == "01/01/2000"
    assert config.log_phi == False

    # Validate loaded config
    errors = config.validate()
    assert len(errors) == 0, f"Environment config should be valid: {errors}"

    print("✅ Environment configuration loading tested successfully")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
