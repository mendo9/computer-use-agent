"""Unit tests for automation.core.types module."""

import time
from unittest.mock import patch

from automation.core.types import ActionResult, ConnectionResult


class TestActionResult:
    """Test cases for ActionResult dataclass."""

    def test_action_result_creation_with_timestamp(self):
        """Test ActionResult creation with explicit timestamp."""
        timestamp = time.time()
        result = ActionResult(success=True, message="Test action completed", timestamp=timestamp)

        assert result.success is True
        assert result.message == "Test action completed"
        assert result.timestamp == timestamp

    def test_action_result_creation_without_timestamp(self):
        """Test ActionResult creation with auto-generated timestamp."""
        with patch("automation.core.types.time.time", return_value=1234567890.0):
            result = ActionResult(success=False, message="Test action failed")

        assert result.success is False
        assert result.message == "Test action failed"
        assert result.timestamp == 1234567890.0

    def test_action_result_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated when None."""
        before_time = time.time()
        result = ActionResult(success=True, message="Test message", timestamp=None)
        after_time = time.time()

        assert before_time <= result.timestamp <= after_time

    def test_action_result_success_types(self):
        """Test ActionResult with different success values."""
        success_result = ActionResult(success=True, message="Success")
        failure_result = ActionResult(success=False, message="Failure")

        assert success_result.success is True
        assert failure_result.success is False

    def test_action_result_message_types(self):
        """Test ActionResult with different message types."""
        result = ActionResult(success=True, message="Test message")
        empty_result = ActionResult(success=True, message="")

        assert result.message == "Test message"
        assert empty_result.message == ""


class TestConnectionResult:
    """Test cases for ConnectionResult dataclass."""

    def test_connection_result_creation_with_timestamp(self):
        """Test ConnectionResult creation with explicit timestamp."""
        timestamp = time.time()
        result = ConnectionResult(
            success=True, message="Connected successfully", timestamp=timestamp
        )

        assert result.success is True
        assert result.message == "Connected successfully"
        assert result.timestamp == timestamp

    def test_connection_result_creation_without_timestamp(self):
        """Test ConnectionResult creation with auto-generated timestamp."""
        with patch("automation.core.types.time.time", return_value=9876543210.0):
            result = ConnectionResult(success=False, message="Connection failed")

        assert result.success is False
        assert result.message == "Connection failed"
        assert result.timestamp == 9876543210.0

    def test_connection_result_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated when None."""
        before_time = time.time()
        result = ConnectionResult(success=True, message="Test connection", timestamp=None)
        after_time = time.time()

        assert before_time <= result.timestamp <= after_time

    def test_connection_result_success_types(self):
        """Test ConnectionResult with different success values."""
        success_result = ConnectionResult(success=True, message="Connected")
        failure_result = ConnectionResult(success=False, message="Failed")

        assert success_result.success is True
        assert failure_result.success is False

    def test_connection_result_message_variations(self):
        """Test ConnectionResult with various message formats."""
        messages = [
            "Connection established",
            "Failed to connect: timeout",
            "",
            "192.168.1.100:5900 connected",
        ]

        for msg in messages:
            result = ConnectionResult(success=True, message=msg)
            assert result.message == msg


class TestTimestampBehavior:
    """Test timestamp behavior across both result types."""

    def test_timestamp_consistency_across_types(self):
        """Test that both result types handle timestamps consistently."""
        timestamp = 1234567890.123

        action_result = ActionResult(success=True, message="Action", timestamp=timestamp)
        connection_result = ConnectionResult(
            success=True, message="Connection", timestamp=timestamp
        )

        assert action_result.timestamp == connection_result.timestamp
        assert action_result.timestamp == timestamp

    def test_none_timestamp_handling(self):
        """Test that None timestamp triggers auto-generation for both types."""
        action_result = ActionResult(success=True, message="Action", timestamp=None)
        connection_result = ConnectionResult(success=True, message="Connection", timestamp=None)

        assert action_result.timestamp is not None
        assert connection_result.timestamp is not None
        assert isinstance(action_result.timestamp, float)
        assert isinstance(connection_result.timestamp, float)

    @patch("automation.core.types.time.time")
    def test_multiple_instances_same_time(self, mock_time):
        """Test multiple instances created at the same mocked time."""
        mock_time.return_value = 1500000000.0

        result1 = ActionResult(success=True, message="First")
        result2 = ConnectionResult(success=True, message="Second")

        assert result1.timestamp == 1500000000.0
        assert result2.timestamp == 1500000000.0
        assert result1.timestamp == result2.timestamp
