#!/usr/bin/env python3
"""
Desktop VM Demo - Uses the full VM infrastructure on local desktop.
Demonstrates the same code that works with VNC/RDP connections.
"""

import sys
from pathlib import Path

from ocr.vision.finder import UIElement, UIFinder
from vm.connections.desktop_connection import DesktopConnection


class DesktopVMDemo:
    """Demo using VM infrastructure on local desktop"""

    def __init__(self):
        self.connection = DesktopConnection()
        self.ui_finder = None
        self.models_dir = Path(__file__).parent.parent / "ocr" / "models"
        self.yolo_model_path = self.models_dir / "yolov8s.onnx"

    def setup_models(self) -> bool:
        """Ensure YOLO model is available"""
        if not self.yolo_model_path.exists():
            print("❌ YOLO model not found. Run: uv run python -m ocr.setup_models")
            print(f"   Expected path: {self.yolo_model_path}")
            return False

        print(f"✅ Using YOLO model: {self.yolo_model_path}")
        return True

    def initialize_components(self):
        """Initialize the VM infrastructure components"""
        print("🔧 Initializing VM infrastructure components...")

        # Use the advanced UI finder from VM infrastructure
        self.ui_finder = UIFinder(
            yolo_model_path=str(self.yolo_model_path), yolo_confidence=0.5, use_gpu=False
        )
        print("✅ VM infrastructure components initialized")

    def connect_to_desktop(self) -> bool:
        """Connect to desktop using VM connection interface"""
        print("🖥️  Connecting to desktop...")
        result = self.connection.connect()

        if result.success:
            print(f"✅ {result.message}")
            return True
        else:
            print(f"❌ {result.message}")
            return False

    def capture_and_analyze(self) -> tuple[bool, list[UIElement]]:
        """Capture desktop and analyze using VM infrastructure"""
        print("\n📸 Capturing desktop using VM connection...")

        # Use window capture if requested
        interactive = "--window" in sys.argv
        if interactive:
            success, frame = self.connection.capture_window(interactive=True)
        else:
            success, frame = self.connection.capture_screen()

        if not success or frame is None:
            print("❌ Failed to capture screen")
            return False, []

        print(f"✅ Captured frame: {frame.shape} pixels")

        # Analyze using advanced UI finder
        print("🔍 Analyzing UI using VM infrastructure...")
        print("  🎯 Running YOLO object detection...")
        print("  📝 Running PaddleOCR text recognition...")
        print("  🔗 Merging detections with spatial reasoning...")

        ui_elements = self.ui_finder.find_ui_elements(frame)

        print(f"📊 Found {len(ui_elements)} UI elements")
        return True, ui_elements

    def show_analysis_results(self, ui_elements: list[UIElement]):
        """Show detailed analysis results"""
        print("\n📋 VM Infrastructure Analysis Results:")

        # Separate by type
        yolo_elements = [e for e in ui_elements if e.yolo_detection is not None]
        text_elements = [e for e in ui_elements if e.text_detection is not None]
        combined_elements = [e for e in ui_elements if e.element_type == "combined"]

        if yolo_elements:
            print(f"\n🎯 YOLO Detections ({len(yolo_elements)}):")
            for i, elem in enumerate(
                sorted(yolo_elements, key=lambda e: e.confidence, reverse=True)[:5]
            ):
                det = elem.yolo_detection
                print(f"  {i + 1}. {det.class_name}: {elem.confidence:.2f} at {elem.bbox}")

        if text_elements:
            print(f"\n📝 OCR Text Regions ({len(text_elements)}):")
            for i, elem in enumerate(
                sorted(text_elements, key=lambda e: e.confidence, reverse=True)[:10]
            ):
                text = elem.text or ""
                print(f"  {i + 1}. '{text[:30]}': {elem.confidence:.2f} at {elem.bbox}")

        if combined_elements:
            print(f"\n🔗 Combined Elements ({len(combined_elements)}):")
            for i, elem in enumerate(combined_elements[:5]):
                print(f"  {i + 1}. {elem.description}: {elem.confidence:.2f} at {elem.bbox}")

    def find_clickable_elements(self, ui_elements: list[UIElement]) -> list[UIElement]:
        """Find potentially clickable UI elements"""
        clickable_terms = [
            "button",
            "submit",
            "click",
            "ok",
            "cancel",
            "close",
            "save",
            "open",
            "file",
            "edit",
            "view",
            "help",
            "menu",
            "new",
            "search",
            "login",
            "sign",
            "next",
            "back",
            "yes",
            "no",
            "apply",
            "reset",
            "clear",
        ]

        clickable_elements = []

        for elem in ui_elements:
            is_clickable = False

            # Check if YOLO detected a button-like object
            if elem.yolo_detection:
                yolo_class = elem.yolo_detection.class_name.lower()
                if any(term in yolo_class for term in ["button", "menu", "icon"]):
                    is_clickable = True

            # Check if text matches clickable terms
            if elem.text:
                text_lower = elem.text.lower().strip()
                if any(term in text_lower for term in clickable_terms):
                    is_clickable = True

                # Short text is often clickable (buttons, links)
                if len(text_lower) <= 20 and len(text_lower.split()) <= 3:
                    is_clickable = True

            if is_clickable:
                clickable_elements.append(elem)

        return clickable_elements

    def demonstrate_clicking(self, clickable_elements: list[UIElement]):
        """Demonstrate clicking using VM infrastructure"""
        if not clickable_elements:
            print("\n🤖 No clickable elements found")
            return

        print(f"\n🎯 Found {len(clickable_elements)} clickable elements:")

        for i, elem in enumerate(clickable_elements[:5]):
            text_desc = f"'{elem.text}'" if elem.text else "UI element"
            yolo_desc = f"({elem.yolo_detection.class_name})" if elem.yolo_detection else ""
            print(f"  {i + 1}. {text_desc} {yolo_desc} at {elem.center}")

        # Check if user wants real clicking
        do_real_clicks = "--click" in sys.argv

        if do_real_clicks:
            print("\n🎯 REAL INTERACTION MODE using VM infrastructure:")
            print("⚠️  WARNING: This will perform actual mouse clicks!")

            for i, elem in enumerate(clickable_elements[:2]):  # Only demo first 2
                x, y = elem.center
                text_desc = elem.text or "element"

                print(f"\n  🖱️  Clicking '{text_desc}' at ({x}, {y}) via VM connection...")

                # Use VM infrastructure for clicking
                result = self.connection.click(x, y, button="left")

                if result.success:
                    print(f"  ✅ {result.message}")
                else:
                    print(f"  ❌ {result.message}")

                if i < len(clickable_elements) - 1:
                    import time

                    time.sleep(1.5)  # Brief pause between clicks
        else:
            print("\n🤖 Demonstration Mode (use --click for real interaction):")
            print("  VM infrastructure can:")
            print("  • Use same connection abstraction as VNC/RDP")
            print("  • Leverage advanced YOLO + OCR spatial reasoning")
            print("  • Perform precise clicking via VM connection interface")
            print("  • Use the same code for desktop, VNC, and RDP")

            for i, elem in enumerate(clickable_elements[:3]):
                x, y = elem.center
                text_desc = elem.text or "element"
                print(f"\n  🎯 Would click '{text_desc}' at ({x}, {y})")
                print(f"     → VM method: connection.click({x}, {y}, 'left')")

    def run_demo(self):
        """Run the complete VM infrastructure demo"""
        print("🚀 Desktop VM Demo - Full Infrastructure")
        print("=" * 60)
        print("This demo uses the SAME code that works with VNC/RDP connections!")
        print()

        # Setup models
        if not self.setup_models():
            return False

        # Initialize VM infrastructure components
        self.initialize_components()

        # Connect using VM interface
        if not self.connect_to_desktop():
            return False

        # Capture and analyze using VM infrastructure
        success, ui_elements = self.capture_and_analyze()
        if not success:
            return False

        # Show detailed results
        self.show_analysis_results(ui_elements)

        # Find clickable elements
        clickable_elements = self.find_clickable_elements(ui_elements)

        # Demonstrate interaction
        self.demonstrate_clicking(clickable_elements)

        print("\n✅ VM Infrastructure Demo completed!")
        print("🚀 Key benefits demonstrated:")
        print("   • Same VMConnection interface works for desktop/VNC/RDP")
        print("   • Advanced YOLO + PaddleOCR integration")
        print("   • Spatial UI reasoning and element combining")
        print("   • Production-ready computer vision pipeline")
        print("   • Extensible to healthcare workflows and patient safety")

        # Disconnect
        result = self.connection.disconnect()
        print(f"🔚 {result.message}")

        return True


def main():
    """Main demo function"""
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: python desktop_vm_demo.py [options]")
        print()
        print("Options:")
        print("  --window    Capture specific window (interactive)")
        print("  --click     Perform actual mouse clicks (use carefully!)")
        print("  --help      Show this help message")
        print()
        print("This demo uses the full VM infrastructure on your desktop,")
        print("showing the same code that works with VNC/RDP connections.")
        return

    demo = DesktopVMDemo()
    success = demo.run_demo()

    if not success:
        print("\n❌ Demo failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
