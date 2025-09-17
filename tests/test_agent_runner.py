from unittest.mock import MagicMock, patch

import pytest

from src.agent_runner import build_agent, make_computer, run_prompt
from src.backends.remote_cua_server import RemoteCuaComputer


class TestMakeComputer:
    @pytest.mark.asyncio
    async def test_make_computer_remote_mode(self):
        """Test make_computer creates RemoteCuaComputer in remote mode"""
        with patch("src.agent_runner.config") as mock_config:
            mock_config.COMPUTER_MODE = "remote"

            result = await make_computer()

            assert isinstance(result, RemoteCuaComputer)

    @pytest.mark.asyncio
    async def test_make_computer_lume_mode(self):
        """Test make_computer creates lume vm computer in lume mode"""
        mock_computer = MagicMock()

        with (
            patch("src.agent_runner.config") as mock_config,
            patch("src.agent_runner.get_computer_lume", return_value=mock_computer) as mock_get,
        ):
            mock_config.COMPUTER_MODE = "lume"

            result = await make_computer()

            mock_get.assert_called_once()
            assert result == mock_computer

    @pytest.mark.asyncio
    async def test_make_computer_unsupported_mode(self):
        """Test make_computer raises error for unsupported mode"""
        with patch("src.agent_runner.config") as mock_config:
            mock_config.COMPUTER_MODE = "unsupported_mode"

            with pytest.raises(RuntimeError, match="Unsupported COMPUTER_MODE=unsupported_mode"):
                await make_computer()


class TestBuildAgent:
    def test_build_agent_creates_computer_agent(self):
        """Test build_agent creates ComputerAgent with correct parameters"""
        mock_computer = MagicMock()

        with (
            patch("src.agent_runner.ComputerAgent") as mock_agent_class,
            patch("src.agent_runner.config") as mock_config,
        ):
            mock_config.OPENAI_MODEL = "omniparser+openai/gpt-4o"
            mock_config.TRAJECTORY_DIR = "./test_trajectories"

            mock_agent_instance = MagicMock()
            mock_agent_class.return_value = mock_agent_instance

            result = build_agent(mock_computer)

            mock_agent_class.assert_called_once_with(
                model="omniparser+openai/gpt-4o",
                tools=[mock_computer],
                trajectory_dir="./test_trajectories",
                only_n_most_recent_images=3,
                max_retries=3,
                screenshot_delay=0.5,
            )
            assert result == mock_agent_instance

    def test_build_agent_logs_model_info(self):
        """Test build_agent logs model information"""
        mock_computer = MagicMock()

        with (
            patch("src.agent_runner.ComputerAgent") as mock_agent_class,
            patch("src.agent_runner.config") as mock_config,
            patch("src.agent_runner.logger") as mock_logger,
        ):
            mock_config.OPENAI_MODEL = "claude-3.5-sonnet"
            mock_config.TRAJECTORY_DIR = "./trajectories"

            build_agent(mock_computer)

            mock_logger.info.assert_called_once_with("Using model: {}", "claude-3.5-sonnet")

    def test_build_agent_with_different_models(self):
        """Test build_agent works with different model configurations"""
        mock_computer = MagicMock()
        test_models = [
            "openai/gpt-4o",
            "anthropic/claude-3.5-sonnet",
            "omniparser+gpt-4o-mini",
            "local/llama-3.1-70b",
        ]

        with (
            patch("src.agent_runner.ComputerAgent") as mock_agent_class,
            patch("src.agent_runner.config") as mock_config,
        ):
            mock_config.TRAJECTORY_DIR = "./trajectories"

            for model in test_models:
                mock_config.OPENAI_MODEL = model
                build_agent(mock_computer)

                # Check that the model was passed correctly
                call_kwargs = mock_agent_class.call_args[1]
                assert call_kwargs["model"] == model


class TestRunPrompt:
    @pytest.mark.asyncio
    async def test_run_prompt_basic_flow(self):
        """Test run_prompt basic execution flow"""
        mock_computer = MagicMock()
        mock_agent = MagicMock()

        # Mock async iteration
        async def mock_run(prompt):
            yield {"type": "message", "content": "Starting task"}
            yield {"type": "computer_call", "content": "screenshot()"}
            yield {"type": "computer_call_output", "content": "Screenshot taken"}
            yield {"type": "message", "content": "Task completed"}

        mock_agent.run = mock_run

        with (
            patch("src.agent_runner.make_computer", return_value=mock_computer),
            patch("src.agent_runner.build_agent", return_value=mock_agent),
            patch("src.agent_runner.logger") as mock_logger,
        ):
            await run_prompt("Take a screenshot")

            # Verify logging calls
            assert mock_logger.info.call_count == 4

    @pytest.mark.asyncio
    async def test_run_prompt_handles_message_items(self):
        """Test run_prompt handles message items correctly"""
        mock_computer = MagicMock()
        mock_agent = MagicMock()

        async def mock_run(prompt):
            yield {"type": "message", "content": "Test message"}

        mock_agent.run = mock_run

        with (
            patch("src.agent_runner.make_computer", return_value=mock_computer),
            patch("src.agent_runner.build_agent", return_value=mock_agent),
            patch("src.agent_runner.logger") as mock_logger,
        ):
            await run_prompt("Test prompt")

            mock_logger.info.assert_called_once_with("[LLM] {}", "Test message")

    @pytest.mark.asyncio
    async def test_run_prompt_handles_computer_call_items(self):
        """Test run_prompt handles computer call items correctly"""
        mock_computer = MagicMock()
        mock_agent = MagicMock()

        async def mock_run(prompt):
            yield {"type": "computer_call", "content": "click(100, 200)"}

        mock_agent.run = mock_run

        with (
            patch("src.agent_runner.make_computer", return_value=mock_computer),
            patch("src.agent_runner.build_agent", return_value=mock_agent),
            patch("src.agent_runner.logger") as mock_logger,
        ):
            await run_prompt("Click somewhere")

            mock_logger.info.assert_called_once_with("[CALL] {}", "click(100, 200)")

    @pytest.mark.asyncio
    async def test_run_prompt_handles_computer_call_output_items(self):
        """Test run_prompt handles computer call output items correctly"""
        mock_computer = MagicMock()
        mock_agent = MagicMock()

        async def mock_run(prompt):
            yield {"type": "computer_call_output", "content": "Click executed successfully"}

        mock_agent.run = mock_run

        with (
            patch("src.agent_runner.make_computer", return_value=mock_computer),
            patch("src.agent_runner.build_agent", return_value=mock_agent),
            patch("src.agent_runner.logger") as mock_logger,
        ):
            await run_prompt("Test")

            mock_logger.info.assert_called_once_with("[OUT ] {}", "Click executed successfully")

    @pytest.mark.asyncio
    async def test_run_prompt_ignores_unknown_item_types(self):
        """Test run_prompt ignores unknown item types"""
        mock_computer = MagicMock()
        mock_agent = MagicMock()

        async def mock_run(prompt):
            yield {"type": "unknown_type", "content": "Should be ignored"}
            yield {"type": "message", "content": "Should be logged"}

        mock_agent.run = mock_run

        with (
            patch("src.agent_runner.make_computer", return_value=mock_computer),
            patch("src.agent_runner.build_agent", return_value=mock_agent),
            patch("src.agent_runner.logger") as mock_logger,
        ):
            await run_prompt("Test")

            # Should only log the message, not the unknown type
            mock_logger.info.assert_called_once_with("[LLM] {}", "Should be logged")

    @pytest.mark.asyncio
    async def test_run_prompt_passes_prompt_to_agent(self):
        """Test run_prompt passes the prompt to the agent"""
        mock_computer = MagicMock()
        mock_agent = MagicMock()

        async def mock_run(received_prompt):
            assert received_prompt == "Test prompt for agent"
            yield {"type": "message", "content": "Got prompt"}

        mock_agent.run = mock_run

        with (
            patch("src.agent_runner.make_computer", return_value=mock_computer),
            patch("src.agent_runner.build_agent", return_value=mock_agent),
        ):
            await run_prompt("Test prompt for agent")

    @pytest.mark.asyncio
    async def test_run_prompt_creates_computer_and_agent(self):
        """Test run_prompt creates computer and agent instances"""
        mock_computer = MagicMock()
        mock_agent = MagicMock()

        async def mock_run(prompt):
            yield {"type": "message", "content": "Test"}

        mock_agent.run = mock_run

        with (
            patch(
                "src.agent_runner.make_computer", return_value=mock_computer
            ) as mock_make_computer,
            patch("src.agent_runner.build_agent", return_value=mock_agent) as mock_build_agent,
        ):
            await run_prompt("Test")

            mock_make_computer.assert_called_once()
            mock_build_agent.assert_called_once_with(mock_computer)
