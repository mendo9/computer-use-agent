#!/usr/bin/env python3
"""
Demo: Form Automation with OCR + Local Desktop Control

This demonstrates the complete integration:
1. OCR (ocr) - Finds form elements by text
2. Automation (automation) - Clicks and types on local desktop
3. VM (vm) - For remote desktop control (when needed)

The clean separation allows form entry to work both locally and remotely.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from automation import DesktopControl, FormFiller
from ocr import find_elements_by_text


def demo_low_level_automation():
    """Demo low-level desktop control"""
    print("\n🖱️  Low-Level Desktop Automation Demo")
    print("=" * 40)

    desktop = DesktopControl()

    print("1. Capturing desktop screenshot...")
    success, screenshot = desktop.capture_screen()
    if success:
        print(f"✅ Screenshot captured: {screenshot.shape}")
    else:
        print("❌ Failed to capture screenshot")
        return

    print("\n2. Testing desktop info...")
    info = desktop.get_desktop_info()
    print(f"✅ Platform: {info['platform']}")
    print(f"✅ Click capability: {info['click_capability']}")
    print(f"✅ Cliclick available: {info['cliclick_available']}")


def demo_ocr_element_finding():
    """Demo OCR-based element detection"""
    print("\n🔍 OCR Element Detection Demo")
    print("=" * 35)

    desktop = DesktopControl()

    print("1. Capturing current screen...")
    success, screenshot = desktop.capture_screen()
    if not success:
        print("❌ Could not capture screen")
        return

    print("2. Searching for common UI elements...")
    common_elements = [
        "File",
        "Edit",
        "View",
        "Window",
        "Help",  # Menu items
        "Desktop",
        "Finder",
        "Applications",  # macOS elements
        "Search",
        "Login",
        "Username",
        "Password",  # Common form elements
    ]

    found_elements = []

    for element_text in common_elements:
        try:
            elements = find_elements_by_text(
                screenshot, element_text, confidence_threshold=0.5, case_sensitive=False
            )

            if elements:
                best_match = max(elements, key=lambda x: x.confidence)
                found_elements.append(
                    {
                        "text": element_text,
                        "detected": best_match.text,
                        "center": best_match.center,
                        "confidence": best_match.confidence,
                    }
                )
        except Exception as e:
            print(f"   Error searching for '{element_text}': {e}")

    print(f"✅ Found {len(found_elements)} UI elements:")
    for elem in found_elements[:5]:  # Show first 5
        print(
            f"   - '{elem['detected']}' at {elem['center']} (confidence: {elem['confidence']:.2f})"
        )


def demo_high_level_form_filling():
    """Demo high-level form filling interface"""
    print("\n📝 High-Level Form Filling Demo")
    print("=" * 35)

    form_filler = FormFiller()

    print("1. Scanning for form fields on current screen...")
    detected_fields = form_filler.get_form_fields()

    if detected_fields:
        print(f"✅ Found {len(detected_fields)} potential form fields:")
        for field in detected_fields:
            print(
                f"   - '{field['text']}' at {field['center']} (confidence: {field['confidence']:.2f})"
            )
    else:
        print("ℹ️  No form fields detected on current screen")
        print("   (This is normal if no forms are visible)")

    print("\n2. Testing element search capabilities...")
    test_elements = ["Finder", "Desktop", "Applications"]

    for element in test_elements:
        field_info = form_filler.find_field_by_label(element, confidence_threshold=0.4)
        if field_info:
            print(f"✅ Found '{element}' at {field_info['center']}")
        else:
            print(f"   '{element}' not found")


def demo_vm_vs_automation_comparison():
    """Show the difference between VM control and local automation"""
    print("\n🖥️  VM vs Local Automation Comparison")
    print("=" * 42)

    print("LOCAL AUTOMATION (src/automation/):")
    print("  ├── Uses AppleScript & cliclick")
    print("  ├── Direct macOS desktop control")
    print("  ├── Perfect for local form filling")
    print("  └── Example: FormFiller, DesktopControl")

    print("\nREMOTE VM CONTROL (src/vm/):")
    print("  ├── Uses VNC/RDP protocols")
    print("  ├── Controls remote machines")
    print("  ├── Network-based automation")
    print("  └── Example: vm.click(), vnc_connection")

    print("\nFORM ENTRY WORKFLOW:")
    print("  1. 🔍 OCR finds field locations")
    print("  2. 🤖 Choose automation method:")
    print("     - Local: automation.click(x, y)")
    print("     - Remote: vm.click(x, y)")
    print("  3. ⌨️  Type text into fields")
    print("  4. ✅ Submit form")


def main():
    """Run complete automation demo"""
    print("🚀 Complete Form Automation Architecture Demo")
    print("📁 Clean Separation: OCR + Automation + VM")
    print("=" * 60)

    try:
        # Demo low-level automation
        demo_low_level_automation()

        # Demo OCR capabilities
        demo_ocr_element_finding()

        # Demo high-level form interface
        demo_high_level_form_filling()

        # Show architectural comparison
        demo_vm_vs_automation_comparison()

        print("\n🎉 Demo completed successfully!")

        print("\n📋 Clean Architecture Summary:")
        print("   ├── 🔍 src/ocr/          # Pure computer vision")
        print("   ├── 🖱️  src/automation/   # Local desktop control")
        print("   ├── 🖥️  src/vm/           # Remote desktop control")
        print("   └── 🤖 src/agent/mcp/    # MCP server interface")

        print("\n💡 Ready for both local and remote form automation!")

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
