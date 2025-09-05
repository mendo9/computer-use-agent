"""
Integration demo showing how to use the OCR scaffolding with VNC/RDP backends.
This replaces the previous two-agent architecture with a unified approach.
"""

import os
from pathlib import Path

from ocr.actions.primitives import click_element
from ocr.actions.verify import page_changed
from ocr.adapters.input import Input
from ocr.adapters.screen import Screen
from ocr.runtime.context import Session
from ocr.runtime.runner import Step, StepRunner
from ocr.ui.model import merge_detections_and_text
from ocr.ui.selectors import by_text
from ocr.vision.detector import YOLODetector
from ocr.vision.ocr import OCRReader

from demo.backends import ConnectionAdapter, ControllerAdapter
from src.vm.connections.vnc_connection import VNCConnection
from src.vm.connections.rdp_connection import RDPConnection


def setup_models():
    """Ensure YOLO model is available"""
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    yolo_path = models_dir / "yolov8s.onnx"
    if not yolo_path.exists():
        print("YOLO model not found. Run setup_models.py first:")
        print(f"  uv run python -m src.vm.setup_models")
        return False
    
    print(f"Using YOLO model: {yolo_path}")
    return True


def create_vnc_session(host: str, port: int = 5900, password: str | None = None) -> Session:
    """Create a session using VNC backend"""
    # Create VNC connection using abstraction
    vnc_connection = VNCConnection()
    credentials = {"password": password} if password else {}
    conn_adapter = ConnectionAdapter(
        vm_connection=vnc_connection,
        host=host,
        port=port,
        credentials=credentials
    )
    controller_adapter = ControllerAdapter(vm_connection=vnc_connection)
    
    # Create screen and input adapters
    screen = Screen(conn_adapter)
    inp = Input(controller_adapter)
    
    # Create vision components
    det = YOLODetector()
    ocr = OCRReader()
    
    return Session(screen=screen, input=inp, detector=det, ocr=ocr)


def create_rdp_session(host: str, port: int = 3389, username: str | None = None, 
                      password: str | None = None, domain: str | None = None) -> Session:
    """Create a session using RDP backend"""
    # Create RDP connection using abstraction
    rdp_connection = RDPConnection()
    credentials = {
        "username": username,
        "password": password,
        "domain": domain,
        "width": 1920,
        "height": 1080
    }
    # Remove None values from credentials
    credentials = {k: v for k, v in credentials.items() if v is not None}
    
    conn_adapter = ConnectionAdapter(
        vm_connection=rdp_connection,
        host=host,
        port=port,
        credentials=credentials
    )
    controller_adapter = ControllerAdapter(vm_connection=rdp_connection)
    
    # Create screen and input adapters
    screen = Screen(conn_adapter)
    inp = Input(controller_adapter)
    
    # Create vision components
    det = YOLODetector()
    ocr = OCRReader()
    
    return Session(screen=screen, input=inp, detector=det, ocr=ocr)


def run_unified_demo(session: Session, connection_type: str):
    """Unified demo that tests all functionality regardless of connection type"""
    runner = StepRunner(session)
    
    def capture_and_analyze(sess: Session):
        """Capture screen and run OCR + object detection"""
        frame = sess.screen.capture()
        sess.record(f"Screen size: {frame.shape}")
        
        # Run YOLO detection
        detections = sess.detector.detect(frame)
        sess.record(f"Found {len(detections)} objects")
        
        # Run OCR
        text_boxes = sess.ocr.read(frame)
        sess.record(f"Found {len(text_boxes)} text regions")
        
        # Merge and analyze
        elements = merge_detections_and_text(detections, text_boxes)
        sess.record(f"Total UI elements: {len(elements)}")
        
        return elements
    
    def try_click_submit(sess: Session):
        """Attempt to find and click a Submit button if available"""
        frame_before = sess.screen.capture()
        dets = sess.detector.detect(frame_before)
        tbs = sess.ocr.read(frame_before)
        elements = merge_detections_and_text(dets, tbs)
        submit = by_text("Submit").match(elements)
        
        if not submit:
            sess.record("No Submit button found - this is expected in many cases")
            return
            
        sess.record(f"Found Submit button at {submit[0]}")
        try:
            click_element(sess.input, submit[0])
            frame_after = sess.screen.capture()
            if page_changed(sess.screen, frame_before, frame_after):
                sess.record("Click succeeded (page changed)")
            else:
                sess.record("Click completed (no visible change)")
        except Exception as e:
            sess.record(f"Click failed: {e}")
    
    # Execute comprehensive demo steps
    runner.execute(
        [
            Step(f"Connect via {connection_type.upper()}", lambda s: s.screen.connect()),
            Step("Analyze screen content", capture_and_analyze),
            Step("Test UI interaction", try_click_submit),
            Step(f"Disconnect from {connection_type.upper()}", lambda s: s.screen.disconnect()),
        ]
    )


def demo_vnc():
    """Demo VNC integration with unified functionality"""
    host = os.getenv("VNC_HOST", "localhost")
    port = int(os.getenv("VNC_PORT", "5900"))
    password = os.getenv("VNC_PASSWORD")
    
    print(f"Connecting to VNC at {host}:{port}")
    sess = create_vnc_session(host, port, password)
    run_unified_demo(sess, "vnc")


def demo_rdp():
    """Demo RDP integration with unified functionality"""
    host = os.getenv("RDP_HOST", "localhost")
    port = int(os.getenv("RDP_PORT", "3389"))
    username = os.getenv("RDP_USERNAME")
    password = os.getenv("RDP_PASSWORD")
    domain = os.getenv("RDP_DOMAIN")
    
    print(f"Connecting to RDP at {host}:{port}")
    sess = create_rdp_session(host, port, username, password, domain)
    run_unified_demo(sess, "rdp")


def main():
    """Main demo function"""
    print("Computer Use Agent - OCR Scaffolding Integration Demo")
    print("=" * 50)
    
    # Check models
    if not setup_models():
        print("Please setup models first before running the demo")
        return
    
    # Determine which demo to run based on environment
    demo_type = os.getenv("DEMO_TYPE", "vnc").lower()
    
    print(f"Running {demo_type.upper()} demo with comprehensive functionality testing...")
    print("This demo tests: screen capture, object detection, OCR, and UI interaction")
    print("-" * 50)
    
    if demo_type == "rdp":
        demo_rdp()
    else:
        demo_vnc()
    
    print("Demo completed successfully!")


if __name__ == "__main__":
    main()
