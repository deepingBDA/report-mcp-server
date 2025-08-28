"""Report MCP Server - Backend Application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import setup_logging
from api.base_routes import router as base_router
from api.workflow_routes import router as workflow_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Report MCP Server",
    description="Simple HTTP API server for visitor and comparison analysis workflows",
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
app.include_router(workflow_router)

logger.info("Report MCP Server application initialized")