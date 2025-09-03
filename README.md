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
- **VNC/RDP Protocol**: Flexible VM connection options
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

# Or specify connection type:
uv run vm-automation --connection rdp
uv run vm-automation --connection vnc
```

### 3. Configuration Options

**Via JSON file (vm_config.json):**

*VNC Configuration:*
```json
{
  "vm_host": "192.168.1.100",
  "vm_port": 5900,
  "vm_password": "vnc_password",
  "connection_type": "vnc",
  "target_app_name": "Greenway Dev",
  "target_button_text": "Submit"
}
```

*RDP Configuration:*
```json
{
  "vm_host": "192.168.1.100", 
  "vm_port": 3389,
  "vm_username": "user",
  "vm_password": "password",
  "connection_type": "rdp",
  "rdp_domain": "COMPANY",
  "rdp_width": 1920,
  "rdp_height": 1080,
  "target_app_name": "Greenway Dev",
  "target_button_text": "Submit"
}
```

**Via Environment Variables:**
```bash
# VNC Connection
export CONNECTION_TYPE="vnc"
export VM_HOST="192.168.1.100"
export VM_PORT="5900"
export VM_PASSWORD="vnc_password"
export TARGET_APP="Greenway Dev"
export TARGET_BUTTON="Submit"
vm-automation

# RDP Connection  
export CONNECTION_TYPE="rdp"
export VM_HOST="192.168.1.100"
export VM_PORT="3389"
export VM_USERNAME="user"
export VM_PASSWORD="password"
export RDP_DOMAIN="COMPANY"
export RDP_WIDTH="1920"
export RDP_HEIGHT="1080"
export TARGET_APP="Greenway Dev"
export TARGET_BUTTON="Submit"
vm-automation
```

## 🔗 Connection Types

The system supports both VNC and RDP connections through a flexible abstraction layer:

### VNC Connection
- **Use case**: Any VM with VNC server installed
- **Requirements**: VNC server running on target VM (port 5900)
- **Advantages**: Lightweight, cross-platform
- **Setup**: Install VNC server on VM (TightVNC, RealVNC, UltraVNC)

### RDP Connection  
- **Use case**: Windows VMs with Remote Desktop enabled
- **Requirements**: FreeRDP, Xvfb, xdotool, ImageMagick on automation host
- **Advantages**: Native Windows protocol, no additional VM setup needed
- **Setup**: 
  ```bash
  sudo apt install freerdp2-x11 xvfb xdotool imagemagick
  ```

The same computer vision and UI automation logic works seamlessly with both connection types.

## 🔧 File Structure

```
├── src/
│   ├── main.py              # Main orchestrator (consolidated entry point)
│   ├── setup_models.py      # Download YOLO & PaddleOCR models
│   ├── agents/              # AI agent implementations
│   │   ├── vm_navigator.py  # Agent 1: VM connection & navigation
│   │   ├── app_controller.py # Agent 2: GUI interactions
│   │   └── shared_context.py # Shared data structures
│   ├── connections/         # Connection abstraction layer
│   │   ├── base.py          # Abstract base classes
│   │   ├── vnc_connection.py # VNC implementation
│   │   └── rdp_connection.py # RDP implementation
│   ├── tools/               # Low-level automation tools
│   │   ├── screen_capture.py # Connection-agnostic screen capture
│   │   ├── input_actions.py  # Connection-agnostic input actions
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
  "connection_type": "rdp",
  "vm_username": "user",
  "vm_password": "password",
  "target_app_name": "EMR System",
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

*VNC Issues:*
- Verify VM IP and VNC port (default 5900)
- Check VNC server is running on target VM
- Test manual VNC connection first

*RDP Issues:*
- Verify VM IP and RDP port (default 3389)
- Check RDP is enabled on target VM
- Install dependencies: `sudo apt install freerdp2-x11 xvfb xdotool imagemagick`
- Test manual RDP connection: `xfreerdp /v:VM_IP /u:username`

**Element not found:**
- Check exact text matching (case-sensitive)
- Ensure application is fully loaded
- Try scrolling to make elements visible

**Models not loading:**
```bash
# Re-download AI models
uv run src/setup_models.py
```

## 🐳 Docker Support

The system includes Docker support with connection-specific optimized containers:

### **Container Options:**
- **`vm-automation:vnc`** - Lightweight VNC-only container
- **`vm-automation:rdp`** - RDP-optimized with all dependencies
- **`vm-automation:latest`** - General-purpose (supports both)

### **Quick Run:**
```bash
# Run containers directly
docker run --rm -it vm-automation:vnc
docker run --rm -it vm-automation:rdp
```

### **Docker Compose Usage:**

**VNC Connection:**
```bash
# Set environment variables
export VM_HOST=192.168.1.100
export VM_PASSWORD=vnc_password
export TARGET_APP="Greenway Dev"

# Run VNC-optimized container
docker compose --profile vnc up
```

**RDP Connection:**
```bash
# Set environment variables  
export VM_HOST=192.168.1.100
export VM_USERNAME=your_username
export VM_PASSWORD=your_password
export RDP_DOMAIN=COMPANY
export TARGET_APP="Greenway Dev"

# Run RDP-optimized container
docker compose --profile rdp up
```

**General-purpose container:**
```bash
# Supports both connection types via environment
export CONNECTION_TYPE=rdp  # or vnc
docker compose --profile general up
```

### **Production Docker Usage:**
```bash
# With config file mount
docker run --rm -it \
  -v ./vm_config.json:/app/vm_config.json:ro \
  -v ./logs:/app/logs \
  -v ./screenshots:/app/screenshots \
  vm-automation:rdp

# With environment variables
docker run --rm -it \
  -e VM_HOST=192.168.1.100 \
  -e VM_USERNAME=user \
  -e VM_PASSWORD=pass \
  -e CONNECTION_TYPE=rdp \
  -e TARGET_APP="Greenway Dev" \
  vm-automation:rdp
```

## 📄 Available Commands

| Command | Purpose | Use Case |
|---------|---------|----------|
| `uv run src/main.py` | Direct script execution | Development & testing |
| `uv run vm-automation` | Production CLI | Production deployment |
| `uv run vm-automation --connection rdp` | Use RDP connection | Windows VMs with RDP |
| `uv run vm-automation --connection vnc` | Use VNC connection | Any VM with VNC server |
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
