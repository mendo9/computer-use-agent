# VM Automation - Production Ready GUI Automation System

🤖 **Two-Agent Architecture for Remote Windows VM GUI Automation** 

A production-ready AI system that automates GUI interactions in Windows VMs with computer vision, featuring patient safety verification for healthcare applications.

## 🎯 System Overview

**Two specialized AI agents working together:**
- **Agent 1 (VM Navigator)**: Connects to VMs, launches applications, verifies patient safety
- **Agent 2 (App Controller)**: Performs precise GUI interactions using shared computer vision components

**Key Technologies:**
- **YOLOv8s-ONNX**: Real-time UI element detection 
- **PaddleOCR**: Text recognition and verification
- **VNC Protocol**: Secure VM connections
- **Patient Safety**: Healthcare-grade identity verification

## 🚀 Quick Start

### 1. Setup
```bash
# Install dependencies
uv sync

# Download AI models
uv run src/setup_models.py
```

### 2. Basic Usage

**Simple VM automation:**
```bash
# Run with basic configuration
uv run src/main.py
```

**Production usage with configuration:**
```bash
# Create sample configuration
uv run vm-automation --create-samples

# Edit vm_config.json with your VM details
# Then run:
uv run vm-automation
```

### 3. Configuration Options

**Via JSON file (vm_config.json):**
```json
{
  "vm_host": "192.168.1.100",
  "vm_username": "user",
  "vm_password": "pass",
  "target_app_name": "MyApp.exe",
  "target_button_text": "Submit"
}
```

**Via Environment Variables:**
```bash
export VM_HOST="192.168.1.100"
export VM_USERNAME="user"
export VM_PASSWORD="pass"
export TARGET_APP="MyApp.exe"
export TARGET_BUTTON="Submit"
vm-automation
```

## 🔧 File Structure

```
├── src/
│   ├── main.py              # Main orchestrator (consolidated entry point)
│   ├── setup_models.py      # Download YOLO & PaddleOCR models
│   ├── agents/              # AI agent implementations
│   │   ├── vm_navigator.py  # Agent 1: VM connection & navigation
│   │   ├── app_controller.py # Agent 2: GUI interactions
│   │   └── shared_context.py # Shared data structures
│   ├── tools/               # Low-level automation tools
│   │   ├── screen_capture.py # VNC client wrapper
│   │   ├── input_actions.py  # Mouse/keyboard automation
│   │   └── verification.py   # Action verification
│   └── vision/              # Computer vision components
│       ├── ui_finder.py     # YOLO-based UI detection
│       ├── ocr_reader.py    # PaddleOCR wrapper
│       └── yolo_detector.py # YOLO model interface
├── tests/                   # Test suite
│   ├── mock_components.py   # Mock implementations for testing
│   ├── test_integration.py  # Integration tests
│   └── conftest.py         # Test configuration
├── Dockerfile              # Container deployment
└── vm_config.sample.json   # Sample configuration
```

## 🛡️ Healthcare Features (Optional)

For healthcare applications, the system includes patient safety verification:

**Configuration with patient safety:**
```json
{
  "vm_host": "192.168.1.100",
  "target_app_name": "EMRApp.exe",
  "target_button_text": "Submit",
  "patient_name": "John Doe",
  "patient_mrn": "123456",
  "patient_dob": "01/01/1980",
  "log_phi": false
}
```

**Safety Features:**
- Automatic patient identity verification using OCR
- Requires 2+ matching patient identifiers before proceeding
- Immediately stops if patient verification fails
- PHI-compliant logging (disabled by default)

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/

# Run integration tests
uv run pytest tests/test_integration.py -v

# Run production tests  
uv run pytest tests/test_production_integration.py -v
```

## 🔍 Troubleshooting

**Connection fails:**
- Verify VM IP and VNC port (default 5900)
- Check VNC server is running on target VM
- Test manual VNC connection first

**Element not found:**
- Check exact text matching (case-sensitive)
- Ensure application is fully loaded
- Try scrolling to make elements visible

**Models not loading:**
```bash
# Re-download AI models
uv run src/setup_models.py
```

## 📄 Available Commands

| Command | Purpose | Use Case |
|---------|---------|----------|
| `uv run src/main.py` | Direct script execution | Development & testing |
| `uv run vm-automation` | Production CLI | Production deployment |
| `uv run vm-automation --create-samples` | Generate config files | First-time setup |
| `uv run vm-automation --validate-env` | Environment check | Troubleshooting |

---

## ✅ Production Ready

This system is ready for real-world deployment with:
- **Computer Vision**: YOLO + OCR for precise GUI automation
- **Two-Agent Architecture**: Efficient component sharing
- **Healthcare Safety**: Optional patient verification
- **Production Features**: Configuration management, error handling, audit logging
- **Clean Architecture**: No mock code in production paths
