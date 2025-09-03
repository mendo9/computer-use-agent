"""Shared context and state between agents"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
import time
import numpy as np


@dataclass
class VMConnectionInfo:
    """VM connection configuration"""
    host: str
    port: int = 5900
    username: Optional[str] = None
    password: Optional[str] = None
    connection_type: str = "vnc"  # vnc or rdp


@dataclass
class Screenshot:
    """Screenshot with metadata"""
    image: np.ndarray
    timestamp: float
    resolution: Tuple[int, int]
    description: Optional[str] = None


@dataclass
class VMSession:
    """Shared VM session state between agents"""
    # Connection info
    vm_config: VMConnectionInfo
    session_id: str
    
    # Session state
    is_connected: bool = False
    current_app: Optional[str] = None
    screen_resolution: Optional[Tuple[int, int]] = None
    
    # Screenshots and artifacts
    screenshots: List[Screenshot] = field(default_factory=list)
    action_log: List[str] = field(default_factory=list)
    
    # Agent handoff data
    agent_1_completed: bool = False
    agent_1_results: Dict[str, Any] = field(default_factory=dict)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    
    def add_screenshot(self, image: np.ndarray, description: str = None):
        """Add screenshot to session history"""
        if image is not None:
            height, width = image.shape[:2]
            screenshot = Screenshot(
                image=image,
                timestamp=time.time(),
                resolution=(width, height),
                description=description
            )
            self.screenshots.append(screenshot)
            
            # Keep only last 10 screenshots to manage memory
            if len(self.screenshots) > 10:
                self.screenshots = self.screenshots[-10:]
    
    def log_action(self, action: str):
        """Log an action taken during the session"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        log_entry = f"[{timestamp}] {action}"
        self.action_log.append(log_entry)
        print(f"Session Log: {log_entry}")
    
    def add_error(self, error: str):
        """Add error to session tracking"""
        self.errors.append(f"[{time.strftime('%H:%M:%S')}] {error}")
        print(f"Session Error: {error}")
    
    def get_latest_screenshot(self) -> Optional[Screenshot]:
        """Get the most recent screenshot"""
        return self.screenshots[-1] if self.screenshots else None
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of session state"""
        return {
            "session_id": self.session_id,
            "vm_host": self.vm_config.host,
            "is_connected": self.is_connected,
            "current_app": self.current_app,
            "screen_resolution": self.screen_resolution,
            "screenshots_count": len(self.screenshots),
            "actions_count": len(self.action_log),
            "errors_count": len(self.errors),
            "agent_1_completed": self.agent_1_completed,
            "retry_count": self.retry_count
        }


@dataclass
class VMTarget:
    """VM automation target configuration"""
    # VM login credentials
    vm_host: str
    vm_username: str
    vm_password: str
    vm_port: int = 5900
    
    # Application target
    target_app_name: str = "MyApp.exe"  # Desktop application to open
    target_app_icon: Optional[str] = None  # Path to icon image for matching
    
    # Button target
    target_button_text: str = "Submit"  # Button to click in the app
    target_button_description: Optional[str] = None
    
    # Verification criteria
    expected_desktop_elements: List[str] = field(default_factory=lambda: ["Desktop", "Start", "Taskbar"])
    expected_app_elements: List[str] = field(default_factory=list)
    
    # Timeouts
    vm_connection_timeout: int = 30
    desktop_load_timeout: int = 60
    app_launch_timeout: int = 30
    
    def to_vm_config(self) -> VMConnectionInfo:
        """Convert to VM connection configuration"""
        return VMConnectionInfo(
            host=self.vm_host,
            port=self.vm_port,
            username=self.vm_username,
            password=self.vm_password,
            connection_type="vnc"
        )