"""Email sender service for calling plus-agent-llm-server email functionality."""

import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class EmailSenderService:
    """Service class for sending emails via plus-agent-llm-server."""
    
    def __init__(self):
        """Initialize the email sender service."""
        self.plus_agent_url = os.getenv("PLUS_AGENT_URL", "http://plus-agent-llm-server:8000")
        self.email_endpoint = f"{self.plus_agent_url}/mcp/tools/send-email"
        self.timeout = 120.0  # Increase timeout to 2 minutes for heavy report processing
    
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
            email_content = self._create_email_content(summary, html_content)
            
            # Prepare request payload
            payload = {
                "topic": subject,
                "content": email_content,
                "sender_name": sender_name,
                "content_type": "html"
            }
            
            # Send email via plus-agent-llm-server
            result = await self._send_email_request(payload)
            
            logger.info(f"Successfully sent daily report email: {subject}")
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
            # Prepare request payload
            payload = {
                "topic": subject,
                "content": content,
                "sender_name": sender_name,
                "content_type": content_type
            }
            
            # Send email via plus-agent-llm-server
            result = await self._send_email_request(payload)
            
            logger.info(f"Successfully sent custom email: {subject}")
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
        Test email connection to plus-agent-llm-server.
        
        Returns:
            Dict containing connection test results
        """
        try:
            # Simple test message
            payload = {
                "topic": "🧪 이메일 연결 테스트",
                "content": "이것은 이메일 연결 테스트입니다.\n\n시스템이 정상적으로 작동하고 있습니다.",
                "sender_name": "System Test",
                "content_type": "text"
            }
            
            # Test connection
            result = await self._send_email_request(payload)
            
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
    
    async def _send_email_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send HTTP request to plus-agent-llm-server email endpoint.
        
        Args:
            payload: Email payload to send
            
        Returns:
            Dict containing response from email service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.email_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                
                logger.debug(f"Email service response: {result}")
                return {
                    "success": True,
                    "response": result,
                    "message": "이메일 전송 성공"
                }
                
        except httpx.TimeoutException:
            error_msg = f"Email service timeout after {self.timeout}s"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Email service HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except httpx.RequestError as e:
            error_msg = f"Email service connection error: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error calling email service: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _create_email_content(self, summary: str, html_content: Optional[str] = None) -> str:
        """
        Create formatted email content with summary and optional HTML.
        
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
                    <p>Report MCP Server 📍 Plus Agent LLM Server</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template