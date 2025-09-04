#!/usr/bin/env python3
"""
Report MCP Server
Standard MCP JSON-RPC server for daily report generation and management
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Request, HTTPException
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app for MCP server
app = FastAPI(title="Report MCP Server")

# Base URL for the REST API server
BASE_URL = os.getenv("REST_API_BASE_URL", "http://localhost:8002")

# MCP Server capabilities and tools
MCP_TOOLS = [
    {
        "name": "generate_daily_report_email",
        "description": "Generate and send daily report email",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data_type": {
                    "type": "string",
                    "description": "Type of data to analyze (visitor, sales, etc.)",
                    "default": "visitor"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for the report (YYYY-MM-DD format, defaults to yesterday)"
                },
                "stores": {
                    "type": "string", 
                    "description": "Store selection ('all' for all stores, or specific store names)",
                    "default": "all"
                },
                "periods": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Analysis periods in days (default: [1] for daily)",
                    "default": [1]
                }
            }
        }
    },
    {
        "name": "generate_summary_report",
        "description": "Generate summary report HTML",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data_type": {
                    "type": "string",
                    "description": "Type of data to analyze (visitor, sales, etc.)",
                    "default": "visitor"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for the report (YYYY-MM-DD format, defaults to yesterday)"
                },
                "stores": {
                    "type": "string",
                    "description": "Store selection ('all' for all stores, or specific store names)",
                    "default": "all"
                },
                "periods": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Analysis periods in days (default: [1] for daily)",
                    "default": [1]
                }
            }
        }
    },
    {
        "name": "generate_comparison_report",
        "description": "Generate comparison analysis report",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stores": {
                    "type": "string",
                    "description": "Store selection ('all' for all stores, or specific store names)",
                    "default": "all"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date for the report (YYYY-MM-DD format, defaults to today)"
                },
                "period": {
                    "type": "integer",
                    "description": "Analysis period in days (default: 7)",
                    "default": 7
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis (performance, trend, etc.)",
                    "default": "performance"
                }
            }
        }
    },
    {
        "name": "health_check",
        "description": "Check health status of the report server",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

# Tool implementation functions
async def generate_daily_report_email(
    data_type: str = "visitor",
    end_date: Optional[str] = None,
    stores: str = "all",
    periods: List[int] = [1]
) -> Dict[str, Any]:
    """Generate and send daily report email"""
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

async def generate_summary_report(
    data_type: str = "visitor",
    end_date: Optional[str] = None,
    stores: str = "all", 
    periods: List[int] = [1]
) -> Dict[str, Any]:
    """Generate summary report HTML"""
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

async def generate_comparison_report(
    stores: str = "all",
    end_date: Optional[str] = None,
    period: int = 7,
    analysis_type: str = "performance"
) -> Dict[str, Any]:
    """Generate comparison analysis report"""
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

async def health_check() -> Dict[str, Any]:
    """Check health status of the report server"""
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

# Tool mapping for execution
TOOL_FUNCTIONS = {
    "generate_daily_report_email": generate_daily_report_email,
    "generate_summary_report": generate_summary_report,
    "generate_comparison_report": generate_comparison_report,
    "health_check": health_check
}

# MCP JSON-RPC handlers
@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """Handle MCP JSON-RPC requests"""
    try:
        body = await request.json()
        
        # Validate JSON-RPC structure
        if not all(key in body for key in ["jsonrpc", "id", "method"]):
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC request")
        
        if body["jsonrpc"] != "2.0":
            raise HTTPException(status_code=400, detail="Unsupported JSON-RPC version")
        
        method = body["method"]
        params = body.get("params", {})
        request_id = body["id"]
        
        # Handle MCP protocol methods
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "Report MCP Server",
                    "version": "1.0.0"
                }
            }
        
        elif method == "tools/list":
            result = {
                "tools": MCP_TOOLS
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in TOOL_FUNCTIONS:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
            
            # Execute the tool
            tool_function = TOOL_FUNCTIONS[tool_name]
            tool_result = await tool_function(**arguments)
            
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(tool_result, indent=2)
                    }
                ]
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
        # Return JSON-RPC response
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return {
            "jsonrpc": "2.0", 
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }

if __name__ == "__main__":
    # Run the MCP server
    uvicorn.run(app, host="0.0.0.0", port=3000)