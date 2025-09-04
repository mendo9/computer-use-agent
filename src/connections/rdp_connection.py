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
        self.xvfb_process = None
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

            # Check if Xvfb is available (Linux) or use existing display (macOS)
            if shutil.which("Xvfb"):
                # Linux: Create virtual display with Xvfb
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
                    self.xvfb_process = subprocess.Popen(
                        xvfb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    time.sleep(3)  # Wait for Xvfb to start

                    # Verify Xvfb is running
                    if self.xvfb_process.poll() is not None:
                        return ConnectionResult(False, "Xvfb process died immediately after start")

                except Exception as e:
                    return ConnectionResult(False, f"Failed to start Xvfb: {e}")
            else:
                # macOS: Try to use Xvfb if available via Homebrew, otherwise fail with helpful message
                if shutil.which("Xvfb") is None:
                    return ConnectionResult(
                        False,
                        "RDP on macOS requires isolated X11 display. Install dependencies with:\n"
                        "brew install freerdp imagemagick xorg-server xdotool\n"
                        "Alternative: Use VNC connection instead of RDP for better macOS compatibility.",
                    )
                
                # If we reach here, Xvfb should be available - this shouldn't happen
                # because the outer if-condition should have caught it
                return ConnectionResult(False, "Unexpected Xvfb availability state")

            # Create temp directory for screenshots
            self.temp_dir = tempfile.mkdtemp(prefix="rdp_capture_")
            self.screenshot_path = os.path.join(self.temp_dir, "screenshot.png")

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

            # Clean up Xvfb process
            if self.xvfb_process:
                try:
                    self.xvfb_process.terminate()
                    try:
                        self.xvfb_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.xvfb_process.kill()
                        self.xvfb_process.wait()
                except Exception:
                    pass
                self.xvfb_process = None

            # Clean up X11 display and lock file (for virtual displays)
            if self.display and self.display.startswith(":"):
                # Only clean up if this was a virtual display we created
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
            env = os.environ.copy()
            env["DISPLAY"] = self.display

            if not self.screenshot_path:
                return False, None

            # Try screenshot methods in order of preference
            screenshot_methods = [
                ("scrot", ["scrot", self.screenshot_path]),
                ("xwd + convert", self._capture_with_xwd_convert),
            ]

            success = False
            for method_name, cmd_or_func in screenshot_methods:
                try:
                    if callable(cmd_or_func):
                        # Special handling for xwd+convert method
                        success = cmd_or_func(env)
                    else:
                        # Check if command is available
                        if not shutil.which(cmd_or_func[0]):
                            continue

                        result = subprocess.run(cmd_or_func, env=env, capture_output=True)
                        if result.returncode == 0:
                            success = True
                        else:
                            print(
                                f"RDP capture method '{method_name}' failed: {result.stderr.decode().strip()}"
                            )

                    if success:
                        break

                except Exception as e:
                    print(f"RDP capture method '{method_name}' error: {e}")
                    continue

            if not success:
                print("RDP capture failed: No working screenshot method available")
                return False, None

            # Load image with OpenCV
            if os.path.exists(self.screenshot_path):
                image = cv2.imread(self.screenshot_path)
                os.unlink(self.screenshot_path)  # Clean up
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

    def _capture_with_xwd_convert(self, env: dict) -> bool:
        """Fallback method using xwd + convert/magick for screenshot capture"""
        if not shutil.which("xwd"):
            return False

        # Check for both ImageMagick v6 (convert) and v7 (magick)
        convert_cmd = None
        if shutil.which("magick"):
            convert_cmd = "magick"
        elif shutil.which("convert"):
            convert_cmd = "convert"
        else:
            return False

        if not self.screenshot_path:
            return False

        try:
            # Create temporary XWD file
            xwd_path = self.screenshot_path.replace(".png", ".xwd")

            # Capture with xwd
            xwd_cmd = ["xwd", "-root", "-out", xwd_path]
            result = subprocess.run(xwd_cmd, env=env, capture_output=True)
            if result.returncode != 0:
                return False

            # Convert to PNG using appropriate ImageMagick command
            if convert_cmd == "magick":
                img_cmd = ["magick", xwd_path, self.screenshot_path]
            else:
                img_cmd = ["convert", xwd_path, self.screenshot_path]

            result = subprocess.run(img_cmd, capture_output=True)

            # Clean up XWD file
            if os.path.exists(xwd_path):
                os.unlink(xwd_path)

            # If conversion failed due to XWD format support, return False
            if result.returncode != 0:
                stderr = result.stderr.decode().lower()
                if "no decode delegate" in stderr and "xwd" in stderr:
                    print("ImageMagick XWD format support not available")
                return False

            return True

        except Exception:
            return False


    def _find_free_display(self) -> int:
        """Find a free X11 display number"""
        for display_num in range(10, 100):
            lock_file = f"/tmp/.X{display_num}-lock"
            if not os.path.exists(lock_file):
                return display_num
        return 99  # Fallback
