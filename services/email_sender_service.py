"""Email sender service using local AWS SES integration."""

import logging
from typing import Dict, Any, Optional

from services.aws_ses_service import AWSSESService

logger = logging.getLogger(__name__)


class EmailSenderService:
    """Service class for sending emails via local AWS SES."""
    
    def __init__(self):
        """Initialize the email sender service."""
        self.ses_service = AWSSESService()
    
    async def send_daily_report_with_pdf(
        self,
        summary: str,
        html_content: str,
        report_date: Optional[str] = None,
        sender_name: str = "Daily Report Bot"
    ) -> Dict[str, Any]:
        """
        Send daily report email with text summary and PDF attachment.
        
        Args:
            summary: The summarized report content (text)
            html_content: HTML report content to convert to PDF
            report_date: Optional report date for subject line
            sender_name: Name of the sender
            
        Returns:
            Dict containing success status and response details
        """
        try:
            result = await self.ses_service.send_daily_report_with_pdf(
                summary=summary,
                html_content=html_content,
                report_date=report_date,
                sender_name=sender_name
            )
            
            if result.get("success"):
                logger.info(f"Successfully sent daily report with PDF attachment")
            else:
                logger.error(f"Failed to send daily report with PDF: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send daily report with PDF: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "PDF 첨부 리포트 이메일 전송 실패"
            }

    async def send_daily_report_email(
        self,
        summary: str,
        html_content: Optional[str] = None,
        report_date: Optional[str] = None,
        sender_name: str = "Daily Report Bot"
    ) -> Dict[str, Any]:
        """
        Send daily report email with summary and optional HTML content.
        
        Args:
            summary: The summarized report content
            html_content: Optional HTML report content to include
            report_date: Optional report date for subject line
            sender_name: Name of the sender
            
        Returns:
            Dict containing success status and response details
        """
        try:
            result = await self.ses_service.send_daily_report_email(
                summary=summary,
                html_content=html_content,
                report_date=report_date,
                sender_name=sender_name
            )
            
            if result.get("success"):
                logger.info(f"Successfully sent daily report email")
            else:
                logger.error(f"Failed to send daily report email: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send daily report email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "이메일 전송 실패"
            }
    
    async def send_custom_email(
        self,
        subject: str,
        content: str,
        content_type: str = "html",
        sender_name: str = "Report Server"
    ) -> Dict[str, Any]:
        """
        Send custom email with specified content.
        
        Args:
            subject: Email subject
            content: Email content
            content_type: Content type (html or text)
            sender_name: Name of the sender
            
        Returns:
            Dict containing success status and response details
        """
        try:
            result = await self.ses_service.send_email(
                subject=subject,
                content=content,
                content_type=content_type,
                sender_name=sender_name
            )
            
            if result.get("success"):
                logger.info(f"Successfully sent custom email: {subject}")
            else:
                logger.error(f"Failed to send custom email: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send custom email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "이메일 전송 실패"
            }
    
    async def test_email_connection(self) -> Dict[str, Any]:
        """
        Test email connection using local AWS SES.
        
        Returns:
            Dict containing connection test results
        """
        try:
            result = await self.ses_service.test_connection()
            
            if result.get("success"):
                logger.info("Email connection test successful")
            else:
                logger.warning(f"Email connection test failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "이메일 연결 테스트 실패"
            }
    
    
