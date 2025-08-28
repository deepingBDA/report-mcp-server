#!/usr/bin/env python3
"""Main entry point for Report MCP Server."""

import uvicorn
import logging

from config.settings import get_server_config

logger = logging.getLogger(__name__)


def main():
    """Main function to start the server."""
    config = get_server_config()
    
    logger.info(f"Starting Report MCP Server on {config['host']}:{config['port']}")
    
    uvicorn.run(
        "backend:app",
        host=config["host"],
        port=config["port"],
        reload=config["debug"],
        log_level="info"
    )


if __name__ == "__main__":
    main()