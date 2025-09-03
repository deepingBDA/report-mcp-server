"""Daily report service for generating and sending daily reports via email."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import traceback

from services.report_generator_service import ReportGeneratorService
from services.report_summarizer_service import ReportSummarizerService
from services.email_sender_service import EmailSenderService
from config.scheduler_config import get_daily_report_config, get_email_config

logger = logging.getLogger(__name__)


class DailyReportService:
    """Service for generating, summarizing, and emailing daily reports."""
    
    def __init__(self):
        """Initialize the daily report service."""
        self.report_generator = ReportGeneratorService()
        self.report_summarizer = ReportSummarizerService()
        self.email_sender = EmailSenderService()
        self.daily_config = get_daily_report_config()
        self.email_config = get_email_config()
    
    async def generate_and_send_daily_report(
        self, 
        report_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate, summarize, and send daily report via email.
        
        Args:
            report_date: Date for report (YYYY-MM-DD). If None, uses yesterday.
            
        Returns:
            Dict containing success status and details
        """
        start_time = datetime.now()
        
        # Use yesterday if no date provided
        if not report_date:
            report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        logger.info(f"=== Starting Daily Report Generation for {report_date} ===")
        
        try:
            # Step 1: Generate report
            logger.info("Step 1: Generating HTML report...")
            report_result = await self._generate_report(report_date)
            
            if not report_result["success"]:
                error_msg = f"Report generation failed: {report_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "step_failed": "report_generation",
                    "report_date": report_date
                }
            
            html_content = report_result["html_content"]
            logger.info(f"Report generated successfully (Size: {len(html_content)} chars)")
            
            # Step 2: Summarize report
            logger.info("Step 2: Summarizing report with GPT...")
            summary_result = await self._summarize_report(html_content, report_date)
            
            if not summary_result["success"]:
                error_msg = f"Report summarization failed: {summary_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "step_failed": "summarization",
                    "report_date": report_date
                }
            
            summary = summary_result["summary"]
            logger.info(f"Report summarized successfully (Size: {len(summary)} chars)")
            
            # Step 3: Send email
            logger.info("Step 3: Sending email...")
            email_result = await self._send_email(summary, html_content, report_date)
            
            if not email_result["success"]:
                error_msg = f"Email sending failed: {email_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "step_failed": "email_sending",
                    "report_date": report_date
                }
            
            # Success!
            execution_time = datetime.now() - start_time
            logger.info(f"=== Daily Report Completed Successfully ===")
            logger.info(f"Execution time: {execution_time}")
            
            return {
                "success": True,
                "report_date": report_date,
                "execution_time": str(execution_time),
                "summary_length": len(summary),
                "html_length": len(html_content),
                "email_recipients": email_result.get("recipients", []),
                "message": f"Daily report for {report_date} sent successfully"
            }
            
        except Exception as e:
            logger.error(f"Daily report generation failed: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e),
                "step_failed": "unexpected_error",
                "report_date": report_date
            }
    
    async def _generate_report(self, report_date: str) -> Dict[str, Any]:
        """Generate HTML report via HTTP API."""
        import httpx
        import json
        
        try:
            # Report Server의 자체 API 호출
            url = "http://localhost:8002/mcp/tools/report-generator/summary-report-html"
            
            payload = {
                "data_type": self.daily_config["data_type"],
                "end_date": report_date,
                "stores": self.daily_config["stores"],
                "periods": [self.daily_config["periods"][0]]  # List[int] 형태로 전송
            }
            
            logger.info(f"📤 Daily Report HTML 요청 중...")
            logger.info(f"   URL: {url}")
            logger.info(f"   Data: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                return {
                    "success": result.get("result") == "success",
                    "html_content": result.get("html_content"),
                    "error": None if result.get("result") == "success" else "Report generation failed"
                }
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {
                "success": False,
                "html_content": None,
                "error": str(e)
            }
    
    async def _summarize_report(self, html_content: str, report_date: str) -> Dict[str, Any]:
        """Summarize report using GPT."""
        try:
            result = self.report_summarizer.summarize_html_report(
                html_content=html_content,
                report_type=f"daily_report_{report_date}",
                max_tokens=self.daily_config["max_tokens"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Report summarization error: {e}")
            return {
                "success": False,
                "summary": None,
                "error": str(e)
            }
    
    async def _send_email(
        self,
        summary: str,
        html_content: str,
        report_date: str
    ) -> Dict[str, Any]:
        """Send email with summary and optional HTML content."""
        try:
            # Include HTML content if configured
            html_to_include = html_content if self.email_config["include_html"] else None
            
            result = await self.email_sender.send_daily_report_email(
                summary=summary,
                html_content=html_to_include,
                report_date=report_date,
                sender_name=self.daily_config["sender_name"]
            )
            
            if result.get("success"):
                # Extract recipients from nested response
                response = result.get("response", {})
                recipients = response.get("recipients", [])
                
                return {
                    "success": True,
                    "recipients": recipients,
                    "error": None
                }
            else:
                return result
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {
                "success": False,
                "error": str(e)
            }