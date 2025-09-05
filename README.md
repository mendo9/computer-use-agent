# VM Automation - Production Ready GUI Automation System

🤖 **Two-Agent Architecture for Remote Windows VM GUI Automation** 

A production-ready AI system that automates GUI interactions in Windows VMs with computer vision, featuring patient safety verification for healthcare applications.

## 🎯 System Overview

**Two specialized AI agents working together:**

- **Agent 1 (VM Navigator)**: Connects to VMs, launches applications, verifies patient safety
- **Agent 2 (App Controller)**: Performs precise GUI interactions using shared computer vision components

**Key Technologies:**

- **YOLOv8s-ONNX**: Real-time UI element detection with UI-focused class filtering
- **PaddleOCR**: Professional text recognition and verification with multi-language support
- **UIFinder**: Advanced computer vision system combining YOLO + OCR with spatial reasoning
- **ActionVerifier**: Automated verification of UI interactions and outcomes
- **AI Agent Tools**: Standardized function interface for any AI framework
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

## 🤖 AI Agent Computer Vision Tools

The system includes professional computer vision tools designed for AI agent automation. Any AI agent can use these tools with simple prompts - no complex setup required.

### 🔧 Core Vision Components

**YOLOv8s-ONNX Detector:**
- Real-time UI element detection
- UI-focused class filtering (removes irrelevant objects like animals, food)
- Optimized for screen/desktop environments
- CPU-optimized ONNX inference

**PaddleOCR Integration:**  
- Professional text recognition and extraction
- Multi-language support
- Region-aware text detection
- High-confidence text filtering

**UIFinder (Advanced Vision System):**
- Combines YOLO + OCR with spatial reasoning
- Intelligently merges nearby visual and text elements
- Identifies clickable elements and input fields
- Provides unified UI element representation

**ActionVerifier:**
- Automated verification of UI interactions
- Screenshot-based change detection
- Text input verification
- Element presence confirmation

### 🎯 AI Agent Function Tools

**Simple Function Interface:**

```python
from agent.vision_tools import *

# Analyze current screen
analysis = analyze_screen("What buttons and forms are visible?")

# Find specific elements  
button = find_element("Submit button")
field = find_element("Username input field")

# Perform actions
click_element(button)
type_text_in_field("john.doe", field)

# Verify outcomes
verify_action("Form should be submitted successfully")
```

**Available Functions:**
- `analyze_screen(prompt)` - Analyze screen contents with natural language
- `find_element(description)` - Find UI elements by description  
- `click_element(element)` - Click on elements or coordinates
- `type_text_in_field(text, field)` - Type text in input fields
- `verify_action(expected)` - Verify action outcomes
- `wait_for_element(description)` - Wait for elements to appear
- `scroll_screen(direction, pixels)` - Scroll screen content
- `take_screenshot(path)` - Capture screen images

### 🔌 AI Framework Integration

**OpenAI Functions:**

```python
from openai import OpenAI
from agent.function_definitions import get_vision_function_tools
from agent.vision_tools import *

client = OpenAI()
tools = get_vision_function_tools()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Click the Submit button"}],
    tools=tools,
    tool_choice="auto"
)
```

**Claude Tools:**

```python
import anthropic
from agent.function_definitions import get_vision_function_tools

client = anthropic.Anthropic()
tools = get_vision_function_tools()

response = client.messages.create(
    model="claude-3-opus-20240229",
    tools=tools,
    messages=[{"role": "user", "content": "Fill out this form"}]
)
```

**Other Frameworks:**
- Compatible with any AI framework that supports function calling
- JSON schema definitions provided for easy integration
- Standardized prompt-to-action interface

### 🎬 Usage Examples

**Form Automation:**
```python
# AI agent can automate forms with simple prompts
analysis = analyze_screen("Analyze this login form")
username_field = find_element("username field") 
type_text_in_field("user@example.com", username_field)

password_field = find_element("password field")
type_text_in_field("secure_pass", password_field)

submit_btn = find_element("login button")
click_element(submit_btn)

verify_action("Login should be successful")
```

**Web Navigation:**
```python
# Navigate websites with computer vision
search_box = find_element("search box")
type_text_in_field("computer vision AI", search_box)

search_btn = find_element("search button")
click_element(search_btn)

results = wait_for_element("search results", max_attempts=10)
verify_action("Search results should be displayed")
```

**Settings Management:**
```python
# Navigate application settings
settings = find_element("settings menu")
click_element(settings)

privacy_tab = find_element("privacy tab")
click_element(privacy_tab)

toggle = find_element("data collection toggle")
click_element(toggle)

verify_action("Privacy settings should be updated")
```

### ⚙️ Configuration Options

```python
from agent.vision_tools import configure_vision_tools

# High precision mode (healthcare, financial apps)
configure_vision_tools(
    confidence_threshold=0.8,
    use_ui_focused=True,
    ocr_language="en"
)

# General automation mode
configure_vision_tools(
    confidence_threshold=0.6,
    use_ui_focused=True, 
    ocr_language="en"
)

# Diverse content detection (full COCO classes)
configure_vision_tools(
    confidence_threshold=0.5,
    use_ui_focused=False,
    ocr_language="en"
)
```

### 📁 Vision System Structure

```
src/
├── ocr/                     # Computer vision components
│   ├── vision/              
│   │   ├── detector.py      # YOLOv8s-ONNX UI detection
│   │   ├── ocr.py          # PaddleOCR text recognition
│   │   └── finder.py       # UIFinder (YOLO + OCR fusion)
│   ├── verification/
│   │   └── verification.py # ActionVerifier for outcome validation
│   ├── models/             # Pre-trained models
│   │   ├── yolov8s.onnx   # YOLO model for inference
│   │   └── yolov8s.pt     # YOLO PyTorch model
│   └── setup_models.py    # Model download and setup
├── agent/                  # AI Agent Tools  
│   ├── vision_tools.py     # Main function interface
│   ├── function_definitions.py # JSON schemas for AI frameworks
│   └── examples.py         # Usage examples and demos
```

### 🧪 Testing Vision Tools

```bash
# Test vision components
uv run python -c "from agent.vision_tools import analyze_screen; print('✅ Vision tools ready')"

# Run examples (simulation mode)
uv run python src/agent/examples.py

# Setup models if not already downloaded
uv run python src/ocr/setup_models.py
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
- **Note**: Works best on Linux. For macOS, consider VNC for simpler setup.
- **Setup**: 

  **Linux:**
  ```bash
  sudo apt install freerdp2-x11 xvfb xdotool imagemagick scrot
  ```
  
  **macOS:**
  ```bash
  # Core RDP dependencies
  brew install freerdp imagemagick xorg-server xdotool
  
  # Optional: Install scrot for better screenshot performance (if available)
  brew install scrot || echo "scrot not available, will use xwd fallback"
  ```

The same computer vision and UI automation logic works seamlessly with both connection types.

## 🔧 File Structure

```
├── src/
│   ├── main.py              # Main orchestrator (consolidated entry point)
│   ├── ocr/                 # Computer vision and OCR components
│   │   ├── vision/          # Core vision system
│   │   │   ├── detector.py  # YOLOv8s-ONNX UI detection
│   │   │   ├── ocr.py      # PaddleOCR text recognition
│   │   │   └── finder.py   # UIFinder (YOLO + OCR fusion)
│   │   ├── verification/    # Action verification system
│   │   │   └── verification.py # ActionVerifier for outcome validation
│   │   ├── models/         # Pre-trained models
│   │   │   ├── yolov8s.onnx # YOLO ONNX model
│   │   │   └── yolov8s.pt  # YOLO PyTorch model
│   │   ├── adapters/       # Input/output adapters
│   │   ├── actions/        # Primitive actions
│   │   ├── runtime/        # Runtime context management
│   │   └── setup_models.py # Model download and setup
│   ├── agent/              # AI Agent Tools
│   │   ├── vision_tools.py # Function interface for AI agents
│   │   ├── function_definitions.py # JSON schemas for AI frameworks
│   │   └── examples.py     # Usage examples and demos
│   ├── vm/                 # VM connection management
│   │   ├── connections/    # Connection implementations
│   │   │   ├── base.py     # Abstract base classes
│   │   │   ├── vnc_connection.py # VNC implementation
│   │   │   ├── rdp_connection.py # RDP implementation
│   │   │   └── desktop_connection.py # Local desktop connection
│   │   └── agents/         # VM-specific agent implementations
│   │       ├── vm_navigator.py # Agent 1: VM connection & navigation
│   │       └── app_controller.py # Agent 2: GUI interactions
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

The system includes comprehensive tests for both unit and integration testing scenarios:

### 📋 Test Overview

| Test Type | Description | VM Required | 
|-----------|-------------|-------------|
| **Unit Tests (Mocks)** | Fast tests using mock components | ❌ No |
| **Integration Tests** | Full VM connection & workflow tests | ✅ Yes |
| **Patient Workflow Tests** | Healthcare application testing | ✅ Yes |

### 🚀 Quick Test Commands

```bash
# Run all unit tests (no VM required)
uv run pytest tests/test_clicking_unit_mocks.py -v

# Run existing integration tests
uv run pytest tests/test_integration.py -v

# Discover all available tests
uv run pytest tests/ --collect-only

# Run tests with specific markers
uv run pytest -m "not integration" tests/  # Skip integration tests
uv run pytest -m "mock" tests/             # Run only mock tests
```

### 🔧 Unit Tests (No VM Required)

These tests use mock components and can run immediately without any VM setup:

```bash
# Run all unit tests with mocks
uv run pytest tests/test_clicking_unit_mocks.py -v

# Run specific test categories
uv run pytest tests/test_clicking_unit_mocks.py::TestInputActionsMocking -v
uv run pytest tests/test_clicking_unit_mocks.py::TestUIFinderMocking -v
uv run pytest tests/test_clicking_unit_mocks.py::TestOCRMocking -v
uv run pytest tests/test_clicking_unit_mocks.py::TestPatientSafetyWithMocks -v
```

**Unit tests cover:**

- Click, type, scroll actions with mocks
- UI element finding and detection
- OCR text extraction simulation  
- Patient safety verification
- Error handling scenarios
- Agent workflow logic

### 🌐 Integration Tests (VM Required)

Integration tests require real VM connections and will be **skipped by default**. To enable them, you must configure VM connection details:

#### VNC Integration Tests

```bash
# Set VNC connection parameters
export TEST_VNC_HOST="192.168.1.100"
export TEST_VNC_PORT="5900" 
export TEST_VNC_PASSWORD="your_vnc_password"
export TEST_APP_NAME="Calculator.exe"
export TEST_BUTTON_TEXT="1"

# Remove skip markers and run VNC tests
uv run pytest tests/test_vm_integration.py::TestVNCIntegration -v --tb=short
```

#### RDP Integration Tests  

```bash
# Set RDP connection parameters
export TEST_RDP_HOST="192.168.1.101"
export TEST_RDP_PORT="3389"
export TEST_RDP_USERNAME="your_username" 
export TEST_RDP_PASSWORD="your_password"
export TEST_RDP_DOMAIN="COMPANY"  # Optional
export TEST_APP_NAME="Calculator.exe"
export TEST_BUTTON_TEXT="1"

# Remove skip markers and run RDP tests
uv run pytest tests/test_vm_integration.py::TestRDPIntegration -v --tb=short
```

**Integration tests cover:**

- Direct RDP/VNC connection establishment
- VM Navigator agent full workflow
- App Controller agent workflows  
- Complete end-to-end automation
- Connection error handling

### 🏥 Patient Workflow Tests (Healthcare VM Required)

For testing patient-specific application workflows using computer vision:

```bash
# Set patient application parameters
export PATIENT_TEST_VM_HOST="192.168.1.100"
export PATIENT_TEST_VM_PORT="5900"
export PATIENT_TEST_VM_PASSWORD="vnc_password"
export PATIENT_APP_NAME="EMR_System.exe"
export PATIENT_APP_TITLE="Electronic Medical Records"
export TEST_PATIENT_ID="PAT001234"
export TEST_PATIENT_NAME="John Smith"
export TEST_PATIENT_MRN="12345678"
export TEST_PATIENT_DOB="01/15/1975"
export SEARCH_FIELD_LABEL="Patient ID"
export SEARCH_BUTTON_TEXT="Search"

# Remove skip markers and run patient workflow tests
uv run pytest tests/test_patient_workflow_integration.py::TestPatientWorkflowIntegration -v
```

**Patient workflow tests cover:**

- PaddleOCR text extraction from patient applications
- YOLO-based UI element detection
- Patient search and verification workflows
- Computer vision tool integration
- Healthcare safety verification

### 📊 Test Configuration & Environment Variables

#### Required Environment Variables by Test Type:

**VNC Integration Tests:**

```bash
TEST_VNC_HOST=192.168.1.100        # VM IP address
TEST_VNC_PORT=5900                  # VNC port (default 5900) 
TEST_VNC_PASSWORD=vnc_password      # VNC password
```

**RDP Integration Tests:**

```bash
TEST_RDP_HOST=192.168.1.101         # VM IP address
TEST_RDP_PORT=3389                  # RDP port (default 3389)
TEST_RDP_USERNAME=your_username     # Windows username
TEST_RDP_PASSWORD=your_password     # Windows password  
TEST_RDP_DOMAIN=COMPANY             # Domain (optional)
```

**Patient Application Tests:**

```bash
PATIENT_TEST_VM_HOST=192.168.1.100  # Patient app VM IP
PATIENT_TEST_VM_PORT=5900           # Connection port
PATIENT_TEST_VM_PASSWORD=password   # Connection password
PATIENT_APP_NAME=EMR_System.exe     # Patient application name
TEST_PATIENT_ID=PAT001234           # Test patient ID
TEST_PATIENT_NAME=John_Smith        # Test patient name
TEST_PATIENT_MRN=12345678           # Test patient MRN
```

**Application Test Parameters:**

```bash
TEST_APP_NAME=Calculator.exe        # Target application to launch
TEST_BUTTON_TEXT=1                  # Target button to click
SEARCH_FIELD_LABEL=Patient_ID       # Input field label
SEARCH_BUTTON_TEXT=Search           # Search button text
```

### ⚠️ Important Testing Notes

1. **VM Setup Required**: Integration tests assume VMs are running and accessible
2. **Tests Will Fail**: Without proper VM configuration, integration tests will fail - this is expected
3. **Skip Markers**: Tests are marked with `@pytest.mark.skip` by default to prevent accidental VM connections
4. **Mock Tests First**: Always run unit tests with mocks first to verify system logic
5. **Environment Isolation**: Each test type uses different environment variable prefixes

### 🔍 Test Development & Debugging

```bash  
# Run tests with detailed output
uv run pytest tests/test_clicking_unit_mocks.py -v -s

# Run single test method  
uv run pytest tests/test_clicking_unit_mocks.py::TestInputActionsMocking::test_mock_click_success -v

# Run tests with coverage (if available)
uv run pytest tests/ --cov=src --cov-report=term-missing

# Debug test collection issues
uv run pytest tests/ --collect-only -v
```

### 🎯 Recommended Test Workflow

1. **Start with Unit Tests**: `uv run pytest tests/test_clicking_unit_mocks.py -v`
2. **Verify System Logic**: Ensure all mock-based tests pass
3. **Setup VM Environment**: Configure VM connection environment variables  
4. **Enable Integration Tests**: Remove `@pytest.mark.skip` decorators as needed
5. **Run Integration Tests**: Test real VM connections and workflows
6. **Validate Patient Workflows**: Test healthcare application scenarios

This testing approach ensures system reliability while providing flexibility for different deployment environments.

## 🔍 Troubleshooting

**Connection fails:**

*VNC Issues:*

- Verify VM IP and VNC port (default 5900)
- Check VNC server is running on target VM
- Test manual VNC connection first

*RDP Issues:*

- Verify VM IP and RDP port (default 3389)
- Check RDP is enabled on target VM
- Install dependencies:
  - **Linux**: `sudo apt install freerdp2-x11 xvfb xdotool imagemagick scrot`
  - **Mac**: `brew install freerdp imagemagick xorg-server xdotool xinit` (for isolated X11 display)
    - Note: Requires Xvfb from xorg-server for proper VM display isolation
    - May need additional setup if ImageMagick lacks XWD format support
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
