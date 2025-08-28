"""Request models for the Report MCP Server."""

from typing import List, Optional, Union
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
