import asyncio

from src.backends.lume_vm import get_computer_lume


async def demo_textedit_demo():
    """
    TextEdit demo with step-by-step screenshots and file verification.
    """
    print("Starting TextEdit demo...")

    computer = get_computer_lume()

    try:
        print("Starting VM...")
        await computer.run()

        # Step 1: Initial state
        print("Step 1: Taking initial screenshot...")
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step1_initial.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 1 complete: {len(screenshot)} bytes saved")

        # Step 2: Open Spotlight
        print("Step 2: Opening Spotlight (Cmd+Space)...")
        await computer.interface.hotkey("cmd", "space")
        await asyncio.sleep(2)
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step2_spotlight.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 2 complete: {len(screenshot)} bytes saved")

        # Step 3: Type "TextEdit"
        print("Step 3: Typing 'TextEdit'...")
        await computer.interface.type_text("TextEdit")
        await asyncio.sleep(1)
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step3_typed.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 3 complete: {len(screenshot)} bytes saved")

        # Step 4: Press Enter to launch
        print("Step 4: Pressing Enter to launch TextEdit...")
        await computer.interface.press_key("return")
        await asyncio.sleep(4)  # Wait longer for app to launch
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step4_launched.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 4 complete: {len(screenshot)} bytes saved")

        # Step 5: Type message
        print("Step 5: Typing message...")
        await computer.interface.type_text("Hello from CUA via Lume VM!")
        await asyncio.sleep(1)
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step5_typed_message.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 5 complete: {len(screenshot)} bytes saved")

        # Step 6: Save file (Cmd+S)
        print("Step 6: Opening save dialog (Cmd+S)...")
        await computer.interface.hotkey("cmd", "s")
        await asyncio.sleep(2)
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step6_save_dialog.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 6 complete: {len(screenshot)} bytes saved")

        # Step 7: Navigate to Desktop (Cmd+D)
        print("Step 7: Navigating to Desktop (Cmd+D)...")
        await computer.interface.hotkey("cmd", "d")
        await asyncio.sleep(1)
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step7_desktop_nav.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 7 complete: {len(screenshot)} bytes saved")

        # Step 8: Type filename
        print("Step 8: Typing filename...")
        await computer.interface.type_text("hello_from_lume.txt")
        await asyncio.sleep(1)
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step8_filename.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 8 complete: {len(screenshot)} bytes saved")

        # Step 9: Confirm save (Enter)
        print("Step 9: Confirming save (Enter)...")
        await computer.interface.press_key("return")
        await asyncio.sleep(2)
        screenshot = await computer.interface.screenshot()
        with open("/tmp/step9_saved.png", "wb") as f:
            f.write(screenshot)
        print(f"Step 9 complete: {len(screenshot)} bytes saved")

        # Step 10: Check if file exists
        print("Step 10: Checking if file was created...")
        try:
            file_exists = await computer.interface.file_exists(
                "/Users/lume/Desktop/hello_from_lume.txt"
            )
            print(f"File exists on Desktop: {file_exists}")

            if file_exists:
                content = await computer.interface.read_text(
                    "/Users/lume/Desktop/hello_from_lume.txt"
                )
                print(f"File content: '{content}'")
            else:
                # Try listing Desktop contents
                desktop_files = await computer.interface.list_dir("/Users/lume/Desktop")
                print(f"Desktop contents: {desktop_files}")
        except Exception as e:
            print(f"Error checking file: {e}")

        print("Debug demo completed successfully!")

    except Exception as e:
        print(f"Error during demo: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Don't close immediately - keep VM running for inspection
        print("Disconnected from VM (VM kept running)")
        print("Demo finished. VM kept running for inspection.")
        print("Screenshots saved to /tmp/step*.png")
        try:
            # Only disconnect if the computer has a disconnect method (Lume VMs)
            if hasattr(computer, "disconnect"):
                await computer.disconnect()
                print("Disconnected from VM (VM kept running)")
            else:
                print("Remote computer doesn't require disconnect")
        except Exception as e:
            print(f"Error during disconnect: {e}")


def run():
    """Entry point for the demo"""
    asyncio.run(demo_textedit_demo())


if __name__ == "__main__":
    run()
