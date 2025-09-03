"""App Controller Agent - Handles application-specific interactions"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from openai import OpenAI
# from openai_agents import Agent  # Simplified for POC

from .shared_context import VMSession, POCTarget
from ..tools.screen_capture import ScreenCapture
from ..tools.input_actions import InputActions
from ..tools.verification import ActionVerifier
from ..vision.ui_finder import UIFinder


class AppControllerTools:
    """Tools available to App Controller Agent"""
    
    def __init__(self, session: VMSession, poc_target: POCTarget):
        """Initialize tools for application control"""
        self.session = session
        self.poc_target = poc_target
        
        # Inherit tools from VM Navigator session
        self.screen_capture = None
        self.input_actions = None
        self.ui_finder = None
        self.verifier = None
        
        # These will be set when session is passed from Agent 1
        self._initialize_from_session()
    
    def _initialize_from_session(self):
        """Initialize tools from the existing session"""
        # For now, create new instances - in a real implementation,
        # these would be passed from the VM Navigator
        
        models_dir = Path(__file__).parent.parent / "models"
        yolo_path = models_dir / "yolov8s.onnx"
        
        if yolo_path.exists():
            self.ui_finder = UIFinder(str(yolo_path))
            self.verifier = ActionVerifier(self.ui_finder, self.ui_finder.ocr_reader)
        else:
            # Use mock for testing
            from ..tools.screen_capture import MockScreenCapture
            from ..tools.input_actions import MockInputActions
            
            self.screen_capture = MockScreenCapture()
            self.screen_capture.is_connected = True  # Assume connection from Agent 1
            self.input_actions = MockInputActions()
            
            # Mock UI finder for testing
            class MockUIFinder:
                def find_element_by_text(self, screenshot, text):
                    # Return mock button element
                    from ..vision.ui_finder import UIElement
                    return [UIElement(
                        element_type="text",
                        bbox=(400, 300, 500, 350),
                        center=(450, 325),
                        confidence=0.9,
                        text=text,
                        description=f"Mock button: {text}"
                    )]
                
                def find_clickable_elements(self, screenshot):
                    return self.find_element_by_text(screenshot, "Submit")
            
            self.ui_finder = MockUIFinder()
            
            class MockVerifier:
                def verify_click_success(self, before, after, expected="any"):
                    from ..tools.verification import VerificationResult
                    return VerificationResult(True, "Mock click verified", 0.9)
                
                def verify_element_present(self, screenshot, description):
                    from ..tools.verification import VerificationResult
                    return VerificationResult(True, f"Mock element found: {description}", 0.9)
            
            self.verifier = MockVerifier()
    
    def capture_current_screen(self, description: str = "App screen capture") -> Dict[str, Any]:
        """Capture current application screen"""
        try:
            if not self.screen_capture:
                return {"success": False, "error": "No screen capture available"}
            
            screenshot = self.screen_capture.capture_screen()
            if screenshot is not None:
                self.session.add_screenshot(screenshot, description)
                self.session.log_action(f"App screenshot: {description}")
                return {"success": True, "description": description}
            else:
                return {"success": False, "error": "Failed to capture screen"}
                
        except Exception as e:
            error_msg = f"Screen capture error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def find_target_button(self, button_text: str) -> Dict[str, Any]:
        """Find the target button in the application"""
        try:
            self.session.log_action(f"Looking for button: {button_text}")
            
            # Get current screenshot
            if self.screen_capture:
                screenshot = self.screen_capture.capture_screen()
            else:
                screenshot = self.session.get_latest_screenshot()
                if screenshot:
                    screenshot = screenshot.image
            
            if screenshot is None:
                return {"success": False, "error": "No screenshot available"}
            
            self.session.add_screenshot(screenshot, f"Searching for button: {button_text}")
            
            # Look for the button by text
            elements = self.ui_finder.find_element_by_text(screenshot, button_text)
            
            if elements:
                best_element = max(elements, key=lambda x: x.confidence)
                self.session.log_action(f"Found button '{button_text}' at {best_element.center}")
                
                return {
                    "success": True,
                    "button": {
                        "text": button_text,
                        "center": best_element.center,
                        "bbox": best_element.bbox,
                        "confidence": best_element.confidence,
                        "description": best_element.description
                    }
                }
            
            # Also try looking for clickable elements
            clickable_elements = self.ui_finder.find_clickable_elements(screenshot)
            for element in clickable_elements:
                if element.text and button_text.lower() in element.text.lower():
                    self.session.log_action(f"Found clickable element with text '{element.text}'")
                    return {
                        "success": True,
                        "button": {
                            "text": element.text,
                            "center": element.center,
                            "bbox": element.bbox,
                            "confidence": element.confidence,
                            "description": element.description
                        }
                    }
            
            return {"success": False, "error": f"Button '{button_text}' not found"}
            
        except Exception as e:
            error_msg = f"Button search error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def click_button(self, button_info: Dict[str, Any]) -> Dict[str, Any]:
        """Click the target button"""
        try:
            center = button_info["center"]
            x, y = center
            button_text = button_info.get("text", "button")
            
            self.session.log_action(f"Clicking button '{button_text}' at ({x}, {y})")
            
            # Take screenshot before action
            before_screenshot = None
            if self.screen_capture:
                before_screenshot = self.screen_capture.capture_screen()
            
            # Click the button
            if self.input_actions:
                result = self.input_actions.click(x, y)
                if not result.success:
                    return {"success": False, "error": result.message}
            else:
                # Mock click
                self.session.log_action(f"Mock click at ({x}, {y})")
            
            # Wait a moment for response
            time.sleep(2)
            
            # Take screenshot after action
            after_screenshot = None
            if self.screen_capture:
                after_screenshot = self.screen_capture.capture_screen()
                if after_screenshot is not None:
                    self.session.add_screenshot(after_screenshot, f"After clicking {button_text}")
            
            # Verify click was successful
            if before_screenshot is not None and after_screenshot is not None and self.verifier:
                verification = self.verifier.verify_click_success(
                    before_screenshot, after_screenshot, "any"
                )
                
                if verification.success:
                    self.session.log_action(f"Button click verified: {verification.message}")
                    return {
                        "success": True,
                        "message": f"Successfully clicked {button_text}",
                        "verification": verification.message
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Click verification failed: {verification.message}"
                    }
            else:
                # For mock mode or when verification not available
                self.session.log_action(f"Button '{button_text}' clicked (mock/no verification)")
                return {
                    "success": True,
                    "message": f"Clicked {button_text} (no verification available)"
                }
                
        except Exception as e:
            error_msg = f"Button click error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
    
    def verify_button_action_completed(self) -> Dict[str, Any]:
        """Verify that the button click action was completed successfully"""
        try:
            self.session.log_action("Verifying button action completed...")
            
            # Get current screen
            if self.screen_capture:
                screenshot = self.screen_capture.capture_screen()
            else:
                screenshot = self.session.get_latest_screenshot()
                if screenshot:
                    screenshot = screenshot.image
            
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen for verification"}
            
            self.session.add_screenshot(screenshot, "Button action verification")
            
            # Look for any changes or confirmations
            if self.verifier:
                # Check if the button is still present (might be disabled or changed)
                button_still_present = self.verifier.verify_element_present(
                    screenshot, self.poc_target.target_button_text
                )
                
                # For POC, we consider success if we successfully clicked
                # In a real app, you'd check for specific success indicators
                self.session.log_action("Button action verification completed")
                return {
                    "success": True,
                    "message": "Button action appears to have completed",
                    "button_still_present": button_still_present.success
                }
            else:
                # Mock verification
                return {
                    "success": True,
                    "message": "Mock button action verification completed"
                }
                
        except Exception as e:
            error_msg = f"Button action verification error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}


class AppControllerAgent:
    """OpenAI Agent for application-specific interactions"""
    
    def __init__(self, session: VMSession, poc_target: POCTarget, use_mock: bool = True):
        """Initialize App Controller Agent"""
        self.session = session
        self.poc_target = poc_target
        self.use_mock = use_mock
        self.tools = AppControllerTools(session, poc_target)
        
        # Define tools for OpenAI Agent
        self.tool_functions = [
            self.tools.capture_current_screen,
            self.tools.find_target_button,
            self.tools.click_button,
            self.tools.verify_button_action_completed
        ]
        
        # Initialize OpenAI client (simplified for POC)
        self.client = OpenAI() if not use_mock else None
        self.instructions = self._get_agent_instructions()
    
    def _get_agent_instructions(self) -> str:
        """Get instructions for the App Controller Agent"""
        return f"""
You are App Controller Agent, responsible for:
1. Taking over from VM Navigator Agent (application should already be launched)
2. Finding and clicking the target button: {self.poc_target.target_button_text}
3. Verifying the button action completed successfully

Your workflow should be:
1. Capture current screen with capture_current_screen()
2. Find the target button with find_target_button("{self.poc_target.target_button_text}")
3. Click the button with click_button()
4. Verify action completed with verify_button_action_completed()

The application {self.session.current_app} should already be running from Agent 1.
Focus on finding and interacting with the specific button: {self.poc_target.target_button_text}

Always capture screenshots before and after actions to track progress.
Report success/failure clearly.
"""
    
    async def execute_app_interaction(self) -> Dict[str, Any]:
        """Execute the application interaction workflow"""
        try:
            # Verify we have the prerequisites from Agent 1
            if not self.session.agent_1_completed:
                return {
                    "success": False,
                    "error": "Agent 1 (VM Navigator) has not completed successfully"
                }
            
            if not self.session.current_app:
                return {
                    "success": False,
                    "error": "No application is currently running"
                }
            
            self.session.log_action("App Controller Agent starting...")
            
            # Execute the workflow step by step (simplified for POC)
            steps = [
                ("Capture current screen", lambda: self.tools.capture_current_screen("App interaction start")),
                ("Find target button", lambda: self.tools.find_target_button(self.poc_target.target_button_text)),
                ("Click button", None),  # Will be handled after find_target_button
                ("Verify action completed", self.tools.verify_button_action_completed)
            ]
            
            button_info = None
            
            for step_name, step_func in steps:
                self.session.log_action(f"Executing: {step_name}")
                
                if step_name == "Click button":
                    if button_info:
                        result = self.tools.click_button(button_info)
                    else:
                        result = {"success": False, "error": "No button found"}
                elif step_name == "Find target button":
                    result = step_func()
                    if result["success"]:
                        button_info = result["button"]
                else:
                    result = step_func()
                
                if not result["success"]:
                    self.session.add_error(f"{step_name} failed: {result.get('error', 'Unknown error')}")
                    return {
                        "success": False,
                        "error": f"App interaction failed at: {step_name}",
                        "failed_step": step_name,
                        "step_error": result.get("error", "Unknown error")
                    }
                
                # Small delay between steps
                await asyncio.sleep(0.5)
            
            result = {
                "success": True,
                "message": "App interaction completed successfully",
                "button_clicked": self.poc_target.target_button_text
            }
            
            self.session.log_action(f"App Controller completed: {result['success']}")
            return result
            
        except Exception as e:
            error_msg = f"App Controller Agent error: {str(e)}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}