"""Input actions for VM interaction (click, type, keys)"""

import time
from dataclasses import dataclass


@dataclass
class ActionResult:
    """Result of an input action"""

    success: bool
    message: str
    timestamp: float


class InputActions:
    """Handle input actions to remote VM"""

    def __init__(self, vnc_client=None):
        """
        Initialize input actions

        Args:
            vnc_client: VNC client connection
        """
        self.vnc_client = vnc_client
        self.action_delay = 0.1  # Default delay between actions

    def set_vnc_client(self, vnc_client):
        """Set VNC client connection"""
        self.vnc_client = vnc_client

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """
        Click at specific coordinates

        Args:
            x: X coordinate
            y: Y coordinate
            button: "left", "right", or "middle"

        Returns:
            ActionResult with success status
        """
        if not self.vnc_client:
            return ActionResult(False, "No VNC connection", time.time())

        try:
            # Move to position and click
            if button == "left":
                self.vnc_client.mouseMove(x, y)
                time.sleep(0.1)
                self.vnc_client.mousePress(1)  # Left button
                time.sleep(0.05)
                self.vnc_client.mouseRelease(1)

            elif button == "right":
                self.vnc_client.mouseMove(x, y)
                time.sleep(0.1)
                self.vnc_client.mousePress(3)  # Right button
                time.sleep(0.05)
                self.vnc_client.mouseRelease(3)

            elif button == "middle":
                self.vnc_client.mouseMove(x, y)
                time.sleep(0.1)
                self.vnc_client.mousePress(2)  # Middle button
                time.sleep(0.05)
                self.vnc_client.mouseRelease(2)

            time.sleep(self.action_delay)
            return ActionResult(True, f"Clicked {button} at ({x}, {y})", time.time())

        except Exception as e:
            return ActionResult(False, f"Click failed: {e}", time.time())

    def double_click(self, x: int, y: int) -> ActionResult:
        """
        Double-click at specific coordinates

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            ActionResult with success status
        """
        if not self.vnc_client:
            return ActionResult(False, "No VNC connection", time.time())

        try:
            self.vnc_client.mouseMove(x, y)
            time.sleep(0.1)

            # First click
            self.vnc_client.mousePress(1)
            time.sleep(0.05)
            self.vnc_client.mouseRelease(1)

            # Short delay
            time.sleep(0.1)

            # Second click
            self.vnc_client.mousePress(1)
            time.sleep(0.05)
            self.vnc_client.mouseRelease(1)

            time.sleep(self.action_delay)
            return ActionResult(True, f"Double-clicked at ({x}, {y})", time.time())

        except Exception as e:
            return ActionResult(False, f"Double-click failed: {e}", time.time())

    def type_text(self, text: str, delay_between_chars: float = 0.05) -> ActionResult:
        """
        Type text

        Args:
            text: Text to type
            delay_between_chars: Delay between each character

        Returns:
            ActionResult with success status
        """
        if not self.vnc_client:
            return ActionResult(False, "No VNC connection", time.time())

        try:
            for char in text:
                self.vnc_client.keyPress(char)
                time.sleep(delay_between_chars)

            time.sleep(self.action_delay)
            return ActionResult(True, f"Typed: {text}", time.time())

        except Exception as e:
            return ActionResult(False, f"Type text failed: {e}", time.time())

    def press_key(self, key: str) -> ActionResult:
        """
        Press a special key

        Args:
            key: Key name (e.g., "enter", "tab", "esc", "ctrl-c")

        Returns:
            ActionResult with success status
        """
        if not self.vnc_client:
            return ActionResult(False, "No VNC connection", time.time())

        try:
            self.vnc_client.keyPress(key)
            time.sleep(self.action_delay)
            return ActionResult(True, f"Pressed key: {key}", time.time())

        except Exception as e:
            return ActionResult(False, f"Key press failed: {e}", time.time())

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> ActionResult:
        """
        Drag from start to end coordinates

        Args:
            start_x: Start X coordinate
            start_y: Start Y coordinate
            end_x: End X coordinate
            end_y: End Y coordinate

        Returns:
            ActionResult with success status
        """
        if not self.vnc_client:
            return ActionResult(False, "No VNC connection", time.time())

        try:
            # Move to start position
            self.vnc_client.mouseMove(start_x, start_y)
            time.sleep(0.1)

            # Press and hold left button
            self.vnc_client.mousePress(1)
            time.sleep(0.1)

            # Drag to end position
            self.vnc_client.mouseMove(end_x, end_y)
            time.sleep(0.1)

            # Release button
            self.vnc_client.mouseRelease(1)
            time.sleep(self.action_delay)

            return ActionResult(
                True, f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})", time.time()
            )

        except Exception as e:
            return ActionResult(False, f"Drag failed: {e}", time.time())

    def scroll(self, x: int, y: int, direction: str = "up", clicks: int = 3) -> ActionResult:
        """
        Scroll at specific position

        Args:
            x: X coordinate
            y: Y coordinate
            direction: "up" or "down"
            clicks: Number of scroll clicks

        Returns:
            ActionResult with success status
        """
        if not self.vnc_client:
            return ActionResult(False, "No VNC connection", time.time())

        try:
            self.vnc_client.mouseMove(x, y)
            time.sleep(0.1)

            for _ in range(clicks):
                if direction == "up":
                    self.vnc_client.mousePress(4)  # Scroll up
                    time.sleep(0.05)
                    self.vnc_client.mouseRelease(4)
                else:  # down
                    self.vnc_client.mousePress(5)  # Scroll down
                    time.sleep(0.05)
                    self.vnc_client.mouseRelease(5)

                time.sleep(0.1)

            time.sleep(self.action_delay)
            return ActionResult(
                True, f"Scrolled {direction} {clicks} times at ({x}, {y})", time.time()
            )

        except Exception as e:
            return ActionResult(False, f"Scroll failed: {e}", time.time())


class MockInputActions(InputActions):
    """Mock input actions for testing without actual VM"""

    def __init__(self):
        super().__init__()
        self.actions_log = []

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Mock click action"""
        action = f"Click {button} at ({x}, {y})"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())

    def double_click(self, x: int, y: int) -> ActionResult:
        """Mock double-click action"""
        action = f"Double-click at ({x}, {y})"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())

    def type_text(self, text: str, delay_between_chars: float = 0.05) -> ActionResult:
        """Mock type text action"""
        action = f"Type: {text}"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())

    def press_key(self, key: str) -> ActionResult:
        """Mock key press action"""
        action = f"Press key: {key}"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> ActionResult:
        """Mock drag action"""
        action = f"Drag from ({start_x}, {start_y}) to ({end_x}, {end_y})"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())

    def scroll(self, x: int, y: int, direction: str = "up", clicks: int = 3) -> ActionResult:
        """Mock scroll action"""
        action = f"Scroll {direction} {clicks} times at ({x}, {y})"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())

    def get_actions_log(self) -> list[str]:
        """Get log of all mock actions"""
        return self.actions_log.copy()

    def clear_log(self):
        """Clear actions log"""
        self.actions_log.clear()
