"""Unit tests for automation.remote.connections.vnc module."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from automation.core.types import ActionResult, ConnectionResult
from automation.remote.connections.vnc import VNCConnection


class TestVNCConnection:
    """Test cases for VNCConnection class."""

    def test_init(self):
        """Test VNCConnection initialization."""
        vnc = VNCConnection()

        assert vnc.vnc_client is None
        assert vnc.is_connected is False
        assert vnc.connection_info == {}

    @patch("automation.remote.connections.vnc.vnc.connect")
    def test_connect_success(self, mock_vnc_connect):
        """Test successful VNC connection."""
        vnc = VNCConnection()

        # Mock vncdotool client
        mock_client = Mock()
        mock_vnc_connect.return_value = mock_client

        result = vnc.connect("192.168.1.100", 5900, password="secret")

        assert isinstance(result, ConnectionResult)
        assert result.success is True
        assert "Connected to VNC server at 192.168.1.100:5900" in result.message
        assert vnc.is_connected is True
        assert vnc.vnc_client is mock_client
        assert vnc.connection_info["type"] == "vnc"
        assert vnc.connection_info["host"] == "192.168.1.100"
        assert vnc.connection_info["port"] == 5900
        assert vnc.connection_info["has_password"] is True

        mock_vnc_connect.assert_called_once_with("192.168.1.100", password="secret")

    @patch("automation.remote.connections.vnc.vnc.connect")
    def test_connect_default_port(self, mock_vnc_connect):
        """Test VNC connection with default port."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_vnc_connect.return_value = mock_client

        result = vnc.connect("test.host")

        assert result.success is True
        assert vnc.connection_info["port"] == 5900
        mock_vnc_connect.assert_called_once_with("test.host", password=None)

    @patch("automation.remote.connections.vnc.vnc.connect")
    def test_connect_custom_port(self, mock_vnc_connect):
        """Test VNC connection with custom port."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_vnc_connect.return_value = mock_client

        result = vnc.connect("test.host", 5901)

        assert result.success is True
        assert vnc.connection_info["port"] == 5901
        mock_vnc_connect.assert_called_once_with("test.host::5901", password=None)

    @patch("automation.remote.connections.vnc.vnc.connect")
    def test_connect_no_password(self, mock_vnc_connect):
        """Test VNC connection without password."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_vnc_connect.return_value = mock_client

        result = vnc.connect("test.host")

        assert result.success is True
        assert vnc.connection_info["has_password"] is False
        mock_vnc_connect.assert_called_once_with("test.host", password=None)

    @patch("automation.remote.connections.vnc.vnc.connect")
    def test_connect_failure(self, mock_vnc_connect):
        """Test VNC connection failure."""
        vnc = VNCConnection()

        mock_vnc_connect.side_effect = Exception("Connection refused")

        result = vnc.connect("invalid.host")

        assert isinstance(result, ConnectionResult)
        assert result.success is False
        assert "VNC connection failed: Connection refused" in result.message
        assert vnc.is_connected is False

    def test_disconnect_success(self):
        """Test successful VNC disconnection."""
        vnc = VNCConnection()

        # Set up connected state
        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True
        vnc.connection_info = {"type": "vnc", "host": "test"}

        result = vnc.disconnect()

        assert isinstance(result, ConnectionResult)
        assert result.success is True
        assert result.message == "VNC disconnected"
        assert vnc.is_connected is False
        assert vnc.vnc_client is None
        assert vnc.connection_info == {}
        mock_client.disconnect.assert_called_once()

    def test_disconnect_no_client(self):
        """Test disconnection when no client exists."""
        vnc = VNCConnection()

        result = vnc.disconnect()

        assert result.success is True
        assert result.message == "VNC disconnected"

    def test_disconnect_exception(self):
        """Test disconnection with exception."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_client.disconnect.side_effect = Exception("Disconnect error")
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.disconnect()

        assert result.success is False
        assert "VNC disconnect error: Disconnect error" in result.message

    @patch("automation.remote.connections.vnc.cv2.cvtColor")
    @patch("automation.remote.connections.vnc.np.array")
    def test_capture_screen_success(self, mock_np_array, mock_cvtColor):
        """Test successful screen capture."""
        vnc = VNCConnection()

        # Set up connected state
        mock_client = Mock()
        mock_pil_image = Mock()
        mock_client.screen = mock_pil_image
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        # Mock numpy array conversion
        mock_rgb_array = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_bgr_array = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_np_array.return_value = mock_rgb_array
        mock_cvtColor.return_value = mock_bgr_array

        success, image = vnc.capture_screen()

        assert success is True
        assert np.array_equal(image, mock_bgr_array)
        mock_np_array.assert_called_once_with(mock_pil_image)
        mock_cvtColor.assert_called_once_with(mock_rgb_array, cv2.COLOR_RGB2BGR)

    def test_capture_screen_not_connected(self):
        """Test screen capture when not connected."""
        vnc = VNCConnection()

        success, image = vnc.capture_screen()

        assert success is False
        assert image is None

    def test_capture_screen_no_client(self):
        """Test screen capture when no client exists."""
        vnc = VNCConnection()
        vnc.is_connected = True  # Connected but no client

        success, image = vnc.capture_screen()

        assert success is False
        assert image is None

    def test_capture_screen_no_image(self):
        """Test screen capture when client returns no image."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_client.screen = None
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        success, image = vnc.capture_screen()

        assert success is False
        assert image is None

    @patch("automation.remote.connections.vnc.cv2.cvtColor")
    @patch("automation.remote.connections.vnc.np.array")
    def test_capture_screen_exception(self, mock_np_array, mock_cvtColor):
        """Test screen capture with exception."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_client.screen = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        mock_np_array.side_effect = Exception("Conversion error")

        success, image = vnc.capture_screen()

        assert success is False
        assert image is None

    @patch("automation.remote.connections.vnc.time.sleep")
    def test_click_left_success(self, mock_sleep):
        """Test successful left click."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.click(100, 200, "left")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Clicked left at (100, 200)" in result.message

        mock_client.mousemove.assert_called_once_with(100, 200)
        mock_client.mousedown.assert_called_once_with(1)
        mock_client.mouseup.assert_called_once_with(1)
        mock_sleep.assert_called_once_with(0.05)

    @patch("automation.remote.connections.vnc.time.sleep")
    def test_click_right_success(self, mock_sleep):
        """Test successful right click."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.click(50, 75, "right")

        assert result.success is True
        assert "Clicked right at (50, 75)" in result.message

        mock_client.mousemove.assert_called_once_with(50, 75)
        mock_client.mousedown.assert_called_once_with(3)
        mock_client.mouseup.assert_called_once_with(3)

    @patch("automation.remote.connections.vnc.time.sleep")
    def test_click_middle_success(self, mock_sleep):
        """Test successful middle click."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.click(25, 30, "middle")

        assert result.success is True
        assert "Clicked middle at (25, 30)" in result.message

        mock_client.mousemove.assert_called_once_with(25, 30)
        mock_client.mousedown.assert_called_once_with(2)
        mock_client.mouseup.assert_called_once_with(2)

    def test_click_unknown_button(self):
        """Test click with unknown button."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.click(10, 20, "unknown")

        assert result.success is False
        assert "Unknown button: unknown" in result.message

    def test_click_not_connected(self):
        """Test click when not connected."""
        vnc = VNCConnection()

        result = vnc.click(100, 200)

        assert result.success is False
        assert result.message == "No VNC connection"

    def test_click_exception(self):
        """Test click with exception."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_client.mousemove.side_effect = Exception("Mouse error")
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.click(100, 200)

        assert result.success is False
        assert "VNC click error: Mouse error" in result.message

    @patch("automation.remote.connections.vnc.time.sleep")
    def test_type_text_success(self, mock_sleep):
        """Test successful text typing."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.type_text("Hello")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Typed: Hello" in result.message

        # Should call keypress for each character
        assert mock_client.keypress.call_count == 5
        mock_client.keypress.assert_any_call("H")
        mock_client.keypress.assert_any_call("e")
        mock_client.keypress.assert_any_call("l")
        mock_client.keypress.assert_any_call("l")
        mock_client.keypress.assert_any_call("o")

        # Should sleep between keystrokes
        assert mock_sleep.call_count == 5

    def test_type_text_not_connected(self):
        """Test text typing when not connected."""
        vnc = VNCConnection()

        result = vnc.type_text("Hello")

        assert result.success is False
        assert result.message == "No VNC connection"

    def test_type_text_exception(self):
        """Test text typing with exception."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_client.keypress.side_effect = Exception("Keypress error")
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.type_text("H")

        assert result.success is False
        assert "VNC type error: Keypress error" in result.message

    def test_key_press_success(self):
        """Test successful key press."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.key_press("enter")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Pressed key: enter" in result.message
        mock_client.keypress.assert_called_once_with("Return")

    def test_key_press_unmapped_key(self):
        """Test key press with unmapped key."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.key_press("F1")

        assert result.success is True
        mock_client.keypress.assert_called_once_with("F1")  # Should pass through unchanged

    def test_key_press_mapping(self):
        """Test key press mapping for common keys."""
        vnc = VNCConnection()

        mock_client = Mock()
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        test_cases = [
            ("enter", "Return"),
            ("escape", "Escape"),
            ("tab", "Tab"),
            ("space", "space"),
            ("backspace", "BackSpace"),
            ("delete", "Delete"),
            ("ctrl", "Control_L"),
            ("alt", "Alt_L"),
            ("shift", "Shift_L"),
            ("up", "Up"),
            ("down", "Down"),
            ("left", "Left"),
            ("right", "Right"),
        ]

        for input_key, expected_vnc_key in test_cases:
            mock_client.reset_mock()
            result = vnc.key_press(input_key)
            assert result.success is True
            mock_client.keypress.assert_called_once_with(expected_vnc_key)

    def test_key_press_not_connected(self):
        """Test key press when not connected."""
        vnc = VNCConnection()

        result = vnc.key_press("enter")

        assert result.success is False
        assert result.message == "No VNC connection"

    def test_key_press_exception(self):
        """Test key press with exception."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_client.keypress.side_effect = Exception("Key error")
        vnc.vnc_client = mock_client
        vnc.is_connected = True

        result = vnc.key_press("enter")

        assert result.success is False
        assert "VNC key press error: Key error" in result.message


class TestVNCConnectionIntegration:
    """Integration-style tests for VNCConnection."""

    @patch("automation.remote.connections.vnc.vnc.connect")
    def test_full_connection_workflow(self, mock_vnc_connect):
        """Test complete connection workflow."""
        vnc = VNCConnection()

        # Mock vncdotool client
        mock_client = Mock()
        mock_client.screen = Mock()
        mock_vnc_connect.return_value = mock_client

        # Connect
        connect_result = vnc.connect("test.host", 5900, password="secret")
        assert connect_result.success is True
        assert vnc.is_connected is True

        # Use connection
        click_result = vnc.click(100, 100)
        assert click_result.success is True

        type_result = vnc.type_text("test")
        assert type_result.success is True

        key_result = vnc.key_press("enter")
        assert key_result.success is True

        # Disconnect
        disconnect_result = vnc.disconnect()
        assert disconnect_result.success is True
        assert vnc.is_connected is False

    def test_operations_without_connection(self):
        """Test that operations fail gracefully without connection."""
        vnc = VNCConnection()

        # All operations should fail when not connected
        assert vnc.capture_screen()[0] is False
        assert vnc.click(100, 100).success is False
        assert vnc.type_text("test").success is False
        assert vnc.key_press("enter").success is False

        # Connection info should be empty
        assert vnc.get_connection_info() == {}

    @patch("automation.remote.connections.vnc.vnc.connect")
    def test_connection_info_accuracy(self, mock_vnc_connect):
        """Test that connection info is accurate."""
        vnc = VNCConnection()

        mock_client = Mock()
        mock_vnc_connect.return_value = mock_client

        # Test with password
        vnc.connect("192.168.1.100", 5901, password="secret123")

        info = vnc.get_connection_info()
        assert info["type"] == "vnc"
        assert info["host"] == "192.168.1.100"
        assert info["port"] == 5901
        assert info["has_password"] is True

        # Test without password
        vnc.disconnect()
        vnc.connect("test.host")

        info = vnc.get_connection_info()
        assert info["host"] == "test.host"
        assert info["port"] == 5900  # Default port
        assert info["has_password"] is False
