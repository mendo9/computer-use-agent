import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.queue_consumer.azure_sb import PROMPT_TEMPLATE, consume, handle_message


class TestHandleMessage:
    @pytest.mark.asyncio
    async def test_handle_message_creates_work_item(self):
        """Test handle_message creates WorkItem from body dict"""
        test_body = {
            "job_id": "test-123",
            "task": "fill_form",
            "payload": {"field1": "value1", "field2": "value2"},
        }

        with patch("src.queue_consumer.azure_sb.run_prompt") as mock_run_prompt:
            await handle_message(test_body)

            # Verify run_prompt was called with properly formatted prompt
            mock_run_prompt.assert_called_once()
            call_args = mock_run_prompt.call_args[0][0]

            assert "fill_form" in call_args
            assert '{"field1": "value1", "field2": "value2"}' in call_args

    @pytest.mark.asyncio
    async def test_handle_message_formats_prompt_correctly(self):
        """Test handle_message formats prompt with correct template"""
        test_body = {
            "job_id": "format-test-456",
            "task": "automation_task",
            "payload": {"username": "testuser", "action": "login"},
        }

        with patch("src.queue_consumer.azure_sb.run_prompt") as mock_run_prompt:
            await handle_message(test_body)

            call_args = mock_run_prompt.call_args[0][0]

            # Check that all template elements are present
            assert "You are a computer-use agent" in call_args
            assert "Task: automation_task" in call_args
            assert "Row data:" in call_args
            assert "Rules:" in call_args
            assert "Never guess coordinates" in call_args
            assert "use grounding (OmniParser or available tools)" in call_args
            assert "take a screenshot and verify" in call_args

    @pytest.mark.asyncio
    async def test_handle_message_with_complex_payload(self):
        """Test handle_message handles complex nested payload"""
        complex_payload = {
            "user_data": {
                "profile": {"name": "John", "age": 30},
                "permissions": ["read", "write"],
            },
            "config": {"timeout": 60, "retries": 3},
        }

        test_body = {
            "job_id": "complex-789",
            "task": "complex_automation",
            "payload": complex_payload,
        }

        with patch("src.queue_consumer.azure_sb.run_prompt") as mock_run_prompt:
            await handle_message(test_body)

            call_args = mock_run_prompt.call_args[0][0]

            # Check that complex payload is properly serialized
            payload_str = json.dumps(complex_payload)
            assert payload_str in call_args

    @pytest.mark.asyncio
    async def test_handle_message_with_empty_payload(self):
        """Test handle_message handles empty payload"""
        test_body = {"job_id": "empty-payload-001", "task": "screenshot_task", "payload": {}}

        with patch("src.queue_consumer.azure_sb.run_prompt") as mock_run_prompt:
            await handle_message(test_body)

            call_args = mock_run_prompt.call_args[0][0]

            assert "screenshot_task" in call_args
            assert "{}" in call_args  # Empty JSON object

    @pytest.mark.asyncio
    async def test_handle_message_propagates_run_prompt_errors(self):
        """Test handle_message propagates errors from run_prompt"""
        test_body = {"job_id": "error-test-001", "task": "error_task", "payload": {"test": "data"}}

        with patch("src.queue_consumer.azure_sb.run_prompt") as mock_run_prompt:
            mock_run_prompt.side_effect = Exception("Agent execution failed")

            with pytest.raises(Exception, match="Agent execution failed"):
                await handle_message(test_body)


class TestConsume:
    @pytest.mark.asyncio
    async def test_consume_missing_connection_string(self):
        """Test consume raises error when connection string is missing"""
        with patch("src.queue_consumer.azure_sb.SB_CONNECTION_STRING", ""):
            with patch("src.queue_consumer.azure_sb.SB_QUEUE_NAME", "test-queue"):
                with pytest.raises(
                    RuntimeError, match="SB_CONNECTION_STRING and SB_QUEUE_NAME are required"
                ):
                    await consume()

    @pytest.mark.asyncio
    async def test_consume_missing_queue_name(self):
        """Test consume raises error when queue name is missing"""
        with patch("src.queue_consumer.azure_sb.SB_CONNECTION_STRING", "test-connection"):
            with patch("src.queue_consumer.azure_sb.SB_QUEUE_NAME", ""):
                with pytest.raises(
                    RuntimeError, match="SB_CONNECTION_STRING and SB_QUEUE_NAME are required"
                ):
                    await consume()

    @pytest.mark.asyncio
    async def test_consume_successful_message_processing(self):
        """Test consume successfully processes messages"""
        # Mock message
        mock_message = MagicMock()
        mock_message.__str__ = MagicMock(
            return_value='{"job_id": "test", "task": "test", "payload": {}}'
        )

        # Mock receiver that yields one message then stops
        mock_receiver = AsyncMock()
        mock_receiver.__aenter__.return_value = mock_receiver
        mock_receiver.__aiter__.return_value = iter([mock_message])
        mock_receiver.complete_message = AsyncMock()

        # Mock receiver context manager
        mock_receiver_cm = AsyncMock()
        mock_receiver_cm.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver_cm.__aexit__ = AsyncMock(return_value=None)

        # Mock client
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get_queue_receiver = MagicMock(return_value=mock_receiver_cm)

        with (
            patch("src.queue_consumer.azure_sb.SB_CONNECTION_STRING", "test-conn"),
            patch("src.queue_consumer.azure_sb.SB_QUEUE_NAME", "test-queue"),
            patch("src.queue_consumer.azure_sb.ServiceBusClient") as mock_sb_client,
            patch("src.queue_consumer.azure_sb.handle_message") as mock_handle,
        ):
            mock_sb_client.from_connection_string.return_value = mock_client

            # Run consume but break after first iteration
            consume_task = asyncio.create_task(consume())
            await asyncio.sleep(0.01)  # Let it process one message
            consume_task.cancel()

            try:
                await consume_task
            except asyncio.CancelledError:
                pass

            # Verify message was processed
            mock_handle.assert_called_once()
            mock_receiver.complete_message.assert_called_once_with(mock_message)

    @pytest.mark.asyncio
    async def test_consume_handles_message_processing_error(self):
        """Test consume handles errors during message processing"""
        # Mock message
        mock_message = MagicMock()
        mock_message.__str__ = MagicMock(
            return_value='{"job_id": "test", "task": "test", "payload": {}}'
        )

        # Mock receiver
        mock_receiver = AsyncMock()
        mock_receiver.__aenter__.return_value = mock_receiver
        mock_receiver.__aiter__.return_value = iter([mock_message])
        mock_receiver.complete_message = AsyncMock()
        mock_receiver.abandon_message = AsyncMock()

        # Mock receiver context manager
        mock_receiver_cm = AsyncMock()
        mock_receiver_cm.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver_cm.__aexit__ = AsyncMock(return_value=None)

        # Mock client
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get_queue_receiver = MagicMock(return_value=mock_receiver_cm)

        with (
            patch("src.queue_consumer.azure_sb.SB_CONNECTION_STRING", "test-conn"),
            patch("src.queue_consumer.azure_sb.SB_QUEUE_NAME", "test-queue"),
            patch("src.queue_consumer.azure_sb.ServiceBusClient") as mock_sb_client,
            patch("src.queue_consumer.azure_sb.handle_message") as mock_handle,
            patch("src.queue_consumer.azure_sb.logger") as mock_logger,
        ):
            mock_sb_client.from_connection_string.return_value = mock_client
            mock_handle.side_effect = Exception("Processing failed")

            # Run consume but break after first iteration
            consume_task = asyncio.create_task(consume())
            await asyncio.sleep(0.01)
            consume_task.cancel()

            try:
                await consume_task
            except asyncio.CancelledError:
                pass

            # Verify error handling
            mock_logger.exception.assert_called_once_with("Failed to process message")
            mock_receiver.abandon_message.assert_called_once_with(mock_message)

    @pytest.mark.asyncio
    async def test_consume_creates_correct_client_and_receiver(self):
        """Test consume creates ServiceBus client and receiver correctly"""
        mock_receiver = AsyncMock()
        mock_receiver.__aenter__.return_value = mock_receiver
        mock_receiver.__aiter__.return_value = iter([])  # No messages

        # Mock receiver context manager
        mock_receiver_cm = AsyncMock()
        mock_receiver_cm.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver_cm.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get_queue_receiver = MagicMock(return_value=mock_receiver_cm)

        test_connection = "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test"
        test_queue = "work-items-test"

        with (
            patch("src.queue_consumer.azure_sb.SB_CONNECTION_STRING", test_connection),
            patch("src.queue_consumer.azure_sb.SB_QUEUE_NAME", test_queue),
            patch("src.queue_consumer.azure_sb.ServiceBusClient") as mock_sb_client,
        ):
            mock_sb_client.from_connection_string.return_value = mock_client

            # Run consume briefly
            consume_task = asyncio.create_task(consume())
            await asyncio.sleep(0.01)
            consume_task.cancel()

            try:
                await consume_task
            except asyncio.CancelledError:
                pass

            # Verify correct client creation
            mock_sb_client.from_connection_string.assert_called_once_with(test_connection)
            mock_client.get_queue_receiver.assert_called_once_with(queue_name=test_queue)

    @pytest.mark.asyncio
    async def test_consume_parses_json_messages(self):
        """Test consume correctly parses JSON from messages"""
        test_payload = {
            "job_id": "json-test",
            "task": "parse_test",
            "payload": {"data": "value"},
        }
        mock_message = MagicMock()
        mock_message.__str__ = MagicMock(return_value=json.dumps(test_payload))

        mock_receiver = AsyncMock()
        mock_receiver.__aenter__.return_value = mock_receiver
        mock_receiver.__aiter__.return_value = iter([mock_message])
        mock_receiver.complete_message = AsyncMock()

        # Mock receiver context manager
        mock_receiver_cm = AsyncMock()
        mock_receiver_cm.__aenter__ = AsyncMock(return_value=mock_receiver)
        mock_receiver_cm.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get_queue_receiver = MagicMock(return_value=mock_receiver_cm)

        with (
            patch("src.queue_consumer.azure_sb.SB_CONNECTION_STRING", "test"),
            patch("src.queue_consumer.azure_sb.SB_QUEUE_NAME", "test"),
            patch("src.queue_consumer.azure_sb.ServiceBusClient") as mock_sb_client,
            patch("src.queue_consumer.azure_sb.handle_message") as mock_handle,
        ):
            mock_sb_client.from_connection_string.return_value = mock_client

            consume_task = asyncio.create_task(consume())
            await asyncio.sleep(0.01)
            consume_task.cancel()

            try:
                await consume_task
            except asyncio.CancelledError:
                pass

            # Verify handle_message was called with parsed JSON
            mock_handle.assert_called_once_with(test_payload)


class TestPromptTemplate:
    def test_prompt_template_format(self):
        """Test PROMPT_TEMPLATE has correct format placeholders"""
        # Test that template has required placeholders
        assert "{task}" in PROMPT_TEMPLATE
        assert "{payload}" in PROMPT_TEMPLATE

        # Test formatting works
        formatted = PROMPT_TEMPLATE.format(task="test_task", payload='{"key": "value"}')

        assert "test_task" in formatted
        assert '{"key": "value"}' in formatted

        # Check key instructions are present
        assert "computer-use agent" in formatted
        assert "Never guess coordinates" in formatted
        assert "grounding" in formatted
        assert "screenshot and verify" in formatted

    def test_prompt_template_contains_safety_rules(self):
        """Test PROMPT_TEMPLATE contains important safety rules"""
        # Format with dummy values to check content
        formatted = PROMPT_TEMPLATE.format(task="test", payload="{}")

        safety_keywords = [
            "Never guess coordinates",
            "grounding",
            "OmniParser",
            "screenshot",
            "verify",
        ]

        for keyword in safety_keywords:
            assert keyword in formatted, f"Safety keyword '{keyword}' missing from template"
