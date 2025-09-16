import asyncio
from pathlib import Path

from src.backends.lume_vm import get_computer_lume
from src.vision.finder import find_target_center

# Set up shared directory for screenshots
shared_dir = Path(__file__).parent.parent.parent / "shared"
shared_dir.mkdir(exist_ok=True)


async def template_matching_google_news_demo():
    """
    Safari demo using template matching for precise Safari icon detection.
    Uses the enhanced find_target_center function with template matching.
    """
    print("Starting Template Matching Safari demo...")

    computer = get_computer_lume()

    try:
        print("Starting VM...")
        await computer.run()

        # Step 1: Take initial screenshot
        print("Step 1: Taking screenshot...")
        screenshot_bytes = await computer.interface.screenshot()

        # Step 2: Use template matching to find Safari icon
        print("Step 2: Using template matching to find Safari...")

        coords = find_target_center(screenshot_bytes, "safari")
        if coords:
            x, y = coords
            print(f"✅ Template matching found safari at pixel coordinates: ({x}, {y})")
            await computer.interface.left_click(int(x), int(y))  # Click on Safari
            await asyncio.sleep(2)  # Wait for Safari to open
        else:
            print("❌ Template matching couldn't find Safari icon")
            return

        print("Step 3: Enter in url news.google.com...")
        await computer.interface.type_text("news.google.com")
        await asyncio.sleep(1)

        print("Step 4: Navigating to news.google.com...")
        await computer.interface.press_key("return")
        await asyncio.sleep(5)  # Wait for page load

        print("Step 5: Click on google_news_tech_button...")
        coords = find_target_center(screenshot_bytes, "google_news_tech_button")
        if coords:
            x, y = coords
            print(
                f"✅ Template matching found google_news_tech_button at pixel coordinates: ({x}, {y})"
            )
            await computer.interface.left_click(int(x), int(y))
            await asyncio.sleep(5)
        else:
            print("❌ Template matching couldn't find google_news_tech_button icon")
            return

        print("Step 6: Click on google_news_virtual_reality_button...")
        coords = find_target_center(screenshot_bytes, "google_news_virtual_reality_button")
        if coords:
            x, y = coords
            print(
                f"✅ Template matching found google_news_virtual_reality_button at pixel coordinates: ({x}, {y})"
            )
            await computer.interface.left_click(int(x), int(y))
            await asyncio.sleep(5)
        else:
            print("❌ Template matching couldn't find google_news_virtual_reality_button icon")
            return

        print("Step 7: Click on google_news_sign_in_button...")
        coords = find_target_center(screenshot_bytes, "google_news_sign_in_button")
        if coords:
            x, y = coords
            print(
                f"✅ Template matching found google_news_sign_in_button at pixel coordinates: ({x}, {y})"
            )
            await computer.interface.left_click(int(x), int(y))
            await asyncio.sleep(5)
        else:
            print("❌ Template matching couldn't find google_news_sign_in_button icon")
            return

        print("Step 8: Click on google_news_language_dropdown...")
        coords = find_target_center(screenshot_bytes, "google_news_language_dropdown")
        if coords:
            x, y = coords
            print(
                f"✅ Template matching found google_news_language_dropdown at pixel coordinates: ({x}, {y})"
            )
            await computer.interface.left_click(int(x), int(y))
            await asyncio.sleep(2)  # Wait for dropdown to open
        else:
            print("❌ Template matching couldn't find google_news_language_dropdown icon")
            return

        print("Step 9: Scroll down in the dropdown to find Italian option...")
        # Take screenshot after dropdown opens to see current state
        screenshot_bytes = await computer.interface.screenshot()

        # Try to find Italian dropdown option first
        coords = find_target_center(screenshot_bytes, "google_news_italian_dropdown")
        scroll_attempts = 0
        max_scroll_attempts = 5

        while not coords and scroll_attempts < max_scroll_attempts:
            print(
                f"Italian option not visible, scrolling down (attempt {scroll_attempts + 1}/{max_scroll_attempts})..."
            )

            # Scroll down in the dropdown area
            await computer.interface.scroll_down(clicks=3)
            await asyncio.sleep(1)

            # Take new screenshot and check again
            screenshot_bytes = await computer.interface.screenshot()
            coords = find_target_center(screenshot_bytes, "google_news_italian_dropdown")
            scroll_attempts += 1

        if coords:
            x, y = coords
            print(f"✅ Found Italian option after scrolling at coordinates: ({x}, {y})")
            await computer.interface.left_click(int(x), int(y))
            await asyncio.sleep(2)
        else:
            print("❌ Could not find Italian option even after scrolling")
            print("💡 Trying alternative scroll approach...")

            # Alternative: Scroll up in case we went too far
            await computer.interface.scroll_up(clicks=10)
            await asyncio.sleep(1)
            screenshot_bytes = await computer.interface.screenshot()
            coords = find_target_center(screenshot_bytes, "google_news_italian_dropdown")

            if coords:
                x, y = coords
                print(f"✅ Found Italian option after scrolling up at coordinates: ({x}, {y})")
                await computer.interface.left_click(int(x), int(y))
                await asyncio.sleep(2)
            else:
                print("❌ Still could not find Italian option")
                return

        print("🎉 Template matching google news demo completed!")
        print(f"Check {shared_dir}/template_step*.png for the full sequence")
        print("✅ Successfully used template matching and scrolling to navigate Google News")

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
    asyncio.run(template_matching_google_news_demo())


if __name__ == "__main__":
    run()
