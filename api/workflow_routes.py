"""Workflow API routes."""

import logging
from fastapi import APIRouter, HTTPException

from models.request_models import SummaryReportRequest, ComparisonAnalysisRequest
from services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp/tools/workflow", tags=["workflow"])


@router.post("/summary-report-html")
async def summary_report_html(request: SummaryReportRequest):
    """[SUMMARY_REPORT] Generate a summary report HTML with specified data type."""
    logger.info(f"summary_report_html 호출: data_type={request.data_type}, end_date={request.end_date}")
    
    try:
        # Normalize stores list
        stores_list = WorkflowService.normalize_stores_list(request.stores)
        
        # Execute workflow
        result = WorkflowService.execute_summary_report(
            data_type=request.data_type or "visitor",
            end_date=request.end_date,
            stores=stores_list,
            periods=(request.periods[0] if request.periods else 1),
            user_prompt=request.user_prompt or "요약 리포트 생성(HTML)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Summary report workflow 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"워크플로우 실행 실패: {e}")


@router.post("/comparison-analysis-html")
async def comparison_analysis_html(request: ComparisonAnalysisRequest):
    """[COMPARISON_ANALYSIS] Generate a comparison analysis HTML report."""
    logger.info(f"comparison_analysis_html 호출: {request.end_date}")
    
    try:
        # Normalize stores list
        stores_list = WorkflowService.normalize_stores_list(request.stores)
        
        # Execute workflow
        result = WorkflowService.execute_comparison_analysis(
            stores=stores_list,
            end_date=request.end_date,
            period=request.period or 7,
            analysis_type=request.analysis_type or "all",
            user_prompt=request.user_prompt or "매장 비교 분석 리포트"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Comparison analysis workflow 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"워크플로우 실행 실패: {e}")