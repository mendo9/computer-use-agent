"""Main POC orchestrator - coordinates both agents"""

import asyncio
import uuid
import time
from typing import Dict, Any, Optional
from pathlib import Path

from .agents import VMSession, POCTarget, VMNavigatorAgent, AppControllerAgent


class VMAutomationPOC:
    """Main POC class that orchestrates both agents"""
    
    def __init__(self, poc_target: POCTarget, use_mock: bool = True):
        """
        Initialize VM Automation POC
        
        Args:
            poc_target: POC target configuration
            use_mock: Use mock implementations for testing
        """
        self.poc_target = poc_target
        self.use_mock = use_mock
        self.session_id = str(uuid.uuid4())[:8]
        
        # Initialize session
        self.session = VMSession(
            vm_config=poc_target.to_vm_config(),
            session_id=self.session_id
        )
        
        # Initialize agents
        self.vm_navigator = VMNavigatorAgent(self.session, poc_target, use_mock)
        self.app_controller = AppControllerAgent(self.session, poc_target, use_mock)
        
        print(f"VM Automation POC initialized (Session: {self.session_id})")
        print(f"Target VM: {poc_target.vm_host}")
        print(f"Target App: {poc_target.target_app_name}")
        print(f"Target Button: {poc_target.target_button_text}")
        print(f"Mock Mode: {use_mock}")
    
    async def run_full_poc(self) -> Dict[str, Any]:
        """
        Run the complete POC workflow
        
        Returns:
            Dictionary with POC results
        """
        start_time = time.time()
        self.session.log_action("Starting VM Automation POC")
        
        try:
            # Phase 1: VM Navigation (Agent 1)
            self.session.log_action("=== PHASE 1: VM Navigation ===")
            nav_result = await self.vm_navigator.execute_navigation()
            
            if not nav_result["success"]:
                return {
                    "success": False,
                    "phase_failed": "vm_navigation",
                    "error": nav_result.get("error", "VM navigation failed"),
                    "session_summary": self.session.get_session_summary(),
                    "execution_time": time.time() - start_time
                }
            
            self.session.log_action("Phase 1 completed successfully")
            
            # Brief pause between agents
            await asyncio.sleep(1)
            
            # Phase 2: App Interaction (Agent 2)
            self.session.log_action("=== PHASE 2: App Interaction ===")
            app_result = await self.app_controller.execute_app_interaction()
            
            if not app_result["success"]:
                return {
                    "success": False,
                    "phase_failed": "app_interaction",
                    "error": app_result.get("error", "App interaction failed"),
                    "session_summary": self.session.get_session_summary(),
                    "execution_time": time.time() - start_time
                }
            
            self.session.log_action("Phase 2 completed successfully")
            
            # POC completed successfully
            execution_time = time.time() - start_time
            self.session.log_action(f"POC completed successfully in {execution_time:.2f}s")
            
            return {
                "success": True,
                "message": "VM Automation POC completed successfully",
                "phases": {
                    "vm_navigation": nav_result,
                    "app_interaction": app_result
                },
                "session_summary": self.session.get_session_summary(),
                "execution_time": execution_time,
                "session_id": self.session_id
            }
            
        except Exception as e:
            error_msg = f"POC execution error: {str(e)}"
            self.session.add_error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "session_summary": self.session.get_session_summary(),
                "execution_time": time.time() - start_time
            }
    
    async def run_vm_navigation_only(self) -> Dict[str, Any]:
        """Run only the VM navigation phase (for testing)"""
        self.session.log_action("Running VM Navigation phase only")
        return await self.vm_navigator.execute_navigation()
    
    async def run_app_interaction_only(self) -> Dict[str, Any]:
        """Run only the app interaction phase (assumes app is already running)"""
        # Mark agent 1 as completed for testing
        self.session.agent_1_completed = True
        self.session.current_app = self.poc_target.target_app_name
        
        self.session.log_action("Running App Interaction phase only")
        return await self.app_controller.execute_app_interaction()
    
    def get_session_log(self) -> Dict[str, Any]:
        """Get complete session log and state"""
        return {
            "session_id": self.session_id,
            "poc_target": {
                "vm_host": self.poc_target.vm_host,
                "target_app": self.poc_target.target_app_name,
                "target_button": self.poc_target.target_button_text
            },
            "session_summary": self.session.get_session_summary(),
            "action_log": self.session.action_log,
            "errors": self.session.errors,
            "screenshots_count": len(self.session.screenshots)
        }
    
    def save_session_log(self, filepath: Optional[str] = None) -> str:
        """Save session log to file"""
        if not filepath:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"poc_session_{self.session_id}_{timestamp}.json"
        
        import json
        log_data = self.get_session_log()
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        print(f"Session log saved to: {filepath}")
        return filepath


def create_default_poc_target() -> POCTarget:
    """Create a default POC target for testing"""
    return POCTarget(
        vm_host="192.168.1.100",  # Update with actual VM IP
        vm_username="testuser",
        vm_password="testpass",
        target_app_name="MyApp.exe",
        target_button_text="Submit",
        expected_desktop_elements=["Desktop", "Start", "Taskbar"],
        expected_app_elements=["Submit", "Button"]
    )


async def main():
    """Main function for running the POC"""
    print("VM Automation POC - Starting...")
    
    # Create POC target
    poc_target = create_default_poc_target()
    
    # Initialize and run POC
    poc = VMAutomationPOC(poc_target, use_mock=True)
    
    # Run the complete workflow
    result = await poc.run_full_poc()
    
    print("\n" + "="*50)
    print("POC RESULTS:")
    print("="*50)
    print(f"Success: {result['success']}")
    
    if result['success']:
        print(f"Execution Time: {result['execution_time']:.2f}s")
        print(f"Session ID: {result['session_id']}")
        print("\nPhases completed:")
        for phase, phase_result in result['phases'].items():
            print(f"  - {phase}: {phase_result['success']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        if 'phase_failed' in result:
            print(f"Failed Phase: {result['phase_failed']}")
    
    print("\nSession Summary:")
    summary = result['session_summary']
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Save session log
    log_file = poc.save_session_log()
    print(f"\nFull session log saved to: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())