"""AWS SES service for direct email sending."""

import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, List, Optional

from config.email_config import get_smtp_config, get_recipients

logger = logging.getLogger(__name__)


class AWSSESService:
    """Service class for sending emails via AWS SES SMTP."""
    
    def __init__(self):
        """Initialize the AWS SES service."""
        self.smtp_config = None
        self.recipients = None
        self._load_config()
    
    def _load_config(self):
        """Load SMTP configuration and recipients."""
        try:
            self.smtp_config = get_smtp_config()
            logger.info("AWS SES SMTP configuration loaded successfully")
            
            # Load recipients from JSON file only
            self.recipients = get_recipients()
            logger.info(f"Email recipients loaded from config file: {len(self.recipients)} recipients")
                
        except Exception as e:
            logger.error(f"Failed to load email configuration: {e}")
            raise
    
    def reload_config(self):
        """Reload configuration (useful for testing or config changes)."""
        self._load_config()
    
    async def send_email(
        self,
        subject: str,
        content: str,
        content_type: str = "html",
        sender_name: str = "Report Server",
        custom_recipients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send email using AWS SES SMTP.
        
        Args:
            subject: Email subject line
            content: Email body content
            content_type: "html" or "text" (default: "html")
            sender_name: Display name of sender
            custom_recipients: Optional custom recipients list (overrides default)
            
        Returns:
            Dict containing success status and response details
        """
        try:
            # Use custom recipients if provided, otherwise use configured recipients
            recipients = custom_recipients if custom_recipients else self.recipients
            
            if not recipients:
                raise ValueError("No email recipients configured")
            
            # Send email via SMTP
            result = await self._send_smtp_email(
                recipients=recipients,
                subject=subject,
                content=content,
                content_type=content_type,
                sender_name=sender_name
            )
            
            logger.info(f"Successfully sent email: {subject} to {len(recipients)} recipients")
            return {
                "success": True,
                "message": f"Email sent successfully to {len(recipients)} recipients",
                "recipients": recipients,
                "subject": subject,
                "sender": f"{sender_name} <{self.smtp_config['sender_email']}>",
                "content_type": content_type,
                "sent_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "이메일 전송 실패"
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
            # Create email subject
            subject = "📊 데일리 리포트"
            if report_date:
                subject += f" - {report_date}"
            
            # Create email content with summary and optional HTML
            email_content = self._create_daily_report_content(summary, html_content)
            
            # Send email
            return await self.send_email(
                subject=subject,
                content=email_content,
                content_type="html",
                sender_name=sender_name
            )
            
        except Exception as e:
            logger.error(f"Failed to send daily report email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "데일리 리포트 이메일 전송 실패"
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test SMTP connection to AWS SES.
        
        Returns:
            Dict containing connection test results
        """
        try:
            # Test with simple message
            test_result = await self.send_email(
                subject="🧪 이메일 연결 테스트",
                content="이것은 이메일 연결 테스트입니다.\n\n시스템이 정상적으로 작동하고 있습니다.",
                content_type="text",
                sender_name="System Test"
            )
            
            if test_result.get("success"):
                logger.info("Email connection test successful")
            else:
                logger.warning(f"Email connection test failed: {test_result.get('error')}")
            
            return test_result
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "이메일 연결 테스트 실패"
            }
    
    async def _send_smtp_email(
        self,
        recipients: List[str],
        subject: str,
        content: str,
        content_type: str,
        sender_name: str
    ) -> Dict[str, Any]:
        """
        Send email via SMTP.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            content: Email content
            content_type: Content type (html or text)
            sender_name: Sender display name
            
        Returns:
            Dict with send results
        """
        try:
            smtp_username = self.smtp_config['username']
            smtp_password = self.smtp_config['password']
            smtp_server = self.smtp_config['server']
            smtp_port = self.smtp_config['port']
            sender_email = self.smtp_config['sender_email']
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                
                for recipient in recipients:
                    # Create a fresh message for each recipient to avoid header duplication
                    message = MIMEMultipart('alternative')  # Support both plain and HTML
                    message['From'] = f'{sender_name} <{sender_email}>'
                    message['Subject'] = subject
                    message['To'] = recipient
                    
                    # Add body to email based on content type
                    if content_type == 'text':
                        # Plain text only
                        message.attach(MIMEText(content, 'plain'))
                    else:
                        # HTML format (default)
                        # Convert newlines to <br> for HTML
                        html_content = content.replace('\n', '<br>')
                        
                        # Also create a plain text version for better compatibility
                        plain_content = content  # Keep original with newlines
                        
                        # Attach both versions - email clients will choose the best one
                        message.attach(MIMEText(plain_content, 'plain'))
                        message.attach(MIMEText(html_content, 'html'))
                    
                    server.send_message(message)
            
            return {"success": True}
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _create_daily_report_content(self, summary: str, html_content: Optional[str] = None) -> str:
        """
        Create formatted email content for daily reports.
        
        Args:
            summary: The report summary text
            html_content: Optional full HTML report content
            
        Returns:
            Formatted HTML email content
        """
        # Basic HTML email template
        html_template = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>데일리 리포트</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .summary {{ padding: 30px; border-bottom: 1px solid #eee; }}
                .summary h2 {{ color: #333; font-size: 20px; margin-bottom: 15px; }}
                .summary-content {{ background-color: #f8f9fa; padding: 20px; border-radius: 6px; border-left: 4px solid #667eea; }}
                .report-section {{ padding: 30px; }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; background-color: #f8f9fa; border-radius: 0 0 8px 8px; }}
                pre {{ white-space: pre-wrap; word-wrap: break-word; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 편의점 데일리 리포트</h1>
                    <p>자동화된 매출 분석 보고서</p>
                </div>
                
                <div class="summary">
                    <h2>🔍 요약 분석</h2>
                    <div class="summary-content">
                        <pre>{summary}</pre>
                    </div>
                </div>
        """
        
        # Add HTML content if provided
        if html_content:
            html_template += f"""
                <div class="report-section">
                    <h2>📈 상세 리포트</h2>
                    <div style="border: 1px solid #ddd; border-radius: 6px; overflow: hidden;">
                        {html_content}
                    </div>
                </div>
            """
        
        # Close HTML template
        html_template += """
                <div class="footer">
                    <p>본 리포트는 자동으로 생성되었습니다.</p>
                    <p>Report MCP Server 📍 Direct AWS SES Integration</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template