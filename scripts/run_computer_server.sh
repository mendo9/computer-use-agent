#!/bin/bash
set -e

# Script to run the computer-server
# Usage: ./run_computer_server.sh [--host HOST] [--port PORT] [--log-level LEVEL]

# Default values
HOST="0.0.0.0"
PORT="8000"
LOG_LEVEL="info"
TEMP_SCRIPT="$(mktemp)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --host)
      HOST="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --log-level)
      LOG_LEVEL="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--host HOST] [--port PORT] [--log-level LEVEL]"
      exit 1
      ;;
  esac
done

# Create a temporary script file that uses the Server class directly
cat > "${TEMP_SCRIPT}" << 'EOF'
#!/usr/bin/env python
"""
Standalone script to run the computer-server.
This script directly uses the Server class from the computer_server package.
"""
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Run computer-server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--log-level", default="info", help="Log level")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Import the Server class
    from computer_server import Server
    
    # Create and start the server
    print(f"Starting computer-server on {args.host}:{args.port}...")
    server = Server(host=args.host, port=args.port, log_level=args.log_level)
    server.start()  # This will block until stopped

if __name__ == "__main__":
    main()
EOF

# Make the temporary script executable
chmod +x "${TEMP_SCRIPT}"

# Run the server
echo "==> Starting computer-server on ${HOST}:${PORT}..."
python "${TEMP_SCRIPT}" --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"

# Clean up the temporary script when the server is stopped
trap "rm -f ${TEMP_SCRIPT}" EXIT