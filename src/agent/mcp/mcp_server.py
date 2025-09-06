"""MCP Server Implementation for Computer Vision

Implements the Model Context Protocol (MCP) server that exposes computer vision
functions as tools for LLMs. This server can be used with any MCP-compatible
LLM client (Claude, GPT-4, etc.).
"""

import asyncio
import json
import sys
from typing import Any

from .handlers import execute_tool
from .tools import get_function_tools


class MCPServer:
    """Simple MCP server for computer vision tools"""

    def __init__(self):
        self.tools = get_function_tools()
        self.server_info = {
            "name": "Computer Vision MCP Server",
            "version": "1.0.0",
            "protocol_version": "2024-11-05",
        }

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        Handle incoming MCP requests

        Args:
            request: MCP request object

        Returns:
            MCP response object
        """
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                return self._handle_initialize(request_id, params)
            elif method == "tools/list":
                return self._handle_list_tools(request_id)
            elif method == "tools/call":
                return await self._handle_call_tool(request_id, params)
            else:
                return self._create_error_response(
                    request_id, -32601, f"Method not found: {method}"
                )

        except Exception as e:
            return self._create_error_response(request.get("id"), -32603, f"Internal error: {e!s}")

    def _handle_initialize(self, request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": self.server_info["protocol_version"],
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {
                    "name": self.server_info["name"],
                    "version": self.server_info["version"],
                },
            },
        }

    def _handle_list_tools(self, request_id: Any) -> dict[str, Any]:
        """Handle tools list request"""
        # Convert our function tools to MCP tool format
        mcp_tools = []
        for tool in self.tools:
            func_def = tool["function"]
            mcp_tool = {
                "name": func_def["name"],
                "description": func_def["description"],
                "inputSchema": func_def["parameters"],
            }
            mcp_tools.append(mcp_tool)

        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": mcp_tools}}

    async def _handle_call_tool(self, request_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Handle tool call request"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        if not tool_name:
            return self._create_error_response(request_id, -32602, "Missing tool name")

        # Execute the tool
        try:
            result = execute_tool(tool_name, arguments)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                    "isError": not result.get("success", True),
                },
            }

        except Exception as e:
            return self._create_error_response(request_id, -32603, f"Tool execution error: {e!s}")

    def _create_error_response(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        """Create error response"""
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


class StdioMCPServer:
    """MCP server that communicates via stdio"""

    def __init__(self):
        self.server = MCPServer()

    async def run(self):
        """Run the server, reading from stdin and writing to stdout"""
        print("Computer Vision MCP Server starting...", file=sys.stderr)

        try:
            while True:
                # Read line from stdin
                line = sys.stdin.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON request
                    request = json.loads(line)

                    # Handle request
                    response = await self.server.handle_request(request)

                    # Write response to stdout
                    print(json.dumps(response), flush=True)

                except json.JSONDecodeError:
                    # Invalid JSON
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"},
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            print("Server shutting down...", file=sys.stderr)
        except Exception as e:
            print(f"Server error: {e}", file=sys.stderr)


def create_mcp_server() -> StdioMCPServer:
    """
    Create MCP server instance

    Returns:
        MCP server ready to run

    Example:
        server = create_mcp_server()
        await server.run()
    """
    return StdioMCPServer()


async def start_server():
    """
    Start the MCP server

    This is the main entry point for running the server.
    """
    server = create_mcp_server()
    await server.run()


def main():
    """Command line entry point"""
    print("Starting Computer Vision MCP Server...", file=sys.stderr)

    # Check if models are available
    try:
        import sys
        from pathlib import Path

        # Add parent directory to path to import ocr_clean
        parent_dir = Path(__file__).parent.parent
        sys.path.append(str(parent_dir))

        from vision.setup_models import verify_models

        verification = verify_models()
        if not all(verification.values()):
            print("⚠️  Warning: Some models are not available.", file=sys.stderr)
            print("Run: python -m ocr_clean.setup_models", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Could not verify models: {e}", file=sys.stderr)

    # Run server
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n👋 Server stopped", file=sys.stderr)
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
