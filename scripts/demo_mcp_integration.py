#!/usr/bin/env python3
"""
Demo: Complete MCP Server Integration

This script demonstrates the clean architecture with:
1. Pure OCR functions (vision package)
2. MCP server interface (agent.mcp package)
3. End-to-end computer vision tool integration

Run this demo to test the complete system.
"""

import asyncio
import base64
import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import cv2
import numpy as np

from agent.mcp import create_mcp_server
from vision import extract_text


def create_demo_image() -> np.ndarray:
    """Create a demo image with text and shapes for testing"""
    img = np.ones((200, 600, 3), dtype=np.uint8) * 255

    # Add some text
    cv2.putText(img, "Computer Vision Demo", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.putText(
        img, "MCP Server Integration", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2
    )
    cv2.putText(img, "Button", (250, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Add some shapes (simulating UI elements)
    cv2.rectangle(img, (200, 120), (350, 170), (100, 100, 200), -1)  # Button
    cv2.rectangle(img, (400, 50), (550, 90), (200, 200, 200), 2)  # Input field outline

    return img


def image_to_base64(image: np.ndarray) -> str:
    """Convert image to base64 string"""
    _, buffer = cv2.imencode(".png", image)
    return base64.b64encode(buffer).decode("utf-8")


async def test_mcp_tools():
    """Test all MCP tools with demo image"""
    print("🔍 Computer Vision MCP Server Demo")
    print("=" * 50)

    # Create demo image
    demo_image = create_demo_image()
    base64_data = image_to_base64(demo_image)

    # Create MCP server
    server = create_mcp_server()
    mcp = server.server

    print("\n1. Testing MCP Server Initialization...")
    init_response = await mcp.handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    print(f"✅ Server initialized (protocol: {init_response['result']['protocolVersion']})")

    print("\n2. Listing Available Tools...")
    tools_response = await mcp.handle_request(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    )
    tools = tools_response["result"]["tools"]
    print(f"✅ Found {len(tools)} tools:")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")

    print("\n3. Testing Text Extraction...")
    text_response = await mcp.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "extract_text",
                "arguments": {"image_base64": base64_data, "confidence_threshold": 0.5},
            },
        }
    )

    text_result = json.loads(text_response["result"]["content"][0]["text"])
    print(f"✅ Text extraction: {text_result['success']}")
    print(f"   Found {text_result['total_found']} text elements:")
    for text_item in text_result["text_results"][:3]:  # Show first 3
        print(f'     "{text_item["text"]}" (confidence: {text_item["confidence"]:.3f})')

    print("\n4. Testing Element Search...")
    search_response = await mcp.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "find_elements_by_text",
                "arguments": {
                    "image_base64": base64_data,
                    "text_query": "Button",
                    "confidence_threshold": 0.5,
                },
            },
        }
    )

    search_result = json.loads(search_response["result"]["content"][0]["text"])
    print(f"✅ Element search: {search_result['success']}")
    print(f"   Found {search_result['total_found']} elements matching 'Button'")

    print("\n5. Testing Screen Analysis...")
    analysis_response = await mcp.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "analyze_screen_content",
                "arguments": {
                    "image_base64": base64_data,
                    "query": "Find all interactive elements and text on this demo screen",
                },
            },
        }
    )

    analysis_result = json.loads(analysis_response["result"]["content"][0]["text"])
    print(f"✅ Screen analysis: {analysis_result['success']}")
    if analysis_result["success"]:
        analysis = analysis_result["analysis"]
        print(f"   Summary: {analysis['summary'][:100]}...")
        print(f"   UI Elements: {len(analysis['ui_elements'])}")
        print(f"   Text Elements: {len(analysis['text_elements'])}")
        print(f"   Clickable Elements: {len(analysis['clickable_elements'])}")


def test_pure_ocr_functions():
    """Test pure OCR functions directly (no MCP)"""
    print("\n🔧 Testing Pure OCR Functions")
    print("=" * 30)

    demo_image = create_demo_image()

    print("1. Direct text extraction...")
    text_results = extract_text(demo_image, confidence_threshold=0.5)
    print(f"✅ Found {len(text_results)} text elements")
    for result in text_results[:2]:
        print(f'   "{result.text}" at {result.center}')


async def main():
    """Run complete demo"""
    print("🚀 Clean Computer Vision Architecture Demo")
    print("🔍 OCR Functions + 🤖 MCP Server Interface")
    print("=" * 60)

    # Test pure OCR functions
    test_pure_ocr_functions()

    # Test MCP integration
    await test_mcp_tools()

    print("\n🎉 Demo completed successfully!")
    print("\n📋 Architecture Summary:")
    print("   └── src/")
    print("       ├── vision/           # Pure computer vision functions")
    print("       └── agent/mcp/     # MCP server interface")
    print("\n💡 The system is ready for LLM integration via MCP protocol!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
