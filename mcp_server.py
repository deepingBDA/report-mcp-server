#!/usr/bin/env python3
"""
Report MCP Server
MCP server for daily report generation and management
"""

import asyncio
import json
import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP("Report MCP Server")

# Base URL for the REST API server
BASE_URL = os.getenv("REST_API_BASE_URL", "http://localhost:8002")

@mcp.tool()
async def generate_daily_report_email(
    data_type: str = "visitor",
    end_date: Optional[str] = None,
    stores: str = "all",
    periods: List[int] = [1]
) -> Dict[str, Any]:
    """
    Generate and send daily report email
    
    Args:
        data_type: Type of data to analyze (visitor, sales, etc.)
        end_date: End date for the report (YYYY-MM-DD format, defaults to yesterday)
        stores: Store selection ('all' for all stores, or specific store names)
        periods: Analysis periods in days (default: [1] for daily)
    
    Returns:
        Dict containing result status and details
    """
    if end_date is None:
        end_date = (date.today()).strftime("%Y-%m-%d")
    
    payload = {
        "data_type": data_type,
        "end_date": end_date,
        "stores": stores,
        "periods": periods
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp/tools/daily-report-email",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {
                "result": "failed",
                "error": f"Request failed: {str(e)}",
                "message": "Failed to connect to report server"
            }
        except httpx.HTTPStatusError as e:
            return {
                "result": "failed", 
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "message": "Report generation failed"
            }

@mcp.tool()
async def generate_summary_report(
    data_type: str = "visitor",
    end_date: Optional[str] = None,
    stores: str = "all", 
    periods: List[int] = [1]
) -> Dict[str, Any]:
    """
    Generate summary report HTML
    
    Args:
        data_type: Type of data to analyze (visitor, sales, etc.)
        end_date: End date for the report (YYYY-MM-DD format, defaults to yesterday)
        stores: Store selection ('all' for all stores, or specific store names)  
        periods: Analysis periods in days (default: [1] for daily)
    
    Returns:
        Dict containing HTML content and metadata
    """
    if end_date is None:
        end_date = (date.today()).strftime("%Y-%m-%d")
    
    payload = {
        "data_type": data_type,
        "end_date": end_date,
        "stores": stores,
        "periods": periods
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp/tools/report-generator/summary-report-html",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {
                "result": "failed",
                "error": f"Request failed: {str(e)}",
                "message": "Failed to connect to report server"
            }
        except httpx.HTTPStatusError as e:
            return {
                "result": "failed",
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "message": "Report generation failed"
            }

@mcp.tool()
async def generate_comparison_report(
    stores: str = "all",
    end_date: Optional[str] = None,
    period: int = 7,
    analysis_type: str = "performance"
) -> Dict[str, Any]:
    """
    Generate comparison analysis report
    
    Args:
        stores: Store selection ('all' for all stores, or specific store names)
        end_date: End date for the report (YYYY-MM-DD format, defaults to today)
        period: Analysis period in days (default: 7)
        analysis_type: Type of analysis (performance, trend, etc.)
    
    Returns:
        Dict containing HTML content and metadata
    """
    if end_date is None:
        end_date = (date.today()).strftime("%Y-%m-%d")
    
    payload = {
        "stores": stores,
        "end_date": end_date,
        "period": period,
        "analysis_type": analysis_type
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/mcp/tools/report-generator/comparison-analysis",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {
                "result": "failed",
                "error": f"Request failed: {str(e)}",
                "message": "Failed to connect to report server"
            }
        except httpx.HTTPStatusError as e:
            return {
                "result": "failed",
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "message": "Report generation failed"
            }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Check health status of the report server
    
    Returns:
        Dict containing health status and details
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/health",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {
                "result": "failed",
                "error": f"Request failed: {str(e)}",
                "message": "Failed to connect to report server"
            }
        except httpx.HTTPStatusError as e:
            return {
                "result": "failed",
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "message": "Health check failed"
            }

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()