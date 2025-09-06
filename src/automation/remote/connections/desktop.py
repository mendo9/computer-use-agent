"""Desktop connection implementation for local macOS desktop interaction"""

import subprocess
from pathlib import Path

import cv2
import numpy as np

from automation.core import ActionResult, ConnectionResult
from automation.core.base import VMConnection


class DesktopConnection(VMConnection):
    """Desktop connection implementation for local macOS desktop manipulation"""

    def __init__(self):
        super().__init__()
        self.screenshot_path = Path("/tmp/desktop_screenshot.png")

    def connect(
        self,
        host: str = "localhost",
        port: int = 0,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> ConnectionResult:
        """Connect to local desktop (always succeeds)"""
        try:
            # No actual connection needed for local desktop
            self.is_connected = True

            self.connection_info = {
                "type": "desktop",
                "host": "localhost",
                "platform": "macOS",
                "screenshot_path": str(self.screenshot_path),
            }

            return ConnectionResult(True, "Connected to local desktop")

        except Exception as e:
            self.is_connected = False
            return ConnectionResult(False, f"Desktop connection failed: {e}")

    def disconnect(self) -> ConnectionResult:
        """Disconnect from desktop (cleanup only)"""
        try:
            self.is_connected = False
            self.connection_info = {}

            # Clean up screenshot file if it exists
            if self.screenshot_path.exists():
                self.screenshot_path.unlink()

            return ConnectionResult(True, "Desktop disconnected")

        except Exception as e:
            return ConnectionResult(False, f"Desktop disconnect error: {e}")

    def capture_screen(self) -> tuple[bool, np.ndarray | None]:
        """Capture desktop screenshot using macOS screencapture"""
        if not self.is_connected:
            return False, None

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
        """Capture specific window (interactive selection)"""
        if not self.is_connected:
            return False, None

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
        """Click at coordinates using AppleScript"""
        if not self.is_connected:
            return ActionResult(False, "No desktop connection")

        try:
            # Map button names to AppleScript button numbers
            button_map = {"left": "1", "right": "2", "middle": "3"}
            btn_num = button_map.get(button, "1")

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
        """Alternative click method using cliclick (if installed)"""
        if not self.is_connected:
            return ActionResult(False, "No desktop connection")

        try:
            # Check if cliclick is available (brew install cliclick)
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

    def type_text(self, text: str) -> ActionResult:
        """Type text using AppleScript"""
        if not self.is_connected:
            return ActionResult(False, "No desktop connection")

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
        """Press key using AppleScript"""
        if not self.is_connected:
            return ActionResult(False, "No desktop connection")

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
                script = f'tell application "System Events" to key code (key code of "{apple_key}")'
                # Simpler approach for single keys
                if apple_key in ["return", "escape", "tab", "space", "delete"]:
                    script = f'tell application "System Events" to keystroke "{apple_key}"'

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

    def get_desktop_info(self) -> dict:
        """Get desktop-specific information"""
        try:
            # Get screen resolution
            cmd = ["system_profiler", "SPDisplaysDataType", "-json"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            info = {
                "platform": "macOS",
                "connection_type": "desktop",
                "screenshot_capability": True,
                "click_capability": True,
                "keyboard_capability": True,
            }

            if result.returncode == 0:
                # Could parse JSON for detailed display info
                info["system_profiler_available"] = True

            return info

        except Exception as e:
            return {"platform": "macOS", "connection_type": "desktop", "error": str(e)}
