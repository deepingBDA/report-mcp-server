"""MCP Tools routes for Report MCP Server."""

import logging
from fastapi import APIRouter, HTTPException, status

from models.email_models import (
    EmailRequest, DailyReportEmailRequest, 
    EmailResponse, EmailConfigResponse
)
from services.aws_ses_service import AWSSESService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp/tools", tags=["MCP Tools"])

# Initialize AWS SES service (lazy initialization to avoid startup errors)
ses_service = None

def get_ses_service():
    """Get AWS SES service instance with lazy initialization."""
    global ses_service
    if ses_service is None:
        ses_service = AWSSESService()
    return ses_service


@router.post(
    "/send-email",
    response_model=EmailResponse,
    summary="Send email using AWS SES SMTP",
    description="""
    Send email to predefined or custom recipients using AWS Simple Email Service (SES) SMTP interface.
    
    Supports both HTML and plain text content formats. When HTML format is selected, 
    the tool automatically creates a multipart message with both plain text and HTML versions 
    for better email client compatibility.
    
    Features:
    - Direct AWS SES SMTP integration (no external dependencies)
    - HTML and plain text email support
    - Custom or default recipients
    - Automatic multipart message creation
    - Comprehensive error handling
    """
)
async def send_email(request: EmailRequest) -> EmailResponse:
    """Send email using AWS SES SMTP."""
    try:
        service = get_ses_service()
        result = await service.send_email(
            subject=request.topic,
            content=request.content,
            content_type=request.content_type,
            sender_name=request.sender_name,
            custom_recipients=request.recipients
        )
        
        return EmailResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post(
    "/send-daily-report",
    response_model=EmailResponse,
    summary="Send daily report email",
    description="""
    Send formatted daily report email with summary and optional HTML content.
    
    Creates a professionally formatted email template with:
    - Report summary section
    - Optional detailed HTML report content
    - Automatic date formatting in subject
    - Responsive email design
    """
)
async def send_daily_report(request: DailyReportEmailRequest) -> EmailResponse:
    """Send daily report email with formatted template."""
    try:
        service = get_ses_service()
        result = await service.send_daily_report_email(
            summary=request.summary,
            html_content=request.html_content,
            report_date=request.report_date,
            sender_name=request.sender_name
        )
        
        return EmailResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to send daily report email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send daily report email: {str(e)}"
        )




@router.get(
    "/email-config",
    response_model=EmailConfigResponse,
    summary="Get email configuration status",
    description="""
    Get current email configuration status including:
    - SMTP configuration status
    - Number of configured recipients
    - Sender email address
    - SMTP server details
    """
)
async def get_email_config() -> EmailConfigResponse:
    """Get email configuration status."""
    try:
        # Try to reload config to get current status
        service = get_ses_service()
        service.reload_config()
        
        smtp_config = service.smtp_config
        recipients = service.recipients
        
        return EmailConfigResponse(
            smtp_configured=smtp_config is not None,
            recipients_count=len(recipients) if recipients else 0,
            sender_email=smtp_config.get('sender_email') if smtp_config else None,
            smtp_server=smtp_config.get('server') if smtp_config else None
        )
        
    except Exception as e:
        logger.error(f"Failed to get email config: {e}")
        return EmailConfigResponse(
            smtp_configured=False,
            recipients_count=0,
            error=str(e)
        )


@router.post(
    "/reload-email-config",
    response_model=EmailConfigResponse,
    summary="Reload email configuration",
    description="""
    Reload email configuration from environment variables and config files.
    
    Useful for updating configuration without restarting the server.
    """
)
async def reload_email_config() -> EmailConfigResponse:
    """Reload email configuration."""
    try:
        service = get_ses_service()
        service.reload_config()
        
        smtp_config = service.smtp_config
        recipients = service.recipients
        
        logger.info("Email configuration reloaded successfully")
        
        return EmailConfigResponse(
            smtp_configured=smtp_config is not None,
            recipients_count=len(recipients) if recipients else 0,
            sender_email=smtp_config.get('sender_email') if smtp_config else None,
            smtp_server=smtp_config.get('server') if smtp_config else None
        )
        
    except Exception as e:
        logger.error(f"Failed to reload email config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload email config: {str(e)}"
        )