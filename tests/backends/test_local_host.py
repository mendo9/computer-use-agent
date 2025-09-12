from unittest.mock import MagicMock, patch

from src.backends.local_host import get_computer_local_host


class TestLocalHost:
    @patch("src.backends.local_host.Computer")
    @patch("src.backends.local_host.logger")
    def test_get_computer_local_host(self, mock_logger, mock_computer_class):
        """Test get_computer_local_host creates Computer with correct parameters"""
        mock_computer_instance = MagicMock()
        mock_computer_class.return_value = mock_computer_instance

        result = get_computer_local_host()

        mock_computer_class.assert_called_once_with(os_type="macos", use_host_computer_server=True)
        mock_logger.info.assert_called_once_with(
            "Attached to local host-desktop (macOS) via computer_server"
        )
        assert result == mock_computer_instance
