from computer import Computer
from loguru import logger


def get_computer_local_host() -> Computer:
    # Prereq on your Mac:
    #   pip install cua-computer-server
    #   python -m computer_server  (grant Accessibility + Screen Recording)
    comp = Computer(os_type="macos", use_host_computer_server=True)
    logger.info("Attached to local host-desktop (macOS) via computer_server")
    return comp
