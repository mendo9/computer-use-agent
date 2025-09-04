"""RDP connection implementation using FreeRDP + X11 forwarding"""

import builtins
import contextlib
import os
import shutil
import subprocess
import tempfile
import time

import cv2
import numpy as np

from .base import ActionResult, ConnectionResult, VMConnection


class RDPConnection(VMConnection):
    """RDP connection implementation using FreeRDP"""

    def __init__(self):
        super().__init__()
        self.rdp_process = None
        self.display = None
        self.temp_dir = None
        self.screenshot_path = None

    def connect(
        self,
        host: str,
        port: int = 3389,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> ConnectionResult:
        """Connect via RDP using FreeRDP"""
        try:
            # Extract RDP-specific parameters
            domain = kwargs.get("domain")
            width = kwargs.get("width", 1920)
            height = kwargs.get("height", 1080)

            # Check if FreeRDP is available
            if not shutil.which("xfreerdp"):
                return ConnectionResult(
                    False,
                    "FreeRDP (xfreerdp) not found. Install with: sudo apt install freerdp2-x11",
                )

            # Set up X11 virtual display
            display_num = self._find_free_display()
            self.display = f":{display_num}"

            # Ensure X11 socket directory exists (critical for macOS)
            x11_dir = "/tmp/.X11-unix"
            if not os.path.exists(x11_dir):
                try:
                    os.makedirs(x11_dir, mode=0o1777, exist_ok=True)
                except PermissionError:
                    return ConnectionResult(
                        False,
                        f"X11 socket directory {x11_dir} does not exist and cannot be created. "
                        f"Run: sudo mkdir -p {x11_dir} && sudo chmod 1777 {x11_dir}",
                    )

            # Start Xvfb for virtual display
            xvfb_cmd = [
                "Xvfb",
                self.display,
                "-screen",
                "0",
                f"{width}x{height}x24",
                "-ac",
                "+extension",
                "GLX",
            ]

            try:
                subprocess.Popen(xvfb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)  # Wait for Xvfb to start
            except Exception as e:
                return ConnectionResult(False, f"Failed to start Xvfb: {e}")

            # Create temp directory for screenshots
            self.temp_dir = tempfile.mkdtemp(prefix="rdp_capture_")
            self.screenshot_path = os.path.join(self.temp_dir, "screenshot.xwd")

            # Build FreeRDP command
            rdp_cmd = [
                "xfreerdp",
                f"/v:{host}:{port}",
                f"/size:{width}x{height}",
                "/cert:ignore",
                "/compression",
                "/clipboard",
            ]

            # Add authentication
            if username:
                rdp_cmd.append(f"/u:{username}")
            if password:
                rdp_cmd.append(f"/p:{password}")
            if domain:
                rdp_cmd.append(f"/d:{domain}")

            # Set environment for X11 display
            env = os.environ.copy()
            env["DISPLAY"] = self.display

            # Start FreeRDP
            try:
                self.rdp_process = subprocess.Popen(
                    rdp_cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
                )

                # Wait a bit and check if process is still running
                time.sleep(3)
                if self.rdp_process.poll() is not None:
                    # Process died, get error
                    _, stderr = self.rdp_process.communicate()
                    return ConnectionResult(False, f"FreeRDP failed: {stderr.decode()}")

                self.is_connected = True
                self.connection_info = {
                    "type": "rdp",
                    "host": host,
                    "port": port,
                    "username": username,
                    "domain": domain,
                    "display": self.display,
                    "resolution": f"{width}x{height}",
                }

                return ConnectionResult(True, f"Connected to RDP server at {host}:{port}")

            except Exception as e:
                return ConnectionResult(False, f"Failed to start FreeRDP: {e}")

        except Exception as e:
            return ConnectionResult(False, f"RDP connection error: {e}")

    def disconnect(self) -> ConnectionResult:
        """Disconnect from RDP"""
        try:
            # Kill RDP process
            if self.rdp_process:
                self.rdp_process.terminate()
                try:
                    self.rdp_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.rdp_process.kill()
                    self.rdp_process.wait()
                self.rdp_process = None

            # Clean up X11 display and lock file
            if self.display:
                with contextlib.suppress(builtins.BaseException):
                    subprocess.run(
                        ["pkill", "-f", f"Xvfb {self.display}"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                # Remove X11 lock file
                display_num = self.display.lstrip(":")
                lock_file = f"/tmp/.X{display_num}-lock"
                with contextlib.suppress(builtins.BaseException):
                    if os.path.exists(lock_file):
                        os.unlink(lock_file)

                self.display = None

            # Clean up temp directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None

            self.is_connected = False
            self.connection_info = {}

            return ConnectionResult(True, "RDP disconnected")

        except Exception as e:
            return ConnectionResult(False, f"RDP disconnect error: {e}")

    def capture_screen(self) -> tuple[bool, np.ndarray | None]:
        """Capture screenshot via X11"""
        if not self.is_connected or not self.display:
            return False, None

        try:
            # Use xwd to capture screenshot
            env = os.environ.copy()
            env["DISPLAY"] = self.display

            # Capture to temporary file
            cmd = ["xwd", "-root", "-out", self.screenshot_path]
            result = subprocess.run(cmd, env=env, capture_output=True)

            if result.returncode != 0:
                return False, None

            # Convert xwd to PNG using ImageMagick
            if self.screenshot_path:
                png_path = self.screenshot_path.replace(".xwd", ".png")
                
                # Check if ImageMagick convert is available
                if not shutil.which("convert"):
                    print("RDP conversion failed: ImageMagick 'convert' not available. Install with: brew install imagemagick")
                    return False, None
                
                convert_cmd = ["convert", self.screenshot_path, png_path]
                result = subprocess.run(convert_cmd, capture_output=True)

                if result.returncode != 0:
                    print(f"RDP conversion failed: {result.stderr.decode().strip()}")
                    print(f"Command: {' '.join(convert_cmd)}")
                    print(f"XWD file exists: {os.path.exists(self.screenshot_path)}")
                    if os.path.exists(self.screenshot_path):
                        print(f"XWD file size: {os.path.getsize(self.screenshot_path)} bytes")
                    return False, None
            else:
                return False, None

            # Load image with OpenCV
            if os.path.exists(png_path):
                image = cv2.imread(png_path)
                os.unlink(png_path)  # Clean up
                if image is not None:
                    return True, image

            return False, None

        except Exception as e:
            print(f"RDP screen capture error: {e}")
            return False, None

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Click at coordinates via X11"""
        if not self.is_connected or not self.display:
            return ActionResult(False, "No RDP connection")

        try:
            env = os.environ.copy()
            env["DISPLAY"] = self.display

            # Map button names to X11 button numbers
            button_map = {"left": "1", "middle": "2", "right": "3"}
            btn_num = button_map.get(button, "1")

            # Use xdotool to perform click
            cmd = ["xdotool", "mousemove", str(x), str(y), "click", btn_num]
            result = subprocess.run(cmd, env=env, capture_output=True)

            if result.returncode == 0:
                return ActionResult(True, f"Clicked {button} at ({x}, {y})")
            else:
                return ActionResult(False, f"Click failed: {result.stderr.decode()}")

        except Exception as e:
            return ActionResult(False, f"RDP click error: {e}")

    def type_text(self, text: str) -> ActionResult:
        """Type text via X11"""
        if not self.is_connected or not self.display:
            return ActionResult(False, "No RDP connection")

        try:
            env = os.environ.copy()
            env["DISPLAY"] = self.display

            # Use xdotool to type text
            cmd = ["xdotool", "type", "--delay", "50", text]
            result = subprocess.run(cmd, env=env, capture_output=True)

            if result.returncode == 0:
                return ActionResult(True, f"Typed: {text}")
            else:
                return ActionResult(False, f"Type failed: {result.stderr.decode()}")

        except Exception as e:
            return ActionResult(False, f"RDP type error: {e}")

    def key_press(self, key: str) -> ActionResult:
        """Press key via X11"""
        if not self.is_connected or not self.display:
            return ActionResult(False, "No RDP connection")

        try:
            env = os.environ.copy()
            env["DISPLAY"] = self.display

            # Map common key names to xdotool key names
            key_mapping = {
                "enter": "Return",
                "escape": "Escape",
                "tab": "Tab",
                "space": "space",
                "backspace": "BackSpace",
                "delete": "Delete",
                "ctrl": "ctrl",
                "alt": "alt",
                "shift": "shift",
                "up": "Up",
                "down": "Down",
                "left": "Left",
                "right": "Right",
            }

            xdo_key = key_mapping.get(key.lower(), key)
            cmd = ["xdotool", "key", xdo_key]
            result = subprocess.run(cmd, env=env, capture_output=True)

            if result.returncode == 0:
                return ActionResult(True, f"Pressed key: {key}")
            else:
                return ActionResult(False, f"Key press failed: {result.stderr.decode()}")

        except Exception as e:
            return ActionResult(False, f"RDP key press error: {e}")

    def _find_free_display(self) -> int:
        """Find a free X11 display number"""
        for display_num in range(10, 100):
            lock_file = f"/tmp/.X{display_num}-lock"
            if not os.path.exists(lock_file):
                return display_num
        return 99  # Fallback
