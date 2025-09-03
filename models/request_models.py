"""Request models for the Report MCP Server."""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class SummaryReportRequest(BaseModel):
    """Request model for summary report workflow."""
    data_type: Optional[str] = Field(default="visitor", description="데이터 타입")
    end_date: str = Field(description="기준일 (YYYY-MM-DD)")
    stores: Union[str, List[str]] = Field(description="매장 목록 (문자열 콤마 구분 또는 리스트)")
    periods: Optional[List[int]] = Field(default=None, description="분석 기간 목록")


class ComparisonAnalysisRequest(BaseModel):
    """Request model for comparison analysis workflow."""
    stores: Union[str, List[str]] = Field(description="매장 목록 (문자열 콤마 구분 또는 리스트)")
    end_date: str = Field(description="기준일 (YYYY-MM-DD)")
    period: Optional[int] = Field(default=7, description="분석 기간 (일)")
    analysis_type: Optional[str] = Field(default="all", description="분석 타입")


class ReportSummarizerRequest(BaseModel):
    """Request model for report summarizer."""
    html_content: Optional[str] = Field(default=None, description="HTML 리포트 콘텐츠")
    json_data: Optional[Dict[str, Any]] = Field(default=None, description="JSON 리포트 데이터")
    report_type: Optional[str] = Field(default="daily_report", description="리포트 타입")
    max_tokens: Optional[int] = Field(default=500, description="요약 최대 토큰 수")


class DailyReportEmailRequest(BaseModel):
    """Request model for daily report email workflow."""
    report_date: Optional[str] = Field(default=None, description="리포트 날짜 (YYYY-MM-DD). 기본값: 어제 날짜")


class DailyReportTestRequest(BaseModel):
    """Request model for daily report testing."""
    use_sample_data: Optional[bool] = Field(default=False, description="Use sample data instead of real database query")


class SchedulerConfigResponse(BaseModel):
    """Response model for scheduler configuration."""
    result: str = Field(description="결과 상태")
    status: Optional[Dict[str, Any]] = Field(default=None, description="스케줄러 상태 정보")
    config: Optional[Dict[str, Any]] = Field(default=None, description="스케줄러 설정")


class DailyReportResponse(BaseModel):
    """Response model for daily report operations."""
    result: str = Field(description="결과 상태 (success/failed)")
    message: str = Field(description="결과 메시지")
    report_date: Optional[str] = Field(default=None, description="리포트 날짜")
    execution_time: Optional[str] = Field(default=None, description="실행 시간")
    step_failed: Optional[str] = Field(default=None, description="실패한 단계")
    error_details: Optional[str] = Field(default=None, description="에러 상세 정보")
    details: Optional[Dict[str, Any]] = Field(default=None, description="추가 실행 정보")


class EmailServiceResponse(BaseModel):
    """Response model for email service operations."""
    success: bool = Field(description="이메일 전송 성공 여부")
    message: Optional[str] = Field(default=None, description="결과 메시지")
    recipients: Optional[List[str]] = Field(default=None, description="수신자 목록")
    response: Optional[Dict[str, Any]] = Field(default=None, description="이메일 서비스 응답")
