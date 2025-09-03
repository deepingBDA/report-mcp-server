"""Report summarizer API routes."""

import logging
from fastapi import APIRouter, HTTPException

from models.request_models import ReportSummarizerRequest
from services.report_summarizer_service import ReportSummarizerService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp/tools/report-summarizer", tags=["report-summarizer"])


@router.post("/summarize-report")
async def summarize_report(request: ReportSummarizerRequest):
    """[REPORT_SUMMARIZER] Summarize HTML or JSON report content using OpenAI GPT."""
    logger.info(f"summarize_report 호출: report_type={request.report_type}")
    
    try:
        # Validate input - either html_content or json_data must be provided
        if not request.html_content and not request.json_data:
            raise HTTPException(
                status_code=400, 
                detail="html_content 또는 json_data 중 하나는 반드시 제공되어야 합니다"
            )
        
        if request.html_content and request.json_data:
            raise HTTPException(
                status_code=400,
                detail="html_content와 json_data는 동시에 제공할 수 없습니다"
            )
        
        # Initialize summarizer service
        summarizer = ReportSummarizerService()
        
        # Process based on content type
        if request.html_content:
            result = summarizer.summarize_html_report(
                html_content=request.html_content,
                report_type=request.report_type,
                max_tokens=request.max_tokens
            )
        else:
            result = summarizer.summarize_json_data(
                json_data=request.json_data,
                report_type=request.report_type,
                max_tokens=request.max_tokens
            )
        
        # Check if summarization was successful
        if not result.get("success", False):
            logger.error(f"Summarization failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail=f"리포트 요약 실패: {result.get('error', 'Unknown error')}"
            )
        
        logger.info(f"Successfully summarized {request.report_type} report")
        
        return {
            "result": "success",
            "summary": result["summary"],
            "metadata": {
                "report_type": result["report_type"],
                "tokens_used": result.get("tokens_used"),
                "content_length": result.get("original_content_length") or result.get("data_size"),
                "processing_info": {
                    "extracted_content_length": result.get("extracted_content_length"),
                    "model": "gpt-4o-mini"
                }
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Report summarization 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=f"리포트 요약 실패: {e}")


@router.get("/health")
async def health_check():
    """Health check endpoint for report summarizer."""
    try:
        # Simple check to ensure OpenAI client can be initialized
        summarizer = ReportSummarizerService()
        return {
            "status": "healthy",
            "service": "report-summarizer",
            "model": "gpt-4o-mini"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"서비스 상태 확인 실패: {e}"
        )