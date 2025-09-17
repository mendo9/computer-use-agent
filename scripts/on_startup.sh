#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Set Poetry environment
export PATH="/usr/local/bin:$HOME/Library/Python/3.12/bin:$PATH"

# Always install/upgrade to the latest version of cua-computer-server without prompting
pip install --upgrade --no-input cua-computer-server

./run_computer_server.sh
