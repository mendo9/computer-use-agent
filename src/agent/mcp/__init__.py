"""MCP Server Interface for Computer Vision

Provides a clean Model Context Protocol (MCP) server that exposes
computer vision functions as tools for LLMs.

This module acts as the interface layer between LLMs and the pure OCR functions,
handling:
- MCP protocol implementation
- Image data encoding/decoding (base64)
- Function tool definitions for LLMs
- Error handling and response formatting

Example usage:
    from agent.mcp import create_mcp_server, get_function_tools

    # Get function tools for LLM integration
    tools = get_function_tools()

    # Create and run MCP server
    server = create_mcp_server()
    server.run()
"""

from .handlers import (
    handle_analyze_screen,
    handle_detect_elements,
    handle_extract_text,
    handle_find_elements,
)
from .mcp_server import create_mcp_server, start_server
from .tools import get_function_tools, get_tool_schemas

__version__ = "1.0.0"

__all__ = [
    # MCP server functions
    "create_mcp_server",
    "start_server",
    # Tool definitions
    "get_function_tools",
    "get_tool_schemas",
    # Tool handlers
    "handle_detect_elements",
    "handle_extract_text",
    "handle_find_elements",
    "handle_analyze_screen",
]
