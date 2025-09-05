"""Local macOS Desktop Automation

Provides direct control over the local macOS desktop environment using native tools:
- AppleScript for mouse clicks and keyboard input
- screencapture for screenshots
- cliclick as alternative click method (if installed)

This is completely separate from VM/remote control and operates on the local machine only.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ActionResult:
    """Result of local desktop action"""

    success: bool
    message: str


class DesktopControl:
    """Local macOS desktop automation controller"""

    def __init__(self):
        """Initialize desktop control"""
        self.screenshot_path = Path("/tmp/desktop_screenshot.png")
        self.is_active = True

    def capture_screen(self) -> tuple[bool, np.ndarray | None]:
        """
        Capture desktop screenshot using macOS screencapture

        Returns:
            Tuple of (success, image_array) where image_array is BGR format for OpenCV

        Example:
            success, screenshot = desktop.capture_screen()
            if success:
                cv2.imshow("Desktop", screenshot)
        """
        try:
            # Use macOS screencapture for entire screen
            cmd = ["screencapture", "-x", str(self.screenshot_path)]
            result = subprocess.run(cmd, check=True, capture_output=True)

            if result.returncode != 0:
                print(f"Screenshot command failed: {result.stderr.decode()}")
                return False, None

            # Load image with OpenCV
            if self.screenshot_path.exists():
                image = cv2.imread(str(self.screenshot_path))
                if image is not None:
                    return True, image

            return False, None

        except subprocess.CalledProcessError as e:
            print(f"Desktop screen capture error: {e}")
            return False, None
        except Exception as e:
            print(f"Desktop screen capture error: {e}")
            return False, None

    def capture_window(self, interactive: bool = True) -> tuple[bool, np.ndarray | None]:
        """
        Capture specific window (interactive selection)

        Args:
            interactive: If True, user selects window interactively

        Returns:
            Tuple of (success, image_array)
        """
        try:
            if interactive:
                # Interactive window selection
                cmd = ["screencapture", "-w", "-x", str(self.screenshot_path)]
                print("Click on the window you want to capture...")
            else:
                # Fallback to full screen
                return self.capture_screen()

            result = subprocess.run(cmd, check=True)

            if result.returncode != 0:
                print("Window capture failed, falling back to full screen")
                return self.capture_screen()

            # Load image with OpenCV
            if self.screenshot_path.exists():
                image = cv2.imread(str(self.screenshot_path))
                if image is not None:
                    return True, image

            return False, None

        except subprocess.CalledProcessError as e:
            print(f"Window capture error: {e}, falling back to full screen")
            return self.capture_screen()
        except Exception as e:
            print(f"Window capture error: {e}")
            return False, None

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """
        Click at coordinates using AppleScript

        Args:
            x: X coordinate
            y: Y coordinate
            button: "left", "right", or "middle"

        Returns:
            ActionResult with success status

        Example:
            result = desktop.click(100, 200)
            if result.success:
                print("Click successful")
        """
        try:
            # Use AppleScript for clicking
            script = f'tell application "System Events" to click at {{{x}, {y}}}'
            if button != "left":
                # For non-left clicks, use control-click as approximation
                script = f'tell application "System Events" to tell (click at {{{x}, {y}}}) to key down control'

            cmd = ["osascript", "-e", script]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                return ActionResult(True, f"Clicked {button} at ({x}, {y})")
            else:
                return ActionResult(False, f"Click failed: {result.stderr}")

        except subprocess.CalledProcessError as e:
            return ActionResult(False, f"Desktop click error: {e}")
        except Exception as e:
            return ActionResult(False, f"Desktop click error: {e}")

    def click_with_cliclick(self, x: int, y: int, button: str = "left") -> ActionResult:
        """
        Alternative click method using cliclick (if installed)

        Install with: brew install cliclick

        Args:
            x: X coordinate
            y: Y coordinate
            button: "left", "right", or "middle"

        Returns:
            ActionResult with success status
        """
        try:
            # Check if cliclick is available
            import shutil

            if not shutil.which("cliclick"):
                return self.click(x, y, button)  # Fallback to AppleScript

            # Map button names
            button_map = {"left": "c", "right": "rc", "middle": "mc"}
            click_type = button_map.get(button, "c")

            cmd = ["cliclick", f"{click_type}:{x},{y}"]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                return ActionResult(True, f"Clicked {button} at ({x}, {y}) via cliclick")
            else:
                return ActionResult(False, f"Cliclick failed: {result.stderr}")

        except subprocess.CalledProcessError as e:
            return ActionResult(False, f"Cliclick error: {e}")
        except Exception:
            # Fallback to AppleScript
            return self.click(x, y, button)

    def double_click(self, x: int, y: int) -> ActionResult:
        """
        Double-click at coordinates

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            ActionResult with success status
        """
        result1 = self.click(x, y, "left")
        if not result1.success:
            return result1

        # Small delay between clicks
        import time

        time.sleep(0.1)

        result2 = self.click(x, y, "left")
        if not result2.success:
            return result2

        return ActionResult(True, f"Double-clicked at ({x}, {y})")

    def type_text(self, text: str) -> ActionResult:
        """
        Type text using AppleScript

        Args:
            text: Text to type

        Returns:
            ActionResult with success status

        Example:
            result = desktop.type_text("Hello World")
        """
        try:
            # Escape quotes in text for AppleScript
            escaped_text = text.replace('"', '\\"').replace("'", "\\'")

            script = f'tell application "System Events" to keystroke "{escaped_text}"'
            cmd = ["osascript", "-e", script]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                return ActionResult(True, f"Typed: {text}")
            else:
                return ActionResult(False, f"Type failed: {result.stderr}")

        except subprocess.CalledProcessError as e:
            return ActionResult(False, f"Desktop type error: {e}")
        except Exception as e:
            return ActionResult(False, f"Desktop type error: {e}")

    def key_press(self, key: str) -> ActionResult:
        """
        Press key using AppleScript

        Args:
            key: Key name or combination (e.g., "enter", "cmd+c", "ctrl+v")

        Returns:
            ActionResult with success status

        Example:
            desktop.key_press("enter")
            desktop.key_press("cmd+c")  # Copy
        """
        try:
            # Map common key names to AppleScript key codes
            key_mapping = {
                "enter": "return",
                "return": "return",
                "escape": "escape",
                "tab": "tab",
                "space": "space",
                "backspace": "delete",
                "delete": "forward delete",
                "up": "up arrow",
                "down": "down arrow",
                "left": "left arrow",
                "right": "right arrow",
                "cmd": "command",
                "ctrl": "control",
                "alt": "option",
                "shift": "shift",
            }

            apple_key = key_mapping.get(key.lower(), key)

            # Handle special key combinations
            if key.lower().startswith("cmd+") or key.lower().startswith("ctrl+"):
                parts = key.lower().split("+")
                modifier = parts[0]
                target_key = parts[1] if len(parts) > 1 else ""

                modifier_map = {"cmd": "command", "ctrl": "control"}
                mod_key = modifier_map.get(modifier, modifier)

                script = f'tell application "System Events" to keystroke "{target_key}" using {mod_key} down'
            else:
                # Simpler approach for single keys
                if apple_key in ["return", "escape", "tab", "space", "delete"]:
                    script = f'tell application "System Events" to keystroke "{apple_key}"'
                else:
                    script = (
                        f'tell application "System Events" to key code (key code of "{apple_key}")'
                    )

            cmd = ["osascript", "-e", script]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            if result.returncode == 0:
                return ActionResult(True, f"Pressed key: {key}")
            else:
                return ActionResult(False, f"Key press failed: {result.stderr}")

        except subprocess.CalledProcessError as e:
            return ActionResult(False, f"Desktop key press error: {e}")
        except Exception as e:
            return ActionResult(False, f"Desktop key press error: {e}")

    def scroll(self, x: int, y: int, direction: str = "up", clicks: int = 3) -> ActionResult:
        """
        Scroll at specific position using arrow keys

        Args:
            x: X coordinate (for positioning cursor)
            y: Y coordinate (for positioning cursor)
            direction: "up" or "down"
            clicks: Number of scroll steps

        Returns:
            ActionResult with success status
        """
        try:
            # First click at position to focus
            self.click(x, y)

            # Then use arrow keys to scroll
            for _ in range(clicks):
                if direction == "up":
                    result = self.key_press("up")
                else:
                    result = self.key_press("down")

                if not result.success:
                    return result

                import time

                time.sleep(0.1)

            return ActionResult(True, f"Scrolled {direction} {clicks} times at ({x}, {y})")

        except Exception as e:
            return ActionResult(False, f"Scroll failed: {e}")

    def get_desktop_info(self) -> dict:
        """
        Get desktop-specific information

        Returns:
            Dictionary with platform and capability information
        """
        try:
            # Get screen resolution
            cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            info = {
                "platform": "macOS",
                "type": "local_desktop",
                "screenshot_capability": True,
                "click_capability": True,
                "keyboard_capability": True,
                "cliclick_available": bool(__import__("shutil").which("cliclick")),
            }

            if result.returncode == 0:
                info["system_profiler_available"] = True

            return info

        except Exception as e:
            return {"platform": "macOS", "type": "local_desktop", "error": str(e)}

    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.screenshot_path.exists():
                self.screenshot_path.unlink()
        except Exception:
            pass
