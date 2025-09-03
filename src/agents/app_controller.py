"""App Controller Agent - Production version without mocks"""

import asyncio
import time
from typing import Any

from .shared_context import VMSession, VMTarget


class AppControllerTools:
    """Production tools for App Controller Agent"""

    def __init__(self, session: VMSession, vm_target: VMTarget, shared_components: dict[str, Any]):
        """
        Initialize tools for application control using shared components from Agent 1

        Args:
            session: VM session state
            vm_target: VM target configuration
            shared_components: Components shared from VM Navigator Agent
        """
        self.session = session
        self.vm_target = vm_target

        # Use shared components from Agent 1 (more efficient, consistent state)
        self.screen_capture = shared_components["screen_capture"]
        self.input_actions = shared_components["input_actions"]
        self.ui_finder = shared_components["ui_finder"]
        self.verifier = shared_components["verifier"]

        self.session.log_action(
            "App Controller initialized with shared components from VM Navigator"
        )

    def capture_current_screen(self, description: str = "App screen capture") -> dict[str, Any]:
        """Capture current application screen"""
        try:
            screenshot = self.screen_capture.capture_screen()
            if screenshot is not None:
                self.session.add_screenshot(screenshot, description)
                self.session.log_action(f"App screenshot: {description}")
                return {"success": True, "description": description}
            else:
                return {"success": False, "error": "Failed to capture screen"}

        except Exception as e:
            error_msg = f"Screen capture error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    def find_target_element_with_retry(
        self, element_description: str, max_retries: int = 3
    ) -> dict[str, Any]:
        """
        Find target UI element with retry and multiple search strategies

        Args:
            element_description: Text or description of element to find
            max_retries: Number of retry attempts
        """
        for attempt in range(max_retries):
            try:
                self.session.log_action(
                    f"Looking for element: {element_description} (attempt {attempt + 1})"
                )

                screenshot = self.screen_capture.capture_screen()
                if screenshot is None:
                    if attempt < max_retries - 1:
                        time.sleep(1.0)
                        continue
                    return {"success": False, "error": "Cannot capture screen"}

                self.session.add_screenshot(
                    screenshot, f"Searching for {element_description} (attempt {attempt + 1})"
                )

                # Strategy 1: Direct text search
                elements = self.ui_finder.find_element_by_text(screenshot, element_description)
                if elements:
                    best_element = max(elements, key=lambda x: x.confidence)
                    self.session.log_action(
                        f"Found element '{element_description}' at {best_element.center}"
                    )

                    return {
                        "success": True,
                        "element": {
                            "text": element_description,
                            "center": best_element.center,
                            "bbox": best_element.bbox,
                            "confidence": best_element.confidence,
                            "description": best_element.description,
                            "search_strategy": "text_search",
                        },
                    }

                # Strategy 2: Look for clickable elements with partial text match
                clickable_elements = self.ui_finder.find_clickable_elements(screenshot)
                for element in clickable_elements:
                    if element.text and element_description.lower() in element.text.lower():
                        self.session.log_action(
                            f"Found clickable element with matching text: '{element.text}'"
                        )
                        return {
                            "success": True,
                            "element": {
                                "text": element.text,
                                "center": element.center,
                                "bbox": element.bbox,
                                "confidence": element.confidence,
                                "description": element.description,
                                "search_strategy": "clickable_partial_match",
                            },
                        }

                # Strategy 3: Keyword-based search
                keywords = element_description.lower().split()
                for element in self.ui_finder.find_ui_elements(screenshot):
                    if element.text:
                        element_text_lower = element.text.lower()
                        if any(keyword in element_text_lower for keyword in keywords):
                            self.session.log_action(
                                f"Found element by keyword match: '{element.text}'"
                            )
                            return {
                                "success": True,
                                "element": {
                                    "text": element.text,
                                    "center": element.center,
                                    "bbox": element.bbox,
                                    "confidence": element.confidence,
                                    "description": element.description,
                                    "search_strategy": "keyword_match",
                                },
                            }

                if attempt < max_retries - 1:
                    self.session.log_action(
                        f"Element '{element_description}' not found, retrying..."
                    )
                    time.sleep(2.0)

            except Exception as e:
                if attempt < max_retries - 1:
                    self.session.log_action(f"Element search error (attempt {attempt + 1}): {e}")
                    time.sleep(1.0)
                else:
                    error_msg = f"Element search error: {e!s}"
                    self.session.add_error(error_msg)
                    return {"success": False, "error": error_msg}

        return {
            "success": False,
            "error": f"Element '{element_description}' not found after {max_retries} attempts",
        }

    def click_element_verified(self, element_info: dict[str, Any]) -> dict[str, Any]:
        """Click element with comprehensive verification"""
        try:
            center = element_info["center"]
            x, y = center
            element_text = element_info.get("text", "element")

            self.session.log_action(f"Clicking element '{element_text}' at ({x}, {y})")

            # Take screenshot before action
            before_screenshot = self.screen_capture.capture_screen()
            if before_screenshot is None:
                return {"success": False, "error": "Cannot capture screen before click"}

            # Perform click
            result = self.input_actions.click(x, y)
            if not result.success:
                return {"success": False, "error": result.message}

            # Wait for UI response
            time.sleep(2.0)

            # Take screenshot after action
            after_screenshot = self.screen_capture.capture_screen()
            if after_screenshot is None:
                return {"success": False, "error": "Cannot capture screen after click"}

            self.session.add_screenshot(after_screenshot, f"After clicking {element_text}")

            # Verify click was successful
            verification = self.verifier.verify_click_success(
                before_screenshot, after_screenshot, "any"
            )

            if verification.success:
                self.session.log_action(f"Element click verified: {verification.message}")
                return {
                    "success": True,
                    "message": f"Successfully clicked {element_text}",
                    "verification": verification.message,
                }
            else:
                return {
                    "success": False,
                    "error": f"Click verification failed: {verification.message}",
                }

        except Exception as e:
            error_msg = f"Element click error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    def verify_action_outcome(self, expected_outcomes: list[str]) -> dict[str, Any]:
        """
        Verify that the action produced expected outcomes

        Args:
            expected_outcomes: List of expected text/elements that should appear after action
        """
        try:
            self.session.log_action("Verifying action outcome...")

            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return {"success": False, "error": "Cannot capture screen for verification"}

            self.session.add_screenshot(screenshot, "Action outcome verification")

            # Look for expected outcomes
            found_outcomes = []
            missing_outcomes = []

            for expected in expected_outcomes:
                elements = self.ui_finder.find_element_by_text(screenshot, expected)
                if elements:
                    found_outcomes.append(expected)
                    self.session.log_action(f"✓ Found expected outcome: {expected}")
                else:
                    missing_outcomes.append(expected)
                    self.session.log_action(f"✗ Missing expected outcome: {expected}")

            # Determine success (at least one outcome should be found)
            if found_outcomes:
                success_rate = len(found_outcomes) / len(expected_outcomes)
                return {
                    "success": True,
                    "message": f"Action outcome verified - found {len(found_outcomes)}/{len(expected_outcomes)} expected outcomes",
                    "found_outcomes": found_outcomes,
                    "missing_outcomes": missing_outcomes,
                    "success_rate": success_rate,
                }
            else:
                return {
                    "success": False,
                    "error": "No expected outcomes found after action",
                    "missing_outcomes": missing_outcomes,
                }

        except Exception as e:
            error_msg = f"Action outcome verification error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    def scroll_and_search(self, element_description: str, max_scrolls: int = 3) -> dict[str, Any]:
        """
        Scroll the view to find an element that might not be visible

        Args:
            element_description: Element to search for
            max_scrolls: Maximum number of scroll attempts
        """
        try:
            self.session.log_action(f"Scrolling to find element: {element_description}")

            for scroll_attempt in range(max_scrolls + 1):  # +1 for initial check without scrolling
                if scroll_attempt > 0:
                    # Scroll down
                    screenshot = self.screen_capture.capture_screen()
                    if screenshot:
                        height, width = screenshot.shape[:2]
                        center_x, center_y = width // 2, height // 2
                        scroll_result = self.input_actions.scroll(center_x, center_y, "down", 3)

                        if not scroll_result.success:
                            self.session.log_action(
                                f"Scroll attempt {scroll_attempt} failed: {scroll_result.message}"
                            )
                            continue

                        time.sleep(1.0)  # Wait for scroll to complete

                # Try to find element
                find_result = self.find_target_element_with_retry(
                    element_description, max_retries=1
                )

                if find_result["success"]:
                    self.session.log_action(f"Found element after {scroll_attempt} scrolls")
                    return find_result

            return {
                "success": False,
                "error": f"Element not found after {max_scrolls} scroll attempts",
            }

        except Exception as e:
            error_msg = f"Scroll and search error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}


class AppControllerAgent:
    """Production App Controller Agent"""

    def __init__(self, session: VMSession, vm_target: VMTarget, shared_components: dict[str, Any]):
        """
        Initialize App Controller Agent with shared components from VM Navigator

        Args:
            session: VM session state
            vm_target: VM target configuration
            shared_components: Shared components from VM Navigator Agent
        """
        self.session = session
        self.vm_target = vm_target
        self.tools = AppControllerTools(session, vm_target, shared_components)

    async def execute_button_click_workflow(
        self, expected_outcomes: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Execute button click workflow with comprehensive verification

        Args:
            expected_outcomes: List of expected outcomes after button click
        """
        try:
            # Verify prerequisites from Agent 1
            if not self.session.agent_1_completed:
                return {
                    "success": False,
                    "error": "Agent 1 (VM Navigator) has not completed successfully",
                }

            if not self.session.current_app:
                return {"success": False, "error": "No application is currently running"}

            self.session.log_action("App Controller Agent starting...")

            # Define workflow steps
            steps = [
                (
                    "Capture current screen",
                    lambda: self.tools.capture_current_screen("App interaction start"),
                ),
                ("Find target element", None),  # Handled specially
                ("Click element", None),  # Handled specially
                ("Verify action outcome", None),  # Handled specially
            ]

            element_info = None

            for step_name, step_func in steps:
                self.session.log_action(f"Executing: {step_name}")

                if step_name == "Find target element":
                    # Try direct search first, then scroll if needed
                    result = self.tools.find_target_element_with_retry(
                        self.vm_target.target_button_text
                    )

                    if not result["success"]:
                        self.session.log_action("Direct search failed, trying scroll search...")
                        result = self.tools.scroll_and_search(self.vm_target.target_button_text)

                    if result["success"]:
                        element_info = result["element"]

                elif step_name == "Click element":
                    if element_info:
                        result = self.tools.click_element_verified(element_info)
                    else:
                        result = {"success": False, "error": "No element found to click"}

                elif step_name == "Verify action outcome":
                    if expected_outcomes:
                        result = self.tools.verify_action_outcome(expected_outcomes)
                    else:
                        # Default verification - check if element is still there or changed
                        result = {
                            "success": True,
                            "message": "Action outcome verification skipped (no expected outcomes specified)",
                        }

                else:
                    result = step_func()

                if not result["success"]:
                    self.session.add_error(
                        f"{step_name} failed: {result.get('error', 'Unknown error')}"
                    )
                    return {
                        "success": False,
                        "error": f"App interaction failed at: {step_name}",
                        "failed_step": step_name,
                        "step_error": result.get("error", "Unknown error"),
                    }

                # Small delay between steps
                await asyncio.sleep(0.5)

            result = {
                "success": True,
                "message": "App interaction completed successfully",
                "element_clicked": self.vm_target.target_button_text,
                "element_info": element_info,
            }

            self.session.log_action(f"App Controller completed: {result['success']}")
            return result

        except Exception as e:
            error_msg = f"App Controller Agent error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}

    async def execute_form_filling_workflow(
        self, form_fields: list[dict[str, str]], submit_button: str | None = None
    ) -> dict[str, Any]:
        """
        Execute form filling workflow for multiple fields

        Args:
            form_fields: List of dicts with 'field_name' and 'value' keys
            submit_button: Optional submit button text (defaults to poc_target.target_button_text)
        """
        try:
            self.session.log_action(
                f"Starting form filling workflow with {len(form_fields)} fields"
            )

            # Fill each form field
            for field_info in form_fields:
                field_name = field_info.get("field_name", "")
                field_value = field_info.get("value", "")

                if not field_name or not field_value:
                    self.session.log_action(f"Skipping incomplete field: {field_info}")
                    continue

                self.session.log_action(f"Filling field: {field_name} = {field_value}")

                # Find field
                field_result = self.tools.find_target_element_with_retry(field_name)
                if not field_result["success"]:
                    return {
                        "success": False,
                        "error": f"Could not find field: {field_name}",
                        "failed_field": field_name,
                    }

                # Click field to focus
                click_result = self.tools.click_element_verified(field_result["element"])
                if not click_result["success"]:
                    return {
                        "success": False,
                        "error": f"Could not click field: {field_name}",
                        "failed_field": field_name,
                    }

                # Type value
                type_result = self.tools.input_actions.type_text(field_value)
                if not type_result.success:
                    return {
                        "success": False,
                        "error": f"Could not type in field {field_name}: {type_result.message}",
                        "failed_field": field_name,
                    }

                self.session.log_action(f"Successfully filled field: {field_name}")
                await asyncio.sleep(0.5)  # Brief pause between fields

            # Submit form if submit button specified
            submit_button_text = submit_button or self.vm_target.target_button_text
            if submit_button_text:
                self.session.log_action(f"Submitting form using button: {submit_button_text}")

                # Use the button click workflow for submission
                submit_result = await self.execute_button_click_workflow()
                if not submit_result["success"]:
                    return {
                        "success": False,
                        "error": f"Form submission failed: {submit_result['error']}",
                    }

            return {
                "success": True,
                "message": f"Form filling workflow completed - filled {len(form_fields)} fields",
                "fields_filled": len(form_fields),
                "submitted": submit_button_text is not None,
            }

        except Exception as e:
            error_msg = f"Form filling workflow error: {e!s}"
            self.session.add_error(error_msg)
            return {"success": False, "error": error_msg}
