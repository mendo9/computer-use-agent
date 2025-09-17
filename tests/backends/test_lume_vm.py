from unittest.mock import patch

from src.backends.lume_vm import get_computer_lume


class TestLumeVM:
    @patch("src.backends.lume_vm.Computer")
    @patch("src.backends.lume_vm.logger")
    def test_get_computer_lume(self, mock_logger, mock_computer_class):
        """Test get_computer_lume creates Computer with correct parameters"""
        mock_computer_instance = mock_computer_class.return_value

        result = get_computer_lume()

        mock_computer_class.assert_called_once()
        call_kwargs = mock_computer_class.call_args[1]

        # Check key parameters
        assert call_kwargs["display"] == "1024x768"
        assert call_kwargs["memory"] == "8GB"
        assert call_kwargs["cpu"] == "4"
        assert call_kwargs["os_type"] == "macos"
        assert call_kwargs["name"] == "macos-sequoia-cua_15.4"
        assert call_kwargs["ephemeral"] is False

        mock_logger.info.assert_called_once_with("Attached to Lume macOS VM via Computer class")
        assert result == mock_computer_instance
