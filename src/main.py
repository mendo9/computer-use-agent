"""Main VM automation orchestrator - coordinates both agents"""

import argparse
import asyncio
import atexit
import json
import os
import signal
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.agents import AppControllerAgent, VMNavigatorAgent, VMSession, VMTarget


@dataclass
class VMConfig:
    """VM automation configuration"""

    # VM Connection
    vm_host: str
    vm_port: int = 5900
    vm_username: str | None = None
    vm_password: str | None = None
    connection_type: str = "vnc"  # "vnc" or "rdp"

    # RDP-specific parameters
    rdp_domain: str | None = None
    rdp_width: int = 1920
    rdp_height: int = 1080

    # Application Target
    target_app_name: str = "MyApp.exe"
    target_button_text: str = "Submit"

    # Patient Safety
    patient_name: str | None = None
    patient_mrn: str | None = None
    patient_dob: str | None = None

    # Expected UI Elements
    expected_desktop_elements: list | None = None
    expected_app_elements: list | None = None

    # Timeouts (seconds)
    vm_connection_timeout: int = 30
    desktop_load_timeout: int = 60
    app_launch_timeout: int = 30

    # Logging
    log_level: str = "INFO"
    save_screenshots: bool = True
    log_phi: bool = False  # Whether to log patient identifiable info

    def __post_init__(self):
        if self.expected_desktop_elements is None:
            self.expected_desktop_elements = ["Desktop", "Start", "Taskbar"]
        if self.expected_app_elements is None:
            self.expected_app_elements = []

    @classmethod
    def from_env(cls) -> "VMConfig":
        """Create config from environment variables"""
        return cls(
            vm_host=os.getenv("VM_HOST", "192.168.1.100"),
            vm_port=int(os.getenv("VM_PORT", "5900")),
            vm_username=os.getenv("VM_USERNAME"),
            vm_password=os.getenv("VM_PASSWORD"),
            connection_type=os.getenv("CONNECTION_TYPE", "vnc"),
            rdp_domain=os.getenv("RDP_DOMAIN"),
            rdp_width=int(os.getenv("RDP_WIDTH", "1920")),
            rdp_height=int(os.getenv("RDP_HEIGHT", "1080")),
            target_app_name=os.getenv("TARGET_APP", "MyApp.exe"),
            target_button_text=os.getenv("TARGET_BUTTON", "Submit"),
            patient_name=os.getenv("PATIENT_NAME"),
            patient_mrn=os.getenv("PATIENT_MRN"),
            patient_dob=os.getenv("PATIENT_DOB"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            save_screenshots=os.getenv("SAVE_SCREENSHOTS", "true").lower() == "true",
            log_phi=os.getenv("LOG_PHI", "false").lower() == "true",
        )

    @classmethod
    def from_file(cls, config_path: str) -> "VMConfig":
        """Create config from JSON file"""
        with open(config_path) as f:
            config_data = json.load(f)
        return cls(**config_data)

    def to_vm_target(self) -> VMTarget:
        """Convert to VM target configuration"""
        return VMTarget(
            vm_host=self.vm_host,
            vm_port=self.vm_port,
            vm_username=self.vm_username or "",
            vm_password=self.vm_password or "",
            connection_type=self.connection_type,
            target_app_name=self.target_app_name,
            target_button_text=self.target_button_text,
            expected_desktop_elements=self.expected_desktop_elements,
            expected_app_elements=self.expected_app_elements,
            vm_connection_timeout=self.vm_connection_timeout,
            desktop_load_timeout=self.desktop_load_timeout,
            app_launch_timeout=self.app_launch_timeout,
        )

    def get_patient_info(self) -> dict[str, str]:
        """Get patient information for safety verification"""
        return {
            "name": self.patient_name or "",
            "mrn": self.patient_mrn or "",
            "dob": self.patient_dob or "",
        }


class VMAutomation:
    """Main VM Automation class that orchestrates both agents"""

    def __init__(self, config: VMConfig):
        """
        Initialize VM Automation system

        Args:
            config: VM automation configuration
        """
        self.config = config
        self.vm_target = config.to_vm_target()
        self.session_id = str(uuid.uuid4())[:8]

        # Initialize session
        self.session = VMSession(
            vm_config=self.vm_target.to_vm_config(), session_id=self.session_id
        )

        # Initialize VM Navigator Agent
        self.vm_navigator = VMNavigatorAgent(self.session, self.vm_target)
        self.app_controller = (
            None  # Will be initialized with shared components after VM Navigator runs
        )

        # Track connections for cleanup
        self._connections_to_cleanup = []

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        print(f"VM Automation initialized (Session: {self.session_id})")
        print(f"Target VM: {config.vm_host}")
        print(f"Target App: {config.target_app_name}")
        print(f"Target Button: {config.target_button_text}")
        if config.patient_name:
            if config.log_phi:
                print(f"Patient: {config.patient_name}, MRN: {config.patient_mrn}")
            else:
                print("Patient safety verification enabled")

    async def run_full_automation(self) -> dict[str, Any]:
        """
        Run the complete VM automation workflow

        Returns:
            Dictionary with automation results
        """
        start_time = time.time()
        self.session.log_action("Starting VM automation")

        try:
            # Phase 1: VM Navigation with Patient Safety
            self.session.log_action("=== PHASE 1: VM Navigation & Patient Safety ===")

            patient_info = self.config.get_patient_info()
            nav_result = await self.vm_navigator.execute_navigation(
                patient_info=patient_info if any(patient_info.values()) else None
            )

            if not nav_result["success"]:
                return {
                    "success": False,
                    "phase_failed": "vm_navigation",
                    "error": nav_result.get("error", "VM navigation failed"),
                    "session_summary": self.session.get_session_summary(),
                    "execution_time": time.time() - start_time,
                }

            self.session.log_action("Phase 1 completed successfully")

            # Initialize App Controller with shared components from VM Navigator
            shared_components = nav_result.get("shared_components", {})
            if not shared_components:
                return {
                    "success": False,
                    "phase_failed": "component_sharing",
                    "error": "Failed to share components between agents",
                    "session_summary": self.session.get_session_summary(),
                    "execution_time": time.time() - start_time,
                }

            self.app_controller = AppControllerAgent(
                self.session, self.vm_target, shared_components
            )

            # Brief pause between agents
            await asyncio.sleep(1)

            # Phase 2: App Interaction (Agent 2)
            self.session.log_action("=== PHASE 2: App Interaction ===")
            app_result = await self.app_controller.execute_button_click_workflow()

            if not app_result["success"]:
                return {
                    "success": False,
                    "phase_failed": "app_interaction",
                    "error": app_result.get("error", "App interaction failed"),
                    "session_summary": self.session.get_session_summary(),
                    "execution_time": time.time() - start_time,
                }

            self.session.log_action("Phase 2 completed successfully")

            # Automation completed successfully
            execution_time = time.time() - start_time
            self.session.log_action(
                f"VM automation completed successfully in {execution_time:.2f}s"
            )

            return {
                "success": True,
                "message": "VM automation completed successfully",
                "phases": {"vm_navigation": nav_result, "app_interaction": app_result},
                "session_summary": self.session.get_session_summary(),
                "execution_time": execution_time,
                "session_id": self.session_id,
            }

        except Exception as e:
            error_msg = f"Automation execution error: {e!s}"
            self.session.add_error(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "session_summary": self.session.get_session_summary(),
                "execution_time": time.time() - start_time,
            }
        finally:
            # Always clean up connections regardless of success/failure
            self.cleanup()

    async def run_vm_navigation_only(self) -> dict[str, Any]:
        """Run only the VM navigation phase (for testing)"""
        try:
            self.session.log_action("Running VM Navigation phase only")
            return await self.vm_navigator.execute_navigation()
        finally:
            self.cleanup()

    async def run_app_interaction_only(self) -> dict[str, Any]:
        """Run only the app interaction phase (assumes app is already running)"""
        try:
            # Mark agent 1 as completed for testing
            self.session.agent_1_completed = True
            self.session.current_app = self.vm_target.target_app_name

            # Initialize app_controller if not initialized
            if self.app_controller is None:
                raise RuntimeError(
                    "Cannot run app interaction only without shared components from VM Navigator. Run VM navigation phase first."
                )

            self.session.log_action("Running App Interaction phase only")
            return await self.app_controller.execute_button_click_workflow()
        finally:
            self.cleanup()

    def get_session_log(self) -> dict[str, Any]:
        """Get complete session log and state"""
        return {
            "session_id": self.session_id,
            "vm_target": {
                "vm_host": self.vm_target.vm_host,
                "target_app": self.vm_target.target_app_name,
                "target_button": self.vm_target.target_button_text,
            },
            "session_summary": self.session.get_session_summary(),
            "action_log": self.session.action_log,
            "errors": self.session.errors,
            "screenshots_count": len(self.session.screenshots),
        }

    def save_session_log(self, filepath: str | None = None) -> str:
        """Save session log to file"""
        if not filepath:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"vm_session_{self.session_id}_{timestamp}.json"

        import json

        log_data = self.get_session_log()

        with open(filepath, "w") as f:
            json.dump(log_data, f, indent=2, default=str)

        print(f"Session log saved to: {filepath}")
        return filepath

    def cleanup(self):
        """Clean up all connections and resources"""
        print("\n🧹 Cleaning up connections...")
        
        try:
            # Clean up any tracked connections
            for connection in self._connections_to_cleanup:
                try:
                    if hasattr(connection, 'disconnect'):
                        result = connection.disconnect()
                        if result.success:
                            print(f"✓ {result.message}")
                        else:
                            print(f"⚠ {result.message}")
                    elif hasattr(connection, 'close'):
                        connection.close()
                        print("✓ Connection closed")
                except Exception as e:
                    print(f"⚠ Error disconnecting: {e}")
            
            # Clean up VM Navigator connections
            if hasattr(self.vm_navigator, 'tools') and self.vm_navigator.tools and hasattr(self.vm_navigator.tools, 'screen_capture'):
                try:
                    self.vm_navigator.tools.screen_capture.disconnect()
                    print("✓ VM Navigator connection cleaned up")
                except Exception as e:
                    print(f"⚠ Error cleaning VM Navigator: {e}")
            
            # Clean up App Controller connections
            if self.app_controller and hasattr(self.app_controller, 'tools') and self.app_controller.tools and hasattr(self.app_controller.tools, 'screen_capture'):
                try:
                    self.app_controller.tools.screen_capture.disconnect()
                    print("✓ App Controller connection cleaned up")
                except Exception as e:
                    print(f"⚠ Error cleaning App Controller: {e}")
                    
        except Exception as e:
            print(f"⚠ Error during cleanup: {e}")

    def _signal_handler(self, signum, _frame):
        """Handle interrupt signals"""
        print(f"\n⏹️ Received signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(1)

    def register_connection(self, connection):
        """Register a connection for cleanup tracking"""
        if connection not in self._connections_to_cleanup:
            self._connections_to_cleanup.append(connection)


def cli_main():
    """CLI entry point for production deployment"""
    parser = argparse.ArgumentParser(description="VM Automation - Production GUI Automation System")
    parser.add_argument("--config", "-c", help="Configuration file path (JSON)")
    parser.add_argument(
        "--connection",
        choices=["vnc", "rdp"],
        default="vnc",
        help="Connection type: vnc or rdp (default: vnc)",
    )
    parser.add_argument("--validate-env", action="store_true", help="Validate environment and exit")
    parser.add_argument(
        "--create-samples", action="store_true", help="Create sample configuration files"
    )

    args = parser.parse_args()

    if args.create_samples:
        create_sample_files()
        return True

    if args.validate_env:
        return validate_environment()

    # Run the automation
    try:
        # Load configuration
        if args.config and os.path.exists(args.config):
            config = VMConfig.from_file(args.config)
            print(f"✓ Loaded configuration from {args.config}")
        elif os.path.exists("vm_config.json"):
            config = VMConfig.from_file("vm_config.json")
            print("✓ Loaded configuration from vm_config.json")
        else:
            config = VMConfig.from_env()
            print("✓ Using environment variables and defaults")

        # Override connection type from CLI if provided
        if args.connection:
            config.connection_type = args.connection
            print(f"✓ Using {args.connection.upper()} connection (CLI override)")

        # Run automation
        automation = VMAutomation(config)
        result = asyncio.run(automation.run_full_automation())

        # Show results
        print("\n" + "=" * 50)
        print("🤖 AUTOMATION RESULTS:")
        print("=" * 50)

        if result["success"]:
            print("✅ STATUS: SUCCESS")
            print(f"⏱️  Execution Time: {result['execution_time']:.2f} seconds")
            if config.patient_name and result.get("patient_verified"):
                print("🛡️  Patient Safety: ✅ VERIFIED")
        else:
            print("❌ STATUS: FAILED")
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
            if result.get("safety_critical"):
                print("🚨 CRITICAL SAFETY FAILURE")

        # Save session report
        log_file = automation.save_session_log()
        print(f"📋 Session Report: {log_file}")

        return result["success"]

    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return False
    except Exception as e:
        print(f"💥 FATAL ERROR: {e!s}")
        return False


def validate_environment() -> bool:
    """Validate that environment is ready for automation"""
    issues = []

    # Check for AI models
    models_dir = Path(__file__).parent / "models"
    yolo_path = models_dir / "yolov8s.onnx"

    if not yolo_path.exists():
        issues.append(f"❌ YOLO model missing: {yolo_path}")
        issues.append("   Run: uv run src/setup_models.py")

    # Check configuration
    if not os.path.exists("vm_config.json") and not os.getenv("VM_HOST"):
        issues.append("❌ No configuration found")
        issues.append("   Create vm_config.json or set VM_HOST environment variable")

    if issues:
        print("🚨 ENVIRONMENT ISSUES:")
        for issue in issues:
            print(f"   {issue}")
        return False

    print("✅ Environment validation passed")
    return True


def create_sample_files():
    """Create sample configuration files"""
    # Create sample VM config
    sample_config = {
        "vm_host": "192.168.1.100",
        "vm_port": 5900,
        "vm_username": "username",
        "vm_password": "password",
        "connection_type": "vnc",
        "rdp_domain": None,
        "rdp_width": 1920,
        "rdp_height": 1080,
        "target_app_name": "MyApp.exe",
        "target_button_text": "Submit",
        "expected_desktop_elements": ["Desktop", "Start", "Taskbar"],
        "expected_app_elements": ["Submit", "Button"],
        "log_level": "INFO",
        "save_screenshots": True,
        "log_phi": False,
    }

    with open("vm_config.sample.json", "w") as f:
        json.dump(sample_config, f, indent=2)

    print("✓ Created vm_config.sample.json")
    print("  Copy to vm_config.json and customize for your environment")


if __name__ == "__main__":
    success = cli_main()
    sys.exit(0 if success else 1)
