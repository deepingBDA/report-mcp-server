"""Daily report API routes for generating and emailing reports."""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from services.daily_report_service import DailyReportService
from models.request_models import DailyReportResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp/tools", tags=["daily-report"])


@router.post("/daily-report-email", response_model=DailyReportResponse)
async def send_daily_report_email(
    report_date: Optional[str] = Query(
        default=None,
        description="리포트 날짜 (YYYY-MM-DD). 기본값: 어제 날짜"
    )
) -> DailyReportResponse:
    """
    [DAILY_REPORT_EMAIL] Generate daily report, summarize with GPT, and send via email.
    
    This endpoint performs the complete daily report workflow:
    1. Generate HTML report for specified date
    2. Summarize the report using GPT-4o-mini
    3. Send email with summary and full report
    
    Args:
        report_date: Date for report (YYYY-MM-DD). If not provided, uses yesterday.
        
    Returns:
        Success status with execution details and email information.
    """
    # Calculate default date if not provided
    if not report_date:
        report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"daily-report-email API 호출: report_date={report_date}")
    
    # Validate date format
    try:
        datetime.strptime(report_date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"Invalid date format: {report_date}")
        raise HTTPException(
            status_code=400,
            detail="올바르지 않은 날짜 형식입니다. YYYY-MM-DD 형식을 사용하세요."
        )
    
    try:
        # Initialize daily report service
        daily_service = DailyReportService()
        
        # Execute the complete workflow
        result = await daily_service.generate_and_send_daily_report(report_date)
        
        if result["success"]:
            logger.info(f"Daily report email sent successfully for {report_date}")
            
            return {
                "result": "success",
                "message": f"{report_date} 데일리 리포트가 성공적으로 생성되고 이메일로 전송되었습니다",
                "report_date": result["report_date"],
                "execution_time": result["execution_time"],
                "details": {
                    "summary_length": result["summary_length"],
                    "html_length": result["html_length"],
                    "email_recipients": result["email_recipients"]
                }
            }
        else:
            # Log the error but return structured response
            error_message = result.get("error", "Unknown error")
            step_failed = result.get("step_failed", "unknown")
            
            logger.error(f"Daily report failed at step '{step_failed}': {error_message}")
            
            return {
                "result": "failed",
                "message": f"데일리 리포트 처리 중 오류가 발생했습니다: {error_message}",
                "report_date": result["report_date"],
                "step_failed": step_failed,
                "error_details": error_message
            }
            
    except Exception as e:
        logger.error(f"Unexpected error in daily-report-email API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"데일리 리포트 처리 중 예상치 못한 오류가 발생했습니다: {str(e)}"
        )


@router.get("/daily-report-status", response_model=dict)
async def get_daily_report_status() -> dict:
    """
    [DAILY_REPORT_STATUS] Get the current status of daily report service.
    
    Returns service configuration and health status.
    """
    logger.info("daily-report-status API 호출")
    
    try:
        # Initialize service to check configuration
        daily_service = DailyReportService()
        
        return {
            "result": "success",
            "status": "healthy",
            "service": "daily-report-email",
            "configuration": {
                "data_type": daily_service.daily_config["data_type"],
                "max_tokens": daily_service.daily_config["max_tokens"],
                "sender_name": daily_service.daily_config["sender_name"],
                "include_html": daily_service.email_config["include_html"]
            }
        }
        
    except Exception as e:
        logger.error(f"Daily report status check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"데일리 리포트 서비스 상태 확인 실패: {str(e)}"
        )


