"""Unit tests for automation.local.desktop_control module."""

import pytest
import subprocess
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from automation.local.desktop_control import DesktopControl
from automation.core.types import ActionResult


class TestDesktopControl:
    """Test cases for DesktopControl class."""

    def test_init(self):
        """Test DesktopControl initialization."""
        desktop = DesktopControl()
        
        assert desktop.screenshot_path == Path("/tmp/desktop_screenshot.png")
        assert desktop.is_active is True

    @patch('subprocess.run')
    @patch('cv2.imread')
    def test_capture_screen_success(self, mock_imread, mock_subprocess):
        """Test successful screen capture."""
        desktop = DesktopControl()
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Mock OpenCV image loading
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image
        
        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            success, image = desktop.capture_screen()
        
        assert success is True
        assert np.array_equal(image, mock_image)
        mock_subprocess.assert_called_once_with(
            ["screencapture", "-x", str(desktop.screenshot_path)],
            check=True,
            capture_output=True
        )

    @patch('subprocess.run')
    def test_capture_screen_subprocess_error(self, mock_subprocess):
        """Test screen capture with subprocess error."""
        desktop = DesktopControl()
        
        # Mock subprocess error
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "screencapture")
        
        success, image = desktop.capture_screen()
        
        assert success is False
        assert image is None

    @patch('subprocess.run')
    @patch('cv2.imread')
    def test_capture_screen_file_not_exists(self, mock_imread, mock_subprocess):
        """Test screen capture when file doesn't exist."""
        desktop = DesktopControl()
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Mock file not existing
        with patch('pathlib.Path.exists', return_value=False):
            success, image = desktop.capture_screen()
        
        assert success is False
        assert image is None

    @patch('subprocess.run')
    def test_capture_screen_nonzero_returncode(self, mock_subprocess):
        """Test screen capture with non-zero return code."""
        desktop = DesktopControl()
        
        # Mock subprocess with non-zero return code
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr.decode.return_value = "Permission denied"
        mock_subprocess.return_value = mock_result
        
        success, image = desktop.capture_screen()
        
        assert success is False
        assert image is None

    @patch('subprocess.run')
    @patch('cv2.imread')
    def test_capture_window_interactive(self, mock_imread, mock_subprocess):
        """Test interactive window capture."""
        desktop = DesktopControl()
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Mock OpenCV image loading
        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image
        
        with patch('pathlib.Path.exists', return_value=True):
            success, image = desktop.capture_window(interactive=True)
        
        assert success is True
        assert np.array_equal(image, mock_image)
        mock_subprocess.assert_called_once_with(
            ["screencapture", "-w", "-x", str(desktop.screenshot_path)],
            check=True
        )

    @patch.object(DesktopControl, 'capture_screen')
    def test_capture_window_non_interactive(self, mock_capture_screen):
        """Test non-interactive window capture falls back to screen capture."""
        desktop = DesktopControl()
        mock_capture_screen.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
        
        success, image = desktop.capture_window(interactive=False)
        
        assert success is True
        mock_capture_screen.assert_called_once()

    @patch('subprocess.run')
    def test_click_left_button_success(self, mock_subprocess):
        """Test successful left click."""
        desktop = DesktopControl()
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = desktop.click(100, 200, "left")
        
        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Clicked left at (100, 200)" in result.message
        mock_subprocess.assert_called_once_with(
            ["osascript", "-e", 'tell application "System Events" to click at {100, 200}'],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_click_right_button(self, mock_subprocess):
        """Test right click with control modifier."""
        desktop = DesktopControl()
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = desktop.click(50, 75, "right")
        
        assert result.success is True
        assert "Clicked right at (50, 75)" in result.message
        # Should use control-click for right click
        expected_script = 'tell application "System Events" to tell (click at {50, 75}) to key down control'
        mock_subprocess.assert_called_once_with(
            ["osascript", "-e", expected_script],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_click_subprocess_error(self, mock_subprocess):
        """Test click with subprocess error."""
        desktop = DesktopControl()
        
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "osascript")
        
        result = desktop.click(100, 200)
        
        assert result.success is False
        assert "Desktop click error" in result.message

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_click_with_cliclick_available(self, mock_subprocess, mock_which):
        """Test click with cliclick when available."""
        desktop = DesktopControl()
        
        # Mock cliclick being available
        mock_which.return_value = "/opt/homebrew/bin/cliclick"
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = desktop.click_with_cliclick(100, 200, "left")
        
        assert result.success is True
        assert "Clicked left at (100, 200) via cliclick" in result.message
        mock_subprocess.assert_called_once_with(
            ["cliclick", "c:100,200"],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('shutil.which')
    @patch.object(DesktopControl, 'click')
    def test_click_with_cliclick_fallback(self, mock_click, mock_which):
        """Test cliclick fallback to AppleScript when not available."""
        desktop = DesktopControl()
        
        # Mock cliclick not being available
        mock_which.return_value = None
        mock_click.return_value = ActionResult(True, "Clicked via AppleScript")
        
        result = desktop.click_with_cliclick(100, 200)
        
        assert result.success is True
        mock_click.assert_called_once_with(100, 200, "left")

    @patch.object(DesktopControl, 'click')
    @patch('time.sleep')
    def test_double_click_success(self, mock_sleep, mock_click):
        """Test successful double click."""
        desktop = DesktopControl()
        
        # Mock successful single clicks
        mock_click.return_value = ActionResult(True, "Clicked")
        
        result = desktop.double_click(150, 250)
        
        assert result.success is True
        assert "Double-clicked at (150, 250)" in result.message
        assert mock_click.call_count == 2
        mock_click.assert_has_calls([
            call(150, 250, "left"),
            call(150, 250, "left")
        ])
        mock_sleep.assert_called_once_with(0.1)

    @patch.object(DesktopControl, 'click')
    def test_double_click_first_fail(self, mock_click):
        """Test double click when first click fails."""
        desktop = DesktopControl()
        
        # Mock first click failure
        mock_click.return_value = ActionResult(False, "Click failed")
        
        result = desktop.double_click(150, 250)
        
        assert result.success is False
        assert "Click failed" in result.message
        assert mock_click.call_count == 1

    @patch('subprocess.run')
    def test_type_text_success(self, mock_subprocess):
        """Test successful text typing."""
        desktop = DesktopControl()
        
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = desktop.type_text("Hello World")
        
        assert result.success is True
        assert "Typed: Hello World" in result.message
        expected_script = 'tell application "System Events" to keystroke "Hello World"'
        mock_subprocess.assert_called_once_with(
            ["osascript", "-e", expected_script],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_type_text_with_quotes(self, mock_subprocess):
        """Test typing text with quotes (should be escaped)."""
        desktop = DesktopControl()
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = desktop.type_text('Hello "World" and \'test\'')
        
        assert result.success is True
        # Should escape both double and single quotes
        expected_script = r'tell application "System Events" to keystroke "Hello \"World\" and \'test\'"'
        mock_subprocess.assert_called_once_with(
            ["osascript", "-e", expected_script],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_key_press_simple_key(self, mock_subprocess):
        """Test pressing simple key."""
        desktop = DesktopControl()
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = desktop.key_press("enter")
        
        assert result.success is True
        assert "Pressed key: enter" in result.message
        expected_script = 'tell application "System Events" to keystroke "return"'
        mock_subprocess.assert_called_once_with(
            ["osascript", "-e", expected_script],
            check=True,
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_key_press_combination(self, mock_subprocess):
        """Test pressing key combination."""
        desktop = DesktopControl()
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = desktop.key_press("cmd+c")
        
        assert result.success is True
        expected_script = 'tell application "System Events" to keystroke "c" using command down'
        mock_subprocess.assert_called_once_with(
            ["osascript", "-e", expected_script],
            check=True,
            capture_output=True,
            text=True
        )

    @patch.object(DesktopControl, 'click')
    @patch.object(DesktopControl, 'key_press')
    @patch('time.sleep')
    def test_scroll_up_success(self, mock_sleep, mock_key_press, mock_click):
        """Test successful upward scrolling."""
        desktop = DesktopControl()
        
        mock_click.return_value = ActionResult(True, "Clicked")
        mock_key_press.return_value = ActionResult(True, "Key pressed")
        
        result = desktop.scroll(100, 200, "up", 3)
        
        assert result.success is True
        assert "Scrolled up 3 times at (100, 200)" in result.message
        mock_click.assert_called_once_with(100, 200)
        assert mock_key_press.call_count == 3
        mock_key_press.assert_has_calls([call("up")] * 3)
        assert mock_sleep.call_count == 3

    @patch('subprocess.run')
    def test_get_desktop_info(self, mock_subprocess):
        """Test getting desktop information."""
        desktop = DesktopControl()
        
        # Mock successful system_profiler call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        with patch('shutil.which', return_value="/usr/bin/cliclick"):
            info = desktop.get_desktop_info()
        
        assert info["platform"] == "macOS"
        assert info["type"] == "local_desktop"
        assert info["screenshot_capability"] is True
        assert info["click_capability"] is True
        assert info["keyboard_capability"] is True
        assert info["cliclick_available"] is True
        assert info["system_profiler_available"] is True

    def test_cleanup(self):
        """Test cleanup method."""
        desktop = DesktopControl()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.unlink') as mock_unlink:
                desktop.cleanup()
                mock_unlink.assert_called_once()

    def test_cleanup_file_not_exists(self):
        """Test cleanup when file doesn't exist."""
        desktop = DesktopControl()
        
        with patch('pathlib.Path.exists', return_value=False):
            # Should not raise exception
            desktop.cleanup()

    def test_cleanup_exception(self):
        """Test cleanup handles exceptions gracefully."""
        desktop = DesktopControl()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.unlink', side_effect=OSError("Permission denied")):
                # Should not raise exception
                desktop.cleanup()


class TestDesktopControlIntegration:
    """Integration-style tests for DesktopControl with multiple components."""

    @patch('subprocess.run')
    @patch('cv2.imread')
    @patch('time.sleep')
    def test_screenshot_and_click_workflow(self, mock_sleep, mock_imread, mock_subprocess):
        """Test combined screenshot and click workflow."""
        desktop = DesktopControl()
        
        # Mock screenshot capture
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        mock_image = np.zeros((1080, 1920, 3), dtype=np.uint8)
        mock_imread.return_value = mock_image
        
        # Test workflow
        with patch('pathlib.Path.exists', return_value=True):
            # Capture screenshot
            success, image = desktop.capture_screen()
            assert success is True
            
            # Click on screen
            click_result = desktop.click(960, 540)  # Center of screen
            assert click_result.success is True
            
            # Type some text
            type_result = desktop.type_text("test input")
            assert type_result.success is True

    @patch('subprocess.run')
    def test_key_combinations(self, mock_subprocess):
        """Test various key combinations."""
        desktop = DesktopControl()
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        test_keys = [
            ("cmd+c", 'tell application "System Events" to keystroke "c" using command down'),
            ("ctrl+v", 'tell application "System Events" to keystroke "v" using control down'),
            ("tab", 'tell application "System Events" to keystroke "tab"'),
            ("escape", 'tell application "System Events" to keystroke "escape"')
        ]
        
        for key, expected_script in test_keys:
            result = desktop.key_press(key)
            assert result.success is True
            
        # Verify all calls were made
        assert mock_subprocess.call_count == len(test_keys)