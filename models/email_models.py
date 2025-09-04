"""Email-related Pydantic models for Report MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field


class EmailRequest(BaseModel):
    """Request model for sending emails."""

    topic: str = Field(description='Subject line of the email')
    content: str = Field(description='Body content of the email')
    sender_name: Optional[str] = Field(default='Report Server', description='Name of the sender')
    content_type: Optional[str] = Field(
        default='html', description="Content type: 'html' or 'text'. Default is 'html'", pattern='^(html|text)$'
    )
    recipients: Optional[List[str]] = Field(
        default=None, description='Optional custom recipients list (overrides default configuration)'
    )


class EmailTestRequest(BaseModel):
    """Request model for testing email connection."""
    
    message: Optional[str] = Field(default="테스트 메시지", description='Test message content')


class DailyReportEmailRequest(BaseModel):
    """Request model for sending daily report emails."""

    summary: str = Field(description='Report summary content')
    html_content: Optional[str] = Field(default=None, description='Optional HTML report content')
    report_date: Optional[str] = Field(default=None, description='Report date for subject line')
    sender_name: Optional[str] = Field(default='Daily Report Bot', description='Name of the sender')


class EmailResponse(BaseModel):
    """Response model for email operations."""

    success: bool = Field(description='Whether the operation was successful')
    message: str = Field(description='Status message')
    recipients: Optional[List[str]] = Field(default=None, description='List of recipients')
    subject: Optional[str] = Field(default=None, description='Email subject that was sent')
    sender: Optional[str] = Field(default=None, description='Full sender information')
    content_type: Optional[str] = Field(default=None, description='Content type used')
    sent_at: Optional[str] = Field(default=None, description='Timestamp when email was sent')
    error: Optional[str] = Field(default=None, description='Error message if failed')


class EmailConfigResponse(BaseModel):
    """Response model for email configuration status."""

    smtp_configured: bool = Field(description='Whether SMTP is configured')
    recipients_count: int = Field(description='Number of configured recipients')
    sender_email: Optional[str] = Field(default=None, description='Configured sender email')
    smtp_server: Optional[str] = Field(default=None, description='SMTP server')
    error: Optional[str] = Field(default=None, description='Error message if configuration failed')