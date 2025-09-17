import os
from pathlib import Path

from computer import Computer, VMProviderType
from computer.logger import LogLevel
from loguru import logger

project_root = Path(__file__).parent.parent.parent


def get_computer_lume() -> Computer:
    """
    Get a Computer instance connected to a Lume macOS VM.

    Assumes the Lume VM is already running on localhost:8000
    with the default configuration from lume.sh
    """

    storage_path = os.path.join(project_root, "storage")
    shared_path = os.path.join(project_root, "shared")

    # Ensure directories exist
    os.makedirs(storage_path, exist_ok=True)
    os.makedirs(shared_path, exist_ok=True)

    comp = Computer(
        display="1024x768",
        memory="8GB",
        cpu="4",
        os_type="macos",
        name="macos-sequoia-cua_15.4",
        verbosity=LogLevel.VERBOSE,
        provider_type=VMProviderType.LUME,
        storage=storage_path,
        shared_directories=[shared_path],
        ephemeral=False,
    )

    logger.info("Attached to Lume macOS VM via Computer class")
    return comp
