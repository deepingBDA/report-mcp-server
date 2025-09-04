#!/usr/bin/env python3
"""AWS SES SMTP Password Generator.

This script converts AWS IAM access keys to SES SMTP credentials.
Based on the official AWS documentation: https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html
"""

import base64
import hashlib
import hmac
import sys
from typing import Tuple


def calculate_smtp_password(secret_access_key: str, region: str = 'ap-northeast-2') -> str:
    """Convert AWS secret access key to SES SMTP password.

    Args:
        secret_access_key: AWS secret access key
        region: AWS region (default: ap-northeast-2)

    Returns:
        SES SMTP password
    """
    # AWS SES SMTP signing key and version
    message = 'SendRawEmail'
    version = 0x04

    # Create the signing key
    signing_key = f'AWS4{secret_access_key}'.encode()

    # Create the date key
    date_key = hmac.new(signing_key, region.encode('utf-8'), hashlib.sha256).digest()

    # Create the region key
    region_key = hmac.new(date_key, b'ses', hashlib.sha256).digest()

    # Create the service key
    service_key = hmac.new(region_key, b'aws4_request', hashlib.sha256).digest()

    # Create the signing key for SMTP
    smtp_key = hmac.new(service_key, message.encode('utf-8'), hashlib.sha256).digest()

    # Prepend version byte and encode
    smtp_key_with_version = bytes([version]) + smtp_key
    smtp_password = base64.b64encode(smtp_key_with_version).decode('utf-8')

    return smtp_password


def get_smtp_credentials(access_key_id: str, secret_access_key: str, region: str = 'ap-northeast-2') -> Tuple[str, str]:
    """Get complete SMTP credentials from AWS access keys.

    Args:
        access_key_id: AWS access key ID (becomes SMTP username)
        secret_access_key: AWS secret access key
        region: AWS region

    Returns:
        Tuple of (smtp_username, smtp_password)
    """
    smtp_username = access_key_id
    smtp_password = calculate_smtp_password(secret_access_key, region)

    return smtp_username, smtp_password


def main():
    """Main function for command line usage."""
    if len(sys.argv) < 2:
        print('Usage: python aws_ses_smtp_converter.py <SECRET_ACCESS_KEY> [REGION]')
        print('Example: python aws_ses_smtp_converter.py wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY ap-northeast-2')
        sys.exit(1)

    secret_access_key = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'ap-northeast-2'

    smtp_password = calculate_smtp_password(secret_access_key, region)

    print(f'SMTP Password: {smtp_password}')
    print(f'Region: {region}')


if __name__ == '__main__':
    main()