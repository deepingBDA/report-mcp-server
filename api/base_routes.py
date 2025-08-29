"""Base API routes for health checks and server info."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/")
async def root():
    """루트 엔드포인트."""
    return {
        "message": "Report MCP Server",
        "version": "4.0.0",
        "endpoints": {
            "report_generation": [
                "/mcp/tools/report-generator/summary-report-html",
                "/mcp/tools/report-generator/comparison-analysis-html"
            ],
            "report_management": [
                "/api/reports/list",
                "/api/reports/latest/{report_type}",
                "/api/reports/types"
            ],
            "web_interface": [
                "/static/index.html - 리포트 뷰어",
                "/reports/ - 생성된 리포트 파일들"
            ]
        }
    }


@router.get("/viewer")
async def report_viewer():
    """리포트 뷰어로 리다이렉트."""
    return RedirectResponse(url="/static/index.html")


@router.get("/health")
async def health_check():
    """서버 상태 확인."""
    return {"status": "healthy", "message": "Report MCP Server is running"}