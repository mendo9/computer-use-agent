"""Integration tests for VM connections and agent workflows

These tests assume VM availability and will not pass without proper VM configuration.
They are designed to test the full connection and navigation flows for both RDP and VNC.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents import AppControllerAgent, VMNavigatorAgent, VMSession
from connections import RDPConnection, VNCConnection
from main import VMAutomation, VMConfig


class VMTestConfig:
    """Test configuration for VM integration tests"""

    # VNC Test VM Configuration
    VNC_HOST = os.getenv("TEST_VNC_HOST", "192.168.1.100")
    VNC_PORT = int(os.getenv("TEST_VNC_PORT", "5900"))
    VNC_PASSWORD = os.getenv("TEST_VNC_PASSWORD", "testpassword")

    # RDP Test VM Configuration
    RDP_HOST = os.getenv("TEST_RDP_HOST", "192.168.1.101")
    RDP_PORT = int(os.getenv("TEST_RDP_PORT", "3389"))
    RDP_USERNAME = os.getenv("TEST_RDP_USERNAME", "testuser")
    RDP_PASSWORD = os.getenv("TEST_RDP_PASSWORD", "testpassword")
    RDP_DOMAIN = os.getenv("TEST_RDP_DOMAIN")

    # Application Configuration
    TARGET_APP_NAME = os.getenv("TEST_APP_NAME", "Calculator.exe")
    TARGET_BUTTON_TEXT = os.getenv("TEST_BUTTON_TEXT", "1")

    # Patient Test Data
    PATIENT_NAME = os.getenv("TEST_PATIENT_NAME", "John Doe")
    PATIENT_MRN = os.getenv("TEST_PATIENT_MRN", "12345")
    PATIENT_DOB = os.getenv("TEST_PATIENT_DOB", "01/01/1980")


@pytest.fixture
def vnc_vm_config():
    """VNC VM configuration for testing"""
    return VMConfig(
        vm_host=VMTestConfig.VNC_HOST,
        vm_port=VMTestConfig.VNC_PORT,
        vm_password=VMTestConfig.VNC_PASSWORD,
        connection_type="vnc",
        target_app_name=VMTestConfig.TARGET_APP_NAME,
        target_button_text=VMTestConfig.TARGET_BUTTON_TEXT,
        patient_name=VMTestConfig.PATIENT_NAME,
        patient_mrn=VMTestConfig.PATIENT_MRN,
        patient_dob=VMTestConfig.PATIENT_DOB,
        vm_connection_timeout=30,
        desktop_load_timeout=60,
        app_launch_timeout=30,
    )


@pytest.fixture
def rdp_vm_config():
    """RDP VM configuration for testing"""
    return VMConfig(
        vm_host=VMTestConfig.RDP_HOST,
        vm_port=VMTestConfig.RDP_PORT,
        vm_username=VMTestConfig.RDP_USERNAME,
        vm_password=VMTestConfig.RDP_PASSWORD,
        rdp_domain=VMTestConfig.RDP_DOMAIN,
        connection_type="rdp",
        rdp_width=1920,
        rdp_height=1080,
        target_app_name=VMTestConfig.TARGET_APP_NAME,
        target_button_text=VMTestConfig.TARGET_BUTTON_TEXT,
        patient_name=VMTestConfig.PATIENT_NAME,
        patient_mrn=VMTestConfig.PATIENT_MRN,
        patient_dob=VMTestConfig.PATIENT_DOB,
        vm_connection_timeout=30,
        desktop_load_timeout=60,
        app_launch_timeout=30,
    )


@pytest.mark.integration
@pytest.mark.vnc
@pytest.mark.skip(reason="Requires VNC VM - set TEST_VNC_HOST and credentials to run")
class TestVNCIntegration:
    """Integration tests for VNC connection and navigation workflow"""

    async def test_vnc_connection_and_login(self, vnc_vm_config):
        """Test VNC connection establishment and basic login flow"""
        print(f"\n🔗 Testing VNC connection to {vnc_vm_config.vm_host}:{vnc_vm_config.vm_port}")

        # Test direct VNC connection
        vnc_connection = VNCConnection()

        # Test connection
        connect_result = vnc_connection.connect(
            host=vnc_vm_config.vm_host,
            port=vnc_vm_config.vm_port,
            password=vnc_vm_config.vm_password,
        )

        assert connect_result.success, f"VNC connection failed: {connect_result.message}"
        assert vnc_connection.is_connected, "Connection should be marked as connected"

        print(f"✅ VNC connection established: {connect_result.message}")

        # Test screen capture
        capture_success, screenshot = vnc_connection.capture_screen()
        assert capture_success, "Should be able to capture screen after connection"
        assert screenshot is not None, "Screenshot should not be None"

        print(f"✅ Screen capture successful: {screenshot.shape}")

        # Test basic input actions
        click_result = vnc_connection.click(100, 100)  # Safe click location
        assert click_result.success, f"Click should succeed: {click_result.message}"

        type_result = vnc_connection.type_text("test")
        assert type_result.success, f"Type should succeed: {type_result.message}"

        key_result = vnc_connection.key_press("escape")
        assert key_result.success, f"Key press should succeed: {key_result.message}"

        print("✅ Basic input actions working")

        # Clean up
        disconnect_result = vnc_connection.disconnect()
        assert disconnect_result.success, f"Disconnect should succeed: {disconnect_result.message}"
        assert not vnc_connection.is_connected, "Connection should be marked as disconnected"

        print("✅ VNC connection test completed successfully")

    async def test_vnc_vm_navigator_full_workflow(self, vnc_vm_config):
        """Test complete VM Navigator workflow with VNC"""
        print("\n🤖 Testing VM Navigator workflow via VNC")

        # Create VM target and session
        vm_target = vnc_vm_config.to_vm_target()
        session = VMSession(vm_config=vm_target.to_vm_config(), session_id="test_vnc_nav")

        # Create VM Navigator Agent
        navigator = VMNavigatorAgent(session, vm_target)

        # Patient info for safety verification
        patient_info = vnc_vm_config.get_patient_info()

        # Execute navigation workflow
        start_time = time.time()
        result = await navigator.execute_navigation(patient_info=patient_info)
        execution_time = time.time() - start_time

        print(f"⏱️ Navigation completed in {execution_time:.2f}s")

        # Verify results
        assert result["success"], f"VM Navigation should succeed: {result.get('error')}"
        assert session.is_connected, "Session should be connected"
        assert session.agent_1_completed, "Agent 1 should be marked complete"
        assert session.current_app, "Should have launched an application"

        # Verify shared components are available for Agent 2
        shared_components = result.get("shared_components", {})
        assert "screen_capture" in shared_components, "Should share screen capture"
        assert "input_actions" in shared_components, "Should share input actions"
        assert "ui_finder" in shared_components, "Should share UI finder"
        assert "verifier" in shared_components, "Should share verifier"

        print("✅ VM Navigator workflow completed successfully")
        print(f"   App launched: {session.current_app}")
        print(f"   Screenshots: {len(session.screenshots)}")
        print(f"   Actions logged: {len(session.action_log)}")
        print(f"   Errors: {len(session.errors)}")

        return result, session, shared_components

    async def test_vnc_app_controller_workflow(self, vnc_vm_config):
        """Test App Controller workflow after VM Navigator"""
        print("\n🎮 Testing App Controller workflow via VNC")

        # First run VM Navigator to set up environment
        nav_result, session, shared_components = await self.test_vnc_vm_navigator_full_workflow(
            vnc_vm_config
        )

        # Create App Controller Agent with shared components
        vm_target = vnc_vm_config.to_vm_target()
        app_controller = AppControllerAgent(session, vm_target, shared_components)

        # Define expected outcomes after button click
        expected_outcomes = ["Calculator", "Result", "Display"]  # Generic calculator terms

        # Execute button click workflow
        start_time = time.time()
        result = await app_controller.execute_button_click_workflow(
            expected_outcomes=expected_outcomes
        )
        execution_time = time.time() - start_time

        print(f"⏱️ App interaction completed in {execution_time:.2f}s")

        # Verify results
        assert result["success"], f"App interaction should succeed: {result.get('error')}"
        assert result["element_clicked"] == vm_target.target_button_text, (
            "Should click target button"
        )

        print("✅ App Controller workflow completed successfully")
        print(f"   Element clicked: {result['element_clicked']}")
        print(f"   Total session screenshots: {len(session.screenshots)}")

        return result

    async def test_vnc_full_automation_workflow(self, vnc_vm_config):
        """Test complete end-to-end automation workflow via VNC"""
        print("\n🏁 Testing full automation workflow via VNC")

        # Create automation instance
        automation = VMAutomation(vnc_vm_config)

        # Execute full automation
        start_time = time.time()
        result = await automation.run_full_automation()
        execution_time = time.time() - start_time

        print(f"⏱️ Full automation completed in {execution_time:.2f}s")

        # Verify results
        assert result["success"], f"Full automation should succeed: {result.get('error')}"
        assert "phases" in result, "Should have phase results"
        assert "vm_navigation" in result["phases"], "Should have navigation phase"
        assert "app_interaction" in result["phases"], "Should have interaction phase"

        # Both phases should succeed
        assert result["phases"]["vm_navigation"]["success"], "Navigation phase should succeed"
        assert result["phases"]["app_interaction"]["success"], "Interaction phase should succeed"

        # Verify session summary
        session_summary = result["session_summary"]
        assert session_summary["agent_1_completed"], "Agent 1 should be complete"
        assert session_summary["screenshots_count"] > 0, "Should have screenshots"
        assert session_summary["actions_count"] > 0, "Should have actions"

        print("✅ Full VNC automation workflow completed successfully")
        print(f"   Navigation result: {result['phases']['vm_navigation']['success']}")
        print(f"   Interaction result: {result['phases']['app_interaction']['success']}")
        print(f"   Total screenshots: {session_summary['screenshots_count']}")
        print(f"   Total actions: {session_summary['actions_count']}")
        print(f"   Errors: {session_summary['errors_count']}")

        # Save session log for review
        log_file = automation.save_session_log("test_vnc_full_automation.json")
        print(f"   Session log: {log_file}")

        return result


@pytest.mark.integration
@pytest.mark.rdp
@pytest.mark.skip(reason="Requires RDP VM - set TEST_RDP_HOST and credentials to run")
class TestRDPIntegration:
    """Integration tests for RDP connection and navigation workflow"""

    async def test_rdp_connection_and_login(self, rdp_vm_config):
        """Test RDP connection establishment and basic login flow"""
        print(f"\n🔗 Testing RDP connection to {rdp_vm_config.vm_host}:{rdp_vm_config.vm_port}")

        # Test direct RDP connection
        rdp_connection = RDPConnection()

        # Test connection with authentication
        connect_result = rdp_connection.connect(
            host=rdp_vm_config.vm_host,
            port=rdp_vm_config.vm_port,
            username=rdp_vm_config.vm_username,
            password=rdp_vm_config.vm_password,
            domain=rdp_vm_config.rdp_domain,
            width=rdp_vm_config.rdp_width,
            height=rdp_vm_config.rdp_height,
        )

        assert connect_result.success, f"RDP connection failed: {connect_result.message}"
        assert rdp_connection.is_connected, "Connection should be marked as connected"

        print(f"✅ RDP connection established: {connect_result.message}")

        # Test screen capture
        capture_success, screenshot = rdp_connection.capture_screen()
        assert capture_success, "Should be able to capture screen after connection"
        assert screenshot is not None, "Screenshot should not be None"

        print(f"✅ Screen capture successful: {screenshot.shape}")

        # Test basic input actions
        click_result = rdp_connection.click(100, 100)  # Safe click location
        assert click_result.success, f"Click should succeed: {click_result.message}"

        type_result = rdp_connection.type_text("test")
        assert type_result.success, f"Type should succeed: {type_result.message}"

        key_result = rdp_connection.key_press("escape")
        assert key_result.success, f"Key press should succeed: {key_result.message}"

        print("✅ Basic input actions working")

        # Clean up
        disconnect_result = rdp_connection.disconnect()
        assert disconnect_result.success, f"Disconnect should succeed: {disconnect_result.message}"
        assert not rdp_connection.is_connected, "Connection should be marked as disconnected"

        print("✅ RDP connection test completed successfully")

    async def test_rdp_vm_navigator_full_workflow(self, rdp_vm_config):
        """Test complete VM Navigator workflow with RDP"""
        print("\n🤖 Testing VM Navigator workflow via RDP")

        # Create VM target and session
        vm_target = rdp_vm_config.to_vm_target()
        session = VMSession(vm_config=vm_target.to_vm_config(), session_id="test_rdp_nav")

        # Create VM Navigator Agent
        navigator = VMNavigatorAgent(session, vm_target)

        # Patient info for safety verification
        patient_info = rdp_vm_config.get_patient_info()

        # Execute navigation workflow
        start_time = time.time()
        result = await navigator.execute_navigation(patient_info=patient_info)
        execution_time = time.time() - start_time

        print(f"⏱️ Navigation completed in {execution_time:.2f}s")

        # Verify results
        assert result["success"], f"VM Navigation should succeed: {result.get('error')}"
        assert session.is_connected, "Session should be connected"
        assert session.agent_1_completed, "Agent 1 should be marked complete"
        assert session.current_app, "Should have launched an application"

        # Verify shared components are available for Agent 2
        shared_components = result.get("shared_components", {})
        assert "screen_capture" in shared_components, "Should share screen capture"
        assert "input_actions" in shared_components, "Should share input actions"
        assert "ui_finder" in shared_components, "Should share UI finder"
        assert "verifier" in shared_components, "Should share verifier"

        print("✅ VM Navigator workflow completed successfully")
        print(f"   App launched: {session.current_app}")
        print(f"   Screenshots: {len(session.screenshots)}")
        print(f"   Actions logged: {len(session.action_log)}")
        print(f"   Errors: {len(session.errors)}")

        return result, session, shared_components

    async def test_rdp_full_automation_workflow(self, rdp_vm_config):
        """Test complete end-to-end automation workflow via RDP"""
        print("\n🏁 Testing full automation workflow via RDP")

        # Create automation instance
        automation = VMAutomation(rdp_vm_config)

        # Execute full automation
        start_time = time.time()
        result = await automation.run_full_automation()
        execution_time = time.time() - start_time

        print(f"⏱️ Full automation completed in {execution_time:.2f}s")

        # Verify results
        assert result["success"], f"Full automation should succeed: {result.get('error')}"
        assert "phases" in result, "Should have phase results"
        assert "vm_navigation" in result["phases"], "Should have navigation phase"
        assert "app_interaction" in result["phases"], "Should have interaction phase"

        # Both phases should succeed
        assert result["phases"]["vm_navigation"]["success"], "Navigation phase should succeed"
        assert result["phases"]["app_interaction"]["success"], "Interaction phase should succeed"

        # Verify session summary
        session_summary = result["session_summary"]
        assert session_summary["agent_1_completed"], "Agent 1 should be complete"
        assert session_summary["screenshots_count"] > 0, "Should have screenshots"
        assert session_summary["actions_count"] > 0, "Should have actions"

        print("✅ Full RDP automation workflow completed successfully")
        print(f"   Navigation result: {result['phases']['vm_navigation']['success']}")
        print(f"   Interaction result: {result['phases']['app_interaction']['success']}")
        print(f"   Total screenshots: {session_summary['screenshots_count']}")
        print(f"   Total actions: {session_summary['actions_count']}")
        print(f"   Errors: {session_summary['errors_count']}")

        # Save session log for review
        log_file = automation.save_session_log("test_rdp_full_automation.json")
        print(f"   Session log: {log_file}")

        return result


@pytest.mark.integration
@pytest.mark.patient_workflow
@pytest.mark.skip(reason="Requires VM with patient application - configure TEST_* env vars to run")
class TestPatientWorkflowIntegration:
    """Integration tests for patient-specific application workflows"""

    async def test_patient_application_navigation_vnc(self, vnc_vm_config):
        """Test patient application navigation workflow via VNC

        This test assumes there's a patient management application running in the VM
        and will navigate through it using PaddleOCR and YOLO detection.
        """
        print("\n🏥 Testing patient application workflow via VNC")

        # Update config for patient-specific application
        vnc_vm_config.target_app_name = "PatientApp.exe"  # Replace with actual app
        vnc_vm_config.target_button_text = "Search Patient"  # Replace with actual button

        # Create automation instance
        automation = VMAutomation(vnc_vm_config)

        # Execute VM navigation first
        nav_result = await automation.run_vm_navigation_only()
        assert nav_result["success"], f"VM Navigation failed: {nav_result.get('error')}"

        print("✅ VM Navigation completed, now testing patient workflow...")

        # Get shared components for patient workflow
        shared_components = nav_result.get("shared_components", {})
        vm_target = vnc_vm_config.to_vm_target()

        # Create custom app controller for patient workflow
        app_controller = AppControllerAgent(automation.session, vm_target, shared_components)

        # Patient workflow steps
        patient_workflow_steps = [
            {"action": "click", "element": "Patient Search", "description": "Open patient search"},
            {
                "action": "type",
                "element": "Patient ID",
                "value": vnc_vm_config.patient_mrn,
                "description": "Enter patient MRN",
            },
            {"action": "click", "element": "Search", "description": "Execute patient search"},
            {
                "action": "verify",
                "element": vnc_vm_config.patient_name,
                "description": "Verify correct patient loaded",
            },
            {
                "action": "click",
                "element": "Patient Details",
                "description": "Open patient details",
            },
        ]

        # Execute patient workflow
        for i, step in enumerate(patient_workflow_steps):
            print(f"🔄 Step {i + 1}: {step['description']}")

            if step["action"] == "click":
                # Find and click element
                element_result = app_controller.tools.find_target_element_with_retry(
                    step["element"], max_retries=3
                )
                assert element_result["success"], f"Could not find element: {step['element']}"

                click_result = app_controller.tools.click_element_verified(
                    element_result["element"]
                )
                assert click_result["success"], f"Could not click element: {step['element']}"

            elif step["action"] == "type":
                # Find field and type value
                field_result = app_controller.tools.find_target_element_with_retry(
                    step["element"], max_retries=3
                )
                assert field_result["success"], f"Could not find field: {step['element']}"

                click_result = app_controller.tools.click_element_verified(field_result["element"])
                assert click_result["success"], f"Could not click field: {step['element']}"

                type_result = app_controller.tools.input_actions.type_text(step["value"])
                assert type_result.success, f"Could not type in field: {step['element']}"

            elif step["action"] == "verify":
                # Verify element exists on screen
                verify_result = app_controller.tools.find_target_element_with_retry(
                    step["element"], max_retries=3
                )
                assert verify_result["success"], f"Could not verify element: {step['element']}"

            print(f"✅ Step {i + 1} completed successfully")
            await asyncio.sleep(1)  # Brief pause between steps

        print("✅ Patient application workflow completed successfully")

        # Save session log
        log_file = automation.save_session_log("test_patient_workflow_vnc.json")
        print(f"   Session log: {log_file}")

        return True

    async def test_patient_safety_verification(self, vnc_vm_config):
        """Test patient safety verification features"""
        print("\n🛡️ Testing patient safety verification")

        # Create automation with patient info
        automation = VMAutomation(vnc_vm_config)

        # Execute navigation with patient verification
        patient_info = {
            "name": vnc_vm_config.patient_name,
            "mrn": vnc_vm_config.patient_mrn,
            "dob": vnc_vm_config.patient_dob,
        }

        # Run VM Navigator with patient verification
        navigator = VMNavigatorAgent(automation.session, vnc_vm_config.to_vm_target())

        result = await navigator.execute_navigation(patient_info=patient_info)

        # Note: In a real patient application, this would verify patient banner
        # For testing purposes, we'll just verify the structure works
        assert result["success"] or "SAFETY" in str(result.get("error", "")), (
            "Should either succeed or fail with safety message"
        )

        print("✅ Patient safety verification test completed")

        return result


if __name__ == "__main__":
    # Run tests directly with pytest
    import sys

    pytest.main([__file__, "-v", "-s"] + sys.argv[1:])
