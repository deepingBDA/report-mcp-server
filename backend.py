"""Report MCP Server - Backend Application."""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastmcp import FastMCP

from config.settings import setup_logging
from config.scheduler_config import validate_scheduler_config, print_config_summary
from api.base_routes import router as base_router
from api.report_generator_routes import router as report_generator_router
from api.report_viewer_routes import router as report_viewer_router
from api.report_summarizer_routes import router as report_summarizer_router
from api.scheduler_routes import router as scheduler_router
from api.daily_report_routes import router as daily_report_router
from api.mcp_tools_routes import router as mcp_tools_router
from libs.html_output_config import HTML_OUTPUT_ROOT
from scheduler.daily_report_scheduler import start_daily_scheduler, stop_daily_scheduler

# Import services for MCP tools
from scheduler.daily_report_scheduler import get_scheduler_status
from libs.html_output_config import HTML_OUTPUT_PATHS
from pathlib import Path
from services.report_generator_service import ReportGeneratorService
from models.request_models import SummaryReportRequest, ComparisonAnalysisRequest

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Report MCP Server...")
    
    # Validate scheduler configuration
    try:
        config_errors = validate_scheduler_config()
        if config_errors:
            logger.warning(f"Scheduler configuration issues: {config_errors}")
        else:
            logger.info("Scheduler configuration is valid")
        
        # Print configuration summary for debugging
        print_config_summary()
        
        # Start the daily report scheduler
        try:
            await start_daily_scheduler()
            logger.info("Daily report scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start daily report scheduler: {e}")
            # Don't fail the entire app if scheduler fails
            
    except Exception as e:
        logger.error(f"Startup configuration error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Report MCP Server...")
    try:
        await stop_daily_scheduler()
        logger.info("Daily report scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


# Create FastAPI app with lifespan manager
app = FastAPI(
    title="Report MCP Server",
    description="HTTP API server for visitor analysis reports with automated email delivery",
    version="4.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(base_router)
app.include_router(report_generator_router)
app.include_router(report_viewer_router)
app.include_router(report_summarizer_router)
app.include_router(scheduler_router)
app.include_router(daily_report_router)
app.include_router(mcp_tools_router)

# =============================================================================
# MCP SERVER SETUP
# =============================================================================

# Create MCP server
mcp = FastMCP(
    "Report MCP Server",
    description="MCP server for generating reports and sending emails",
)

# MCP Tools
@mcp.tool()
async def health_check():
    """Health check endpoint for the report server."""
    return {
        "status": "healthy",
        "message": "Report MCP Server is running"
    }

@mcp.tool()
async def summary_report_html(data_type: str = "visitor", end_date: str = None, stores: str = None, periods: list = None):
    """요약 리포트 HTML을 생성합니다.
    
    매개변수:
        data_type (str): 리포트 데이터 타입. 기본값: "visitor"
        end_date (str): 기준일 (YYYY-MM-DD 형식). None이면 어제 날짜 사용.
                       예: "2024-09-04"
        stores (str): 매장 목록 - 콤마로 구분된 문자열 또는 단일 매장명.
                     예: "매장1,매장2,매장3" 또는 "매장1"  
        periods (list): 분석 기간(일 단위). 요약 리포트는 [1, 7]만 지원.
                       기본값: [1]
    
    반환값:
        dict: HTML 파일 경로와 메타데이터가 포함된 리포트 생성 결과
    """
    try:
        # Create request model
        request = SummaryReportRequest(
            data_type=data_type,
            end_date=end_date,
            stores=stores,
            periods=periods or [1]
        )
        
        logger.info(f"summary_report_html 호출: data_type={request.data_type}, end_date={request.end_date}")
        
        # Normalize stores list
        stores_list = ReportGeneratorService.normalize_stores_list(request.stores)
        
        # Generate report
        result = ReportGeneratorService.generate_summary_report(
            data_type=request.data_type or "visitor",
            end_date=request.end_date,
            stores=stores_list,
            periods=(request.periods if request.periods else [1])
        )
        
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Error in summary_report_html: {str(e)}")
        return {
            "result": "error",
            "message": str(e)
        }

@mcp.tool()
async def comparison_analysis_html(stores: str, end_date: str, period: int = 7, analysis_type: str = "all"):
    """비교 분석 HTML 리포트를 생성합니다.
    
    매개변수:
        stores (str): 매장 목록 - 콤마로 구분된 문자열 (필수).
                     예: "매장1,매장2,매장3"
        end_date (str): 기준일 (YYYY-MM-DD 형식, 필수).
                       예: "2024-09-04"
        period (int): 분석 기간(일 단위). 비교 분석은 7일만 지원.
                     기본값: 7
        analysis_type (str): 분석 타입. 기본값: "all"
    
    반환값:
        dict: HTML 파일 경로와 메타데이터가 포함된 리포트 생성 결과
    """
    try:
        # Create request model
        request = ComparisonAnalysisRequest(
            stores=stores,
            end_date=end_date,
            period=period,
            analysis_type=analysis_type
        )
        
        logger.info(f"comparison_analysis_html 호출: stores={stores}, end_date={end_date}")
        
        # Normalize stores list
        stores_list = ReportGeneratorService.normalize_stores_list(request.stores)
        
        # Generate report
        result = ReportGeneratorService.generate_comparison_analysis(
            stores=stores_list,
            end_date=request.end_date,
            period=request.period or 7,
            analysis_type=request.analysis_type or "all"
        )
        
        return {"result": result}
        
    except Exception as e:
        logger.error(f"Error in comparison_analysis_html: {str(e)}")
        return {
            "result": "error", 
            "message": str(e)
        }

# Mount the MCP server
mcp.mount(app)

# Mount static files for HTML reports
reports_path = Path(HTML_OUTPUT_ROOT)
reports_path.mkdir(exist_ok=True)  # Ensure directory exists
app.mount("/reports", StaticFiles(directory=str(reports_path)), name="reports")

# Mount static files for web interface
static_path = Path("static")
static_path.mkdir(exist_ok=True)  # Ensure directory exists
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

logger.info("Report MCP Server application initialized")
logger.info(f"Static files mounted at /reports -> {reports_path}")
logger.info("New features: Report Summarization, Email Automation, Daily Scheduler")