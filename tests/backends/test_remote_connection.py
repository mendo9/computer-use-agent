#!/usr/bin/env python3
"""
Test script for remote CUA server connection.
Tests the SSE response parsing and basic commands.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from backends.remote_cua_server import RemoteCuaComputer, _cmd


async def test_basic_connection():
    """Test basic connection to remote computer-server."""
    print("🔗 Testing basic connection...")

    vm_url = os.getenv("VM_PROXY_URL")
    if not vm_url:
        print("❌ VM_PROXY_URL not set in environment")
        return False

    print(f"📡 Connecting to: {vm_url}")

    try:
        # Test version command
        print("📋 Testing version command...")
        result = await _cmd("version", {})
        print(f"✅ Version result: {result}")

        # Test screen size
        print("📐 Testing screen size...")
        result = await _cmd("get_screen_size", {})
        print(f"✅ Screen size result: {result}")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_computer_interface():
    """Test the RemoteCuaComputer interface."""
    print("\n🖥️  Testing RemoteCuaComputer interface...")

    try:
        computer = RemoteCuaComputer()

        # Test environment detection
        env = await computer.get_environment()
        print(f"✅ Environment: {env}")

        # Test screen dimensions
        width, height = await computer.get_dimensions()
        print(f"✅ Screen dimensions: {width}x{height}")

        # Test screenshot (this might be large, so just check if it works)
        print("📸 Testing screenshot...")
        screenshot = await computer.screenshot()
        if screenshot.startswith("data:image/png;base64,"):
            print("✅ Screenshot successful (base64 PNG data received)")
        else:
            print(f"⚠️  Unexpected screenshot format: {screenshot[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Interface test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Remote CUA Server Connection Test")
    print("=" * 50)

    # Check environment
    vm_url = os.getenv("VM_PROXY_URL")
    if not vm_url:
        print("❌ Please set VM_PROXY_URL environment variable")
        print("   Example: export VM_PROXY_URL=http://192.168.1.100:8000")
        return 1

    # Run tests
    basic_ok = await test_basic_connection()
    interface_ok = await test_computer_interface()

    print("\n📊 Test Results:")
    print(f"   Basic Connection: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    print(f"   Computer Interface: {'✅ PASS' if interface_ok else '❌ FAIL'}")

    if basic_ok and interface_ok:
        print("\n🎉 All tests passed! Remote connection is working.")
        return 0
    else:
        print("\n💥 Some tests failed. Check your computer-server setup.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        sys.exit(1)