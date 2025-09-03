"""VM Navigator Agent - Handles VM connection and application launching"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid

from openai import OpenAI
# from openai_agents import Agent  # Will implement simple agent for POC

from .shared_context import VMSession, POCTarget
from ..tools.screen_capture import ScreenCapture, MockScreenCapture
from ..tools.input_actions import InputActions, MockInputActions
from ..tools.verification import ActionVerifier
from ..vision.ui_finder import UIFinder


class VMNavigatorTools:
    """Tools available to VM Navigator Agent"""
    
    def __init__(self, session: VMSession, poc_target: POCTarget, use_mock: bool = True):
        """Initialize tools for VM navigation"""
        self.session = session
        self.poc_target = poc_target
        self.use_mock = use_mock
        
        # Initialize tools
        if use_mock:
            self.screen_capture = MockScreenCapture()
            self.input_actions = MockInputActions()
        else:
            self.screen_capture = ScreenCapture("vnc")
            self.input_actions = InputActions()
        
        # Initialize vision components
        if use_mock:
            # Use mock implementations for POC testing
            from ..vision.ui_finder import UIElement
            
            class MockUIFinder:
                def find_element_by_text(self, screenshot, text):
                    # Return mock element
                    return [UIElement(
                        element_type="text",
                        bbox=(150, 150, 250, 200),
                        center=(200, 175),
                        confidence=0.9,
                        text=text,
                        description=f"Mock element: {text}"
                    )]
                
                def find_ui_elements(self, screenshot):
                    return self.find_element_by_text(screenshot, "Mock UI Element")
            
            class MockVerifier:
                def verify_page_loaded(self, screenshot, indicators, timeout=5):
                    from ..tools.verification import VerificationResult
                    return VerificationResult(True, f"Mock verification: found {indicators}", 0.9)
                
                def verify_click_success(self, before, after, expected="any"):
                    from ..tools.verification import VerificationResult
                    return VerificationResult(True, "Mock click verified", 0.9)
            
            self.ui_finder = MockUIFinder()
            self.verifier = MockVerifier()
            
        else:
            models_dir = Path(__file__).parent.parent / "models"
            yolo_path = models_dir / "yolov8s.onnx"
            
            if yolo_path.exists():
                self.ui_finder = UIFinder(str(yolo_path))
                self.verifier = ActionVerifier(self.ui_finder, self.ui_finder.ocr_reader)
            else:
                raise FileNotFoundError(f"YOLO model not found: {yolo_path}. Run setup_models.py first.")
    
    def connect_to_vm(self) -> Dict[str, Any]:
        """Connect to the VM"""
        try:
            self.session.log_action("Attempting VM connection...")
            
            success = self.screen_capture.connect(
                host=self.poc_target.vm_host,
                port=self.poc_target.vm_port,
                password=self.poc_target.vm_password
            )
            
            if success:
                self.session.is_connected = True
                self.session.log_action(f"Connected to VM at {self.poc_target.vm_host}")
                
                # Set up input actions with VNC client
                if hasattr(self.screen_capture, 'vnc_client'):
                    self.input_actions.set_vnc_client(self.screen_capture.vnc_client)
                
                return {"success": True, "message": "VM connection established"}
            else:
                self.session.add_error("Failed to connect to VM")
                return {"success": False, "error": "VM connection failed"}
                
        except Exception as e:
            error_msg = f"VM connection error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def capture_screen(self, description: str = "Screen capture") -> Dict[str, Any]:
        """Capture current screen"""
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
                    "description": description
                }
            else:
                return {"success": False, "error": "Failed to capture screen"}
                
        except Exception as e:
            error_msg = f"Screen capture error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def wait_for_desktop(self) -> Dict[str, Any]:
        """Wait for desktop to load"""
        try:
            self.session.log_action("Waiting for desktop to load...")
            
            # Take initial screenshot
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen"}
            
            self.session.add_screenshot(screenshot, "Desktop loading check")
            
            # Use verifier to check for desktop elements
            result = self.verifier.verify_page_loaded(
                screenshot, 
                self.poc_target.expected_desktop_elements,
                timeout=self.poc_target.desktop_load_timeout
            )
            
            if result.success:
                self.session.log_action("Desktop loaded successfully")
                return {"success": True, "message": result.message, "confidence": result.confidence}
            else:
                # For mock/testing, assume desktop is loaded after a short delay
                if self.use_mock:
                    time.sleep(2)
                    self.session.log_action("Mock desktop loaded")
                    return {"success": True, "message": "Mock desktop ready"}
                
                return {"success": False, "error": result.message}
                
        except Exception as e:
            error_msg = f"Desktop loading error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def find_application(self, app_name: str) -> Dict[str, Any]:
        """Find application icon on desktop"""
        try:
            self.session.log_action(f"Looking for application: {app_name}")
            
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen"}
            
            self.session.add_screenshot(screenshot, f"Searching for {app_name}")
            
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
                        "description": best_element.description
                    }
                }
            else:
                # For mock/testing, return a fake position
                if self.use_mock:
                    mock_center = (200, 200)
                    self.session.log_action(f"Mock: Found {app_name} at {mock_center}")
                    return {
                        "success": True,
                        "element": {
                            "center": mock_center,
                            "bbox": (150, 150, 250, 250),
                            "confidence": 0.9,
                            "description": f"Mock {app_name} icon"
                        }
                    }
                
                return {"success": False, "error": f"Application {app_name} not found"}
                
        except Exception as e:
            error_msg = f"Application search error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def launch_application(self, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """Launch application by clicking on it"""
        try:
            center = element_info["center"]
            x, y = center
            
            self.session.log_action(f"Double-clicking application at ({x}, {y})")
            
            # Take screenshot before action
            before_screenshot = self.screen_capture.capture_screen()
            
            # Double-click to launch application
            result = self.input_actions.double_click(x, y)
            
            if not result.success:
                return {"success": False, "error": result.message}
            
            # Wait a moment for application to start
            time.sleep(3)
            
            # Take screenshot after action
            after_screenshot = self.screen_capture.capture_screen()
            if after_screenshot is not None:
                self.session.add_screenshot(after_screenshot, "After launching application")
            
            # Verify that something changed (app launched)
            if before_screenshot is not None and after_screenshot is not None:
                verification = self.verifier.verify_click_success(
                    before_screenshot, after_screenshot, "page_change"
                )
                
                if verification.success:
                    self.session.log_action(f"Application launched successfully: {verification.message}")
                    self.session.current_app = self.poc_target.target_app_name
                    return {"success": True, "message": verification.message}
            
            # For mock mode, assume success
            if self.use_mock:
                self.session.current_app = self.poc_target.target_app_name
                return {"success": True, "message": "Mock application launched"}
            
            return {"success": False, "error": "Could not verify application launch"}
            
        except Exception as e:
            error_msg = f"Application launch error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def verify_application_loaded(self) -> Dict[str, Any]:
        """Verify that the target application has loaded"""
        try:
            self.session.log_action("Verifying application loaded...")
            
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen"}
            
            self.session.add_screenshot(screenshot, "Application verification")
            
            # Look for application-specific elements
            if self.poc_target.expected_app_elements:
                result = self.verifier.verify_page_loaded(
                    screenshot, 
                    self.poc_target.expected_app_elements
                )
                
                return {
                    "success": result.success, 
                    "message": result.message,
                    "confidence": result.confidence
                }
            else:
                # Generic verification - look for any UI elements
                elements = self.ui_finder.find_ui_elements(screenshot)
                if elements:
                    self.session.log_action(f"Application appears loaded - found {len(elements)} UI elements")
                    return {"success": True, "message": f"Found {len(elements)} UI elements"}
                
                # For mock mode, assume success
                if self.use_mock:
                    return {"success": True, "message": "Mock application verification"}
                
                return {"success": False, "error": "No UI elements found - application may not be loaded"}
                
        except Exception as e:
            error_msg = f"Application verification error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}


class VMNavigatorAgent:
    """OpenAI Agent for VM navigation and application launching"""
    
    def __init__(self, session: VMSession, poc_target: POCTarget, use_mock: bool = True):
        """Initialize VM Navigator Agent"""
        self.session = session
        self.poc_target = poc_target
        self.use_mock = use_mock
        self.tools = VMNavigatorTools(session, poc_target, use_mock)
        
        # Define tools for OpenAI Agent
        self.tool_functions = [
            self.tools.connect_to_vm,
            self.tools.capture_screen,
            self.tools.wait_for_desktop,
            self.tools.find_application,
            self.tools.launch_application,
            self.tools.verify_application_loaded
        ]
        
        # Initialize OpenAI client (simplified for POC)
        self.client = OpenAI() if not self.use_mock else None
        self.instructions = self._get_agent_instructions()
    
    def _get_agent_instructions(self) -> str:
        """Get instructions for the VM Navigator Agent"""
        return f"""
You are VM Navigator Agent, responsible for:
1. Connecting to VM at {self.poc_target.vm_host}
2. Waiting for desktop to load
3. Finding and launching the application: {self.poc_target.target_app_name}
4. Verifying the application loaded successfully

Your workflow should be:
1. Connect to VM using connect_to_vm()
2. Capture initial screen with capture_screen()
3. Wait for desktop to load with wait_for_desktop()
4. Find the target application with find_application("{self.poc_target.target_app_name}")
5. Launch application with launch_application()
6. Verify application loaded with verify_application_loaded()

Always use capture_screen() before and after major actions to track progress.
Report any errors immediately and don't proceed if a critical step fails.

Once completed successfully, mark the session as ready for Agent 2 (App Controller).
"""
    
    async def execute_navigation(self) -> Dict[str, Any]:
        """Execute the full VM navigation workflow"""
        try:
            self.session.log_action("VM Navigator Agent starting...")
            
            # Execute the workflow step by step (simplified for POC)
            steps = [
                ("Connect to VM", self.tools.connect_to_vm),
                ("Capture screen", lambda: self.tools.capture_screen("Initial desktop")),
                ("Wait for desktop", self.tools.wait_for_desktop),
                ("Find application", lambda: self.tools.find_application(self.poc_target.target_app_name)),
                ("Launch application", None),  # Will be handled after find_application
                ("Verify app loaded", self.tools.verify_application_loaded)
            ]
            
            app_element = None
            
            for step_name, step_func in steps:
                self.session.log_action(f"Executing: {step_name}")
                
                if step_name == "Launch application":
                    if app_element:
                        result = self.tools.launch_application(app_element)
                    else:
                        result = {"success": False, "error": "No app element found"}
                elif step_name == "Find application":
                    result = step_func()
                    if result["success"]:
                        app_element = result["element"]
                else:
                    result = step_func()
                
                if not result["success"]:
                    self.session.add_error(f"{step_name} failed: {result.get('error', 'Unknown error')}")
                    return {
                        "success": False,
                        "error": f"VM Navigation failed at: {step_name}",
                        "failed_step": step_name,
                        "step_error": result.get("error", "Unknown error")
                    }
                
                # Small delay between steps
                await asyncio.sleep(0.5)
            
            # Mark as completed if we got here
            self.session.agent_1_completed = True
            self.session.agent_1_results = {
                "app_launched": True,
                "app_name": self.session.current_app,
                "screen_resolution": self.session.screen_resolution
            }
            
            result = {
                "success": True,
                "message": "VM Navigation completed successfully",
                "app_launched": self.session.current_app
            }
            
            self.session.log_action(f"VM Navigator completed: {result['success']}")
            return result
            
        except Exception as e:
            error_msg = f"VM Navigator Agent error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}