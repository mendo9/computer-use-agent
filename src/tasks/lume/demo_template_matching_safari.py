import asyncio
from pathlib import Path

from src.backends.lume_vm import get_computer_lume
from src.vision.finder import find_target_center


async def template_matching_safari_demo():
    """
    Safari demo using template matching for precise Safari icon detection.
    Uses the enhanced find_target_center function with template matching.
    """
    print("Starting Template Matching Safari demo...")

    computer = get_computer_lume()

    # Set up shared directory for screenshots
    shared_dir = Path(__file__).parent.parent.parent / "shared"
    shared_dir.mkdir(exist_ok=True)

    try:
        print("Starting VM...")
        await computer.run()

        # Step 1: Take initial screenshot
        print("Step 1: Taking screenshot...")
        screenshot_bytes = await computer.interface.screenshot()

        # Save initial screenshot
        with open(shared_dir / "template_step1_initial.png", "wb") as f:
            f.write(screenshot_bytes)
        print("Initial screenshot saved")

        # Step 2: Use template matching to find Safari icon
        print("Step 2: Using template matching to find Safari...")

        safari_coords = find_target_center(screenshot_bytes, "safari")

        if safari_coords:
            x, y = safari_coords
            print(f"✅ Template matching found Safari at pixel coordinates: ({x}, {y})")

            # Click on Safari
            await computer.interface.left_click(int(x), int(y))
            await asyncio.sleep(4)  # Wait for Safari to open

            screenshot_bytes = await computer.interface.screenshot()
            with open(shared_dir / "template_step2_safari_clicked.png", "wb") as f:
                f.write(screenshot_bytes)
            print("Safari clicked and opened")
        else:
            print("❌ Template matching couldn't find Safari icon")
            print("💡 Make sure safari_icon.png template exists in the library")
            return

        # Step 3: Find and click address bar
        print("Step 3: Finding address bar...")

        # For address bar, we'll use a simple approach or could add more templates
        screen_size = await computer.interface.get_screen_size()
        # Typical Safari address bar location (middle-top of screen)
        address_x = screen_size["width"] // 2
        address_y = screen_size["height"] // 6  # About 1/6 down from top

        print(f"Clicking estimated address bar location: ({address_x}, {address_y})")
        await computer.interface.left_click(address_x, address_y)
        await asyncio.sleep(1)

        # Clear and type example.com
        await computer.interface.hotkey("cmd", "a")
        await asyncio.sleep(0.5)
        await computer.interface.type_text("example.com")
        await asyncio.sleep(1)

        screenshot_bytes = await computer.interface.screenshot()
        with open(shared_dir / "template_step3_typed_url.png", "wb") as f:
            f.write(screenshot_bytes)
        print("Typed example.com in address bar")

        # Step 4: Press Enter to navigate
        print("Step 4: Navigating to example.com...")
        await computer.interface.press_key("return")
        await asyncio.sleep(5)  # Wait for page load

        screenshot_bytes = await computer.interface.screenshot()
        with open(shared_dir / "template_step4_page_loaded.png", "wb") as f:
            f.write(screenshot_bytes)
        print("Page loaded")

        print("🎉 Template matching Safari demo completed!")
        print(f"Check {shared_dir}/template_step*.png for the full sequence")
        print("✅ Successfully used template matching to find Safari icon")

    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback

        traceback.print_exc()
    finally:
        try:
            if hasattr(computer, "disconnect"):
                await computer.disconnect()
                print("Disconnected from VM")
        except Exception as e:
            print(f"Error during disconnect: {e}")


def run():
    """Entry point"""
    asyncio.run(template_matching_safari_demo())


if __name__ == "__main__":
    run()
