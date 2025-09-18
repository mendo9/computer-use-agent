import os

from computer.interface import BaseComputerInterface, InterfaceFactory
from loguru import logger

VM_IP_ADDRESS = os.getenv("VM_IP_ADDRESS", "").rstrip("/")


class WindowsComputer:
    def __init__(self, interface: BaseComputerInterface) -> None:
        self._interface = interface

    @property
    def interface(self) -> BaseComputerInterface:
        return self._interface


def get_computer_windows() -> WindowsComputer:
    """
    Get a WindowsComputerInterface instance connected to a remote Windows VM.

    Expects a computer-server to be running on the Windows VM.
    Configure VM_IP_ADDRESS environment variable to point to the Windows VM.
    """
    vm_ip = os.getenv("VM_IP_ADDRESS")
    if not vm_ip:
        raise RuntimeError(
            "VM_IP_ADDRESS environment variable is required. Set it to YOUR_WINDOWS_VM_IP"
        )

    interface = InterfaceFactory.create_interface_for_os("windows", vm_ip)
    logger.info(f"Created Windows computer instance for {vm_ip}")
    return WindowsComputer(interface)
