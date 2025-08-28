"""Configuration settings for Report MCP Server."""

import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_server_config():
    """Get server configuration from environment variables."""
    return {
        "host": os.getenv("HOST", "0.0.0.0"),
        "port": int(os.getenv("PORT", 8002)),
        "debug": os.getenv("DEBUG", "false").lower() == "true"
    }