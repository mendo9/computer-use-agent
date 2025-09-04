"""Shared context and state between agents"""

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class VMConnectionInfo:
    """VM connection configuration"""

    host: str
    port: int = 5900
    username: str | None = None
    password: str | None = None
    connection_type: str = "vnc"  # vnc or rdp


@dataclass
class Screenshot:
    """Screenshot with metadata"""

    image: np.ndarray
    timestamp: float
    resolution: tuple[int, int]
    description: str | None = None


@dataclass
class VMSession:
    """Shared VM session state between agents"""

    # Connection info
    vm_config: VMConnectionInfo
    session_id: str

    # Session state
    is_connected: bool = False
    current_app: str | None = None
    screen_resolution: tuple[int, int] | None = None

    # Screenshots and artifacts
    screenshots: list[Screenshot] = field(default_factory=list)
    action_log: list[str] = field(default_factory=list)

    # Agent handoff data
    agent_1_completed: bool = False
    agent_1_results: dict[str, Any] = field(default_factory=dict)

    # Error tracking
    errors: list[str] = field(default_factory=list)
    retry_count: int = 0

    def add_screenshot(self, image: np.ndarray, description: str | None = None):
        """Add screenshot to session history"""
        if image is not None:
            height, width = image.shape[:2]
            screenshot = Screenshot(
                image=image,
                timestamp=time.time(),
                resolution=(width, height),
                description=description,
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

    def get_latest_screenshot(self) -> Screenshot | None:
        """Get the most recent screenshot"""
        return self.screenshots[-1] if self.screenshots else None

    def get_session_summary(self) -> dict[str, Any]:
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
            "retry_count": self.retry_count,
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
    target_app_icon: str | None = None  # Path to icon image for matching

    # Button target
    target_button_text: str = "Submit"  # Button to click in the app
    target_button_description: str | None = None

    # Verification criteria
    expected_desktop_elements: list[str] = field(
        default_factory=lambda: ["Desktop", "Start", "Taskbar"]
    )
    expected_app_elements: list[str] = field(default_factory=list)

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
            connection_type="vnc",
        )
