"""Mock components for testing VM automation POC"""

import time
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from src.tools.screen_capture import ScreenCapture
from src.tools.input_actions import InputActions, ActionResult
from src.tools.verification import VerificationResult
from src.vision.ui_finder import UIElement


class MockScreenCapture(ScreenCapture):
    """Mock screen capture for testing without actual VM"""
    
    def __init__(self):
        super().__init__()
        self.mock_screen = None
        self.mock_sequence = []  # Sequence of screens to return
        self.capture_count = 0
        
    def connect(self, host: str, port: int = 5900, password: Optional[str] = None) -> bool:
        """Mock connection always succeeds"""
        self.is_connected = True
        print(f"Mock connection to {host}:{port} (for testing)")
        return True
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """Return a mock desktop screenshot"""
        if not self.is_connected:
            return None
        
        # If sequence is provided, cycle through it
        if self.mock_sequence:
            screen = self.mock_sequence[self.capture_count % len(self.mock_sequence)]
            self.capture_count += 1
            return screen
        
        # Create a simple mock desktop
        mock_desktop = np.ones((768, 1024, 3), dtype=np.uint8) * 240  # Light gray background
        
        # Add some mock UI elements based on capture count (simulate state changes)
        if self.capture_count == 0:
            # Initial desktop
            cv2.rectangle(mock_desktop, (100, 100), (200, 150), (200, 200, 200), -1)  # Mock window
            cv2.putText(mock_desktop, "Mock Desktop", (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # Add a mock app icon
            cv2.rectangle(mock_desktop, (180, 180), (220, 220), (100, 100, 200), -1)
            cv2.putText(mock_desktop, "App", (185, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
        elif self.capture_count >= 1:
            # Application launched
            cv2.rectangle(mock_desktop, (50, 50), (700, 600), (240, 240, 240), -1)  # App window
            cv2.rectangle(mock_desktop, (50, 50), (700, 80), (100, 100, 150), -1)   # Title bar
            cv2.putText(mock_desktop, "Mock Application", (60, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Patient banner (critical for safety testing)
            cv2.rectangle(mock_desktop, (50, 90), (700, 130), (255, 255, 200), -1)  # Patient banner
            cv2.putText(mock_desktop, "Patient: John Doe | MRN: 123456 | DOB: 01/01/1980", (60, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Mock form fields
            cv2.rectangle(mock_desktop, (100, 200), (300, 230), (255, 255, 255), -1)  # Text field
            cv2.putText(mock_desktop, "Name Field", (105, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            
            # Mock submit button
            cv2.rectangle(mock_desktop, (400, 300), (500, 350), (100, 150, 100), -1)
            cv2.putText(mock_desktop, "Submit", (420, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        self.capture_count += 1
        return mock_desktop
    
    def set_mock_screen_sequence(self, screens: List[np.ndarray]):
        """Set sequence of mock screens for testing state changes"""
        self.mock_sequence = screens
        self.capture_count = 0
    
    def disconnect(self):
        """Mock disconnect"""
        self.is_connected = False
        print("Mock disconnected")


class MockInputActions(InputActions):
    """Mock input actions for testing without actual VM"""
    
    def __init__(self):
        super().__init__()
        self.actions_log = []
        self.should_fail = False  # For testing error scenarios
        
    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        """Mock click action"""
        if self.should_fail:
            action = f"Click {button} at ({x}, {y}) [FAILED]"
            self.actions_log.append(action)
            return ActionResult(False, "Mock click failure", time.time())
            
        action = f"Click {button} at ({x}, {y})"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())
    
    def double_click(self, x: int, y: int) -> ActionResult:
        """Mock double-click action"""
        if self.should_fail:
            action = f"Double-click at ({x}, {y}) [FAILED]"
            self.actions_log.append(action)
            return ActionResult(False, "Mock double-click failure", time.time())
            
        action = f"Double-click at ({x}, {y})"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())
    
    def type_text(self, text: str, delay_between_chars: float = 0.05) -> ActionResult:
        """Mock type text action"""
        if self.should_fail:
            action = f"Type: {text} [FAILED]"
            self.actions_log.append(action)
            return ActionResult(False, "Mock type failure", time.time())
            
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
    
    def scroll(self, x: int, y: int, direction: str = "up", clicks: int = 3) -> ActionResult:
        """Mock scroll action"""
        action = f"Scroll {direction} {clicks} times at ({x}, {y})"
        self.actions_log.append(action)
        print(f"Mock: {action}")
        return ActionResult(True, action, time.time())
    
    def set_failure_mode(self, should_fail: bool):
        """Set whether actions should fail (for testing error handling)"""
        self.should_fail = should_fail
    
    def get_actions_log(self) -> List[str]:
        """Get log of all mock actions"""
        return self.actions_log.copy()
    
    def clear_log(self):
        """Clear actions log"""
        self.actions_log.clear()


class MockUIFinder:
    """Mock UI finder for testing"""
    
    def __init__(self):
        self.elements_to_find = {}  # Dict of text -> UIElement
        self.should_fail_searches = []  # List of texts that should fail
        
    def find_element_by_text(self, screenshot, text) -> List[UIElement]:
        """Mock element finding by text"""
        if text in self.should_fail_searches:
            return []
            
        if text in self.elements_to_find:
            return [self.elements_to_find[text]]
        
        # Default mock elements for common searches
        mock_elements = {
            "MyApp.exe": UIElement(
                element_type="text",
                bbox=(180, 180, 220, 220),
                center=(200, 200),
                confidence=0.9,
                text=text,
                description=f"Mock app icon: {text}"
            ),
            "Submit": UIElement(
                element_type="text", 
                bbox=(400, 300, 500, 350),
                center=(450, 325),
                confidence=0.9,
                text=text,
                description=f"Mock button: {text}"
            ),
            "John Doe": UIElement(
                element_type="text",
                bbox=(60, 90, 200, 130),
                center=(130, 110),
                confidence=0.9,
                text=text,
                description=f"Mock patient name: {text}"
            ),
            "123456": UIElement(
                element_type="text",
                bbox=(250, 90, 350, 130),
                center=(300, 110),
                confidence=0.9,
                text=text,
                description=f"Mock MRN: {text}"
            )
        }
        
        return [mock_elements.get(text, UIElement(
            element_type="text",
            bbox=(100, 100, 200, 150),
            center=(150, 125),
            confidence=0.8,
            text=text,
            description=f"Mock element: {text}"
        ))]
    
    def find_ui_elements(self, screenshot) -> List[UIElement]:
        """Mock finding all UI elements"""
        return [
            UIElement("detected", (50, 50, 700, 600), (375, 325), 0.9, description="Mock app window"),
            UIElement("text", (400, 300, 500, 350), (450, 325), 0.9, text="Submit", description="Mock submit button"),
            UIElement("text", (100, 200, 300, 230), (200, 215), 0.8, text="Name Field", description="Mock input field")
        ]
    
    def find_clickable_elements(self, screenshot) -> List[UIElement]:
        """Mock finding clickable elements"""
        return [
            UIElement("text", (400, 300, 500, 350), (450, 325), 0.9, text="Submit", description="Mock clickable button")
        ]
    
    def add_mock_element(self, text: str, element: UIElement):
        """Add a mock element for testing"""
        self.elements_to_find[text] = element
    
    def set_search_failure(self, text: str, should_fail: bool):
        """Set whether a search should fail"""
        if should_fail:
            self.should_fail_searches.append(text)
        else:
            if text in self.should_fail_searches:
                self.should_fail_searches.remove(text)


class MockOCRReader:
    """Mock OCR reader for testing"""
    
    def __init__(self):
        self.mock_text_regions = {}  # Dict of region -> text
        
    def read_text(self, image: np.ndarray, region: Optional[Tuple[int, int, int, int]] = None):
        """Mock text reading"""
        # Mock patient banner text for safety testing
        if region and region[3] <= image.shape[0] * 0.2:  # Top 20% of screen (banner area)
            return [
                MockTextDetection("Patient: John Doe", 0.95, (60, 90, 200, 130)),
                MockTextDetection("MRN: 123456", 0.93, (220, 90, 300, 130)),
                MockTextDetection("DOB: 01/01/1980", 0.91, (320, 90, 450, 130))
            ]
        
        # Default mock text
        return [
            MockTextDetection("Submit", 0.9, (400, 300, 500, 350)),
            MockTextDetection("Name Field", 0.8, (100, 200, 300, 230))
        ]
    
    def read_field_value(self, image: np.ndarray, field_region: Tuple[int, int, int, int]) -> Optional[str]:
        """Mock field value reading"""
        # Return mock field values based on region
        return "Mock field value"
    
    def find_text(self, image: np.ndarray, target_text: str, threshold: float = 0.8):
        """Mock text finding"""
        mock_detections = self.read_text(image)
        return [det for det in mock_detections if target_text.lower() in det.text.lower()]


@dataclass
class MockTextDetection:
    """Mock text detection result"""
    text: str
    confidence: float
    rect_bbox: Tuple[int, int, int, int]
    
    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.rect_bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property 
    def bbox(self) -> List[Tuple[int, int]]:
        """4 corner points for compatibility"""
        x1, y1, x2, y2 = self.rect_bbox
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


class MockVerifier:
    """Mock action verifier for testing"""
    
    def __init__(self):
        self.should_fail_verifications = []  # List of verification types that should fail
    
    def verify_page_loaded(self, screenshot, indicators, timeout=5) -> VerificationResult:
        """Mock page load verification"""
        if "page_load" in self.should_fail_verifications:
            return VerificationResult(False, "Mock page load verification failed", 0.1)
        
        found_indicators = [ind for ind in indicators if ind in ["Desktop", "Start", "Submit", "MockDesktop"]]
        return VerificationResult(
            len(found_indicators) > 0, 
            f"Mock verification: found {found_indicators}", 
            0.9
        )
    
    def verify_click_success(self, before, after, expected="any") -> VerificationResult:
        """Mock click verification"""
        if "click_success" in self.should_fail_verifications:
            return VerificationResult(False, "Mock click verification failed", 0.1)
        
        return VerificationResult(True, "Mock click verified", 0.9)
    
    def verify_element_present(self, screenshot, description) -> VerificationResult:
        """Mock element presence verification"""
        if "element_present" in self.should_fail_verifications:
            return VerificationResult(False, f"Mock element not found: {description}", 0.1)
        
        return VerificationResult(True, f"Mock element found: {description}", 0.9)
    
    def set_verification_failure(self, verification_type: str, should_fail: bool):
        """Set whether a verification type should fail"""
        if should_fail:
            self.should_fail_verifications.append(verification_type)
        else:
            if verification_type in self.should_fail_verifications:
                self.should_fail_verifications.remove(verification_type)


def create_mock_components() -> Dict[str, Any]:
    """Create a complete set of mock components for testing"""
    screen_capture = MockScreenCapture()
    input_actions = MockInputActions()
    ui_finder = MockUIFinder()
    ui_finder.ocr_reader = MockOCRReader()
    verifier = MockVerifier()
    
    return {
        "screen_capture": screen_capture,
        "input_actions": input_actions, 
        "ui_finder": ui_finder,
        "verifier": verifier
    }


def setup_patient_safety_test_scenario(mock_components: Dict[str, Any], patient_name: str = "John Doe", mrn: str = "123456"):
    """Setup mock components for patient safety testing"""
    # Add patient info to UI finder
    mock_components["ui_finder"].add_mock_element(patient_name, UIElement(
        element_type="text",
        bbox=(60, 90, 200, 130),
        center=(130, 110),
        confidence=0.95,
        text=patient_name,
        description=f"Patient name: {patient_name}"
    ))
    
    mock_components["ui_finder"].add_mock_element(mrn, UIElement(
        element_type="text",
        bbox=(220, 90, 300, 130),
        center=(260, 110),
        confidence=0.95,
        text=mrn,
        description=f"Patient MRN: {mrn}"
    ))


def setup_error_scenario(mock_components: Dict[str, Any], error_type: str):
    """Setup mock components to simulate various error scenarios"""
    if error_type == "connection_failure":
        mock_components["screen_capture"].is_connected = False
        
    elif error_type == "element_not_found":
        mock_components["ui_finder"].set_search_failure("Submit", True)
        
    elif error_type == "click_failure":
        mock_components["input_actions"].set_failure_mode(True)
        
    elif error_type == "verification_failure":
        mock_components["verifier"].set_verification_failure("click_success", True)
        
    elif error_type == "patient_mismatch":
        # Make patient verification fail
        mock_components["ui_finder"].set_search_failure("John Doe", True)