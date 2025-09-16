import asyncio
import base64
from pathlib import Path

from src.backends.lume_vm import get_computer_lume
from src.config import OPENAI_MODEL
from src.vision.omniparser_fork import OmniparserConfig, get_parser

# Set up shared directory for screenshots
shared_dir = Path(__file__).parent.parent.parent / "shared"
shared_dir.mkdir(exist_ok=True)


async def safari_omniparser_demo():
    """
    Safari demo using OmniParser for intelligent element detection.
    No more guessing coordinates - let AI find the UI elements!
    """
    print("Starting Safari OmniParser demo...")

    computer = get_computer_lume()
    omniparser = OmniparserConfig()

    try:
        print("Starting VM...")
        await computer.run()

        # Step 1: Take initial screenshot and analyze with OmniParser
        print("Step 1: Taking screenshot and analyzing with OmniParser...")
        screenshot_bytes = await computer.interface.screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()

        # Save initial screenshot
        with open(shared_dir / "omni_step1_initial.png", "wb") as f:
            f.write(screenshot_bytes)
        print("Initial screenshot saved")

        # Step 2: Use OmniParser to find Safari icon
        print("Step 2: Using OmniParser to find Safari...")

        # Try multiple specific instructions for Safari
        safari_instructions = (
            "Safari browser icon with compass design in the dock at bottom of screen",
            "blue Safari browser icon in dock",
            "compass navigation icon Safari in dock",
        )

        safari_coords = None
        coords = await omniparser.predict_click(
            model=OPENAI_MODEL, image_b64=screenshot_b64, instruction=safari_instructions
        )
        if coords and coords[1] > 0.8:  # Must be in bottom 20% of screen
            safari_coords = coords
            print(f"✅ Found Safari with instruction: '{safari_instructions}'")
        elif coords:
            print(f"❌ Found element at {coords} but not in dock (y < 0.8)")

        # If predict_click fails, use known Safari position from debug results
        if not safari_coords:
            print("🔍 predict_click failed, using known Safari position...")

            # From debug results, we know Safari is typically element ID 39
            # at normalized coordinates around (0.366, 0.947)
            # Let's use common Safari dock positions
            safari_candidates = [
                (0.366, 0.947),  # Position from debug
                (0.35, 0.95),  # Slightly adjusted
                (0.40, 0.95),  # Alternative position
                (0.30, 0.95),  # Further left
                (0.45, 0.95),  # Further right
            ]

            print("Trying known Safari dock positions...")
            for i, (x, y) in enumerate(safari_candidates):
                print(f"Trying Safari position {i + 1}: ({x:.3f}, {y:.3f})")

                # Test this position by taking a screenshot before clicking
                before_bytes = await computer.interface.screenshot()

                # Click at this position
                screen_size = await computer.interface.get_screen_size()
                test_x = int(x * screen_size["width"])
                test_y = int(y * screen_size["height"])

                await computer.interface.left_click(test_x, test_y)
                await asyncio.sleep(4)  # Wait for app to launch

                # Check if Safari window appeared (look for browser-like content)
                after_bytes = await computer.interface.screenshot()

                # Save screenshots for analysis
                with open(shared_dir / f"safari_test_position_{i + 1}.png", "wb") as f:
                    f.write(after_bytes)

                # Basic heuristic: Safari opened if significant visual change
                size_change = len(after_bytes) / len(before_bytes)
                if 1.1 < size_change < 2.0:  # Reasonable size increase
                    print(f"✅ Position {i + 1} likely opened Safari!")
                    safari_coords = (x, y)
                    break
                elif size_change > 2.0:
                    print(f"⚠️ Position {i + 1} opened something big (maybe not Safari)")
                else:
                    print(f"❌ Position {i + 1} no significant change")

            if not safari_coords:
                print("❌ Could not find Safari at known positions")
                print(f"💡 Check {shared_dir}/safari_test_position_*.png to see what was clicked")
                return

        if safari_coords:
            x, y = safari_coords
            print(f"✅ OmniParser found Safari at normalized coordinates: ({x:.3f}, {y:.3f})")

            # Convert normalized coordinates to actual pixels
            screen_size = await computer.interface.get_screen_size()
            actual_x = int(x * screen_size["width"])
            actual_y = int(y * screen_size["height"])
            print(f"✅ Converted to pixel coordinates: ({actual_x}, {actual_y})")

            # Click on Safari
            await computer.interface.left_click(actual_x, actual_y)
            await asyncio.sleep(4)  # Wait for Safari to open

            screenshot_bytes = await computer.interface.screenshot()
            with open(shared_dir / "omni_step2_safari_clicked.png", "wb") as f:
                f.write(screenshot_bytes)
            print("Safari clicked and opened")
        else:
            print("❌ OmniParser couldn't find Safari icon")
            return

        # Step 3: Find and click address bar
        print("Step 3: Finding address bar with OmniParser...")
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()

        address_coords = await omniparser.predict_click(
            model=OPENAI_MODEL,
            image_b64=screenshot_b64,
            instruction="address bar or URL field",
        )

        if address_coords:
            x, y = address_coords
            print(f"✅ Found address bar at normalized coordinates: ({x:.3f}, {y:.3f})")

            # Convert to pixels
            screen_size = await computer.interface.get_screen_size()
            actual_x = int(x * screen_size["width"])
            actual_y = int(y * screen_size["height"])
            print(f"✅ Converted to pixel coordinates: ({actual_x}, {actual_y})")

            await computer.interface.left_click(actual_x, actual_y)
            await asyncio.sleep(1)

            # Clear and type x.com
            await computer.interface.hotkey("cmd", "a")
            await asyncio.sleep(0.5)
            await computer.interface.type_text("x.com")
            await asyncio.sleep(1)

            screenshot_bytes = await computer.interface.screenshot()
            with open(shared_dir / "omni_step3_typed_url.png", "wb") as f:
                f.write(screenshot_bytes)
            print("Typed x.com in address bar")
        else:
            print("❌ Couldn't find address bar")
            return

        # Step 4: Press Enter to navigate
        print("Step 4: Navigating to x.com...")
        await computer.interface.press_key("return")
        await asyncio.sleep(8)  # Wait for page load

        screenshot_bytes = await computer.interface.screenshot()
        with open(shared_dir / "omni_step4_page_loaded.png", "wb") as f:
            f.write(screenshot_bytes)
        print("Page loaded")

        # Step 5: Find "Sign up with Apple" button
        print("Step 5: Looking for 'Sign up with Apple' button...")
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()

        # Try different variations of the button text
        button_searches = [
            "Sign up with Apple",
            "Continue with Apple",
            "Apple ID sign in",
            "Sign in with Apple",
            "Apple login button",
        ]

        found_button = False
        for search_text in button_searches:
            print(f"Searching for: '{search_text}'...")

            button_coords = await omniparser.predict_click(
                model=OPENAI_MODEL, image_b64=screenshot_b64, instruction=search_text
            )

            if button_coords:
                x, y = button_coords
                print(f"✅ Found button '{search_text}' at normalized: ({x:.3f}, {y:.3f})")

                # Convert to pixels
                screen_size = await computer.interface.get_screen_size()
                actual_x = int(x * screen_size["width"])
                actual_y = int(y * screen_size["height"])
                print(f"✅ Clicking at pixel coordinates: ({actual_x}, {actual_y})")

                await computer.interface.left_click(actual_x, actual_y)
                await asyncio.sleep(3)

                screenshot_bytes = await computer.interface.screenshot()
                with open(
                    shared_dir / f"omni_step5_clicked_{search_text.replace(' ', '_')}.png", "wb"
                ) as f:
                    f.write(screenshot_bytes)
                print(f"Clicked on '{search_text}' button")
                found_button = True
                break

        if not found_button:
            print("❌ Could not find any Apple sign-in button")
            # Let's scroll down and try again
            print("Scrolling down to look for more options...")
            await computer.interface.scroll(512, 400, 0, -3)
            await asyncio.sleep(2)

            screenshot_bytes = await computer.interface.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
            with open(shared_dir / "omni_step5_scrolled.png", "wb") as f:
                f.write(screenshot_bytes)

            # Try once more after scrolling
            for search_text in button_searches:
                button_coords = await omniparser.predict_click(
                    model=OPENAI_MODEL,
                    image_b64=screenshot_b64,
                    instruction=search_text,
                )

                if button_coords:
                    x, y = button_coords
                    print(
                        f"✅ Found button after scrolling '{search_text}' at normalized: ({x:.3f}, {y:.3f})"
                    )

                    # Convert to pixels
                    screen_size = await computer.interface.get_screen_size()
                    actual_x = int(x * screen_size["width"])
                    actual_y = int(y * screen_size["height"])
                    print(f"✅ Clicking at pixel coordinates: ({actual_x}, {actual_y})")

                    await computer.interface.left_click(actual_x, actual_y)
                    await asyncio.sleep(3)

                    screenshot_bytes = await computer.interface.screenshot()
                    with open(
                        shared_dir / f"omni_step5_final_{search_text.replace(' ', '_')}.png", "wb"
                    ) as f:
                        f.write(screenshot_bytes)
                    found_button = True
                    break

        # Step 6: Take final screenshot
        print("Step 6: Taking final screenshot...")
        screenshot_bytes = await computer.interface.screenshot()
        with open(shared_dir / "omni_step6_final.png", "wb") as f:
            f.write(screenshot_bytes)

        print("🎉 OmniParser Safari demo completed!")
        print(f"Check {shared_dir}/omni_step*.png for the full sequence")
        if found_button:
            print("✅ Successfully found and clicked Apple sign-in button")
        else:
            print("❌ Apple sign-in button not found on this page")

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


async def debug_omniparser_elements():
    """
    Debug helper to see all elements OmniParser detects on a screenshot
    """
    print("Debug: Analyzing current screen with OmniParser...")

    computer = get_computer_lume()
    try:
        await computer.run()

        # Take screenshot
        screenshot_bytes = await computer.interface.screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()

        # Parse with OmniParser
        parser = get_parser()
        result = parser.parse(screenshot_b64)

        # Save annotated image
        annotated_bytes = base64.b64decode(result.annotated_image_base64)
        shared_dir = Path(__file__).parent.parent.parent / "shared"
        shared_dir.mkdir(exist_ok=True)
        with open(shared_dir / "annotated_elements.png", "wb") as f:
            f.write(annotated_bytes)

        print(f"✅ Found {len(result.elements)} elements")
        print(f"📸 Annotated image saved to {shared_dir / 'annotated_elements.png'}")
        print("\nDetected elements:")

        for element in result.elements:
            center_x = (element.bbox.x1 + element.bbox.x2) / 2
            center_y = (element.bbox.y1 + element.bbox.y2) / 2
            print(f"  ID {element.id}: ({center_x:.1f}, {center_y:.1f}) - {element.type}")

        await computer.disconnect()

    except Exception as e:
        print(f"Error: {e}")


def run():
    """Entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        asyncio.run(debug_omniparser_elements())
    else:
        asyncio.run(safari_omniparser_demo())


if __name__ == "__main__":
    run()
