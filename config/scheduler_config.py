"""Scheduler configuration for daily report automation."""

import os
from typing import Dict, Any, List
from datetime import datetime


def get_scheduler_config() -> Dict[str, Any]:
    """
    Get scheduler configuration from environment variables.
    
    Returns:
        Dict containing scheduler configuration
    """
    return {
        "enabled": os.getenv("SCHEDULER_ENABLED", "true").lower() == "true",
        "timezone": os.getenv("SCHEDULER_TIMEZONE", "Asia/Seoul"),
        "daily_report_time": os.getenv("DAILY_REPORT_TIME", "08:00"),
        "daily_report_enabled": os.getenv("DAILY_REPORT_ENABLED", "true").lower() == "true",
    }


def get_daily_report_config() -> Dict[str, Any]:
    """
    Get daily report specific configuration.
    
    Returns:
        Dict containing daily report configuration
    """
    # Parse stores list from environment variable
    stores_env = os.getenv("DAILY_REPORT_STORES", "all")
    if stores_env.lower().strip() == "all":
        stores_list = "all"
    else:
        stores_list = [store.strip() for store in stores_env.split(",") if store.strip()]
    
    return {
        "stores": stores_list,
        "data_type": os.getenv("DAILY_REPORT_DATA_TYPE", "visitor"),
        "periods": [1],  # Daily report = 1 period
        "max_tokens": int(os.getenv("DAILY_REPORT_MAX_TOKENS", "500")),
        "sender_name": os.getenv("DAILY_REPORT_SENDER_NAME", "Daily Report Bot")
    }


def get_plus_agent_config() -> Dict[str, Any]:
    """
    Get Plus Agent LLM Server configuration.
    
    Returns:
        Dict containing Plus Agent server configuration
    """
    return {
        "url": os.getenv("PLUS_AGENT_URL", "http://localhost:8000"),
        "timeout": int(os.getenv("PLUS_AGENT_TIMEOUT", "30")),
        "retry_attempts": int(os.getenv("PLUS_AGENT_RETRY_ATTEMPTS", "3")),
        "retry_delay": int(os.getenv("PLUS_AGENT_RETRY_DELAY", "5"))
    }


def get_email_config() -> Dict[str, Any]:
    """
    Get email configuration for daily reports.
    
    Returns:
        Dict containing email configuration
    """
    return {
        "subject_prefix": os.getenv("EMAIL_SUBJECT_PREFIX", "📊 데일리 리포트"),
        "include_html": os.getenv("EMAIL_INCLUDE_HTML", "true").lower() == "true",
        "sender_name": os.getenv("EMAIL_SENDER_NAME", "Daily Report Bot")
    }


def validate_scheduler_config() -> List[str]:
    """
    Validate scheduler configuration and return list of validation errors.
    
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Required environment variable {var} is not set")
    
    # Validate time format
    daily_time = os.getenv("DAILY_REPORT_TIME", "08:00")
    try:
        datetime.strptime(daily_time, "%H:%M")
    except ValueError:
        errors.append(f"Invalid DAILY_REPORT_TIME format: {daily_time}. Expected HH:MM format")
    
    # Validate numeric values
    try:
        int(os.getenv("DAILY_REPORT_MAX_TOKENS", "500"))
    except ValueError:
        errors.append("DAILY_REPORT_MAX_TOKENS must be a valid integer")
    
    try:
        int(os.getenv("PLUS_AGENT_TIMEOUT", "30"))
    except ValueError:
        errors.append("PLUS_AGENT_TIMEOUT must be a valid integer")
    
    try:
        int(os.getenv("PLUS_AGENT_RETRY_ATTEMPTS", "3"))
    except ValueError:
        errors.append("PLUS_AGENT_RETRY_ATTEMPTS must be a valid integer")
    
    try:
        int(os.getenv("PLUS_AGENT_RETRY_DELAY", "5"))
    except ValueError:
        errors.append("PLUS_AGENT_RETRY_DELAY must be a valid integer")
    
    # Check Plus Agent URL format
    plus_agent_url = os.getenv("PLUS_AGENT_URL", "http://localhost:8000")
    if not plus_agent_url.startswith(("http://", "https://")):
        errors.append(f"Invalid PLUS_AGENT_URL format: {plus_agent_url}. Must start with http:// or https://")
    
    return errors


def get_all_config() -> Dict[str, Any]:
    """
    Get all configuration sections combined.
    
    Returns:
        Dict containing all configuration sections
    """
    return {
        "scheduler": get_scheduler_config(),
        "daily_report": get_daily_report_config(),
        "plus_agent": get_plus_agent_config(),
        "email": get_email_config()
    }


def print_config_summary():
    """Print a summary of current configuration (for debugging)."""
    config = get_all_config()
    
    print("=== Scheduler Configuration Summary ===")
    print(f"Scheduler Enabled: {config['scheduler']['enabled']}")
    print(f"Timezone: {config['scheduler']['timezone']}")
    print(f"Daily Report Time: {config['scheduler']['daily_report_time']}")
    print(f"Daily Report Enabled: {config['scheduler']['daily_report_enabled']}")
    
    print(f"\nStores: {config['daily_report']['stores']}")
    print(f"Data Type: {config['daily_report']['data_type']}")
    print(f"Max Tokens: {config['daily_report']['max_tokens']}")
    
    print(f"\nPlus Agent URL: {config['plus_agent']['url']}")
    print(f"Plus Agent Timeout: {config['plus_agent']['timeout']}s")
    
    print(f"\nEmail Subject Prefix: {config['email']['subject_prefix']}")
    print(f"Include HTML: {config['email']['include_html']}")
    
    # Check for validation errors
    errors = validate_scheduler_config()
    if errors:
        print(f"\n❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✅ Configuration is valid")
    
    print("=" * 40)