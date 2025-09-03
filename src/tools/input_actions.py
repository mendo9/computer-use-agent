"""Input actions for VM interaction (click, type, keys)"""

import time

from src.connections import VMConnection
from src.connections.base import ActionResult


class InputActions:
    """Handle input actions to remote VM using connection abstraction"""

    def __init__(self, connection: VMConnection):
        """
        Initialize input actions

        Args:
            connection: VM connection instance
        """
        self.connection = connection
        self.action_delay = 0.1  # Default delay between actions

    def set_connection(self, connection: VMConnection):
        """Set VM connection"""
        self.connection = connection

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
        if not self.connection or not self.connection.is_connected:
            return ActionResult(False, "No VM connection")

        try:
            result = self.connection.click(x, y, button)
            time.sleep(self.action_delay)
            return result

        except Exception as e:
            return ActionResult(False, f"Click failed: {e}")

    def double_click(self, x: int, y: int) -> ActionResult:
        """
        Double-click at specific coordinates

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            ActionResult with success status
        """
        if not self.connection or not self.connection.is_connected:
            return ActionResult(False, "No VM connection")

        try:
            # Perform first click
            result1 = self.connection.click(x, y, "left")
            if not result1.success:
                return result1

            # Short delay between clicks
            time.sleep(0.1)

            # Perform second click
            result2 = self.connection.click(x, y, "left")
            if not result2.success:
                return result2

            time.sleep(self.action_delay)
            return ActionResult(True, f"Double-clicked at ({x}, {y})")

        except Exception as e:
            return ActionResult(False, f"Double-click failed: {e}")

    def type_text(self, text: str, delay_between_chars: float = 0.05) -> ActionResult:
        """
        Type text

        Args:
            text: Text to type
            delay_between_chars: Delay between each character (ignored, handled by connection)

        Returns:
            ActionResult with success status
        """
        if not self.connection or not self.connection.is_connected:
            return ActionResult(False, "No VM connection")

        try:
            result = self.connection.type_text(text)
            time.sleep(self.action_delay)
            return result

        except Exception as e:
            return ActionResult(False, f"Type text failed: {e}")

    def press_key(self, key: str) -> ActionResult:
        """
        Press a special key

        Args:
            key: Key name (e.g., "enter", "tab", "esc", "ctrl-c")

        Returns:
            ActionResult with success status
        """
        if not self.connection or not self.connection.is_connected:
            return ActionResult(False, "No VM connection")

        try:
            result = self.connection.key_press(key)
            time.sleep(self.action_delay)
            return result

        except Exception as e:
            return ActionResult(False, f"Key press failed: {e}")

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
        if not self.connection or not self.connection.is_connected:
            return ActionResult(False, "No VM connection")

        try:
            # Note: Drag functionality would need to be implemented in connection classes
            # For now, simulate drag with click at start, then click at end
            result1 = self.connection.click(start_x, start_y, "left")
            if not result1.success:
                return result1

            time.sleep(0.1)

            result2 = self.connection.click(end_x, end_y, "left")
            if not result2.success:
                return result2

            time.sleep(self.action_delay)
            return ActionResult(
                True, f"Simulated drag from ({start_x}, {start_y}) to ({end_x}, {end_y})"
            )

        except Exception as e:
            return ActionResult(False, f"Drag failed: {e}")

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
        if not self.connection or not self.connection.is_connected:
            return ActionResult(False, "No VM connection")

        try:
            # Note: Scroll functionality would need to be implemented in connection classes
            # For now, simulate with key presses
            for _ in range(clicks):
                if direction == "up":
                    result = self.connection.key_press("up")
                else:
                    result = self.connection.key_press("down")

                if not result.success:
                    return result

                time.sleep(0.1)

            time.sleep(self.action_delay)
            return ActionResult(True, f"Simulated scroll {direction} {clicks} times at ({x}, {y})")

        except Exception as e:
            return ActionResult(False, f"Scroll failed: {e}")


class MockInputActions(InputActions):
    """Mock input actions for testing without actual VM"""

    def __init__(self):
        # Create a mock connection
        from src.connections.base import VMConnection

        class MockConnection(VMConnection):
            def __init__(self):
                super().__init__()
                self.is_connected = True

            def connect(self, host, port, username=None, password=None, **kwargs):
                return type("obj", (object,), {"success": True, "message": "Mock connected"})

            def disconnect(self):
                return type("obj", (object,), {"success": True, "message": "Mock disconnected"})

            def capture_screen(self):
                return True, None

            def click(self, x, y, button="left"):
                return ActionResult(True, f"Mock click {button} at ({x}, {y})")

            def type_text(self, text):
                return ActionResult(True, f"Mock typed: {text}")

            def key_press(self, key):
                return ActionResult(True, f"Mock key press: {key}")

        super().__init__(MockConnection())
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
