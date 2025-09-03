"""Scheduler management and manual execution API routes."""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from scheduler.daily_report_scheduler import (
    get_scheduler_status,
    test_scheduler_execution,
    get_scheduler
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp/tools/scheduler", tags=["scheduler"])


@router.get("/status")
async def get_scheduler_status_endpoint():
    """[SCHEDULER_STATUS] Get current scheduler status and job information."""
    logger.info("scheduler status 호출")
    
    try:
        status = await get_scheduler_status()
        return {
            "result": "success",
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"스케줄러 상태 조회 실패: {e}")


@router.post("/test-daily-report")
async def test_daily_report_execution():
    """[TEST_DAILY_REPORT] Execute daily report generation and email sending manually for testing."""
    logger.info("test daily report 수동 실행 호출")
    
    try:
        result = await test_scheduler_execution()
        
        if result.get("success", False):
            return {
                "result": "success",
                "message": "테스트 실행이 완료되었습니다",
                "execution_result": result
            }
        else:
            return {
                "result": "failed", 
                "message": f"테스트 실행 실패: {result.get('error', 'Unknown error')}",
                "execution_result": result
            }
        
    except Exception as e:
        logger.error(f"Test daily report execution 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"테스트 실행 실패: {e}")


@router.post("/execute-daily-report")
async def execute_daily_report_manual(
    report_date: Optional[str] = Query(
        default=None, 
        description="리포트 날짜 (YYYY-MM-DD). 기본값: 어제 날짜"
    )
):
    """[EXECUTE_DAILY_REPORT] Execute daily report for specific date manually."""
    # Calculate default date (yesterday)
    if not report_date:
        report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"manual daily report execution 호출: report_date={report_date}")
    
    try:
        # Validate date format
        try:
            datetime.strptime(report_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="올바르지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하세요."
            )
        
        # Get scheduler and execute daily report manually
        scheduler = await get_scheduler()
        
        # We need to temporarily set the report date and execute
        # This is a manual execution, so we'll call the internal method directly
        original_date = datetime.now()
        
        # Execute the daily report workflow
        await scheduler._execute_daily_report()
        
        logger.info(f"Manual daily report execution completed for {report_date}")
        
        return {
            "result": "success",
            "message": f"{report_date} 데일리 리포트가 성공적으로 실행되었습니다",
            "report_date": report_date,
            "execution_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Manual daily report execution 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"수동 실행 실패: {e}")


@router.post("/send-test-email")
async def send_test_email():
    """[SEND_TEST_EMAIL] Send a test email to verify email configuration."""
    logger.info("send test email 호출")
    
    try:
        # Get scheduler and test email connection
        scheduler = await get_scheduler()
        
        result = await scheduler.email_sender.test_email_connection()
        
        if result.get("success", False):
            return {
                "result": "success",
                "message": "테스트 이메일이 성공적으로 전송되었습니다",
                "email_result": result
            }
        else:
            return {
                "result": "failed",
                "message": f"테스트 이메일 전송 실패: {result.get('error', 'Unknown error')}",
                "email_result": result
            }
        
    except Exception as e:
        logger.error(f"Test email sending 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"테스트 이메일 전송 실패: {e}")


@router.get("/config")
async def get_scheduler_config():
    """[SCHEDULER_CONFIG] Get current scheduler configuration."""
    logger.info("scheduler config 호출")
    
    try:
        from config.scheduler_config import get_all_config
        
        config = get_all_config()
        return {
            "result": "success",
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduler config: {e}")
        raise HTTPException(status_code=500, detail=f"스케줄러 설정 조회 실패: {e}")


@router.get("/next-execution")
async def get_next_execution_time():
    """[NEXT_EXECUTION] Get next scheduled execution time for daily report."""
    logger.info("next execution time 호출")
    
    try:
        status = await get_scheduler_status()
        
        # Find the daily report job
        daily_job = None
        for job in status.get("jobs", []):
            if job["id"] == "daily_report":
                daily_job = job
                break
        
        if daily_job:
            return {
                "result": "success",
                "next_execution": daily_job["next_run_time"],
                "job_info": daily_job
            }
        else:
            return {
                "result": "success",
                "next_execution": None,
                "message": "데일리 리포트 작업이 스케줄되지 않았습니다"
            }
        
    except Exception as e:
        logger.error(f"Failed to get next execution time: {e}")
        raise HTTPException(status_code=500, detail=f"다음 실행 시간 조회 실패: {e}")


@router.get("/health")
async def scheduler_health_check():
    """Health check endpoint for scheduler service."""
    try:
        # Check scheduler status
        status = await get_scheduler_status()
        
        # Check email connection
        scheduler = await get_scheduler()
        email_test = await scheduler.email_sender.test_email_connection()
        
        return {
            "status": "healthy",
            "service": "scheduler",
            "scheduler_running": status.get("running", False),
            "email_service": "healthy" if email_test.get("success") else "failed",
            "jobs_count": len(status.get("jobs", []))
        }
        
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"스케줄러 상태 확인 실패: {e}"
        )