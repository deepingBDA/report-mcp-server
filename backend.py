"""Report MCP Server - Backend Application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config.settings import setup_logging
from api.base_routes import router as base_router
from api.report_generator_routes import router as report_generator_router
from api.report_viewer_routes import router as report_viewer_router
from libs.html_output_config import HTML_OUTPUT_ROOT

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Report MCP Server",
    description="Simple HTTP API server for visitor and comparison analysis reports",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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