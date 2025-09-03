"""Daily report scheduler for automated email delivery."""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from config.scheduler_config import (
    get_scheduler_config,
    get_daily_report_config,
    get_plus_agent_config,
    get_email_config,
    validate_scheduler_config
)
from services.report_generator_service import ReportGeneratorService
from services.report_summarizer_service import ReportSummarizerService
from services.email_sender_service import EmailSenderService

logger = logging.getLogger(__name__)


class DailyReportScheduler:
    """Scheduler for automated daily report generation and email delivery."""
    
    def __init__(self):
        """Initialize the daily report scheduler."""
        self.scheduler = None
        self.is_running = False
        self.config = get_scheduler_config()
        self.daily_config = get_daily_report_config()
        self.email_config = get_email_config()
        
        # Initialize services
        self.report_generator = ReportGeneratorService()
        self.report_summarizer = ReportSummarizerService()
        self.email_sender = EmailSenderService()
    
    async def start_scheduler(self):
        """Start the scheduler with configured jobs."""
        try:
            # Validate configuration first
            errors = validate_scheduler_config()
            if errors:
                logger.error(f"Scheduler configuration errors: {errors}")
                raise ValueError(f"Configuration errors: {', '.join(errors)}")
            
            if not self.config["enabled"]:
                logger.info("Scheduler is disabled by configuration")
                return
            
            # Create scheduler
            timezone = pytz.timezone(self.config["timezone"])
            self.scheduler = AsyncIOScheduler(timezone=timezone)
            
            # Add daily report job if enabled
            if self.config["daily_report_enabled"]:
                await self._add_daily_report_job()
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Daily report scheduler started successfully")
            logger.info(f"Timezone: {self.config['timezone']}")
            logger.info(f"Daily report time: {self.config['daily_report_time']}")
            
            # Log next execution times
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                next_run = job.next_run_time
                logger.info(f"Next execution of '{job.id}': {next_run}")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def stop_scheduler(self):
        """Stop the scheduler."""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Daily report scheduler stopped")
    
    async def _add_daily_report_job(self):
        """Add daily report job to scheduler."""
        # Parse time
        time_parts = self.config["daily_report_time"].split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        # Create cron trigger for daily execution
        trigger = CronTrigger(hour=hour, minute=minute)
        
        # Add job
        self.scheduler.add_job(
            self._execute_daily_report,
            trigger=trigger,
            id="daily_report",
            name="Daily Report Generation and Email",
            misfire_grace_time=300,  # 5 minutes grace time
            coalesce=True,  # Combine missed executions
            max_instances=1  # Only one instance at a time
        )
        
        logger.info(f"Added daily report job: execute at {hour:02d}:{minute:02d} daily")
    
    async def _execute_daily_report(self):
        """Execute daily report generation and email sending."""
        start_time = datetime.now()
        logger.info("=== Starting Daily Report Execution ===")
        
        try:
            # Calculate report date (previous day)
            report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            logger.info(f"Generating daily report for date: {report_date}")
            
            # Step 1: Generate report
            logger.info("Step 1: Generating summary report...")
            report_result = await self._generate_daily_report(report_date)
            
            if not report_result.get("success", False):
                logger.error(f"Report generation failed: {report_result}")
                await self._send_error_notification("보고서 생성 실패", report_result.get("error", "Unknown error"))
                return
            
            html_content = report_result.get("html_content")
            if not html_content:
                logger.error("Report generated but no HTML content received")
                await self._send_error_notification("보고서 생성 실패", "HTML 콘텐츠가 없습니다")
                return
            
            logger.info("Report generated successfully")
            
            # Step 2: Summarize report
            logger.info("Step 2: Summarizing report content...")
            summary_result = await self._summarize_report(html_content, report_date)
            
            if not summary_result.get("success", False):
                logger.error(f"Report summarization failed: {summary_result}")
                await self._send_error_notification("보고서 요약 실패", summary_result.get("error", "Unknown error"))
                return
            
            summary = summary_result.get("summary")
            if not summary:
                logger.error("Report summarized but no summary content received")
                await self._send_error_notification("보고서 요약 실패", "요약 콘텐츠가 없습니다")
                return
            
            logger.info("Report summarized successfully")
            
            # Step 3: Send email
            logger.info("Step 3: Sending email...")
            email_result = await self._send_daily_email(summary, html_content, report_date)
            
            if not email_result.get("success", False):
                logger.error(f"Email sending failed: {email_result}")
                await self._send_error_notification("이메일 전송 실패", email_result.get("error", "Unknown error"))
                return
            
            logger.info("Email sent successfully")
            
            # Success!
            execution_time = datetime.now() - start_time
            logger.info(f"=== Daily Report Execution Completed Successfully ===")
            logger.info(f"Execution time: {execution_time}")
            logger.info(f"Report date: {report_date}")
            logger.info(f"Summary length: {len(summary)} characters")
            logger.info(f"HTML content length: {len(html_content)} characters")
            
        except Exception as e:
            logger.error(f"Daily report execution failed: {e}")
            logger.error(traceback.format_exc())
            await self._send_error_notification("데일리 리포트 실행 실패", str(e))
    
    async def _generate_daily_report(self, report_date: str) -> Dict[str, Any]:
        """Generate daily report using ReportGeneratorService."""
        try:
            result = self.report_generator.generate_summary_report(
                data_type=self.daily_config["data_type"],
                end_date=report_date,
                stores=self.daily_config["stores"],
                periods=self.daily_config["periods"][0]
            )
            
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
        """Summarize report using ReportSummarizerService."""
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
    
    async def _send_daily_email(
        self,
        summary: str,
        html_content: Optional[str],
        report_date: str
    ) -> Dict[str, Any]:
        """Send daily email using EmailSenderService."""
        try:
            # Include HTML content if configured
            html_to_include = html_content if self.email_config["include_html"] else None
            
            result = await self.email_sender.send_daily_report_email(
                summary=summary,
                html_content=html_to_include,
                report_date=report_date,
                sender_name=self.daily_config["sender_name"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_error_notification(self, error_type: str, error_message: str):
        """Send error notification email."""
        try:
            subject = f"🚨 {error_type}"
            content = f"""
데일리 리포트 자동화 시스템에서 오류가 발생했습니다.

오류 유형: {error_type}
오류 메시지: {error_message}
발생 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

시스템 관리자에게 문의하시기 바랍니다.
            """.strip()
            
            await self.email_sender.send_custom_email(
                subject=subject,
                content=content,
                content_type="text",
                sender_name="System Error Bot"
            )
            
            logger.info(f"Error notification sent: {error_type}")
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    async def test_daily_report_execution(self) -> Dict[str, Any]:
        """Test daily report execution manually (for debugging)."""
        logger.info("=== Testing Daily Report Execution ===")
        
        try:
            # Use today's date for testing
            test_date = datetime.now().strftime("%Y-%m-%d")
            
            # Execute the same flow as scheduled job
            await self._execute_daily_report()
            
            return {
                "success": True,
                "message": "Test execution completed successfully",
                "test_date": test_date
            }
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Test execution failed"
            }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and job information."""
        if not self.scheduler:
            return {
                "running": False,
                "message": "Scheduler not initialized"
            }
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "running": self.is_running,
            "timezone": str(self.scheduler.timezone),
            "jobs": jobs,
            "config": {
                "enabled": self.config["enabled"],
                "daily_report_enabled": self.config["daily_report_enabled"],
                "daily_report_time": self.config["daily_report_time"]
            }
        }


# Global scheduler instance
_daily_scheduler: Optional[DailyReportScheduler] = None


async def get_scheduler() -> DailyReportScheduler:
    """Get or create the global scheduler instance."""
    global _daily_scheduler
    if _daily_scheduler is None:
        _daily_scheduler = DailyReportScheduler()
    return _daily_scheduler


async def start_daily_scheduler():
    """Start the daily report scheduler."""
    scheduler = await get_scheduler()
    await scheduler.start_scheduler()


async def stop_daily_scheduler():
    """Stop the daily report scheduler."""
    scheduler = await get_scheduler()
    await scheduler.stop_scheduler()


async def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status."""
    scheduler = await get_scheduler()
    return scheduler.get_scheduler_status()


async def test_scheduler_execution() -> Dict[str, Any]:
    """Test scheduler execution manually."""
    scheduler = await get_scheduler()
    return await scheduler.test_daily_report_execution()