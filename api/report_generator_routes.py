"""Report generator API routes."""

import logging
from fastapi import APIRouter, HTTPException

from models.request_models import SummaryReportRequest, ComparisonAnalysisRequest
from services.report_generator_service import ReportGeneratorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp/tools/report-generator", tags=["report-generator"])


@router.post("/summary-report-html")
async def summary_report_html(request: SummaryReportRequest):
    """[SUMMARY_REPORT] Generate a summary report HTML with specified data type."""
    logger.info(f"summary_report_html 호출: data_type={request.data_type}, end_date={request.end_date}")
    logger.info(f"🔧 Raw request.stores: {request.stores} (type: {type(request.stores)})")
    
    try:
        # Normalize stores list
        logger.info(f"🔧 Before normalize_stores_list: {request.stores}")
        stores_list = ReportGeneratorService.normalize_stores_list(request.stores)
        logger.info(f"🔧 After normalize_stores_list: {stores_list} (length: {len(stores_list)})")
        
        # Generate report
        result = ReportGeneratorService.generate_summary_report(
            data_type=request.data_type or "visitor",
            end_date=request.end_date,
            stores=stores_list,
            periods=(request.periods if request.periods else [1])
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Summary report generation 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {e}")


@router.post("/comparison-analysis-html")
async def comparison_analysis_html(request: ComparisonAnalysisRequest):
    """[COMPARISON_ANALYSIS] Generate a comparison analysis HTML report."""
    logger.info(f"comparison_analysis_html 호출: {request.end_date}")
    
    try:
        # Normalize stores list
        stores_list = ReportGeneratorService.normalize_stores_list(request.stores)
        
        # Generate report
        result = ReportGeneratorService.generate_comparison_analysis(
            stores=stores_list,
            end_date=request.end_date,
            period=request.period or 7,
            analysis_type=request.analysis_type or "all"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Comparison analysis generation 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"리포트 생성 실패: {e}")