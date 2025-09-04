"""VM Navigator Agent - Production version without mocks"""

import asyncio
import time
from pathlib import Path
from typing import Any

from src.tools.input_actions import InputActions
from src.tools.screen_capture import ScreenCapture
from src.tools.verification import ActionVerifier
from src.vision.ui_finder import UIFinder

from .shared_context import VMSession, VMTarget


class VMNavigatorTools:
    """Production tools for VM Navigator Agent"""

    def __init__(self, session: VMSession, vm_target: VMTarget):
        """Initialize production tools for VM navigation"""
        self.session = session
        self.vm_target = vm_target

        # Initialize real tools only
        self.screen_capture = ScreenCapture(vm_target.connection_type)
        # InputActions will be initialized after connection is established
        self.input_actions = None

        # Initialize vision components
        models_dir = Path(__file__).parent.parent / "models"
        yolo_path = models_dir / "yolov8s.onnx"

        if not yolo_path.exists():
            raise FileNotFoundError(
                f"YOLO model not found: {yolo_path}. Run setup_models.py first."
            )

        self.ui_finder = UIFinder(str(yolo_path))
        self.verifier = ActionVerifier(self.ui_finder, self.ui_finder.ocr_reader)

    def connect_to_vm(self) -> dict[str, Any]:
        """Connect to the VM"""
        try:
            self.session.log_action("Attempting VM connection...")

            success = self.screen_capture.connect(
                host=self.vm_target.vm_host,
                port=self.vm_target.vm_port,
                username=self.vm_target.vm_username,
                password=self.vm_target.vm_password,
            )

            if success:
                self.session.is_connected = True
                self.session.log_action(f"Connected to VM at {self.vm_target.vm_host}")

                # Set up input actions with the same connection as screen capture
                if self.screen_capture.connection and self.screen_capture.connection.is_connected:
                    self.input_actions = InputActions(self.screen_capture.connection)

                return {"success": True, "message": "VM connection established"}
            else:
                self.session.add_error("Failed to connect to VM")
                return {"success": False, "error": "VM connection failed"}

        except Exception as e:
            error_msg = f"VM connection error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    def capture_screen_with_retry(
        self, description: str = "Screen capture", max_retries: int = 3
    ) -> dict[str, Any]:
        """Capture current screen with retry logic"""
        for attempt in range(max_retries):
            try:
                screenshot = self.screen_capture.capture_screen()
                if screenshot is not None:
                    self.session.add_screenshot(screenshot, description)

                    # Get screen resolution
                    height, width = screenshot.shape[:2]
                    self.session.screen_resolution = (width, height)

                    self.session.log_action(f"Screenshot captured: {description}")
                    return {
                        "success": True,
                        "resolution": f"{width}x{height}",
                        "description": description,
                    }

                if attempt < max_retries - 1:
                    self.session.log_action(f"Screenshot attempt {attempt + 1} failed, retrying...")
                    time.sleep(1.0)  # Wait before retry

            except Exception as e:
                if attempt < max_retries - 1:
                    self.session.log_action(
                        f"Screenshot error (attempt {attempt + 1}): {e}, retrying..."
                    )
                    time.sleep(1.0)
                else:
                    error_msg = f"Screen capture error after {max_retries} attempts: {e!s}"
                    self.session.add_error(error_msg)
                    return {"success": False, "error": error_msg}

        return {"success": False, "error": "Failed to capture screen after retries"}

    def wait_for_desktop_loaded(self, timeout: int = 60) -> dict[str, Any]:
        """Wait for desktop to load with proper timeout handling"""
        try:
            self.session.log_action("Waiting for desktop to load...")
            start_time = time.time()

            while time.time() - start_time < timeout:
                screenshot = self.screen_capture.capture_screen()
                if screenshot is None:
                    time.sleep(2.0)
                    continue

                self.session.add_screenshot(screenshot, "Desktop loading check")

                # Use verifier to check for desktop elements
                result = self.verifier.verify_page_loaded(
                    screenshot, self.vm_target.expected_desktop_elements, timeout=5
                )

                if result.success:
                    self.session.log_action("Desktop loaded successfully")
                    return {
                        "success": True,
                        "message": result.message,
                        "confidence": result.confidence,
                    }

                # Wait before next check
                time.sleep(3.0)

            return {"success": False, "error": f"Desktop not loaded within {timeout} seconds"}

        except Exception as e:
            error_msg = f"Desktop loading error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    def find_application_with_retry(self, app_name: str, max_retries: int = 3) -> dict[str, Any]:
        """Find application icon on desktop with retry logic"""
        for attempt in range(max_retries):
            try:
                self.session.log_action(
                    f"Looking for application: {app_name} (attempt {attempt + 1})"
                )

                screenshot = self.screen_capture.capture_screen()
                if screenshot is None:
                    if attempt < max_retries - 1:
                        time.sleep(2.0)
                        continue
                    return {"success": False, "error": "Cannot capture screen"}

                self.session.add_screenshot(
                    screenshot, f"Searching for {app_name} (attempt {attempt + 1})"
                )

                # Look for the application by name/text
                elements = self.ui_finder.find_element_by_text(screenshot, app_name)

                if elements:
                    best_element = max(elements, key=lambda x: x.confidence)
                    self.session.log_action(f"Found {app_name} at {best_element.center}")

                    return {
                        "success": True,
                        "element": {
                            "center": best_element.center,
                            "bbox": best_element.bbox,
                            "confidence": best_element.confidence,
                            "description": best_element.description,
                        },
                    }

                if attempt < max_retries - 1:
                    self.session.log_action(f"Application {app_name} not found, retrying...")
                    time.sleep(2.0)

            except Exception as e:
                if attempt < max_retries - 1:
                    self.session.log_action(
                        f"Application search error (attempt {attempt + 1}): {e}"
                    )
                    time.sleep(2.0)
                else:
                    error_msg = f"Application search error: {e!s}"
                    self.session.add_error(error_msg)
                    return {"success": False, "error": error_msg}

        return {
            "success": False,
            "error": f"Application {app_name} not found after {max_retries} attempts",
        }

    def launch_application_verified(self, element_info: dict[str, Any]) -> dict[str, Any]:
        """Launch application with verification"""
        try:
            center = element_info["center"]
            x, y = center

            self.session.log_action(f"Double-clicking application at ({x}, {y})")

            # Take screenshot before action
            before_screenshot = self.screen_capture.capture_screen()
            if before_screenshot is None:
                return {"success": False, "error": "Cannot capture screen before launch"}

            # Double-click to launch application
            if self.input_actions is None:
                return {
                    "success": False,
                    "error": "Input actions not initialized - connection may have failed",
                }

            result = self.input_actions.double_click(x, y)
            if not result.success:
                return {"success": False, "error": result.message}

            # Wait for application to start
            self.session.log_action("Waiting for application to launch...")
            time.sleep(5.0)

            # Take screenshot after action
            after_screenshot = self.screen_capture.capture_screen()
            if after_screenshot is None:
                return {"success": False, "error": "Cannot capture screen after launch"}

            self.session.add_screenshot(after_screenshot, "After launching application")

            # Verify that something changed (app launched)
            verification = self.verifier.verify_click_success(
                before_screenshot, after_screenshot, "page_change"
            )

            if verification.success:
                self.session.log_action(
                    f"Application launched successfully: {verification.message}"
                )
                self.session.current_app = self.vm_target.target_app_name
                return {"success": True, "message": verification.message}
            else:
                return {
                    "success": False,
                    "error": f"Could not verify application launch: {verification.message}",
                }

        except Exception as e:
            error_msg = f"Application launch error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    def verify_patient_banner(self, expected_patient_info: dict[str, str]) -> dict[str, Any]:
        """
        CRITICAL SAFETY FEATURE: Verify patient identity on screen

        Args:
            expected_patient_info: Dict with keys like 'name', 'mrn', 'dob'

        Returns:
            Dict with success status and verification details
        """
        try:
            self.session.log_action("SAFETY CHECK: Verifying patient identity...")

            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen for patient verification"}

            self.session.add_screenshot(screenshot, "Patient banner verification")

            # Define typical patient banner region (top 20% of screen)
            height, width = screenshot.shape[:2]
            banner_region = (0, 0, width, int(height * 0.2))

            # Read text from patient banner area
            text_detections = self.ui_finder.ocr_reader.read_text(screenshot, banner_region)

            if not text_detections:
                return {
                    "success": False,
                    "error": "No text found in patient banner area",
                    "safety_critical": True,
                }

            # Extract all text from banner
            banner_texts = [detection.text.strip() for detection in text_detections]
            banner_text_combined = " ".join(banner_texts).upper()

            # Verify patient identifiers
            verified_fields = []
            failed_fields = []

            for field_name, expected_value in expected_patient_info.items():
                if not expected_value:  # Skip empty values
                    continue

                expected_upper = expected_value.upper().strip()

                # Check if expected value appears in banner text
                if expected_upper in banner_text_combined:
                    verified_fields.append(field_name)
                    self.session.log_action(f"✓ Patient {field_name} verified: {expected_value}")
                else:
                    failed_fields.append(field_name)
                    self.session.add_error(
                        f"✗ Patient {field_name} NOT FOUND: expected '{expected_value}'"
                    )

            # Require at least 2 fields to match for safety
            min_required_matches = min(2, len([v for v in expected_patient_info.values() if v]))

            if len(verified_fields) >= min_required_matches:
                self.session.log_action(
                    f"SAFETY CHECK PASSED: {len(verified_fields)} patient identifiers verified"
                )
                return {
                    "success": True,
                    "verified_fields": verified_fields,
                    "failed_fields": failed_fields,
                    "banner_text": banner_texts,
                    "safety_critical": True,
                }
            else:
                error_msg = f"SAFETY CHECK FAILED: Only {len(verified_fields)} identifiers verified, need {min_required_matches}"
                self.session.add_error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "verified_fields": verified_fields,
                    "failed_fields": failed_fields,
                    "banner_text": banner_texts,
                    "safety_critical": True,
                }

        except Exception as e:
            error_msg = f"Patient verification error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg, "safety_critical": True}

    def verify_application_loaded_enhanced(self) -> dict[str, Any]:
        """Enhanced application verification with multiple checks"""
        try:
            self.session.log_action("Verifying application loaded...")

            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen"}

            self.session.add_screenshot(screenshot, "Application verification")

            # Multiple verification approaches
            verification_results = []

            # 1. Check for expected app elements
            if self.vm_target.expected_app_elements:
                result = self.verifier.verify_page_loaded(
                    screenshot, self.vm_target.expected_app_elements
                )
                verification_results.append(("app_elements", result.success, result.message))

            # 2. Check for any UI elements (generic check)
            elements = self.ui_finder.find_ui_elements(screenshot)
            ui_elements_found = len(elements) > 0
            verification_results.append(
                ("ui_elements", ui_elements_found, f"Found {len(elements)} UI elements")
            )

            # 3. Check window title or specific text
            app_name_elements = self.ui_finder.find_element_by_text(
                screenshot, self.vm_target.target_app_name.replace(".exe", "")
            )
            app_title_found = len(app_name_elements) > 0
            verification_results.append(
                ("app_title", app_title_found, f"App title found: {app_title_found}")
            )

            # Determine overall success
            successful_checks = sum(1 for _, success, _ in verification_results if success)
            total_checks = len(verification_results)

            if successful_checks >= (total_checks // 2 + 1):  # Majority must pass
                self.session.log_action(
                    f"Application verification passed: {successful_checks}/{total_checks} checks"
                )
                return {
                    "success": True,
                    "message": f"Application loaded - {successful_checks}/{total_checks} verifications passed",
                    "verification_details": verification_results,
                }
            else:
                return {
                    "success": False,
                    "error": f"Application verification failed: only {successful_checks}/{total_checks} checks passed",
                    "verification_details": verification_results,
                }

        except Exception as e:
            error_msg = f"Application verification error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}


class VMNavigatorAgent:
    """Production VM Navigator Agent"""

    def __init__(
        self,
        session: VMSession,
        vm_target: VMTarget,
        shared_components: dict[str, Any] | None = None,
    ):
        """
        Initialize VM Navigator Agent

        Args:
            session: VM session state
            poc_target: VM target configuration
            shared_components: Optional shared components to reuse (ui_finder, verifier, etc.)
        """
        self.session = session
        self.vm_target = vm_target
        self.tools = VMNavigatorTools(session, vm_target)

        # Store shared components for Agent 2
        self.shared_components = {
            "screen_capture": self.tools.screen_capture,
            "input_actions": self.tools.input_actions,
            "ui_finder": self.tools.ui_finder,
            "verifier": self.tools.verifier,
        }

    async def execute_navigation(
        self, patient_info: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Execute the full VM navigation workflow with patient safety verification

        Args:
            patient_info: Dict with patient identifiers like {'name': 'John Doe', 'mrn': '12345', 'dob': '01/01/1980'}
        """
        try:
            self.session.log_action("VM Navigator Agent starting...")

            # Define workflow steps
            steps = [
                ("Connect to VM", self.tools.connect_to_vm),
                (
                    "Capture initial screen",
                    lambda: self.tools.capture_screen_with_retry("Initial desktop"),
                ),
                ("Wait for desktop", self.tools.wait_for_desktop_loaded),
                (
                    "Find application",
                    lambda: self.tools.find_application_with_retry(self.vm_target.target_app_name),
                ),
                ("Launch application", None),  # Handled specially
                ("Verify app loaded", self.tools.verify_application_loaded_enhanced),
                ("Verify patient identity", None),  # Handled specially if patient_info provided
            ]

            app_element = None

            for step_name, step_func in steps:
                self.session.log_action(f"Executing: {step_name}")

                if step_name == "Launch application":
                    if app_element:
                        result = self.tools.launch_application_verified(app_element)
                    else:
                        result = {"success": False, "error": "No app element found"}

                elif step_name == "Find application":
                    result = step_func()
                    if result["success"]:
                        app_element = result["element"]

                elif step_name == "Verify patient identity":
                    if patient_info:
                        result = self.tools.verify_patient_banner(patient_info)
                        # Patient verification failure should stop the workflow
                        if not result["success"]:
                            return {
                                "success": False,
                                "error": "CRITICAL SAFETY FAILURE: " + result["error"],
                                "failed_step": step_name,
                                "patient_verification": result,
                            }
                    else:
                        result = {
                            "success": True,
                            "message": "Patient verification skipped (no patient info provided)",
                        }
                        self.session.log_action("WARNING: Patient verification skipped")

                else:
                    if asyncio.iscoroutinefunction(step_func):
                        result = await step_func()
                    else:
                        result = step_func()

                if not result["success"]:
                    self.session.add_error(
                        f"{step_name} failed: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"VM Navigation failed at: {step_name}",
                        "failed_step": step_name,
                        "step_error": result.get("error", "Unknown error"),
                    }

                # Small delay between steps
                await asyncio.sleep(0.5)

            # Mark as completed
            self.session.agent_1_completed = True
            self.session.agent_1_results = {
                "app_launched": True,
                "app_name": self.session.current_app,
                "screen_resolution": self.session.screen_resolution,
                "patient_verified": patient_info is not None,
            }

            result = {
                "success": True,
                "message": "VM Navigation completed successfully",
                "app_launched": self.session.current_app,
                "shared_components": self.shared_components,  # Pass to Agent 2
            }

            self.session.log_action(f"VM Navigator completed: {result['success']}")
            return result

        except Exception as e:
            error_msg = f"VM Navigator Agent error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
