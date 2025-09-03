#!/usr/bin/env python3
"""Simple runner script for VM Automation POC"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import VMAutomation, create_default_poc_target


def print_banner():
    """Print POC banner"""
    print("="*60)
    print("🤖 VM AUTOMATION POC - AI Agent GUI Interaction")
    print("="*60)
    print("Two-Agent Architecture:")
    print("  Agent 1: VM Navigator  → Connect, Login, Launch App") 
    print("  Agent 2: App Controller → Find Button, Click, Verify")
    print("="*60)


async def run_poc_demo():
    """Run the POC demonstration"""
    print_banner()
    
    # Create POC target configuration
    print("📋 Creating POC Configuration...")
    poc_target = create_default_poc_target()
    
    print(f"   VM Host: {poc_target.vm_host}")
    print(f"   Target App: {poc_target.target_app_name}")
    print(f"   Target Button: {poc_target.target_button_text}")
    print(f"   Using Mock Mode: True (for demo)")
    print()
    
    # Initialize POC
    print("🚀 Initializing VM Automation POC...")
    poc = VMAutomation(poc_target, use_mock=True)
    print(f"   Session ID: {poc.session_id}")
    print()
    
    # Run the complete workflow
    print("▶️  Starting POC Execution...")
    print("-" * 40)
    
    try:
        result = await poc.run_full_poc()
        
        print("-" * 40)
        print("📊 POC EXECUTION RESULTS:")
        print("-" * 40)
        
        if result["success"]:
            print("✅ STATUS: SUCCESS")
            print(f"⏱️  Execution Time: {result['execution_time']:.2f} seconds")
            print(f"🆔 Session ID: {result['session_id']}")
            
            print("\n📋 Phase Results:")
            for phase_name, phase_result in result["phases"].items():
                status = "✅" if phase_result["success"] else "❌"
                print(f"   {status} {phase_name}: {phase_result.get('message', 'Completed')}")
            
            print("\n📈 Session Summary:")
            summary = result["session_summary"]
            print(f"   Screenshots Captured: {summary['screenshots_count']}")
            print(f"   Actions Performed: {summary['actions_count']}")
            print(f"   Errors: {summary['errors_count']}")
            print(f"   VM Connected: {summary['is_connected']}")
            print(f"   App Launched: {summary['current_app']}")
            
        else:
            print("❌ STATUS: FAILED")
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
            
            if 'phase_failed' in result:
                print(f"📍 Failed Phase: {result['phase_failed']}")
        
        # Save session log
        print("\n💾 Saving Session Log...")
        log_file = poc.save_session_log()
        print(f"   Log saved to: {log_file}")
        
        # Show action log
        print("\n📝 Action Log (last 10 actions):")
        action_log = poc.session.action_log[-10:]  # Last 10 actions
        for i, action in enumerate(action_log, 1):
            print(f"   {i:2d}. {action}")
        
        if poc.session.errors:
            print("\n⚠️  Errors Encountered:")
            for error in poc.session.errors:
                print(f"   • {error}")
        
    except Exception as e:
        print(f"💥 FATAL ERROR: {str(e)}")
        return False
    
    print("\n" + "="*60)
    print("🏁 POC DEMO COMPLETED")
    print("="*60)
    
    return result["success"]


async def run_individual_phases():
    """Run individual phases for testing"""
    print_banner()
    print("🧪 INDIVIDUAL PHASE TESTING")
    print()
    
    poc_target = create_default_poc_target()
    poc = VMAutomation(poc_target, use_mock=True)
    
    # Test Phase 1 only
    print("▶️  Testing Phase 1: VM Navigation...")
    nav_result = await poc.run_vm_navigation_only()
    print(f"   Result: {'✅ SUCCESS' if nav_result['success'] else '❌ FAILED'}")
    
    # Test Phase 2 only
    print("▶️  Testing Phase 2: App Interaction...")
    app_result = await poc.run_app_interaction_only()
    print(f"   Result: {'✅ SUCCESS' if app_result['success'] else '❌ FAILED'}")
    
    return nav_result["success"] and app_result["success"]


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "phases":
        # Run individual phases
        success = asyncio.run(run_individual_phases())
    else:
        # Run full POC demo
        success = asyncio.run(run_poc_demo())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()