# Computer Use Agent with CUA

A production-ready computer use agent built with **CUA (Computer Use Agent)** framework, **uv** for packaging, and comprehensive **TDD** test coverage. This agent can control Windows VMs via HTTPS proxy or run locally on macOS for development.

## Quick Start

```bash
# 1) Install uv (see https://docs.astral.sh/uv/)
# 2) Create & sync env (installs deps & dev-deps)
uv sync --dev

# 3) Set your API keys
export OPENAI_API_KEY=sk-...
cp .env.example .env  # Edit with your settings

# 4) Run tests
uv run pytest -q

# 5) Lint / type-check
uv run ruff format .
uv run ruff check .
uv run pyright
```

## Local Development Setup (macOS)

For local development and testing on macOS using Lume VM:

```bash
# 1) Install Lume CLI (see https://docs.trycua.com/docs/libraries/lume/installation)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/lume/scripts/install.sh)"

# 2) Pull the macOS VM image
lume pull macos-sequoia-cua-sparse:15.4

# 3) Run the VM
lume run macos-sequoia-cua-sparse:15.4

# 4) Run demo with automatic VM creation
uv run -m src.tasks.demo_template_matching_safari
```

**Lume Documentation**: For detailed installation instructions and VM management, see [Lume Installation Guide](https://docs.trycua.com/docs/libraries/lume/installation)

**Important Network Requirements:**
- The VM runs on a local IP (e.g., `192.168.64.x`) with computer server on port 8000
- Your IDE/terminal must have **local networking enabled** to connect to the VM
- **Cursor IDE**: Enable "Allow local network connections" in settings
- **VS Code**: Ensure local network access isn't blocked by firewall
- **Terminal**: Should work by default, but check firewall settings if connection fails

The `src/backends/lume_vm.py` automatically creates and manages the VM instance using the `macos-sequoia-cua-sparse:15.4` image.

## Remote Windows VM Setup

For production deployments using remote Windows VMs:

### Windows VM Setup (Run on your Windows VM)

**Prerequisites:**
- Windows 10/11 or Windows Server 2019+
- Python 3.8+ installed and added to PATH
- Network connectivity to your host computer

**1. Download PowerShell Scripts:**
Copy the `scripts/` folder to your Windows VM with these files:
- `scripts/on_startup.ps1` - Installs and starts CUA computer-server
- `scripts/run_computer_server.ps1` - Simple server runner with configuration

**2. Install and Start Computer Server:**
```powershell
# Run as Administrator (recommended)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install and start the server
.\scripts\on_startup.ps1

# Or run server directly with custom settings
.\scripts\run_computer_server.ps1 -Host "0.0.0.0" -Port 8000 -LogLevel "info"
```

**3. Verify Server is Running:**
The computer-server will start on `http://0.0.0.0:8000` and display:
```
Starting computer-server on 0.0.0.0:8000...
Server will be accessible at: http://0.0.0.0:8000
Press Ctrl+C to stop the server
```

**4. Setup Auto-Start on Windows Boot (Recommended):**

To automatically start the computer-server when Windows boots:

**Using Task Scheduler**
```powershell
# Open Task Scheduler as Administrator
taskschd.msc

# Or create via command line:
$ScriptPath = "C:\path\to\your\scripts\on_startup.ps1"
$TaskName = "CUA-Computer-Server"

schtasks /create /tn "$TaskName" /tr "powershell.exe -ExecutionPolicy Bypass -File `"$ScriptPath`"" /sc onstart /ru SYSTEM /rl HIGHEST
```

**Verify Auto-Start:**
- Reboot your Windows VM
- Check that the computer-server starts automatically
- Verify it's accessible at `http://VM_IP:8000`

### Host Computer Setup

**1. Configure Environment Variables:**
```bash
# Set in your .env file
COMPUTER_MODE=remote
VM_PROXY_URL=http://YOUR_WINDOWS_VM_IP:8000
```

**2. Test Connection:**
```bash
# Run a simple test
uv run -m src.tasks.debug_remote_connection
```

### Architecture Overview

**Direct Connection Mode:**
```
Host Computer                    Windows VM
├── windows_computer.py    ────► ├── cua-computer-server (port 8000)
├── HTTP/HTTPS requests         ├── Windows automation (pyautogui, win32api)
└── .env configuration          └── Native Windows operations
```

**Security Options:**
- **HTTP**: Simple setup for internal networks
- **HTTPS**: Add SSL certificates to computer-server if needed

### Troubleshooting

**Windows VM Issues:**
- Ensure Python is in PATH: `python --version`
- Check firewall allows port 8000: `netstat -an | findstr :8000`
- Run PowerShell as Administrator if permission errors occur
- Verify computer-server installation: `pip list | findstr cua-computer-server`

**Connection Issues:**
- Test VM connectivity: `curl http://YOUR_VM_IP:8000/version`
- Check network routing between host and VM
- Verify VM_PROXY_URL in .env matches VM's actual IP
- Ensure no proxy or VPN interfering with connection

**Performance Tips:**
- Use dedicated network for VM communication
- Consider VM placement close to processing workloads
- Monitor VM resource usage during automation tasks

## Architecture

**Backends:**
- **Remote Mode**: Self-hosted Windows VM via HTTPS proxy with mTLS
- **Lume VM Mode**: Virtualized macOS via Lume (Apple Virtualization.framework) 

**Models:**
- **Default**: `omniparser+openai/gpt-4o` (OmniParser + GPT-4o)
- **Custom Vision**: Optional PaddleOCR/OpenCV integration
- **Configurable**: Support for Claude, local models

**Features:**
- Azure Service Bus queue consumer for task processing
- Advanced template matching with multi-scale and rotation support
- Comprehensive test coverage with TDD approach
- File-specific test structure matching source code
- Production-ready configuration and error handling

## What's Inside
- **CUA Framework**: Computer use agent with vision grounding
- **TDD Tests**: 100+ tests with comprehensive coverage for template matching
- **Advanced Vision**: Multi-scale template matching with rotation support
- **Dual Backends**: Remote Windows VM + local macOS support
- **Vision Integration**: OmniParser + custom template detection system
- **Queue Processing**: Azure Service Bus consumer
- **Modern Python**: uv + Ruff + Pyright + pytest

## Vision & Template Matching

The agent includes an advanced template matching system for UI element detection:

**Template Detection Features:**
- Multi-scale template matching (0.5x to 2.0x scaling)
- Rotation-invariant detection (-30° to +30°)
- Multiple template strategies: Base64, Library, Multi-template
- Non-Maximum Suppression (NMS) for overlapping detections
- Automatic method selection (TM_CCOEFF_NORMED, TM_SQDIFF_NORMED, etc.)
- Template caching for performance optimization

**Key Components:**
- `src/vision/template_detector.py` - Core detection algorithms
- `src/vision/template_manager.py` - Template resolution and caching
- `src/vision/finder.py` - High-level UI element finder
- `tests/vision/test_*` - Comprehensive test coverage (100+ tests)

**Usage Example:**
```python
from src.vision.finder import find_target_center

# Find UI element center coordinates
coords = find_target_center(screenshot_bytes, "safari")
if coords:
    x, y = coords
    # Click at coordinates
```

## Element Detection Debugging

Two scripts are provided to visualize detected UI elements with their coordinates:

**Simple visualization (recommended):**
```bash
# Analyze screenshot with default elements
python visualize_elements.py screenshot.png

# Search for specific elements
python visualize_elements.py screenshot.png google_news_sign_in_button safari
```

**Advanced debugging:**
```bash
# Use existing screenshot
python debug_element_finder.py screenshot.png

# Take new screenshot and analyze (if backend available)
python debug_element_finder.py
```

**Features:**
- Shows element coordinates as colored circles and labels
- Saves visualization as `elements_<filename>.png`
- Works with all template elements from `TEMPLATE_MAP`
- Useful for debugging template matching accuracy

See `AGENTS.md` for detailed agent architecture and development guide.
