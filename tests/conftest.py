"""Test configuration and fixtures for the automation test suite."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls for testing local automation."""
    mock = Mock()
    mock.run.return_value = Mock(returncode=0, stdout="", stderr="")
    return mock


@pytest.fixture
def mock_vnc_connection():
    """Mock VNC connection for testing."""
    mock = MagicMock()
    mock.connect.return_value = True
    mock.disconnect.return_value = True
    mock.is_connected = True
    return mock


@pytest.fixture
def mock_rdp_connection():
    """Mock RDP connection for testing."""
    mock = MagicMock()
    mock.connect.return_value = True
    mock.disconnect.return_value = True
    mock.is_connected = True
    return mock


@pytest.fixture
def mock_screenshot():
    """Mock screenshot data for testing."""
    import numpy as np
    from PIL import Image

    # Create a simple 100x100 RGB image
    img_array = np.zeros((100, 100, 3), dtype=np.uint8)
    img_array[:, :] = [255, 255, 255]  # White background
    return Image.fromarray(img_array)


@pytest.fixture
def mock_ocr_results():
    """Mock OCR results for testing."""
    return [
        {"text": "Username", "bbox": [10, 10, 100, 30], "confidence": 0.95},
        {"text": "Password", "bbox": [10, 50, 100, 70], "confidence": 0.92},
        {"text": "Login", "bbox": [10, 90, 60, 110], "confidence": 0.98},
    ]


@pytest.fixture
def mock_yolo_results():
    """Mock YOLO detection results for testing."""
    return [
        {"class": "textbox", "bbox": [10, 10, 200, 40], "confidence": 0.89},
        {"class": "button", "bbox": [10, 90, 80, 120], "confidence": 0.94},
    ]


@pytest.fixture
def sample_vm_config():
    """Sample VM configuration for testing."""
    return {
        "host": "192.168.1.100",
        "port": 5900,
        "password": "test_password",
        "connection_type": "vnc",
    }


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_automation"
    test_dir.mkdir()
    return test_dir
