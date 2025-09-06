"""Unit tests for automation.remote.connections.rdp module."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

from automation.core.types import ActionResult, ConnectionResult
from automation.remote.connections.rdp import RDPConnection


class TestRDPConnection:
    """Test cases for RDPConnection class."""

    def test_init(self):
        """Test RDPConnection initialization."""
        rdp = RDPConnection()

        assert rdp.rdp_process is None
        assert rdp.xvfb_process is None
        assert rdp.display is None
        assert rdp.temp_dir is None
        assert rdp.screenshot_path is None
        assert rdp.is_connected is False
        assert rdp.connection_info == {}

    @patch("automation.remote.connections.rdp.shutil.which")
    def test_connect_no_freerdp(self, mock_which):
        """Test connection when FreeRDP is not available."""
        rdp = RDPConnection()

        mock_which.return_value = None

        result = rdp.connect("test.host")

        assert isinstance(result, ConnectionResult)
        assert result.success is False
        assert "FreeRDP (xfreerdp) not found" in result.message

    @patch("automation.remote.connections.rdp.tempfile.mkdtemp")
    @patch("automation.remote.connections.rdp.subprocess.Popen")
    @patch("automation.remote.connections.rdp.shutil.which")
    @patch("automation.remote.connections.rdp.os.path.exists")
    @patch("automation.remote.connections.rdp.os.makedirs")
    @patch("automation.remote.connections.rdp.time.sleep")
    def test_connect_success_with_xvfb(
        self, mock_sleep, mock_makedirs, mock_exists, mock_which, mock_popen, mock_mkdtemp
    ):
        """Test successful RDP connection with Xvfb."""
        rdp = RDPConnection()

        # Mock dependencies are available
        mock_which.side_effect = lambda cmd: {
            "xfreerdp": "/usr/bin/xfreerdp",
            "Xvfb": "/usr/bin/Xvfb",
        }.get(cmd)

        # Mock X11 directory exists
        mock_exists.return_value = True

        # Mock temporary directory
        mock_mkdtemp.return_value = "/tmp/rdp_test"

        # Mock processes
        mock_xvfb_process = Mock()
        mock_xvfb_process.poll.return_value = None  # Still running
        mock_rdp_process = Mock()
        mock_rdp_process.poll.return_value = None  # Still running

        mock_popen.side_effect = [mock_xvfb_process, mock_rdp_process]

        # Mock _find_free_display
        with patch.object(rdp, "_find_free_display", return_value=10):
            result = rdp.connect("test.host", 3389, "user", "pass", domain="DOMAIN")

        assert isinstance(result, ConnectionResult)
        assert result.success is True
        assert "Connected to RDP server at test.host:3389" in result.message
        assert rdp.is_connected is True
        assert rdp.display == ":10"
        assert rdp.temp_dir == "/tmp/rdp_test"
        assert rdp.screenshot_path == "/tmp/rdp_test/screenshot.png"

        # Verify connection info
        assert rdp.connection_info["type"] == "rdp"
        assert rdp.connection_info["host"] == "test.host"
        assert rdp.connection_info["port"] == 3389
        assert rdp.connection_info["username"] == "user"
        assert rdp.connection_info["domain"] == "DOMAIN"
        assert rdp.connection_info["display"] == ":10"
        assert rdp.connection_info["resolution"] == "1920x1080"

    @patch("automation.remote.connections.rdp.shutil.which")
    def test_connect_no_xvfb_macos(self, mock_which):
        """Test connection failure on macOS without Xvfb."""
        rdp = RDPConnection()

        # FreeRDP available but no Xvfb
        mock_which.side_effect = lambda cmd: {"xfreerdp": "/usr/bin/xfreerdp", "Xvfb": None}.get(
            cmd
        )

        result = rdp.connect("test.host")

        assert result.success is False
        assert "RDP on macOS requires isolated X11 display" in result.message
        assert "brew install freerdp imagemagick xorg-server xdotool" in result.message

    @patch("automation.remote.connections.rdp.subprocess.Popen")
    @patch("automation.remote.connections.rdp.shutil.which")
    @patch("automation.remote.connections.rdp.os.path.exists")
    @patch("automation.remote.connections.rdp.time.sleep")
    def test_connect_xvfb_fails(self, mock_sleep, mock_exists, mock_which, mock_popen):
        """Test connection when Xvfb process fails."""
        rdp = RDPConnection()

        mock_which.side_effect = lambda cmd: {
            "xfreerdp": "/usr/bin/xfreerdp",
            "Xvfb": "/usr/bin/Xvfb",
        }.get(cmd)

        mock_exists.return_value = True

        # Mock Xvfb process that dies immediately
        mock_xvfb_process = Mock()
        mock_xvfb_process.poll.return_value = 1  # Process died
        mock_popen.return_value = mock_xvfb_process

        with patch.object(rdp, "_find_free_display", return_value=10):
            result = rdp.connect("test.host")

        assert result.success is False
        assert "Xvfb process died immediately after start" in result.message

    @patch("automation.remote.connections.rdp.tempfile.mkdtemp")
    @patch("automation.remote.connections.rdp.subprocess.Popen")
    @patch("automation.remote.connections.rdp.shutil.which")
    @patch("automation.remote.connections.rdp.os.path.exists")
    @patch("automation.remote.connections.rdp.time.sleep")
    def test_connect_freerdp_fails(
        self, mock_sleep, mock_exists, mock_which, mock_popen, mock_mkdtemp
    ):
        """Test connection when FreeRDP process fails."""
        rdp = RDPConnection()

        mock_which.side_effect = lambda cmd: {
            "xfreerdp": "/usr/bin/xfreerdp",
            "Xvfb": "/usr/bin/Xvfb",
        }.get(cmd)

        mock_exists.return_value = True
        mock_mkdtemp.return_value = "/tmp/rdp_test"

        # Mock Xvfb succeeds, FreeRDP fails
        mock_xvfb_process = Mock()
        mock_xvfb_process.poll.return_value = None

        mock_rdp_process = Mock()
        mock_rdp_process.poll.return_value = 1  # Process died
        mock_rdp_process.communicate.return_value = (b"", b"Authentication failed")

        mock_popen.side_effect = [mock_xvfb_process, mock_rdp_process]

        with patch.object(rdp, "_find_free_display", return_value=10):
            result = rdp.connect("test.host")

        assert result.success is False
        assert "FreeRDP failed: Authentication failed" in result.message

    @patch("automation.remote.connections.rdp.shutil.rmtree")
    @patch("automation.remote.connections.rdp.os.path.exists")
    @patch("automation.remote.connections.rdp.os.unlink")
    @patch("automation.remote.connections.rdp.subprocess.run")
    def test_disconnect_success(self, mock_subprocess_run, mock_unlink, mock_exists, mock_rmtree):
        """Test successful disconnection."""
        rdp = RDPConnection()

        # Set up connected state
        mock_rdp_process = Mock()
        mock_xvfb_process = Mock()
        rdp.rdp_process = mock_rdp_process
        rdp.xvfb_process = mock_xvfb_process
        rdp.display = ":10"
        rdp.temp_dir = "/tmp/rdp_test"
        rdp.is_connected = True
        rdp.connection_info = {"test": "data"}

        # Mock file operations
        mock_exists.return_value = True

        result = rdp.disconnect()

        assert isinstance(result, ConnectionResult)
        assert result.success is True
        assert result.message == "RDP disconnected"
        assert rdp.is_connected is False
        assert rdp.connection_info == {}
        assert rdp.rdp_process is None
        assert rdp.xvfb_process is None
        assert rdp.display is None
        assert rdp.temp_dir is None

        # Verify cleanup calls
        mock_rdp_process.terminate.assert_called_once()
        mock_xvfb_process.terminate.assert_called_once()
        mock_unlink.assert_called_once_with("/tmp/.X10-lock")
        mock_rmtree.assert_called_once_with("/tmp/rdp_test")

    def test_disconnect_no_processes(self):
        """Test disconnection when no processes exist."""
        rdp = RDPConnection()

        result = rdp.disconnect()

        assert result.success is True
        assert result.message == "RDP disconnected"

    def test_disconnect_exception(self):
        """Test disconnection with exception."""
        rdp = RDPConnection()

        mock_rdp_process = Mock()
        mock_rdp_process.terminate.side_effect = Exception("Terminate failed")
        rdp.rdp_process = mock_rdp_process

        result = rdp.disconnect()

        assert result.success is False
        assert "RDP disconnect error: Terminate failed" in result.message

    @patch("automation.remote.connections.rdp.cv2.imread")
    @patch("automation.remote.connections.rdp.os.path.exists")
    @patch("automation.remote.connections.rdp.os.unlink")
    @patch("automation.remote.connections.rdp.subprocess.run")
    @patch("automation.remote.connections.rdp.shutil.which")
    def test_capture_screen_scrot_success(
        self, mock_which, mock_subprocess, mock_unlink, mock_exists, mock_imread
    ):
        """Test successful screen capture using scrot."""
        rdp = RDPConnection()

        # Set up connected state
        rdp.is_connected = True
        rdp.display = ":10"
        rdp.screenshot_path = "/tmp/test_screenshot.png"

        # Mock scrot available and working
        mock_which.return_value = "/usr/bin/scrot"
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Mock image loading
        mock_exists.return_value = True
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image

        success, image = rdp.capture_screen()

        assert success is True
        assert np.array_equal(image, mock_image)
        # Verify subprocess was called with scrot command and DISPLAY env var
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0] == (["scrot", rdp.screenshot_path],)
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["env"]["DISPLAY"] == ":10"
        mock_imread.assert_called_once_with(rdp.screenshot_path)
        mock_unlink.assert_called_once_with(rdp.screenshot_path)

    def test_capture_screen_not_connected(self):
        """Test screen capture when not connected."""
        rdp = RDPConnection()

        success, image = rdp.capture_screen()

        assert success is False
        assert image is None

    def test_capture_screen_no_display(self):
        """Test screen capture when no display is set."""
        rdp = RDPConnection()
        rdp.is_connected = True  # Connected but no display

        success, image = rdp.capture_screen()

        assert success is False
        assert image is None

    @patch("automation.remote.connections.rdp.subprocess.run")
    def test_click_success(self, mock_subprocess):
        """Test successful click."""
        rdp = RDPConnection()

        # Set up connected state
        rdp.is_connected = True
        rdp.display = ":10"

        # Mock successful subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = rdp.click(100, 200, "left")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Clicked left at (100, 200)" in result.message

        expected_cmd = ["xdotool", "mousemove", "100", "200", "click", "1"]
        # Verify subprocess was called with xdotool command and DISPLAY env var
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0] == (expected_cmd,)
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["env"]["DISPLAY"] == ":10"

    def test_click_button_mapping(self):
        """Test click button mapping."""
        rdp = RDPConnection()
        rdp.is_connected = True
        rdp.display = ":10"

        test_cases = [
            ("left", "1"),
            ("middle", "2"),
            ("right", "3"),
            ("unknown", "1"),  # Should default to left
        ]

        with patch("automation.remote.connections.rdp.subprocess.run") as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            for button, expected_num in test_cases:
                result = rdp.click(50, 75, button)
                assert result.success is True

                # Check the button number in the call
                call_args = mock_subprocess.call_args[0][0]
                assert call_args[-1] == expected_num  # Last argument should be button number

    def test_click_not_connected(self):
        """Test click when not connected."""
        rdp = RDPConnection()

        result = rdp.click(100, 200)

        assert result.success is False
        assert result.message == "No RDP connection"

    @patch("automation.remote.connections.rdp.subprocess.run")
    def test_click_failure(self, mock_subprocess):
        """Test click failure."""
        rdp = RDPConnection()
        rdp.is_connected = True
        rdp.display = ":10"

        # Mock failed subprocess
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr.decode.return_value = "xdotool error"
        mock_subprocess.return_value = mock_result

        result = rdp.click(100, 200)

        assert result.success is False
        assert "Click failed: xdotool error" in result.message

    @patch("automation.remote.connections.rdp.subprocess.run")
    def test_type_text_success(self, mock_subprocess):
        """Test successful text typing."""
        rdp = RDPConnection()

        rdp.is_connected = True
        rdp.display = ":10"

        # Mock successful subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = rdp.type_text("Hello World")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Typed: Hello World" in result.message

        expected_cmd = ["xdotool", "type", "--delay", "50", "Hello World"]
        # Verify subprocess was called with xdotool command and DISPLAY env var
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0] == (expected_cmd,)
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["env"]["DISPLAY"] == ":10"

    def test_type_text_not_connected(self):
        """Test text typing when not connected."""
        rdp = RDPConnection()

        result = rdp.type_text("Hello")

        assert result.success is False
        assert result.message == "No RDP connection"

    @patch("automation.remote.connections.rdp.subprocess.run")
    def test_key_press_success(self, mock_subprocess):
        """Test successful key press."""
        rdp = RDPConnection()

        rdp.is_connected = True
        rdp.display = ":10"

        # Mock successful subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = rdp.key_press("enter")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Pressed key: enter" in result.message

        expected_cmd = ["xdotool", "key", "Return"]
        # Verify subprocess was called with xdotool command and DISPLAY env var
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0] == (expected_cmd,)
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["env"]["DISPLAY"] == ":10"

    def test_key_press_mapping(self):
        """Test key press mapping."""
        rdp = RDPConnection()
        rdp.is_connected = True
        rdp.display = ":10"

        test_cases = [
            ("enter", "Return"),
            ("escape", "Escape"),
            ("tab", "Tab"),
            ("space", "space"),
            ("backspace", "BackSpace"),
            ("delete", "Delete"),
            ("ctrl", "ctrl"),
            ("alt", "alt"),
            ("shift", "shift"),
            ("up", "Up"),
            ("down", "Down"),
            ("left", "Left"),
            ("right", "Right"),
            ("F1", "F1"),  # Unmapped key should pass through
        ]

        with patch("automation.remote.connections.rdp.subprocess.run") as mock_subprocess:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result

            for input_key, expected_xdo_key in test_cases:
                result = rdp.key_press(input_key)
                assert result.success is True

                # Check the key in the call
                call_args = mock_subprocess.call_args[0][0]
                assert call_args[-1] == expected_xdo_key

    @patch("automation.remote.connections.rdp.os.path.exists")
    def test_find_free_display(self, mock_exists):
        """Test finding free display number."""
        rdp = RDPConnection()

        # Mock first few displays as taken, 13 as free
        def mock_exists_side_effect(path):
            if path in ["/tmp/.X10-lock", "/tmp/.X11-lock", "/tmp/.X12-lock"]:
                return True  # Taken
            return False  # Free

        mock_exists.side_effect = mock_exists_side_effect

        free_display = rdp._find_free_display()

        assert free_display == 13

    def test_find_free_display_fallback(self):
        """Test find_free_display fallback when all displays taken."""
        rdp = RDPConnection()

        with patch("automation.remote.connections.rdp.os.path.exists", return_value=True):
            free_display = rdp._find_free_display()
            assert free_display == 99  # Fallback value

    @patch("automation.remote.connections.rdp.os.unlink")
    @patch("automation.remote.connections.rdp.os.path.exists")
    @patch("automation.remote.connections.rdp.subprocess.run")
    @patch("automation.remote.connections.rdp.shutil.which")
    def test_capture_with_xwd_convert_success(
        self, mock_which, mock_subprocess, mock_exists, mock_unlink
    ):
        """Test successful xwd+convert capture method."""
        rdp = RDPConnection()
        rdp.screenshot_path = "/tmp/test.png"

        # Mock tools available
        mock_which.side_effect = lambda cmd: {
            "xwd": "/usr/bin/xwd",
            "magick": "/usr/bin/magick",
        }.get(cmd)

        # Mock successful subprocess calls
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Mock file exists after conversion
        mock_exists.return_value = True

        env = {"DISPLAY": ":10"}
        success = rdp._capture_with_xwd_convert(env)

        assert success is True

        # Should call xwd first, then magick
        assert mock_subprocess.call_count == 2

        # First call should be xwd
        first_call = mock_subprocess.call_args_list[0]
        assert first_call[0][0][:3] == ["xwd", "-root", "-out"]

        # Second call should be magick
        second_call = mock_subprocess.call_args_list[1]
        assert second_call[0][0][0] == "magick"

    @patch("automation.remote.connections.rdp.shutil.which")
    def test_capture_with_xwd_convert_no_tools(self, mock_which):
        """Test xwd+convert method when tools unavailable."""
        rdp = RDPConnection()
        rdp.screenshot_path = "/tmp/test.png"

        # Mock no tools available
        mock_which.return_value = None

        env = {"DISPLAY": ":10"}
        success = rdp._capture_with_xwd_convert(env)

        assert success is False


class TestRDPConnectionIntegration:
    """Integration-style tests for RDPConnection."""

    @patch("automation.remote.connections.rdp.tempfile.mkdtemp")
    @patch("automation.remote.connections.rdp.subprocess.Popen")
    @patch("automation.remote.connections.rdp.subprocess.run")
    @patch("automation.remote.connections.rdp.shutil.which")
    @patch("automation.remote.connections.rdp.os.path.exists")
    @patch("automation.remote.connections.rdp.time.sleep")
    def test_full_connection_workflow(
        self, mock_sleep, mock_exists, mock_which, mock_subprocess_run, mock_popen, mock_mkdtemp
    ):
        """Test complete RDP workflow."""
        rdp = RDPConnection()

        # Setup mocks for successful connection
        mock_which.side_effect = lambda cmd: {
            "xfreerdp": "/usr/bin/xfreerdp",
            "Xvfb": "/usr/bin/Xvfb",
        }.get(cmd)

        mock_exists.return_value = True
        mock_mkdtemp.return_value = "/tmp/rdp_test"

        # Mock processes
        mock_xvfb_process = Mock()
        mock_xvfb_process.poll.return_value = None
        mock_rdp_process = Mock()
        mock_rdp_process.poll.return_value = None
        mock_popen.side_effect = [mock_xvfb_process, mock_rdp_process]

        # Mock operations
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        with patch.object(rdp, "_find_free_display", return_value=10):
            # Connect
            connect_result = rdp.connect("test.host")
            assert connect_result.success is True
            assert rdp.is_connected is True

            # Use connection
            click_result = rdp.click(100, 100)
            assert click_result.success is True

            type_result = rdp.type_text("test")
            assert type_result.success is True

            key_result = rdp.key_press("enter")
            assert key_result.success is True

            # Disconnect
            with patch("automation.remote.connections.rdp.shutil.rmtree"):
                with patch("automation.remote.connections.rdp.os.unlink"):
                    disconnect_result = rdp.disconnect()
                    assert disconnect_result.success is True
                    assert rdp.is_connected is False

    def test_operations_without_connection(self):
        """Test that operations fail gracefully without connection."""
        rdp = RDPConnection()

        # All operations should fail when not connected
        assert rdp.capture_screen()[0] is False
        assert rdp.click(100, 100).success is False
        assert rdp.type_text("test").success is False
        assert rdp.key_press("enter").success is False

        # Connection info should be empty
        assert rdp.get_connection_info() == {}
