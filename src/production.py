"""Production POC orchestrator - clean version without mocks"""

import asyncio
import uuid
import time
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
import json

from agents.shared_context import VMSession, VMTarget
from agents.vm_navigator import VMNavigatorAgent
from agents.app_controller import AppControllerAgent


@dataclass
class ProductionConfig:
    """Production configuration for VM automation"""
    # VM Connection
    vm_host: str
    vm_port: int = 5900
    vm_username: Optional[str] = None
    vm_password: Optional[str] = None
    
    # Application Target
    target_app_name: str = "MyApp.exe"
    target_button_text: str = "Submit"
    
    # Patient Safety
    patient_name: Optional[str] = None
    patient_mrn: Optional[str] = None
    patient_dob: Optional[str] = None
    
    # Expected UI Elements
    expected_desktop_elements: List[str] = None
    expected_app_elements: List[str] = None
    
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
    def from_env(cls) -> 'ProductionConfig':
        """Create config from environment variables"""
        return cls(
            vm_host=os.getenv("VM_HOST", "192.168.1.100"),
            vm_port=int(os.getenv("VM_PORT", "5900")),
            vm_username=os.getenv("VM_USERNAME"),
            vm_password=os.getenv("VM_PASSWORD"),
            target_app_name=os.getenv("TARGET_APP", "MyApp.exe"),
            target_button_text=os.getenv("TARGET_BUTTON", "Submit"),
            patient_name=os.getenv("PATIENT_NAME"),
            patient_mrn=os.getenv("PATIENT_MRN"),
            patient_dob=os.getenv("PATIENT_DOB"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            save_screenshots=os.getenv("SAVE_SCREENSHOTS", "true").lower() == "true",
            log_phi=os.getenv("LOG_PHI", "false").lower() == "true"
        )
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ProductionConfig':
        """Create config from JSON file"""
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return cls(**config_data)
    
    def to_vm_target(self) -> VMTarget:
        """Convert to POC target configuration"""
        return VMTarget(
            vm_host=self.vm_host,
            vm_port=self.vm_port,
            vm_username=self.vm_username or "",
            vm_password=self.vm_password or "",
            target_app_name=self.target_app_name,
            target_button_text=self.target_button_text,
            expected_desktop_elements=self.expected_desktop_elements,
            expected_app_elements=self.expected_app_elements,
            vm_connection_timeout=self.vm_connection_timeout,
            desktop_load_timeout=self.desktop_load_timeout,
            app_launch_timeout=self.app_launch_timeout
        )
    
    def get_patient_info(self) -> Dict[str, str]:
        """Get patient information for safety verification"""
        return {
            "name": self.patient_name or "",
            "mrn": self.patient_mrn or "",
            "dob": self.patient_dob or ""
        }
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.vm_host:
            errors.append("VM host is required")
        
        if not self.vm_password and not self.vm_username:
            errors.append("VM credentials are required")
            
        if not self.target_app_name:
            errors.append("Target application name is required")
            
        if not self.target_button_text:
            errors.append("Target button text is required")
            
        # Patient safety validation
        patient_fields = [self.patient_name, self.patient_mrn, self.patient_dob]
        if any(patient_fields) and not all(patient_fields):
            errors.append("If patient info is provided, all fields (name, MRN, DOB) are required for safety")
            
        return errors


class VMAutomationProduction:
    """Production VM Automation orchestrator without mocks"""
    
    def __init__(self, config: ProductionConfig):
        """
        Initialize production VM automation
        
        Args:
            config: Production configuration
        """
        # Validate configuration
        config_errors = config.validate()
        if config_errors:
            raise ValueError(f"Configuration errors: {config_errors}")
            
        self.config = config
        self.session_id = str(uuid.uuid4())[:8]
        
        # Initialize session
        poc_target = config.to_vm_target()
        self.session = VMSession(
            vm_config=poc_target.to_vm_config(),
            session_id=self.session_id
        )
        
        # Initialize agents (no mocks)
        self.vm_navigator = VMNavigatorAgent(self.session, poc_target)
        self.app_controller = None  # Will be initialized with shared components
        
        self.session.log_action(f"Production VM Automation initialized (Session: {self.session_id})")
        self.session.log_action(f"Target VM: {config.vm_host}")
        self.session.log_action(f"Target App: {config.target_app_name}")
        self.session.log_action(f"Target Button: {config.target_button_text}")
        
        if config.patient_name:
            # Log patient info based on PHI policy
            if config.log_phi:
                self.session.log_action(f"Patient: {config.patient_name}, MRN: {config.patient_mrn}")
            else:
                self.session.log_action("Patient information configured (PHI logging disabled)")
    
    async def run_full_automation(self) -> Dict[str, Any]:
        """
        Run the complete production automation workflow
        
        Returns:
            Dictionary with automation results
        """
        start_time = time.time()
        self.session.log_action("Starting production VM automation")
        
        try:
            # Phase 1: VM Navigation with Patient Safety
            self.session.log_action("=== PHASE 1: VM Navigation & Patient Safety ===")
            
            patient_info = self.config.get_patient_info()
            nav_result = await self.vm_navigator.execute_navigation(
                patient_info=patient_info if any(patient_info.values()) else None
            )
            
            if not nav_result["success"]:
                # Check if this was a patient safety failure
                if nav_result.get("failed_step") == "Verify patient identity":
                    return {
                        "success": False,
                        "phase_failed": "patient_safety_verification",
                        "error": "CRITICAL SAFETY FAILURE: " + nav_result.get("error", "Patient verification failed"),
                        "safety_critical": True,
                        "session_summary": self.session.get_session_summary(),
                        "execution_time": time.time() - start_time
                    }
                
                return {
                    "success": False,
                    "phase_failed": "vm_navigation",
                    "error": nav_result.get("error", "VM navigation failed"),
                    "session_summary": self.session.get_session_summary(),
                    "execution_time": time.time() - start_time
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
                    "execution_time": time.time() - start_time
                }
            
            self.app_controller = AppControllerAgent(
                self.session, 
                self.config.to_vm_target(),
                shared_components
            )
            
            # Brief pause between agents
            await asyncio.sleep(1)
            
            # Phase 2: Application Interaction
            self.session.log_action("=== PHASE 2: Application Interaction ===")
            
            app_result = await self.app_controller.execute_button_click_workflow(
                expected_outcomes=["Success", "Completed", "Submitted"]  # Common success indicators
            )
            
            if not app_result["success"]:
                return {
                    "success": False,
                    "phase_failed": "app_interaction",
                    "error": app_result.get("error", "App interaction failed"),
                    "session_summary": self.session.get_session_summary(),
                    "execution_time": time.time() - start_time
                }
            
            self.session.log_action("Phase 2 completed successfully")
            
            # Automation completed successfully
            execution_time = time.time() - start_time
            self.session.log_action(f"Production automation completed successfully in {execution_time:.2f}s")
            
            return {
                "success": True,
                "message": "VM Automation completed successfully",
                "phases": {
                    "vm_navigation": nav_result,
                    "app_interaction": app_result
                },
                "patient_verified": nav_result.get("patient_verified", False),
                "session_summary": self.session.get_session_summary(),
                "execution_time": execution_time,
                "session_id": self.session_id
            }
            
        except Exception as e:
            error_msg = f"Production automation error: {str(e)}"
            self.session.add_error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "session_summary": self.session.get_session_summary(),
                "execution_time": time.time() - start_time
            }
    
    async def run_form_filling_workflow(self, form_data: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Run form filling workflow for multiple fields
        
        Args:
            form_data: List of field data with 'field_name' and 'value' keys
            
        Returns:
            Dictionary with workflow results
        """
        start_time = time.time()
        self.session.log_action(f"Starting form filling workflow with {len(form_data)} fields")
        
        try:
            # First run VM navigation if not already done
            if not self.session.agent_1_completed:
                nav_result = await self.run_vm_navigation_only()
                if not nav_result["success"]:
                    return nav_result
            
            # Ensure we have app controller with shared components
            if not self.app_controller:
                return {
                    "success": False,
                    "error": "App controller not initialized - run VM navigation first"
                }
            
            # Execute form filling
            form_result = await self.app_controller.execute_form_filling_workflow(
                form_fields=form_data,
                submit_button=self.config.target_button_text
            )
            
            execution_time = time.time() - start_time
            
            if form_result["success"]:
                self.session.log_action(f"Form filling completed successfully in {execution_time:.2f}s")
                
            return {
                **form_result,
                "execution_time": execution_time,
                "session_summary": self.session.get_session_summary()
            }
            
        except Exception as e:
            error_msg = f"Form filling workflow error: {str(e)}"
            self.session.add_error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "execution_time": time.time() - start_time
            }
    
    async def run_vm_navigation_only(self) -> Dict[str, Any]:
        """Run only the VM navigation phase"""
        self.session.log_action("Running VM Navigation phase only")
        
        patient_info = self.config.get_patient_info()
        return await self.vm_navigator.execute_navigation(
            patient_info=patient_info if any(patient_info.values()) else None
        )
    
    def get_session_report(self) -> Dict[str, Any]:
        """Get comprehensive session report"""
        return {
            "session_id": self.session_id,
            "config": {
                "vm_host": self.config.vm_host,
                "target_app": self.config.target_app_name,
                "target_button": self.config.target_button_text,
                "patient_configured": bool(self.config.patient_name)
            },
            "session_summary": self.session.get_session_summary(),
            "action_log": self.session.action_log if self.config.log_level == "DEBUG" else self.session.action_log[-10:],
            "errors": self.session.errors,
            "screenshots_count": len(self.session.screenshots)
        }
    
    def save_session_report(self, output_dir: Optional[str] = None) -> str:
        """Save comprehensive session report"""
        if not output_dir:
            output_dir = "session_logs"
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"vm_automation_{self.session_id}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        report = self.get_session_report()
        
        # Filter PHI if needed
        if not self.config.log_phi:
            # Remove patient-specific information from logs
            filtered_logs = []
            for log in report["action_log"]:
                # Simple PHI filtering - in production use more sophisticated methods
                filtered_log = log
                if self.config.patient_name and self.config.patient_name in log:
                    filtered_log = log.replace(self.config.patient_name, "[PATIENT_NAME]")
                if self.config.patient_mrn and self.config.patient_mrn in log:
                    filtered_log = filtered_log.replace(self.config.patient_mrn, "[PATIENT_MRN]")
                filtered_logs.append(filtered_log)
            
            report["action_log"] = filtered_logs
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.session.log_action(f"Session report saved to: {filepath}")
        return filepath


def create_sample_config() -> ProductionConfig:
    """Create a sample configuration for testing"""
    return ProductionConfig(
        vm_host="192.168.1.100",
        vm_port=5900,
        vm_username="testuser",
        vm_password="testpass",
        target_app_name="EMRApp.exe",
        target_button_text="Submit",
        patient_name="John Doe",
        patient_mrn="123456",
        patient_dob="01/01/1980",
        expected_app_elements=["Submit", "Patient", "Save"],
        save_screenshots=True,
        log_phi=False  # Never log PHI in production
    )


async def main():
    """Production main function"""
    print("🏥 VM Automation - Production Mode")
    print("="*50)
    
    try:
        # Load configuration (from env, file, or sample)
        if os.path.exists("vm_config.json"):
            config = ProductionConfig.from_file("vm_config.json")
            print("✓ Loaded configuration from vm_config.json")
        else:
            config = ProductionConfig.from_env()
            print("✓ Loaded configuration from environment variables")
        
        # Initialize production automation
        automation = VMAutomationProduction(config)
        
        print(f"Session ID: {automation.session_id}")
        print(f"VM Target: {config.vm_host}:{config.vm_port}")
        print(f"Patient Safety: {'Enabled' if config.patient_name else 'Disabled'}")
        print()
        
        # Run automation
        print("🚀 Starting automation workflow...")
        result = await automation.run_full_automation()
        
        print("\n" + "="*50)
        print("📊 AUTOMATION RESULTS:")
        print("="*50)
        
        if result["success"]:
            print("✅ STATUS: SUCCESS")
            print(f"⏱️  Execution Time: {result['execution_time']:.2f} seconds")
            print(f"🛡️  Patient Verified: {result.get('patient_verified', 'N/A')}")
            
            summary = result["session_summary"]
            print(f"📸 Screenshots: {summary['screenshots_count']}")
            print(f"⚡ Actions: {summary['actions_count']}")
            print(f"❌ Errors: {summary['errors_count']}")
            
        else:
            print("❌ STATUS: FAILED")
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
            
            if result.get("safety_critical"):
                print("🚨 CRITICAL SAFETY FAILURE - AUTOMATION STOPPED")
            
            if 'phase_failed' in result:
                print(f"📍 Failed Phase: {result['phase_failed']}")
        
        # Save session report
        report_path = automation.save_session_report()
        print(f"📋 Full report: {report_path}")
        
        return result["success"]
        
    except Exception as e:
        print(f"💥 FATAL ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)