"""Report MCP Server - Backend Application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import setup_logging
from api.base_routes import router as base_router
from api.report_generator_routes import router as report_generator_router

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

logger.info("Report MCP Server application initialized")