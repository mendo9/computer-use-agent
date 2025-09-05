"""Function Tool Definitions for AI Agents

This module provides JSON schema definitions for AI agent function tools,
compatible with OpenAI Functions, Claude Tools, and other AI frameworks.

These can be imported and used directly in AI agent configurations.
"""

from typing import Any


def get_vision_function_tools() -> list[dict[str, Any]]:
    """
    Get function tool definitions for computer vision automation

    Returns:
        List of function definitions compatible with AI frameworks
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "analyze_screen",
                "description": "Analyze the current screen and identify UI elements, text, and interactive components",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Natural language description of what to analyze on the screen",
                        }
                    },
                    "required": ["prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "find_element",
                "description": "Find a specific UI element on the screen by description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Natural language description of the element to find (e.g., 'Submit button', 'Username field', 'Settings menu')",
                        }
                    },
                    "required": ["description"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "click_element",
                "description": "Click on a UI element or specific coordinates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "element": {
                            "type": ["object", "array"],
                            "description": "Element object from find_element() or [x, y] coordinates",
                        },
                        "button": {
                            "type": "string",
                            "enum": ["left", "right", "middle"],
                            "default": "left",
                            "description": "Mouse button to click",
                        },
                    },
                    "required": ["element"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "type_text_in_field",
                "description": "Type text in an input field, optionally clicking the field first",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to type"},
                        "field_element": {
                            "type": "object",
                            "description": "Optional field element to click first (from find_element)",
                        },
                    },
                    "required": ["text"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "verify_action",
                "description": "Verify that an action had the expected outcome",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expected_outcome": {
                            "type": "string",
                            "description": "Natural language description of what should have happened",
                        }
                    },
                    "required": ["expected_outcome"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "wait_for_element",
                "description": "Wait for a specific element to appear on screen",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Description of element to wait for",
                        },
                        "max_attempts": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum number of attempts",
                        },
                        "delay": {
                            "type": "number",
                            "default": 1.0,
                            "description": "Delay between attempts in seconds",
                        },
                    },
                    "required": ["description"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scroll_screen",
                "description": "Scroll the screen in a specified direction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down", "left", "right"],
                            "default": "down",
                            "description": "Direction to scroll",
                        },
                        "pixels": {
                            "type": "integer",
                            "default": 400,
                            "description": "Number of pixels to scroll",
                        },
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "take_screenshot",
                "description": "Take a screenshot of the current desktop",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "save_path": {
                            "type": "string",
                            "description": "Optional path to save the screenshot",
                        }
                    },
                },
            },
        },
    ]


# Example usage for different AI frameworks
OPENAI_FUNCTIONS_EXAMPLE = """
# OpenAI Functions usage example:

from openai import OpenAI
from agent.function_definitions import get_vision_function_tools
from agent.vision_tools import *

client = OpenAI()

tools = get_vision_function_tools()

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Please click on the Submit button on my screen"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Handle function calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "find_element":
            element = find_element("Submit button")
        elif tool_call.function.name == "click_element":
            result = click_element(element)
"""

CLAUDE_TOOLS_EXAMPLE = """
# Claude Tools usage example:

import anthropic
from agent.function_definitions import get_vision_function_tools  
from agent.vision_tools import *

client = anthropic.Anthropic()

tools = get_vision_function_tools()

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    tools=tools,
    messages=[
        {"role": "user", "content": "Please help me fill out this form on my screen"}
    ]
)

# Handle tool usage
for content in response.content:
    if content.type == "tool_use":
        if content.name == "analyze_screen":
            result = analyze_screen(content.input["prompt"])
        elif content.name == "find_element": 
            element = find_element(content.input["description"])
"""
