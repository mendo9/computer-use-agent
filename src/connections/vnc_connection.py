"""VNC connection implementation"""

import time

import cv2
import numpy as np
import vncdotool.api as vnc

from .base import ActionResult, ConnectionResult, VMConnection


class VNCConnection(VMConnection):
    """VNC connection implementation using vncdotool"""

    def __init__(self):
        super().__init__()
        self.vnc_client = None

    def connect(
        self,
        host: str,
        port: int = 5900,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> ConnectionResult:
        """Connect to VNC server"""
        try:
            # VNC doesn't use username, only password
            server_address = f"{host}::{port}" if port != 5900 else host
            self.vnc_client = vnc.connect(server_address, password=password)
            self.is_connected = True

            self.connection_info = {
                "type": "vnc",
                "host": host,
                "port": port,
                "has_password": password is not None,
            }

            return ConnectionResult(True, f"Connected to VNC server at {host}:{port}")

        except Exception as e:
            self.is_connected = False
            return ConnectionResult(False, f"VNC connection failed: {e}")

    def disconnect(self) -> ConnectionResult:
        """Disconnect from VNC server"""
        try:
            if self.vnc_client:
                self.vnc_client.disconnect()
                self.vnc_client = None

            self.is_connected = False
            self.connection_info = {}

            return ConnectionResult(True, "VNC disconnected")

        except Exception as e:
            return ConnectionResult(False, f"VNC disconnect error: {e}")

    def capture_screen(self) -> tuple[bool, np.ndarray | None]:
        """Capture screenshot via VNC"""
        if not self.is_connected or not self.vnc_client:
            return False, None

        try:
            # Capture screen using vncdotool
            image = self.vnc_client.screen
            if image is None:
                return False, None

            # Convert PIL image to numpy array for OpenCV
            image_array = np.array(image)
            # Convert RGB to BGR for OpenCV
            if len(image_array.shape) == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

            return True, image_array

        except Exception as e:
            print(f"VNC screen capture error: {e}")
            return False, None

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Click at coordinates via VNC"""
        if not self.is_connected or not self.vnc_client:
            return ActionResult(False, "No VNC connection")

        try:
            # Map button names
            if button == "left":
                self.vnc_client.mousemove(x, y)
                self.vnc_client.mousedown(1)  # Left button
                time.sleep(0.05)
                self.vnc_client.mouseup(1)
            elif button == "right":
                self.vnc_client.mousemove(x, y)
                self.vnc_client.mousedown(3)  # Right button
                time.sleep(0.05)
                self.vnc_client.mouseup(3)
            elif button == "middle":
                self.vnc_client.mousemove(x, y)
                self.vnc_client.mousedown(2)  # Middle button
                time.sleep(0.05)
                self.vnc_client.mouseup(2)
            else:
                return ActionResult(False, f"Unknown button: {button}")

            return ActionResult(True, f"Clicked {button} at ({x}, {y})")

        except Exception as e:
            return ActionResult(False, f"VNC click error: {e}")

    def type_text(self, text: str) -> ActionResult:
        """Type text via VNC"""
        if not self.is_connected or not self.vnc_client:
            return ActionResult(False, "No VNC connection")

        try:
            # Type each character
            for char in text:
                self.vnc_client.keypress(char)
                time.sleep(0.01)  # Small delay between keystrokes

            return ActionResult(True, f"Typed: {text}")

        except Exception as e:
            return ActionResult(False, f"VNC type error: {e}")

    def key_press(self, key: str) -> ActionResult:
        """Press key via VNC"""
        if not self.is_connected or not self.vnc_client:
            return ActionResult(False, "No VNC connection")

        try:
            # Map common key names to VNC key names
            key_mapping = {
                "enter": "Return",
                "escape": "Escape",
                "tab": "Tab",
                "space": "space",
                "backspace": "BackSpace",
                "delete": "Delete",
                "ctrl": "Control_L",
                "alt": "Alt_L",
                "shift": "Shift_L",
                "up": "Up",
                "down": "Down",
                "left": "Left",
                "right": "Right",
            }

            vnc_key = key_mapping.get(key.lower(), key)
            self.vnc_client.keypress(vnc_key)

            return ActionResult(True, f"Pressed key: {key}")

        except Exception as e:
            return ActionResult(False, f"VNC key press error: {e}")
