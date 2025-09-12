import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backends.remote_cua_server import RemoteCuaComputer


class TestRemoteCuaComputer:
    @pytest.fixture
    def computer(self):
        """Create RemoteCuaComputer instance for testing"""
        return RemoteCuaComputer()

    @pytest.mark.asyncio
    async def test_get_environment(self, computer):
        """Test get_environment returns windows"""
        result = await computer.get_environment()
        assert result == "windows"

    @pytest.mark.asyncio
    async def test_get_dimensions(self, computer):
        """Test get_dimensions calls correct endpoint and returns dimensions"""
        mock_response = {"width": 1920, "height": 1080}

        with patch("src.backends.remote_cua_server._cmd", return_value=mock_response) as mock_cmd:
            width, height = await computer.get_dimensions()

            mock_cmd.assert_called_once_with("get_screen_size", {})
            assert width == 1920
            assert height == 1080

    @pytest.mark.asyncio
    async def test_screenshot_with_b64_response(self, computer):
        """Test screenshot with base64 response"""
        test_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        mock_response = {"image_b64": test_b64}

        with patch("src.backends.remote_cua_server._cmd", return_value=mock_response):
            result = await computer.screenshot()

            assert result == f"data:image/png;base64,{test_b64}"

    @pytest.mark.asyncio
    async def test_screenshot_with_binary_response(self, computer):
        """Test screenshot with binary image response"""
        test_bytes = b"fake_image_data"
        mock_response = {"image": test_bytes}

        with patch("src.backends.remote_cua_server._cmd", return_value=mock_response):
            result = await computer.screenshot()

            expected_b64 = base64.b64encode(test_bytes).decode()
            assert result == f"data:image/png;base64,{expected_b64}"

    @pytest.mark.asyncio
    async def test_click_left(self, computer):
        """Test left click"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.click(100, 200, "left")

            mock_cmd.assert_called_once_with("left_click", {"x": 100, "y": 200})

    @pytest.mark.asyncio
    async def test_click_right(self, computer):
        """Test right click"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.click(150, 250, "right")

            mock_cmd.assert_called_once_with("right_click", {"x": 150, "y": 250})

    @pytest.mark.asyncio
    async def test_click_middle(self, computer):
        """Test middle click"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.click(300, 400, "middle")

            mock_cmd.assert_called_once_with("middle_click", {"x": 300, "y": 400})

    @pytest.mark.asyncio
    async def test_click_default_left(self, computer):
        """Test click defaults to left button"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.click(75, 125)

            mock_cmd.assert_called_once_with("left_click", {"x": 75, "y": 125})

    @pytest.mark.asyncio
    async def test_type(self, computer):
        """Test type text"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.type("Hello World")

            mock_cmd.assert_called_once_with("type_text", {"text": "Hello World"})

    @pytest.mark.asyncio
    async def test_keypress_single_key(self, computer):
        """Test single key press"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.keypress("Enter")

            mock_cmd.assert_called_once_with("press_key", {"key": "Enter"})

    @pytest.mark.asyncio
    async def test_keypress_hotkey_combination(self, computer):
        """Test hotkey combination"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.keypress(["ctrl", "c"])

            mock_cmd.assert_called_once_with("hotkey", {"keys": ["ctrl", "c"]})

    @pytest.mark.asyncio
    async def test_move(self, computer):
        """Test mouse move"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.move(500, 600)

            mock_cmd.assert_called_once_with("move_cursor", {"x": 500, "y": 600})

    @pytest.mark.asyncio
    async def test_wait(self, computer):
        """Test wait function"""
        start_time = asyncio.get_event_loop().time()
        await computer.wait(100)  # 100ms
        end_time = asyncio.get_event_loop().time()

        # Allow some tolerance for timing
        assert (end_time - start_time) >= 0.09  # At least 90ms
        assert (end_time - start_time) < 0.15  # Less than 150ms

    @pytest.mark.asyncio
    async def test_scroll(self, computer):
        """Test scroll"""
        with patch("src.backends.remote_cua_server._cmd") as mock_cmd:
            await computer.scroll(100, 200, -5, 3)

            mock_cmd.assert_called_once_with(
                "scroll", {"x": 100, "y": 200, "scroll_x": -5, "scroll_y": 3}
            )


class TestRemoteCuaServerHelpers:
    def test_headers_without_api_key(self):
        """Test headers generation without API key"""
        with patch("src.backends.remote_cua_server.PROXY_API_KEY", ""):
            from src.backends.remote_cua_server import _headers

            headers = _headers()

            assert headers == {"Content-Type": "application/json"}

    def test_headers_with_api_key(self):
        """Test headers generation with API key"""
        with patch("src.backends.remote_cua_server.PROXY_API_KEY", "test-key"):
            from src.backends.remote_cua_server import _headers

            headers = _headers()

            assert headers == {"Content-Type": "application/json", "X-API-Key": "test-key"}

    def test_client_with_certificates(self):
        """Test client creation with certificates"""
        with (
            patch("src.backends.remote_cua_server.CLIENT_CERT_PATH", "/path/to/cert.pem"),
            patch("src.backends.remote_cua_server.CLIENT_KEY_PATH", "/path/to/key.pem"),
            patch("src.backends.remote_cua_server.CA_CERT_PATH", "/path/to/ca.pem"),
        ):
            from src.backends.remote_cua_server import _client

            with patch("httpx.AsyncClient") as mock_client:
                _client()

                mock_client.assert_called_once_with(
                    timeout=30.0,
                    verify="/path/to/ca.pem",
                    cert=("/path/to/cert.pem", "/path/to/key.pem"),
                )

    @pytest.mark.asyncio
    async def test_cmd_missing_vm_proxy_url(self):
        """Test _cmd raises error when VM_PROXY_URL is missing"""
        # Remove retry decorator and patch VM_PROXY_URL
        with (
            patch("src.backends.remote_cua_server.VM_PROXY_URL", ""),
            patch("src.backends.remote_cua_server._cmd.retry.stop"),
        ):
            from src.backends.remote_cua_server import _cmd

            # Call the original function without retry
            original_func = _cmd.__wrapped__
            with pytest.raises(RuntimeError, match="VM_PROXY_URL is required for REMOTE mode"):
                await original_func("test_command")

    @pytest.mark.asyncio
    async def test_cmd_success_json_response(self):
        """Test _cmd with successful JSON response"""
        mock_response = AsyncMock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json = AsyncMock(return_value={"result": "success"})
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post.return_value = mock_response

        with (
            patch("src.backends.remote_cua_server.VM_PROXY_URL", "https://test.com"),
            patch("src.backends.remote_cua_server._client", return_value=mock_client),
        ):
            from src.backends.remote_cua_server import _cmd

            # Call the original function without retry to avoid timeout
            original_func = _cmd.__wrapped__
            result = await original_func("test_command", {"param": "value"})

            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_cmd_binary_response(self):
        """Test _cmd with binary response"""
        mock_response = AsyncMock()
        mock_response.headers = {"content-type": "image/png"}
        mock_response.content = b"binary_image_data"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post.return_value = mock_response

        with (
            patch("src.backends.remote_cua_server.VM_PROXY_URL", "https://test.com"),
            patch("src.backends.remote_cua_server._client", return_value=mock_client),
        ):
            from src.backends.remote_cua_server import _cmd

            # Call the original function without retry to avoid timeout
            original_func = _cmd.__wrapped__
            result = await original_func("screenshot")

            assert result == {"image": b"binary_image_data"}
