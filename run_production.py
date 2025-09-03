#!/usr/bin/env python3
"""Production runner for VM Automation - Clean version without mocks"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from production import VMAutomationProduction, ProductionConfig


def print_banner():
    """Print production banner"""
    print("="*60)
    print("🏥 VM AUTOMATION - PRODUCTION MODE")
    print("="*60)
    print("Two-Agent Architecture for Healthcare GUI Automation:")
    print("  Agent 1: VM Navigator  → Connect, Verify Patient, Launch App") 
    print("  Agent 2: App Controller → Find Elements, Fill Forms, Submit")
    print("="*60)
    print("🛡️  PATIENT SAFETY: Automatic patient verification enabled")
    print("🔒 PHI PROTECTION: Patient data logging disabled by default")
    print("="*60)


def validate_environment():
    """Validate production environment"""
    issues = []
    
    # Check required models
    models_dir = Path(__file__).parent / "src" / "models"
    yolo_path = models_dir / "yolov8s.onnx"
    
    if not yolo_path.exists():
        issues.append(f"❌ YOLO model missing: {yolo_path}")
        issues.append("   Run: python src/setup_models.py")
    
    # Check configuration
    if not os.path.exists("vm_config.json") and not os.getenv("VM_HOST"):
        issues.append("❌ No configuration found")
        issues.append("   Either create vm_config.json or set environment variables")
        issues.append("   See vm_config.sample.json for example")
    
    if issues:
        print("\n🚨 ENVIRONMENT ISSUES:")
        for issue in issues:
            print(f"   {issue}")
        print()
        return False
    
    return True


async def run_production_automation(config_file: str = None, form_data_file: str = None):
    """Run production automation"""
    print_banner()
    
    if not validate_environment():
        return False
    
    try:
        # Load configuration
        if config_file and os.path.exists(config_file):
            config = ProductionConfig.from_file(config_file)
            print(f"✓ Loaded configuration from {config_file}")
        elif os.path.exists("vm_config.json"):
            config = ProductionConfig.from_file("vm_config.json")
            print("✓ Loaded configuration from vm_config.json")
        else:
            config = ProductionConfig.from_env()
            print("✓ Loaded configuration from environment variables")
        
        # Validate configuration
        errors = config.validate()
        if errors:
            print("\n🚨 CONFIGURATION ERRORS:")
            for error in errors:
                print(f"   ❌ {error}")
            return False
        
        # Initialize automation
        print(f"\n🚀 Initializing VM Automation...")
        automation = VMAutomationProduction(config)
        
        print(f"   Session ID: {automation.session_id}")
        print(f"   VM Target: {config.vm_host}:{config.vm_port}")
        print(f"   Application: {config.target_app_name}")
        print(f"   Patient Safety: {'✓ Enabled' if config.patient_name else '⚠️ Disabled'}")
        print(f"   PHI Logging: {'✓ Enabled' if config.log_phi else '🔒 Disabled'}")
        
        # Run automation workflow
        if form_data_file and os.path.exists(form_data_file):
            print(f"\n📋 Loading form data from {form_data_file}")
            import json
            with open(form_data_file, 'r') as f:
                form_data = json.load(f)
            
            print(f"   Form fields: {len(form_data)}")
            result = await automation.run_form_filling_workflow(form_data)
            
        else:
            print(f"\n🎯 Running single button click workflow...")
            print(f"   Target: {config.target_button_text}")
            result = await automation.run_full_automation()
        
        # Display results
        print("\n" + "="*60)
        print("📊 AUTOMATION RESULTS:")
        print("="*60)
        
        if result["success"]:
            print("✅ STATUS: SUCCESS")
            print(f"⏱️  Execution Time: {result['execution_time']:.2f} seconds")
            
            if result.get("patient_verified"):
                print("🛡️  Patient Verification: ✅ PASSED")
            elif config.patient_name:
                print("🛡️  Patient Verification: ⚠️ SKIPPED")
            else:
                print("🛡️  Patient Verification: ➖ NOT CONFIGURED")
            
            # Show completion details
            summary = result["session_summary"]
            print(f"📸 Screenshots Captured: {summary['screenshots_count']}")
            print(f"⚡ Actions Performed: {summary['actions_count']}")
            print(f"❌ Errors: {summary['errors_count']}")
            
            if "fields_filled" in result:
                print(f"📝 Form Fields Filled: {result['fields_filled']}")
            
        else:
            print("❌ STATUS: FAILED")
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
            
            if result.get("safety_critical"):
                print("🚨 CRITICAL SAFETY FAILURE")
                print("   Automation stopped to prevent patient safety incident")
            
            if 'phase_failed' in result:
                print(f"📍 Failed Phase: {result['phase_failed']}")
            
            if result.get("phase_failed") == "patient_safety_verification":
                print("\n🛡️  PATIENT SAFETY RECOMMENDATIONS:")
                print("   1. Verify correct patient is displayed on screen")
                print("   2. Check patient name, MRN, and DOB in configuration")
                print("   3. Ensure patient banner is visible in application")
        
        # Save detailed report
        report_path = automation.save_session_report()
        print(f"\n📋 Detailed Report: {report_path}")
        
        # Show recent actions (last 5)
        print(f"\n📝 Recent Actions:")
        recent_actions = automation.session.action_log[-5:]
        for i, action in enumerate(recent_actions, 1):
            print(f"   {i}. {action}")
        
        if automation.session.errors:
            print(f"\n⚠️  Errors Encountered:")
            for error in automation.session.errors[-3:]:  # Show last 3 errors
                print(f"   • {error}")
        
        return result["success"]
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Automation interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def create_sample_form_data():
    """Create sample form data file"""
    sample_data = [
        {"field_name": "First Name", "value": "John"},
        {"field_name": "Last Name", "value": "Doe"},
        {"field_name": "Date of Birth", "value": "01/01/1980"},
        {"field_name": "Medical Record Number", "value": "123456"},
        {"field_name": "Phone Number", "value": "555-1234"},
        {"field_name": "Email", "value": "john.doe@example.com"}
    ]
    
    with open("form_data.sample.json", "w") as f:
        import json
        json.dump(sample_data, f, indent=2)
    
    print("✓ Created form_data.sample.json")
    print("  Copy to form_data.json and customize for your use case")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="VM Automation - Production Mode")
    parser.add_argument("--config", "-c", help="Configuration file path", default=None)
    parser.add_argument("--form-data", "-f", help="Form data JSON file path", default=None)
    parser.add_argument("--create-samples", action="store_true", help="Create sample configuration files")
    parser.add_argument("--validate-env", action="store_true", help="Validate environment only")
    
    args = parser.parse_args()
    
    if args.create_samples:
        print("📁 Creating sample files...")
        
        if not os.path.exists("vm_config.sample.json"):
            print("⚠️  vm_config.sample.json already exists")
        else:
            print("✓ vm_config.sample.json available")
        
        create_sample_form_data()
        print("\n📖 Next steps:")
        print("1. Copy vm_config.sample.json to vm_config.json")
        print("2. Update vm_config.json with your VM details")
        print("3. Copy form_data.sample.json to form_data.json (if needed)")
        print("4. Run: python run_production.py")
        return True
    
    if args.validate_env:
        print("🔍 Validating environment...")
        return validate_environment()
    
    # Run automation
    success = asyncio.run(run_production_automation(args.config, args.form_data))
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
        sys.exit(130)