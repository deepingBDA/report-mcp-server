"""Report MCP Server - Backend Application."""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config.settings import setup_logging
from config.scheduler_config import validate_scheduler_config, print_config_summary
from api.base_routes import router as base_router
from api.report_generator_routes import router as report_generator_router
from api.report_viewer_routes import router as report_viewer_router
from api.report_summarizer_routes import router as report_summarizer_router
from api.scheduler_routes import router as scheduler_router
from libs.html_output_config import HTML_OUTPUT_ROOT
from scheduler.daily_report_scheduler import start_daily_scheduler, stop_daily_scheduler

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