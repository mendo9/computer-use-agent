"""Screen capture from remote VM via connection abstraction"""

import time

import cv2
import numpy as np
from src.connections import create_connection, VMConnection


class ScreenCapture:
    """Screen capture from remote VM using connection abstraction"""

    def __init__(self, connection_type: str = "vnc"):
        """
        Initialize screen capture

        Args:
            connection_type: "vnc" or "rdp"
        """
        self.connection_type = connection_type
        self.connection: VMConnection = create_connection(connection_type)
        self.is_connected = False

    def connect(self, host: str, port: int = 5900, password: str | None = None, username: str | None = None, **kwargs) -> bool:
        """
        Connect to VM

        Args:
            host: VM IP address
            port: Connection port 
            password: Password if required
            username: Username if required (RDP)
            **kwargs: Additional connection parameters (domain, width, height for RDP)

        Returns:
            True if connection successful
        """
        try:
            result = self.connection.connect(host=host, port=port, username=username, password=password, **kwargs)
            self.is_connected = result.success
            
            if result.success:
                print(result.message)
            else:
                print(f"Connection failed: {result.message}")
            
            return result.success
            
        except Exception as e:
            print(f"Connection failed: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from VM"""
        try:
            result = self.connection.disconnect()
            self.is_connected = False
            
            if result.success:
                print(result.message)
            else:
                print(f"Disconnect error: {result.message}")
        except Exception as e:
            print(f"Disconnect error: {e}")

    def capture_screen(self) -> np.ndarray | None:
        """
        Capture current screen

        Returns:
            Screenshot as numpy array (BGR format) or None if failed
        """
        if not self.is_connected:
            print("Not connected to VM")
            return None

        try:
            success, screenshot = self.connection.capture_screen()
            
            if success and screenshot is not None:
                return screenshot
            else:
                print("Screen capture failed")
                return None

        except Exception as e:
            print(f"Screen capture failed: {e}")
            return None

    def save_screenshot(self, filepath: str) -> bool:
        """
        Save current screen to file

        Args:
            filepath: Path to save screenshot

        Returns:
            True if successful
        """
        screenshot = self.capture_screen()
        if screenshot is not None:
            try:
                cv2.imwrite(filepath, screenshot)
                print(f"Screenshot saved to: {filepath}")
                return True
            except Exception as e:
                print(f"Failed to save screenshot: {e}")

        return False

    def wait_for_screen_change(self, timeout: int = 10, threshold: float = 0.1) -> bool:
        """
        Wait for screen to change (useful after actions)

        Args:
            timeout: Maximum wait time in seconds
            threshold: Change threshold (0-1)

        Returns:
            True if screen changed within timeout
        """
        if not self.is_connected:
            return False

        initial_screen = self.capture_screen()
        if initial_screen is None:
            return False

        start_time = time.time()

        while time.time() - start_time < timeout:
            time.sleep(0.5)  # Check every 500ms

            current_screen = self.capture_screen()
            if current_screen is None:
                continue

            # Calculate difference between screens
            if self._screens_different(initial_screen, current_screen, threshold):
                return True

        return False

    def _screens_different(
        self, screen1: np.ndarray, screen2: np.ndarray, threshold: float
    ) -> bool:
        """Check if two screens are significantly different"""
        if screen1.shape != screen2.shape:
            return True

        # Calculate mean squared difference
        diff = cv2.absdiff(screen1, screen2)
        mse = np.mean(diff**2)

        # Normalize MSE (rough approximation)
        normalized_mse = mse / (255**2)

        return bool(normalized_mse > threshold)

    def get_screen_resolution(self) -> tuple[int, int] | None:
        """
        Get current screen resolution

        Returns:
            (width, height) or None if failed
        """
        screenshot = self.capture_screen()
        if screenshot is not None:
            height, width = screenshot.shape[:2]
            return (width, height)
        return None


# Alternative implementation for local testing without actual VM
class MockScreenCapture(ScreenCapture):
    """Mock screen capture for testing without actual VM"""

    def __init__(self):
        super().__init__()
        self.mock_screen = None

    def connect(self, host: str, port: int = 5900, password: str | None = None, username: str | None = None, **kwargs) -> bool:
        """Mock connection always succeeds"""
        self.is_connected = True
        print(f"Mock connection to {host}:{port} (for testing)")
        return True

    def capture_screen(self) -> np.ndarray | None:
        """Return a mock desktop screenshot"""
        if not self.is_connected:
            return None

        # Create a simple mock desktop
        mock_desktop = np.ones((768, 1024, 3), dtype=np.uint8) * 240  # Light gray background

        # Add some mock UI elements
        cv2.rectangle(mock_desktop, (100, 100), (200, 150), (200, 200, 200), -1)  # Mock window
        cv2.putText(
            mock_desktop, "Mock Desktop", (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2
        )

        # Add a mock button
        cv2.rectangle(mock_desktop, (400, 300), (500, 350), (100, 150, 100), -1)
        cv2.putText(
            mock_desktop, "Button", (410, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
        )

        return mock_desktop

    def set_mock_screen(self, screen: np.ndarray):
        """Set custom mock screen for testing"""
        self.mock_screen = screen

    def disconnect(self):
        """Mock disconnect"""
        self.is_connected = False
        print("Mock disconnected")
