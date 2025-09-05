"""Example Usage of AI Agent Vision Tools

Demonstrates how to use the computer vision automation tools
in various scenarios and AI agent frameworks.
"""

from agent.vision_tools import (
    analyze_screen,
    click_element,
    configure_vision_tools,
    find_element,
    take_screenshot,
    type_text_in_field,
    verify_action,
    wait_for_element,
)


def simple_form_automation_example():
    """Example: Automate filling out a simple form"""
    print("=== Simple Form Automation Example ===")

    # 1. Analyze the current screen
    analysis = analyze_screen("What form fields and buttons are visible?")
    print(f"Found {analysis['total_elements']} UI elements")
    print(f"Text regions: {analysis['total_text_regions']}")
    if "summary" in analysis:
        print(f"Summary: {analysis['summary']}")

    # 2. Find and fill username field
    username_field = find_element("username field")
    if username_field:
        print("Found username field")
        result = type_text_in_field("john.doe", username_field)
        print(f"Username entry: {result['success']}")

    # 3. Find and fill password field
    password_field = find_element("password field")
    if password_field:
        print("Found password field")
        result = type_text_in_field("secure_password", password_field)
        print(f"Password entry: {result['success']}")

    # 4. Find and click submit button
    submit_button = find_element("submit button")
    if submit_button:
        print("Found submit button")
        result = click_element(submit_button)
        print(f"Submit click: {result['success']}")

        # 5. Verify the form was submitted
        verification = verify_action("form should be submitted successfully")
        print(f"Verification: {verification['success']} - {verification['message']}")


def web_automation_example():
    """Example: Automate web browsing tasks"""
    print("=== Web Automation Example ===")

    # Take initial screenshot
    screenshot_path = "/tmp/initial_screen.png"
    screenshot = take_screenshot(screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

    # Search for a search box
    search_box = find_element("search box")
    if search_box:
        # Type search query
        type_text_in_field("computer vision automation", search_box)

        # Find and click search button
        search_button = find_element("search button")
        if search_button:
            click_element(search_button)

            # Wait for results to load
            results = wait_for_element("search results", max_attempts=10)
            if results.get("success", False):
                print("Search completed successfully")

                # Verify results appeared
                verification = verify_action("search results should be displayed")
                print(f"Results verification: {verification['success']}")


def settings_navigation_example():
    """Example: Navigate through settings menus"""
    print("=== Settings Navigation Example ===")

    # 1. Find and click settings menu
    settings = find_element("settings menu")
    if settings:
        click_element(settings)

        # Wait for settings dialog to open
        settings_dialog = wait_for_element("settings dialog")
        if settings_dialog:
            print("Settings dialog opened")

            # 2. Find a specific setting
            privacy_setting = find_element("privacy settings")
            if privacy_setting:
                click_element(privacy_setting)

                # 3. Verify we're in privacy settings
                verification = verify_action("privacy settings should be visible")
                print(f"Privacy settings: {verification['success']}")


def error_handling_example():
    """Example: Demonstrate error handling and recovery"""
    print("=== Error Handling Example ===")

    try:
        # Try to find an element that doesn't exist
        missing_element = find_element("nonexistent button")
        if missing_element is None:
            print("Element not found - handling gracefully")

            # Alternative approach: analyze screen for available options
            analysis = analyze_screen("What buttons and options are available?")
            if "error" not in analysis:
                available_elements = [elem for elem in analysis["ui_elements"] if elem.get("text")]

                print("Available text elements:")
                for elem in available_elements[:5]:  # Show first 5
                    print(f"  - {elem['text']} ({elem['type']})")
            else:
                print(f"Analysis failed: {analysis['error']}")

    except Exception as e:
        print(f"Error occurred: {e}")
        print("Taking screenshot for debugging...")
        debug_screenshot = take_screenshot("/tmp/debug_screen.png")


def ai_agent_integration_example():
    """Example: How to integrate with AI agent frameworks"""
    print("=== AI Agent Integration Example ===")

    # This shows how an AI agent would use the tools

    def simulate_ai_agent_task(user_request: str):
        """Simulate how an AI agent would handle a user request"""
        print(f"AI Agent received request: {user_request}")

        if "fill form" in user_request.lower():
            # AI agent would call these functions based on the request
            analysis = analyze_screen("Analyze form fields and buttons")

            # AI would interpret the analysis and decide next steps
            if analysis.get("total_text_regions", 0) > 0 or analysis.get("total_elements", 0) > 0:
                print("AI: I see there are UI elements. Let me interact with them.")

                # Find first field and fill it
                first_field = find_element("first input field")
                if first_field:
                    type_text_in_field("AI-generated content", first_field)

        elif "take screenshot" in user_request.lower():
            screenshot = take_screenshot("/tmp/ai_screenshot.png")
            analysis = analyze_screen("Describe what's visible on screen")
            if "error" not in analysis:
                print(f"AI: I took a screenshot and found {analysis['total_elements']} elements")
            else:
                print(f"AI: Screenshot analysis failed: {analysis['error']}")

        return "Task completed by AI agent"

    # Simulate different requests
    simulate_ai_agent_task("Please take a screenshot and tell me what you see")
    simulate_ai_agent_task("Help me fill out this form")


def configuration_example():
    """Example: Configure vision tools for different scenarios"""
    print("=== Configuration Example ===")

    # Standard configuration for general use
    configure_vision_tools(confidence_threshold=0.6, ocr_language="en")
    print("Configured for general UI automation")

    # High-precision configuration for important tasks
    configure_vision_tools(confidence_threshold=0.8, ocr_language="en")
    print("Configured for high-precision tasks")

    # Configuration for diverse content detection
    configure_vision_tools(
        confidence_threshold=0.5,
        ocr_language="en",
    )
    print("Configured for diverse content detection")


if __name__ == "__main__":
    print("Computer Vision AI Agent Tools - Examples")
    print("=" * 50)

    try:
        # Run examples (commented out to avoid actual automation)
        print("Running examples in simulation mode...")
        print("(Actual automation would require proper screen setup)")

        # Uncomment these to run actual automation:
        # simple_form_automation_example()
        # web_automation_example()
        # settings_navigation_example()
        error_handling_example()
        ai_agent_integration_example()
        configuration_example()

    except Exception as e:
        print(f"Example execution error: {e}")
        print("This is expected when running without proper screen setup")
