"""Email configuration for Report MCP Server."""

import json
import os
from pathlib import Path
from typing import List, Dict, Any


def get_recipients() -> List[str]:
    """Load recipients from JSON config file.

    Loads email recipients from config/email_recipients.json.
    The JSON file should have this structure:
    {
        "recipients": [
            "user1@example.com",
            "user2@example.com"
        ],
        "description": "Optional description",
        "last_updated": "2025-01-28"
    }

    Returns:
        list: List of recipient email addresses.

    Raises:
        FileNotFoundError: If email_recipients.json doesn't exist.
        KeyError: If 'recipients' key is missing from JSON.
        json.JSONDecodeError: If JSON file is malformed.
    """
    config_file = Path(__file__).parent / 'email_recipients.json'

    with open(config_file) as f:
        config = json.load(f)

    return config['recipients']


def get_smtp_config() -> Dict[str, Any]:
    """Get SMTP config from environment variables.

    Loads AWS SES SMTP configuration from environment variables:
    - AWS_SES_SMTP_USERNAME: SMTP username from AWS SES
    - AWS_SES_SMTP_PASSWORD: SMTP password (region-specific)
    - AWS_SES_SMTP_SERVER: SMTP endpoint (default: email-smtp.ap-northeast-2.amazonaws.com)
    - AWS_SES_SMTP_PORT: SMTP port (default: 587)
    - AWS_SES_SENDER_EMAIL: Verified sender email (default: noreply@reportserver.ai)

    Returns:
        dict: SMTP configuration with keys: username, password, server, port, sender_email.

    Raises:
        ValueError: If required credentials (username/password) are not set.
    """
    username = os.getenv('AWS_SES_SMTP_USERNAME')
    password = os.getenv('AWS_SES_SMTP_PASSWORD')

    if not username or not password:
        raise ValueError('AWS SES SMTP credentials not configured')

    return {
        'username': username,
        'password': password,
        'server': os.getenv('AWS_SES_SMTP_SERVER', 'email-smtp.ap-northeast-2.amazonaws.com'),
        'port': int(os.getenv('AWS_SES_SMTP_PORT', '587')),
        'sender_email': os.getenv('AWS_SES_SENDER_EMAIL', 'noreply@reportserver.ai'),
    }


