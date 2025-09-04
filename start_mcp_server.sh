#!/bin/bash

# Start MCP Server for Report Generation
# This runs separately from the main REST API server

echo "🚀 Starting Report MCP Server..."
echo "📍 MCP Server will run on default FastMCP port"
echo "🌐 REST API Server should be running on http://localhost:8002"
echo ""

# Set environment variables
export REST_API_BASE_URL="http://localhost:8002"

# Check if REST API server is running
echo "🔍 Checking if REST API server is running..."
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✅ REST API server is running"
else
    echo "❌ REST API server is not running on port 8002"
    echo "💡 Please start the REST API server first:"
    echo "   python -m uvicorn backend:app --host 0.0.0.0 --port 8002"
    exit 1
fi

echo ""
echo "🎯 Starting MCP Server..."
echo "📝 Available MCP tools:"
echo "   - generate_daily_report_email"
echo "   - generate_summary_report"
echo "   - generate_comparison_report" 
echo "   - health_check"
echo ""

# Start the MCP server
fastmcp dev mcp_server.py