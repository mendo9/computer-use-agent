"""Function Tool Definitions for MCP Server

Defines the function tools that LLMs can call through the MCP server.
Each tool corresponds to a pure OCR function with proper schema validation.
"""

from typing import Any


def get_function_tools() -> list[dict[str, Any]]:
    """
    Get function tool definitions for LLM integration

    Returns:
        List of function tool definitions compatible with MCP protocol

    Example:
        tools = get_function_tools()
        for tool in tools:
            print(f"Tool: {tool['function']['name']}")
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "detect_ui_elements",
                "description": "Detect UI elements in an image using YOLO computer vision",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_base64": {
                            "type": "string",
                            "description": "Base64-encoded image data (PNG, JPG, etc.)",
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "default": 0.6,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum confidence threshold for detections (0.0-1.0)",
                        },
                        "ui_focused": {
                            "type": "boolean",
                            "default": True,
                            "description": "If true, filter to UI-relevant object classes only",
                        },
                        "max_detections": {
                            "type": "integer",
                            "default": 50,
                            "minimum": 1,
                            "maximum": 200,
                            "description": "Maximum number of detections to return",
                        },
                    },
                    "required": ["image_base64"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "extract_text",
                "description": "Extract text from an image using PaddleOCR",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_base64": {
                            "type": "string",
                            "description": "Base64-encoded image data (PNG, JPG, etc.)",
                        },
                        "language": {
                            "type": "string",
                            "default": "en",
                            "description": "Language code for OCR (en, ch, fr, etc.)",
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "default": 0.5,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum confidence threshold for text results",
                        },
                        "region": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "minItems": 4,
                            "maxItems": 4,
                            "description": "Optional region [x1, y1, x2, y2] to extract text from specific area",
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 100,
                            "minimum": 1,
                            "maximum": 500,
                            "description": "Maximum number of text results to return",
                        },
                    },
                    "required": ["image_base64"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "find_elements_by_text",
                "description": "Find UI elements that contain specific text using combined YOLO+OCR",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_base64": {
                            "type": "string",
                            "description": "Base64-encoded image data (PNG, JPG, etc.)",
                        },
                        "text_query": {
                            "type": "string",
                            "description": "Text to search for (e.g., 'Submit', 'Username', 'Login')",
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "default": 0.6,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum confidence threshold for detections",
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether text matching should be case sensitive",
                        },
                        "search_radius": {
                            "type": "integer",
                            "default": 100,
                            "minimum": 10,
                            "maximum": 500,
                            "description": "Radius in pixels to search for nearby visual elements",
                        },
                    },
                    "required": ["image_base64", "text_query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_screen_content",
                "description": "Comprehensive screen analysis with natural language query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_base64": {
                            "type": "string",
                            "description": "Base64-encoded image data (PNG, JPG, etc.)",
                        },
                        "query": {
                            "type": "string",
                            "description": "Natural language description of what to analyze (e.g., 'Find all buttons and input fields')",
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "default": 0.6,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum confidence threshold for detections",
                        },
                    },
                    "required": ["image_base64", "query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "find_clickable_elements",
                "description": "Find elements that are likely to be clickable (buttons, links, etc.)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_base64": {
                            "type": "string",
                            "description": "Base64-encoded image data (PNG, JPG, etc.)",
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "default": 0.6,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum confidence threshold for detections",
                        },
                    },
                    "required": ["image_base64"],
                },
            },
        },
    ]


def get_tool_schemas() -> dict[str, dict[str, Any]]:
    """
    Get tool schemas as a dictionary for easier access

    Returns:
        Dictionary mapping tool names to their schemas
    """
    tools = get_function_tools()
    return {tool["function"]["name"]: tool["function"] for tool in tools}


def validate_tool_parameters(tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Validate parameters for a specific tool

    Args:
        tool_name: Name of the tool to validate
        parameters: Parameters to validate

    Returns:
        Validated parameters with defaults applied

    Raises:
        ValueError: If parameters are invalid
    """
    schemas = get_tool_schemas()

    if tool_name not in schemas:
        raise ValueError(f"Unknown tool: {tool_name}")

    schema = schemas[tool_name]["parameters"]
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required parameters
    for req_param in required:
        if req_param not in parameters:
            raise ValueError(f"Missing required parameter: {req_param}")

    # Apply defaults and validate
    validated = {}
    for param_name, param_value in parameters.items():
        if param_name not in properties:
            continue  # Ignore unknown parameters

        prop_schema = properties[param_name]

        # Apply default if value is None and default exists
        if param_value is None and "default" in prop_schema:
            validated[param_name] = prop_schema["default"]
        else:
            validated[param_name] = param_value

        # Basic type validation
        expected_type = prop_schema.get("type")
        if expected_type == "number" and not isinstance(validated[param_name], (int, float)):
            try:
                validated[param_name] = float(validated[param_name])
            except (ValueError, TypeError):
                raise ValueError(f"Parameter {param_name} must be a number")

        elif expected_type == "integer" and not isinstance(validated[param_name], int):
            try:
                validated[param_name] = int(validated[param_name])
            except (ValueError, TypeError):
                raise ValueError(f"Parameter {param_name} must be an integer")

        elif expected_type == "boolean" and not isinstance(validated[param_name], bool):
            if isinstance(validated[param_name], str):
                validated[param_name] = validated[param_name].lower() in ("true", "1", "yes")
            else:
                validated[param_name] = bool(validated[param_name])

        elif expected_type == "string" and not isinstance(validated[param_name], str):
            validated[param_name] = str(validated[param_name])

        # Range validation for numbers
        if expected_type in ("number", "integer"):
            if "minimum" in prop_schema and validated[param_name] < prop_schema["minimum"]:
                raise ValueError(f"Parameter {param_name} must be >= {prop_schema['minimum']}")
            if "maximum" in prop_schema and validated[param_name] > prop_schema["maximum"]:
                raise ValueError(f"Parameter {param_name} must be <= {prop_schema['maximum']}")

    return validated


# Tool usage examples for documentation
TOOL_EXAMPLES = {
    "detect_ui_elements": {
        "description": "Detect UI elements like buttons, input fields, and interactive components",
        "example": {
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8...",
            "confidence_threshold": 0.7,
            "ui_focused": True,
            "max_detections": 20,
        },
        "response": {
            "detections": [
                {
                    "class_name": "laptop",
                    "confidence": 0.85,
                    "bbox": [100, 200, 300, 400],
                    "center": [200, 300],
                    "area": 40000,
                }
            ],
            "total_found": 1,
        },
    },
    "extract_text": {
        "description": "Extract all text from an image or specific region",
        "example": {
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8...",
            "language": "en",
            "confidence_threshold": 0.8,
            "max_results": 50,
        },
        "response": {
            "text_results": [
                {
                    "text": "Submit",
                    "confidence": 0.95,
                    "bbox": [[120, 50], [180, 50], [180, 80], [120, 80]],
                    "rect_bbox": [120, 50, 180, 80],
                    "center": [150, 65],
                    "area": 1800,
                }
            ],
            "total_found": 1,
        },
    },
    "find_elements_by_text": {
        "description": "Find UI elements containing specific text",
        "example": {
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8...",
            "text_query": "Login",
            "confidence_threshold": 0.6,
            "case_sensitive": False,
        },
        "response": {
            "elements": [
                {
                    "element_type": "combined",
                    "bbox": [100, 45, 200, 85],
                    "center": [150, 65],
                    "confidence": 0.8,
                    "text": "Login",
                    "description": "button: 'Login'",
                }
            ],
            "total_found": 1,
        },
    },
}
