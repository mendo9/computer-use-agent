import os
from unittest.mock import patch


class TestConfig:
    def test_default_computer_mode(self):
        """Test default COMPUTER_MODE is 'lume'"""
        with patch("src.config.COMPUTER_MODE", "lume"):
            from src import config

            assert config.COMPUTER_MODE == "lume"

    def test_custom_computer_mode(self):
        """Test COMPUTER_MODE can be set via environment"""
        with patch.dict(os.environ, {"COMPUTER_MODE": "remote"}):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.COMPUTER_MODE == "remote"

    def test_computer_mode_case_insensitive(self):
        """Test COMPUTER_MODE is converted to lowercase"""
        with patch.dict(os.environ, {"COMPUTER_MODE": "LUME"}):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.COMPUTER_MODE == "lume"

    def test_default_OPENAI_MODEL(self):
        """Test default OPENAI_MODEL is omniparser+openai/gpt-4o"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.OPENAI_MODEL == "omniparser+openai/gpt-4o"

    def test_custom_OPENAI_MODEL(self):
        """Test OPENAI_MODEL can be customized"""
        with patch.dict(os.environ, {"OPENAI_MODEL": "claude-3.5-sonnet"}):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.OPENAI_MODEL == "claude-3.5-sonnet"

    def test_openai_api_key_empty_by_default(self):
        """Test OPENAI_API_KEY defaults to empty string"""
        with patch("src.config.OPENAI_API_KEY", ""):
            from src import config

            assert config.OPENAI_API_KEY == ""

    def test_vm_proxy_url_strips_trailing_slash(self):
        """Test VM_IP_ADDRESS strips trailing slash"""
        with patch.dict(os.environ, {"VM_IP_ADDRESS": "https://example.com/"}):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.VM_IP_ADDRESS == "https://example.com"

    def test_default_trajectory_dir(self):
        """Test default trajectory directory"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.TRAJECTORY_DIR == "./trajectories"

    def test_default_log_level(self):
        """Test default log level"""
        with patch("src.config.LOG_LEVEL", "INFO"):
            from src import config

            assert config.LOG_LEVEL == "INFO"

    def test_all_cert_paths_empty_by_default(self):
        """Test certificate paths default to empty"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.CLIENT_CERT_PATH == ""
            assert config.CLIENT_KEY_PATH == ""
            assert config.CA_CERT_PATH == ""

    def test_service_bus_config_empty_by_default(self):
        """Test Service Bus config defaults to empty"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.SB_CONNECTION_STRING == ""
            assert config.SB_QUEUE_NAME == ""

    def test_proxy_api_key_empty_by_default(self):
        """Test PROXY_API_KEY defaults to empty"""
        with patch.dict(os.environ, {}, clear=True):
            import importlib

            from src import config

            importlib.reload(config)
            assert config.PROXY_API_KEY == ""
