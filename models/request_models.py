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
