#!/usr/bin/env python3
"""
Example usage of the Windows computer backend.
Shows how to use the new WindowsComputer with .interface pattern.
"""

import asyncio
import os

from src.backends.windows_computer import get_computer_windows


async def main():
    """Example of using Windows computer interface."""

    # Set environment variable (or use .env file)
    os.environ["VM_IP_ADDRESS"] = "http://192.168.1.100:8000"  # Replace with your Windows VM IP

    # Get the computer instance (similar to Lume VM pattern)
    computer = get_computer_windows()

    # Use as async context manager
    async with computer:
        # The interface provides all computer operations
        interface = computer.interface

        # Get environment info
        env = await interface.get_environment()
        print(f"Environment: {env}")

        # Get screen dimensions
        width, height = await interface.get_dimensions()
        print(f"Screen dimensions: {width}x{height}")

        # Take a screenshot using interface (returns base64 string - standard)
        screenshot_b64 = await interface.screenshot()
        print(f"Screenshot from interface (base64 length: {len(screenshot_b64)} chars)")

        # Take a screenshot as bytes for image processing (convenience method)
        screenshot_bytes = await computer.screenshot_bytes()
        print(f"Screenshot as bytes (length: {len(screenshot_bytes)} bytes)")

        # Save the screenshot
        with open("screenshot.png", "wb") as f:
            f.write(screenshot_bytes)
        print("Screenshot saved as screenshot.png")

        # Get cursor position
        x, y = await interface.get_cursor_position()
        print(f"Cursor position: ({x}, {y})")

        # Example interactions (uncomment to test)
        # await interface.click(100, 100)
        # await interface.type("Hello from Python!")
        # await interface.keypress("Enter")


if __name__ == "__main__":
    asyncio.run(main())
