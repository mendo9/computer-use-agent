"""Tool Execution Handlers for MCP Server

Handles execution of computer vision function tools, converting between
MCP protocol (base64 images) and pure OCR functions (numpy arrays).
"""

import base64
import io

# Import pure OCR functions
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

sys.path.append(str(Path(__file__).parent.parent))

from vision import (
    analyze_screen_content,
    detect_ui_elements,
    extract_text,
    extract_text_from_region,
    find_clickable_elements,
    find_elements_by_text,
)

from .tools import validate_tool_parameters


def decode_base64_image(base64_data: str) -> np.ndarray:
    """
    Convert base64 image data to OpenCV numpy array

    Args:
        base64_data: Base64 encoded image string

    Returns:
        Image as numpy array in BGR format (OpenCV format)

    Raises:
        ValueError: If image data is invalid
    """
    try:
        # Remove data URL prefix if present
        if base64_data.startswith("data:image"):
            base64_data = base64_data.split(",", 1)[1]

        # Decode base64
        image_bytes = base64.b64decode(base64_data)

        # Convert to PIL Image
        pil_image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Convert to numpy array
        image_array = np.array(pil_image)

        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        return image_bgr

    except Exception as e:
        raise ValueError(f"Failed to decode image: {e!s}")


def handle_detect_elements(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Handle detect_ui_elements tool execution

    Args:
        parameters: Tool parameters from MCP call

    Returns:
        Detection results formatted for MCP response
    """
    try:
        # Validate parameters
        validated_params = validate_tool_parameters("detect_ui_elements", parameters)

        # Decode image
        image = decode_base64_image(validated_params["image_base64"])

        # Call OCR function
        detections = detect_ui_elements(
            image=image,
            confidence_threshold=validated_params.get("confidence_threshold", 0.6),
            ui_focused=validated_params.get("ui_focused", True),
            max_detections=validated_params.get("max_detections", 50),
        )

        # Format response
        formatted_detections = []
        for detection in detections:
            formatted_detections.append(
                {
                    "class_name": detection.class_name,
                    "confidence": float(detection.confidence),
                    "bbox": list(detection.bbox),
                    "center": list(detection.center),
                    "area": detection.area,
                }
            )

        return {
            "success": True,
            "detections": formatted_detections,
            "total_found": len(formatted_detections),
            "image_dimensions": {"height": image.shape[0], "width": image.shape[1]},
        }

    except Exception as e:
        return {"success": False, "error": str(e), "detections": [], "total_found": 0}


def handle_extract_text(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Handle extract_text tool execution

    Args:
        parameters: Tool parameters from MCP call

    Returns:
        Text extraction results formatted for MCP response
    """
    try:
        # Validate parameters
        validated_params = validate_tool_parameters("extract_text", parameters)

        # Decode image
        image = decode_base64_image(validated_params["image_base64"])

        # Check if region is specified
        region = validated_params.get("region")
        if region:
            # Extract text from specific region
            text_results = extract_text_from_region(
                image=image,
                region=tuple(region),
                language=validated_params.get("language", "en"),
                confidence_threshold=validated_params.get("confidence_threshold", 0.5),
            )
        else:
            # Extract text from entire image
            text_results = extract_text(
                image=image,
                language=validated_params.get("language", "en"),
                confidence_threshold=validated_params.get("confidence_threshold", 0.5),
                max_results=validated_params.get("max_results", 100),
            )

        # Format response
        formatted_results = []
        for text_result in text_results:
            formatted_results.append(
                {
                    "text": text_result.text,
                    "confidence": float(text_result.confidence),
                    "bbox": [list(point) for point in text_result.bbox],
                    "rect_bbox": list(text_result.rect_bbox),
                    "center": list(text_result.center),
                    "area": text_result.area,
                }
            )

        return {
            "success": True,
            "text_results": formatted_results,
            "total_found": len(formatted_results),
            "image_dimensions": {"height": image.shape[0], "width": image.shape[1]},
            "language": validated_params.get("language", "en"),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "text_results": [], "total_found": 0}


def handle_find_elements(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Handle find_elements_by_text tool execution

    Args:
        parameters: Tool parameters from MCP call

    Returns:
        Element search results formatted for MCP response
    """
    try:
        # Validate parameters
        validated_params = validate_tool_parameters("find_elements_by_text", parameters)

        # Decode image
        image = decode_base64_image(validated_params["image_base64"])

        # Call OCR function
        elements = find_elements_by_text(
            image=image,
            text_query=validated_params["text_query"],
            confidence_threshold=validated_params.get("confidence_threshold", 0.6),
            search_radius=validated_params.get("search_radius", 100),
            case_sensitive=validated_params.get("case_sensitive", False),
        )

        # Format response
        formatted_elements = []
        for element in elements:
            element_data = {
                "element_type": element.element_type,
                "bbox": list(element.bbox),
                "center": list(element.center),
                "confidence": float(element.confidence),
                "area": element.area,
                "text": element.text,
                "description": element.description,
            }

            # Add visual detection info if available
            if element.visual_detection:
                element_data["visual_detection"] = {
                    "class_name": element.visual_detection.class_name,
                    "confidence": float(element.visual_detection.confidence),
                }

            formatted_elements.append(element_data)

        return {
            "success": True,
            "elements": formatted_elements,
            "total_found": len(formatted_elements),
            "query": validated_params["text_query"],
            "image_dimensions": {"height": image.shape[0], "width": image.shape[1]},
        }

    except Exception as e:
        return {"success": False, "error": str(e), "elements": [], "total_found": 0}


def handle_analyze_screen(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Handle analyze_screen_content tool execution

    Args:
        parameters: Tool parameters from MCP call

    Returns:
        Screen analysis results formatted for MCP response
    """
    try:
        # Validate parameters
        validated_params = validate_tool_parameters("analyze_screen_content", parameters)

        # Decode image
        image = decode_base64_image(validated_params["image_base64"])

        # Call OCR function
        analysis = analyze_screen_content(
            image=image,
            query=validated_params["query"],
            confidence_threshold=validated_params.get("confidence_threshold", 0.6),
        )

        # Format UI elements
        def format_element_list(elements):
            formatted = []
            for element in elements:
                element_data = {
                    "element_type": element.element_type,
                    "bbox": list(element.bbox),
                    "center": list(element.center),
                    "confidence": float(element.confidence),
                    "area": element.area,
                    "text": element.text,
                    "description": element.description,
                }

                if element.visual_detection:
                    element_data["visual_detection"] = {
                        "class_name": element.visual_detection.class_name,
                        "confidence": float(element.visual_detection.confidence),
                    }

                formatted.append(element_data)
            return formatted

        return {
            "success": True,
            "analysis": {
                "ui_elements": format_element_list(analysis.ui_elements),
                "text_elements": format_element_list(analysis.text_elements),
                "visual_elements": format_element_list(analysis.visual_elements),
                "clickable_elements": format_element_list(analysis.clickable_elements),
                "summary": analysis.summary,
                "query": analysis.query,
            },
            "image_dimensions": {"height": image.shape[0], "width": image.shape[1]},
        }

    except Exception as e:
        return {"success": False, "error": str(e), "analysis": None}


def handle_find_clickable(parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Handle find_clickable_elements tool execution

    Args:
        parameters: Tool parameters from MCP call

    Returns:
        Clickable elements results formatted for MCP response
    """
    try:
        # Validate parameters
        validated_params = validate_tool_parameters("find_clickable_elements", parameters)

        # Decode image
        image = decode_base64_image(validated_params["image_base64"])

        # Call OCR function
        elements = find_clickable_elements(
            image=image, confidence_threshold=validated_params.get("confidence_threshold", 0.6)
        )

        # Format response
        formatted_elements = []
        for element in elements:
            element_data = {
                "element_type": element.element_type,
                "bbox": list(element.bbox),
                "center": list(element.center),
                "confidence": float(element.confidence),
                "area": element.area,
                "text": element.text,
                "description": element.description,
            }

            if element.visual_detection:
                element_data["visual_detection"] = {
                    "class_name": element.visual_detection.class_name,
                    "confidence": float(element.visual_detection.confidence),
                }

            formatted_elements.append(element_data)

        return {
            "success": True,
            "clickable_elements": formatted_elements,
            "total_found": len(formatted_elements),
            "image_dimensions": {"height": image.shape[0], "width": image.shape[1]},
        }

    except Exception as e:
        return {"success": False, "error": str(e), "clickable_elements": [], "total_found": 0}


# Map tool names to handler functions
TOOL_HANDLERS = {
    "detect_ui_elements": handle_detect_elements,
    "extract_text": handle_extract_text,
    "find_elements_by_text": handle_find_elements,
    "analyze_screen_content": handle_analyze_screen,
    "find_clickable_elements": handle_find_clickable,
}


def execute_tool(tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a specific tool with given parameters

    Args:
        tool_name: Name of the tool to execute
        parameters: Tool parameters

    Returns:
        Tool execution results

    Raises:
        ValueError: If tool is not found
    """
    if tool_name not in TOOL_HANDLERS:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(TOOL_HANDLERS.keys()),
        }

    handler = TOOL_HANDLERS[tool_name]
    return handler(parameters)
