"""Base API routes for health checks and server info."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def root():
    """루트 엔드포인트."""
    return {
        "message": "Report MCP Server",
        "version": "4.0.0",
        "endpoints": [
            "/mcp/tools/workflow/summary-report-html",
            "/mcp/tools/workflow/comparison-analysis-html"
        ]
    }


@router.get("/health")
async def health_check():
    """서버 상태 확인."""
    return {"status": "healthy", "message": "Report MCP Server is running"}