"""Daily report scheduler for automated email delivery."""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import traceback
import httpx

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
        
        # Initialize email service for testing
        self.email_sender = EmailSenderService()
        
        # API endpoint URL for daily report
        self.daily_report_url = "http://localhost:8002/mcp/tools/daily-report-email"
    
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
        """Execute daily report by calling the API endpoint."""
        start_time = datetime.now()
        logger.info("=== Starting Daily Report Execution via API ===")
        
        try:
            # Calculate report date (previous day)
            report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            logger.info(f"Calling daily report API for date: {report_date}")
            
            # Call the daily report API endpoint
            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout
                response = await client.post(
                    self.daily_report_url,
                    params={"report_date": report_date}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("result") == "success":
                        execution_time = datetime.now() - start_time
                        logger.info(f"=== Daily Report API Call Completed Successfully ===")
                        logger.info(f"Execution time: {execution_time}")
                        logger.info(f"Report date: {report_date}")
                        logger.info(f"API Response: {result.get('message')}")
                        
                        # Log additional details if available
                        details = result.get("details", {})
                        if details:
                            logger.info(f"Summary length: {details.get('summary_length')} characters")
                            logger.info(f"HTML length: {details.get('html_length')} characters")
                            logger.info(f"Email recipients: {details.get('email_recipients')}")
                    else:
                        error_msg = result.get("message", "API call failed")
                        logger.error(f"Daily report API failed: {error_msg}")
                        await self._send_error_notification("API 호출 실패", error_msg)
                        
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Daily report API call failed: {error_msg}")
                    await self._send_error_notification("API 호출 실패", error_msg)
                    
        except httpx.TimeoutException:
            error_msg = "API call timed out after 5 minutes"
            logger.error(f"Daily report API timeout: {error_msg}")
            await self._send_error_notification("API 타임아웃", error_msg)
            
        except Exception as e:
            logger.error(f"Daily report execution failed: {e}")
            logger.error(traceback.format_exc())
            await self._send_error_notification("데일리 리포트 실행 실패", str(e))
    
    
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
        """Test daily report execution manually by calling API endpoint."""
        logger.info("=== Testing Daily Report Execution via API ===")
        
        try:
            # Use yesterday's date for testing
            test_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Call the daily report API endpoint
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    self.daily_report_url,
                    params={"report_date": test_date}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "success": result.get("result") == "success",
                        "message": "Test execution completed",
                        "test_date": test_date,
                        "api_response": result
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "message": "Test execution failed",
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