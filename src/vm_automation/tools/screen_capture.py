"""Screen capture from remote VM via VNC/RDP"""

import cv2
import numpy as np
from typing import Optional, Tuple
import vncdotool.api as vnc
from PIL import Image
import io
import time


class ScreenCapture:
    """Screen capture from remote VM"""
    
    def __init__(self, connection_type: str = "vnc"):
        """
        Initialize screen capture
        
        Args:
            connection_type: "vnc" or "rdp" (vnc recommended for POC)
        """
        self.connection_type = connection_type
        self.vnc_client = None
        self.is_connected = False
        
    def connect(self, host: str, port: int = 5900, password: Optional[str] = None) -> bool:
        """
        Connect to VM
        
        Args:
            host: VM IP address
            port: VNC port (default 5900)
            password: VNC password if required
            
        Returns:
            True if connection successful
        """
        try:
            if self.connection_type == "vnc":
                # Connect to VNC server
                self.vnc_client = vnc.connect(host, port=port, password=password)
                self.is_connected = True
                print(f"Connected to VNC server at {host}:{port}")
                return True
            else:
                raise NotImplementedError("RDP connection not implemented in POC")
                
        except Exception as e:
            print(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from VM"""
        if self.vnc_client:
            try:
                self.vnc_client.disconnect()
                self.is_connected = False
                print("Disconnected from VM")
            except Exception as e:
                print(f"Disconnect error: {e}")
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """
        Capture current screen
        
        Returns:
            Screenshot as numpy array (BGR format) or None if failed
        """
        if not self.is_connected or not self.vnc_client:
            print("Not connected to VM")
            return None
        
        try:
            if self.connection_type == "vnc":
                # Capture screenshot using vncdotool
                screenshot_pil = self.vnc_client.screen
                
                # Convert PIL to numpy array
                screenshot_rgb = np.array(screenshot_pil)
                
                # Convert RGB to BGR for OpenCV
                screenshot_bgr = cv2.cvtColor(screenshot_rgb, cv2.COLOR_RGB2BGR)
                
                return screenshot_bgr
            
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
    
    def _screens_different(self, screen1: np.ndarray, screen2: np.ndarray, threshold: float) -> bool:
        """Check if two screens are significantly different"""
        if screen1.shape != screen2.shape:
            return True
        
        # Calculate mean squared difference
        diff = cv2.absdiff(screen1, screen2)
        mse = np.mean(diff ** 2)
        
        # Normalize MSE (rough approximation)
        normalized_mse = mse / (255 ** 2)
        
        return normalized_mse > threshold
    
    def get_screen_resolution(self) -> Optional[Tuple[int, int]]:
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
        
    def connect(self, host: str, port: int = 5900, password: Optional[str] = None) -> bool:
        """Mock connection always succeeds"""
        self.is_connected = True
        print(f"Mock connection to {host}:{port} (for testing)")
        return True
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """Return a mock desktop screenshot"""
        if not self.is_connected:
            return None
        
        # Create a simple mock desktop
        mock_desktop = np.ones((768, 1024, 3), dtype=np.uint8) * 240  # Light gray background
        
        # Add some mock UI elements
        cv2.rectangle(mock_desktop, (100, 100), (200, 150), (200, 200, 200), -1)  # Mock window
        cv2.putText(mock_desktop, "Mock Desktop", (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        # Add a mock button
        cv2.rectangle(mock_desktop, (400, 300), (500, 350), (100, 150, 100), -1)
        cv2.putText(mock_desktop, "Button", (410, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return mock_desktop
    
    def set_mock_screen(self, screen: np.ndarray):
        """Set custom mock screen for testing"""
        self.mock_screen = screen
    
    def disconnect(self):
        """Mock disconnect"""
        self.is_connected = False
        print("Mock disconnected")