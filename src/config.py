import os

from dotenv import load_dotenv

load_dotenv()

# Keep omniparser_fork import for registration
from src.vision import omniparser_fork  # noqa: F401, E402

COMPUTER_MODE = os.getenv("COMPUTER_MODE", "lume").lower()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Remote (self-hosted VM)
VM_PROXY_URL = os.getenv("VM_PROXY_URL", "").rstrip("/")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
CLIENT_CERT_PATH = os.getenv("CLIENT_CERT_PATH", "")
CLIENT_KEY_PATH = os.getenv("CLIENT_KEY_PATH", "")
CA_CERT_PATH = os.getenv("CA_CERT_PATH", "")

# Azure Service Bus
SB_CONNECTION_STRING = os.getenv("SB_CONNECTION_STRING", "")
SB_QUEUE_NAME = os.getenv("SB_QUEUE_NAME", "")

# Vision
USE_LOCAL_VISION = os.getenv("USE_LOCAL_VISION", "false").lower() == "true"

TRAJECTORY_DIR = os.getenv("TRAJECTORY_DIR", "./trajectories")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
