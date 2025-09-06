"""Unit tests for automation.core.base module."""


import numpy as np
import pytest

from automation.core.base import VMConnection
from automation.core.types import ActionResult, ConnectionResult


class ConcreteVMConnection(VMConnection):
    """Concrete implementation of VMConnection for testing."""

    def connect(
        self,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> ConnectionResult:
        self.is_connected = True
        self.connection_info = {"host": host, "port": port, "username": username, **kwargs}
        return ConnectionResult(success=True, message="Connected")

    def disconnect(self) -> ConnectionResult:
        self.is_connected = False
        self.connection_info = {}
        return ConnectionResult(success=True, message="Disconnected")

    def capture_screen(self) -> tuple[bool, np.ndarray | None]:
        if self.is_connected:
            # Return a mock 100x100 RGB image
            image = np.zeros((100, 100, 3), dtype=np.uint8)
            return True, image
        return False, None

    def click(self, x: int, y: int, button: str = "left") -> ActionResult:
        if self.is_connected:
            return ActionResult(success=True, message=f"Clicked at ({x}, {y}) with {button}")
        return ActionResult(success=False, message="Not connected")

    def type_text(self, text: str) -> ActionResult:
        if self.is_connected:
            return ActionResult(success=True, message=f"Typed: {text}")
        return ActionResult(success=False, message="Not connected")

    def key_press(self, key: str) -> ActionResult:
        if self.is_connected:
            return ActionResult(success=True, message=f"Pressed key: {key}")
        return ActionResult(success=False, message="Not connected")


class TestVMConnection:
    """Test cases for VMConnection abstract base class."""

    def test_vm_connection_initialization(self):
        """Test VMConnection initialization."""
        connection = ConcreteVMConnection()

        assert connection.is_connected is False
        assert connection.connection_info == {}

    def test_cannot_instantiate_abstract_class(self):
        """Test that VMConnection cannot be instantiated directly."""
        with pytest.raises(TypeError):
            VMConnection()

    def test_connect_method(self):
        """Test connect method implementation."""
        connection = ConcreteVMConnection()

        result = connection.connect(
            host="192.168.1.100", port=5900, username="test", password="secret"
        )

        assert isinstance(result, ConnectionResult)
        assert result.success is True
        assert result.message == "Connected"
        assert connection.is_connected is True
        assert connection.connection_info["host"] == "192.168.1.100"
        assert connection.connection_info["port"] == 5900
        assert connection.connection_info["username"] == "test"

    def test_connect_with_kwargs(self):
        """Test connect method with additional kwargs."""
        connection = ConcreteVMConnection()

        result = connection.connect(host="test.host", port=8080, timeout=30, ssl=True)

        assert result.success is True
        assert connection.connection_info["timeout"] == 30
        assert connection.connection_info["ssl"] is True

    def test_disconnect_method(self):
        """Test disconnect method implementation."""
        connection = ConcreteVMConnection()
        connection.connect("192.168.1.100", 5900)

        result = connection.disconnect()

        assert isinstance(result, ConnectionResult)
        assert result.success is True
        assert result.message == "Disconnected"
        assert connection.is_connected is False
        assert connection.connection_info == {}

    def test_capture_screen_when_connected(self):
        """Test screen capture when connected."""
        connection = ConcreteVMConnection()
        connection.connect("192.168.1.100", 5900)

        success, image = connection.capture_screen()

        assert success is True
        assert image is not None
        assert isinstance(image, np.ndarray)
        assert image.shape == (100, 100, 3)
        assert image.dtype == np.uint8

    def test_capture_screen_when_disconnected(self):
        """Test screen capture when not connected."""
        connection = ConcreteVMConnection()

        success, image = connection.capture_screen()

        assert success is False
        assert image is None

    def test_click_when_connected(self):
        """Test click action when connected."""
        connection = ConcreteVMConnection()
        connection.connect("192.168.1.100", 5900)

        result = connection.click(100, 200)

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Clicked at (100, 200) with left" in result.message

    def test_click_with_different_button(self):
        """Test click action with different mouse button."""
        connection = ConcreteVMConnection()
        connection.connect("192.168.1.100", 5900)

        result = connection.click(50, 75, button="right")

        assert result.success is True
        assert "Clicked at (50, 75) with right" in result.message

    def test_click_when_disconnected(self):
        """Test click action when not connected."""
        connection = ConcreteVMConnection()

        result = connection.click(100, 200)

        assert result.success is False
        assert result.message == "Not connected"

    def test_type_text_when_connected(self):
        """Test type text action when connected."""
        connection = ConcreteVMConnection()
        connection.connect("192.168.1.100", 5900)

        result = connection.type_text("Hello, World!")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Typed: Hello, World!" in result.message

    def test_type_text_when_disconnected(self):
        """Test type text action when not connected."""
        connection = ConcreteVMConnection()

        result = connection.type_text("Hello")

        assert result.success is False
        assert result.message == "Not connected"

    def test_key_press_when_connected(self):
        """Test key press action when connected."""
        connection = ConcreteVMConnection()
        connection.connect("192.168.1.100", 5900)

        result = connection.key_press("Enter")

        assert isinstance(result, ActionResult)
        assert result.success is True
        assert "Pressed key: Enter" in result.message

    def test_key_press_when_disconnected(self):
        """Test key press action when not connected."""
        connection = ConcreteVMConnection()

        result = connection.key_press("Escape")

        assert result.success is False
        assert result.message == "Not connected"

    def test_get_connection_info(self):
        """Test get_connection_info method."""
        connection = ConcreteVMConnection()
        connection.connect(host="test.example.com", port=3389, username="admin", timeout=60)

        info = connection.get_connection_info()

        assert isinstance(info, dict)
        assert info["host"] == "test.example.com"
        assert info["port"] == 3389
        assert info["username"] == "admin"
        assert info["timeout"] == 60

    def test_get_connection_info_returns_copy(self):
        """Test that get_connection_info returns a copy, not reference."""
        connection = ConcreteVMConnection()
        connection.connect(host="test.host", port=1234)

        info1 = connection.get_connection_info()
        info2 = connection.get_connection_info()

        # Modify one copy
        info1["modified"] = True

        # Original and second copy should not be affected
        assert "modified" not in connection.connection_info
        assert "modified" not in info2

    def test_get_connection_info_when_disconnected(self):
        """Test get_connection_info when not connected."""
        connection = ConcreteVMConnection()

        info = connection.get_connection_info()

        assert isinstance(info, dict)
        assert len(info) == 0

    def test_connection_state_consistency(self):
        """Test that connection state remains consistent through operations."""
        connection = ConcreteVMConnection()

        # Initially disconnected
        assert connection.is_connected is False

        # Connect
        connection.connect("192.168.1.100", 5900)
        assert connection.is_connected is True

        # Actions work when connected
        assert connection.click(10, 10).success is True
        assert connection.type_text("test").success is True
        assert connection.key_press("Tab").success is True

        # Disconnect
        connection.disconnect()
        assert connection.is_connected is False

        # Actions fail when disconnected
        assert connection.click(10, 10).success is False
        assert connection.type_text("test").success is False
        assert connection.key_press("Tab").success is False
