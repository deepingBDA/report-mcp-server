#!/usr/bin/env python3
"""
Report MCP Server
HTTP API server providing MCP tools for retail analytics and business intelligence
"""

import sys
from pathlib import Path

# Add current directory to Python path for mcp_tools imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uvicorn
import logging

# MCP tools imports  
from mcp_tools.utils.database_manager import get_site_client, get_all_sites, get_site_connection_info
from mcp_tools.utils.mcp_utils import is_token_limit_exceeded, DEFAULT_MODEL

# Import MCP modules
from mcp_tools.queries import mcp_diagnose_new

# Simple settings
class Settings:
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False

settings = Settings()

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Report MCP Server",
    description="Simple HTTP API server providing DA-agent MCP tools",
    version="3.0.0",
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

# Request models
class DateRangeRequest(BaseModel):
    start_date: str = Field(description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(description="종료 날짜 (YYYY-MM-DD)")
    site: str = Field(description="매장명")

class DatabaseDateRangeRequest(BaseModel):
    database: str = Field(description="데이터베이스명")
    start_date: str = Field(description="시작 날짜")
    end_date: str = Field(description="종료 날짜")
    site: str = Field(description="매장명")

class SiteRequest(BaseModel):
    site: str = Field(description="매장명")

class SiteValidationRequest(BaseModel):
    site: str = Field(description="검증할 매장명")

# ============= 간단한 조회 도구들 (GET) =============

@app.get("/mcp/tools/available-sites", tags=["agent"])
async def get_available_sites():
    """사용 가능한 모든 매장 목록을 조회합니다"""
    try:
        sites = get_all_sites()
        if not sites:
            return {"result": "사용 가능한 매장이 없습니다."}
        
        result = "📋 **사용 가능한 매장 목록:**\n\n"
        for i, site in enumerate(sites, 1):
            result += f"{i}. {site}\n"
        result += f"\n총 {len(sites)}개 매장이 등록되어 있습니다."
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"매장 목록 조회 실패: {e}")

@app.get("/mcp/tools/system-info", tags=["agent"])
async def get_system_info():
    """시스템 정보 및 상태를 조회합니다"""
    try:
        sites = get_all_sites()
        site_count = len(sites) if sites else 0
        
        result = f"""🔧 **시스템 정보**

📊 **데이터베이스 상태:**
- 등록된 매장 수: {site_count}개
- 시스템 상태: 정상

🛠️ **사용 가능한 기능:**
- POS 데이터 분석 (매출, 영수증, 행사 등)
- 인사이트 분석 (픽업 전환, 세일즈 퍼널 등)
- 선반 분석 (진열, 재고 등)
- 진단 도구 (데이터 품질 검사)
- 이메일 발송 기능

💡 매장별 분석을 시작하려면 먼저 /mcp/tools/available-sites로 매장 목록을 확인하세요."""
        
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 정보 조회 실패: {e}")

# ============= 복잡한 분석 도구들 (POST) =============

@app.post("/mcp/tools/pos/sales-statistics", tags=["pos"])
async def sales_statistics(request: DateRangeRequest):
    """POS 데이터 기반 매출 통계 요약"""
    logger.info(f"sales_statistics 호출: {request.site}, {request.start_date}~{request.end_date}")
    try:
        # TODO: 실제 로직 구현 필요
        result = f"sales_statistics 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/pos/receipt-ranking", tags=["pos"])
async def receipt_ranking(request: DateRangeRequest):
    """특정 매장의 POS 데이터 기반 영수증 건수 비중 Top 5 조회"""
    logger.info(f"receipt_ranking 호출: {request.site}, {request.start_date}~{request.end_date}")
    try:
        client = get_site_client(request.site, 'cu_base')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")

        query = f"""
WITH receipt_total AS (
    SELECT 
        store_nm,
        COUNT(DISTINCT (tran_ymd, pos_no, tran_no)) as total_receipts
    FROM cu_revenue_total
    WHERE tran_ymd BETWEEN '{request.start_date}' AND '{request.end_date}'
    GROUP BY store_nm
),
small_category_receipts AS (
    SELECT 
        store_nm,
        small_nm,
        COUNT(DISTINCT (tran_ymd, pos_no, tran_no)) as receipt_count,
        ROUND(COUNT(DISTINCT (tran_ymd, pos_no, tran_no)) * 100.0 / rt.total_receipts, 2) as receipt_ratio
    FROM cu_revenue_total
    JOIN receipt_total rt USING(store_nm)
    WHERE tran_ymd BETWEEN '{request.start_date}' AND '{request.end_date}'
    GROUP BY store_nm, small_nm, rt.total_receipts
),
ranked_categories AS (
    SELECT 
        store_nm,
        small_nm,
        receipt_count,
        receipt_ratio,
        ROW_NUMBER() OVER (PARTITION BY store_nm ORDER BY receipt_ratio DESC) as rank
    FROM small_category_receipts
)
SELECT 
    store_nm,
    MAX(IF(rank = 1, CONCAT(small_nm, ' (', toString(receipt_count), ', ', toString(receipt_ratio), '%)'), '')) as top1_small_nm,
    MAX(IF(rank = 2, CONCAT(small_nm, ' (', toString(receipt_count), ', ', toString(receipt_ratio), '%)'), '')) as top2_small_nm,
    MAX(IF(rank = 3, CONCAT(small_nm, ' (', toString(receipt_count), ', ', toString(receipt_ratio), '%)'), '')) as top3_small_nm,
    MAX(IF(rank = 4, CONCAT(small_nm, ' (', toString(receipt_count), ', ', toString(receipt_ratio), '%)'), '')) as top4_small_nm,
    MAX(IF(rank = 5, CONCAT(small_nm, ' (', toString(receipt_count), ', ', toString(receipt_ratio), '%)'), '')) as top5_small_nm
FROM ranked_categories
GROUP BY store_nm
ORDER BY store_nm
"""
        result = client.query(query)
        
        answer = f"🏪 **{request.site} 매장 영수증 랭킹 ({request.start_date} ~ {request.end_date}):**\n\n"
        answer += "(지점, 1위, 2위, 3위, 4위, 5위)"
        if len(result.result_rows) > 0:
            for row in result.result_rows:
                answer += f"\n{row}"
        else:
            answer += "\n데이터가 없습니다."

        logger.info(f"receipt_ranking 완료: {len(result.result_rows)}개 결과")
        return {"result": answer}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"receipt_ranking 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/pos/sales-ranking", tags=["pos"])
async def sales_ranking(request: DateRangeRequest):
    """POS 데이터 기반 총 매출 비중 Top 5 조회"""
    logger.info(f"sales_ranking 호출: {request.site}, {request.start_date}~{request.end_date}")
    try:
        client = get_site_client(request.site, 'cu_base')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")

        query = f"""
WITH store_total AS (
    SELECT 
        store_nm,
        SUM(sale_amt) as total_sales
    FROM cu_revenue_total
    WHERE tran_ymd BETWEEN '{request.start_date}' AND '{request.end_date}'
    GROUP BY store_nm
),
small_category_sales AS (
    SELECT 
        store_nm,
        small_nm,
        SUM(sale_amt) as category_sales,
        ROUND(SUM(sale_amt) * 100.0 / st.total_sales, 2) as sales_ratio
    FROM cu_revenue_total
    JOIN store_total st USING(store_nm)
    WHERE tran_ymd BETWEEN '{request.start_date}' AND '{request.end_date}'
    GROUP BY store_nm, small_nm, st.total_sales
),
ranked_categories AS (
    SELECT 
        store_nm,
        small_nm,
        category_sales,
        sales_ratio,
        ROW_NUMBER() OVER (PARTITION BY store_nm ORDER BY sales_ratio DESC) as rank
    FROM small_category_sales
)
SELECT 
    store_nm,
    MAX(IF(rank = 1, CONCAT(small_nm, ' (', toString(ROUND(category_sales/10000, 0)), '만원, ', toString(sales_ratio), '%)'), '')) as top1_small_nm,
    MAX(IF(rank = 2, CONCAT(small_nm, ' (', toString(ROUND(category_sales/10000, 0)), '만원, ', toString(sales_ratio), '%)'), '')) as top2_small_nm,
    MAX(IF(rank = 3, CONCAT(small_nm, ' (', toString(ROUND(category_sales/10000, 0)), '만원, ', toString(sales_ratio), '%)'), '')) as top3_small_nm,
    MAX(IF(rank = 4, CONCAT(small_nm, ' (', toString(ROUND(category_sales/10000, 0)), '만원, ', toString(sales_ratio), '%)'), '')) as top4_small_nm,
    MAX(IF(rank = 5, CONCAT(small_nm, ' (', toString(ROUND(category_sales/10000, 0)), '만원, ', toString(sales_ratio), '%)'), '')) as top5_small_nm
FROM ranked_categories
GROUP BY store_nm
ORDER BY store_nm
"""
        result = client.query(query)
        
        answer = "(지점, 1위, 2위, 3위, 4위, 5위)"
        if len(result.result_rows) > 0:
            for row in result.result_rows:
                answer += f"\n{row}"
        else:
            answer = "데이터가 없습니다."

        return {"result": answer}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/insight/pickup-transition", tags=["insight"])
async def pickup_transition(request: DatabaseDateRangeRequest):
    """픽업 구역 전환 데이터 조회"""
    logger.info(f"pickup_transition 호출: {request.site}, {request.database}")
    try:
        client = get_site_client(request.site, request.database)
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 실제 복잡한 쿼리 구현
        result = f"pickup_transition 호출됨: {request.site} ({request.database}), {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/validate-site", tags=["agent"])
async def validate_site(request: SiteValidationRequest):
    """특정 매장명이 유효한지 검증합니다"""
    try:
        sites = get_all_sites()
        if request.site in sites:
            result = f"✅ '{request.site}' 매장이 존재합니다."
        else:
            result = f"❌ '{request.site}' 매장을 찾을 수 없습니다.\n\n사용 가능한 매장:\n"
            for site in sites[:10]:  # 처음 10개만 표시
                result += f"- {site}\n"
            if len(sites) > 10:
                result += f"... 외 {len(sites) - 10}개 매장"
        
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"매장 검증 실패: {e}")

# ============= 진단 도구들 =============

@app.post("/mcp/tools/diagnose/db-name", tags=["diagnose"])
async def get_db_name(request: SiteRequest):
    """특정 매장의 데이터베이스명 조회"""
    try:
        connection_info = get_site_connection_info(request.site)
        if not connection_info:
            return {"result": f"❌ {request.site} 매장 정보를 찾을 수 없습니다."}
        
        db_name = connection_info.get('db_name', 'plusinsight')
        result = f"📋 **{request.site} 매장 정보:**\n데이터베이스명: {db_name}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 DB명 조회 실패: {e}")

@app.post("/mcp/tools/diagnose/avg-visitors", tags=["diagnose"])
async def diagnose_avg_visitors(request: DateRangeRequest):
    """방문객 진단 - 일평균 방문객수와 관련 트렌드 분석"""
    logger.info(f"diagnose_avg_visitors 호출: {request.site}")
    try:
        client = get_site_client(request.site, 'plusinsight')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 복잡한 방문객 진단 쿼리 구현
        result = f"방문객 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/diagnose/avg-sales", tags=["diagnose"])
async def diagnose_avg_sales(request: DateRangeRequest):
    """일평균 판매 건수 진단"""
    logger.info(f"diagnose_avg_sales 호출: {request.site}")
    try:
        client = get_site_client(request.site, 'cu_base')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 판매 건수 진단 쿼리 구현
        result = f"판매 건수 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/diagnose/zero-visits", tags=["diagnose"])
async def check_zero_visits(request: DateRangeRequest):
    """방문객수 데이터 이상 조회"""
    logger.info(f"check_zero_visits 호출: {request.site}")
    try:
        client = get_site_client(request.site, 'plusinsight')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 방문객수 데이터 이상 조회 쿼리 구현
        result = f"방문객수 데이터 이상 조회 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/diagnose/purchase-conversion", tags=["diagnose"])
async def diagnose_purchase_conversion(request: DateRangeRequest):
    """구매전환율 진단"""
    logger.info(f"diagnose_purchase_conversion 호출: {request.site}")
    try:
        # 여러 데이터베이스 필요
        client_insight = get_site_client(request.site, 'plusinsight')
        client_base = get_site_client(request.site, 'cu_base')
        
        if not client_insight or not client_base:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 구매전환율 진단 쿼리 구현
        result = f"구매전환율 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/diagnose/exploratory-tendency", tags=["diagnose"])
async def diagnose_exploratory_tendency(request: DateRangeRequest):
    """탐색 경향성 진단"""
    logger.info(f"diagnose_exploratory_tendency 호출: {request.site}")
    try:
        client = get_site_client(request.site, 'plusinsight')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 탐색 경향성 진단 쿼리 구현
        result = f"탐색 경향성 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/diagnose/shelf", tags=["diagnose"])
async def diagnose_shelf(request: DateRangeRequest):
    """진열대 진단"""
    logger.info(f"diagnose_shelf 호출: {request.site}")
    try:
        client = get_site_client(request.site, 'plusinsight')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 진열대 진단 쿼리 구현
        result = f"진열대 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/diagnose/table-occupancy", tags=["diagnose"])
async def diagnose_table_occupancy(request: DateRangeRequest):
    """시식대 혼잡도 진단"""
    logger.info(f"diagnose_table_occupancy 호출: {request.site}")
    try:
        client = get_site_client(request.site, 'plusinsight')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 시식대 혼잡도 진단 쿼리 구현
        result = f"시식대 혼잡도 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ClickHouse 도구들 =============

@app.post("/mcp/tools/clickhouse/show-databases", tags=["clickhouse"])
async def show_databases(request: SiteRequest):
    """데이터베이스 목록을 조회합니다"""
    logger.info(f"show_databases 호출: {request.site}")
    try:
        client = get_site_client(request.site, 'system')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 데이터베이스 목록 조회 쿼리 구현
        result = f"데이터베이스 목록 조회 호출됨: {request.site} 매장"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DatabaseRequest(BaseModel):
    database: str = Field(description="데이터베이스명")
    site: str = Field(description="매장명")

@app.post("/mcp/tools/clickhouse/show-tables", tags=["clickhouse"])
async def show_tables(request: DatabaseRequest):
    """특정 데이터베이스의 테이블 목록을 조회합니다"""
    logger.info(f"show_tables 호출: {request.site}, {request.database}")
    try:
        client = get_site_client(request.site, request.database)
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 테이블 목록 조회 쿼리 구현
        result = f"테이블 목록 조회 호출됨: {request.site} 매장, {request.database} 데이터베이스"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class QueryRequest(BaseModel):
    database: str = Field(description="데이터베이스명")
    query: str = Field(description="실행할 SQL 쿼리")
    site: str = Field(description="매장명")

@app.post("/mcp/tools/clickhouse/execute-query", tags=["clickhouse"])
async def execute_query(request: QueryRequest):
    """ClickHouse 쿼리를 실행합니다"""
    logger.info(f"execute_query 호출: {request.site}, {request.database}")
    try:
        client = get_site_client(request.site, request.database)
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # 보안을 위해 위험한 쿼리 차단
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
        if any(keyword.upper() in request.query.upper() for keyword in dangerous_keywords):
            raise HTTPException(status_code=403, detail="위험한 쿼리는 실행할 수 없습니다")
        
        # TODO: 안전한 쿼리 실행 구현
        result = f"쿼리 실행 호출됨: {request.site} 매장, {request.database} 데이터베이스\n쿼리: {request.query[:100]}..."
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateDatabaseRequest(BaseModel):
    database_name: str = Field(description="생성할 데이터베이스명")
    site: str = Field(description="매장명")

@app.post("/mcp/tools/clickhouse/create-database", tags=["clickhouse"])
async def create_database(request: CreateDatabaseRequest):
    """새 데이터베이스를 생성합니다"""
    logger.info(f"create_database 호출: {request.site}, {request.database_name}")
    try:
        client = get_site_client(request.site, 'system')
        if not client:
            raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
        
        # TODO: 데이터베이스 생성 쿼리 구현 (관리자 권한 필요)
        result = f"데이터베이스 생성 호출됨: {request.site} 매장, {request.database_name}"
        return {"result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= 인사이트 도구들 추가 =============

@app.post("/mcp/tools/insight/sales-funnel", tags=["insight"])
async def sales_funnel(request: DatabaseDateRangeRequest):
    """sales_funnel: 방문, 노출, 픽업의 전환율 조회"""
    try:
        # TODO: 세일즈 퍼널 분석 구현
        result = f"세일즈 퍼널 분석: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/insight/shelf-performance", tags=["insight"])
async def shelf_performance(request: DatabaseDateRangeRequest):
    """shelf_performance: 선반별 성과 지표 조회"""
    try:
        # TODO: 선반 성과 분석 구현
        result = f"선반 성과 분석: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/insight/customer-journey", tags=["insight"])
async def customer_journey(request: DatabaseDateRangeRequest):
    """customer_journey: 고객 여정 분석"""
    try:
        # TODO: 고객 여정 분석 구현
        result = f"고객 여정 분석: {request.site} 매장, {request.start_date}~{request.end_date}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= 선반 도구들 =============

class FlexibleShelfRequest(BaseModel):
    site: str = Field(description="매장명")
    start_date: Optional[str] = Field(default=None, description="시작 날짜")
    end_date: Optional[str] = Field(default=None, description="종료 날짜")
    analysis_type: Optional[str] = Field(default="basic", description="분석 유형")

@app.post("/mcp/tools/shelf/analysis-flexible", tags=["shelf"])
async def get_shelf_analysis_flexible(request: FlexibleShelfRequest):
    """선반 분석 - 유연한 파라미터"""
    try:
        # TODO: 유연한 선반 분석 구현
        result = f"선반 분석: {request.site} 매장, 유형: {request.analysis_type}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/shelf/pickup-gaze-summary", tags=["shelf"])
async def pickup_gaze_summary(request: FlexibleShelfRequest):
    """픽업 및 응시 요약"""
    try:
        # TODO: 픽업 응시 요약 구현
        result = f"픽업 응시 요약: {request.site} 매장"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= 리포트 생성 도구들 =============

class ReportRequest(BaseModel):
    site: str = Field(description="매장명") 
    report_type: str = Field(description="리포트 유형")
    start_date: Optional[str] = Field(default=None, description="시작 날짜")
    end_date: Optional[str] = Field(default=None, description="종료 날짜")
    additional_params: Optional[Dict[str, Any]] = Field(default=None, description="추가 파라미터")

@app.post("/mcp/tools/report/create-html", tags=["report"])
async def create_html_report(request: ReportRequest):
    """HTML 리포트 생성"""
    try:
        # TODO: HTML 리포트 생성 구현
        result = f"HTML 리포트 생성: {request.site} 매장, 유형: {request.report_type}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/report/analyze-data-structure", tags=["report"])
async def analyze_data_structure(request: ReportRequest):
    """데이터 구조 분석"""
    try:
        # TODO: 데이터 구조 분석 구현
        result = f"데이터 구조 분석: {request.site} 매장"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/report/create-from-clickhouse", tags=["report"])
async def create_report_from_clickhouse(request: ReportRequest):
    """ClickHouse 데이터로 리포트 생성"""
    try:
        # TODO: ClickHouse 리포트 생성 구현
        result = f"ClickHouse 리포트 생성: {request.site} 매장, 유형: {request.report_type}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CSVReportRequest(BaseModel):
    csv_path: str = Field(description="CSV 파일 경로")
    report_type: str = Field(description="리포트 유형")
    output_path: Optional[str] = Field(default=None, description="출력 경로")

@app.post("/mcp/tools/report/create-from-csv", tags=["report"])
async def create_report_from_csv(request: CSVReportRequest):
    """CSV 데이터로 리포트 생성"""
    try:
        # TODO: CSV 리포트 생성 구현
        result = f"CSV 리포트 생성: {request.csv_path}, 유형: {request.report_type}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= 이메일 도구들 =============

class EmailReportRequest(BaseModel):
    subject: str = Field(description="이메일 제목")
    html_path: str = Field(description="HTML 파일 경로")
    to_emails: Optional[List[str]] = Field(default=None, description="받는 사람 이메일 주소 목록")
    cc_emails: Optional[List[str]] = Field(default=None, description="참조 이메일 주소 목록")

@app.post("/mcp/tools/email/send-html-report", tags=["email"])
async def send_html_email_report(request: EmailReportRequest):
    """HTML 리포트 이메일 발송"""
    try:
        # TODO: 이메일 발송 구현
        result = f"HTML 이메일 발송: {request.subject}, 파일: {request.html_path}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/email/send-default-report", tags=["email"])
async def send_default_email_report(request: EmailReportRequest):
    """기본 설정으로 리포트 이메일 발송"""
    try:
        # TODO: 기본 리포트 이메일 발송 구현
        result = f"기본 리포트 이메일 발송: {request.subject}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/tools/email/config", tags=["email"])
async def get_email_config():
    """현재 이메일 설정 조회"""
    try:
        # TODO: 이메일 설정 조회 구현
        result = "이메일 설정: 설정 파일을 조회합니다"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/tools/email/test-connection", tags=["email"])
async def test_email_connection():
    """SMTP 연결 테스트"""
    try:
        # TODO: SMTP 연결 테스트 구현
        result = "SMTP 연결 테스트를 수행합니다"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= 워크플로우 도구들 =============

class VisitorSummaryRequest(BaseModel):
    spec: Optional[str] = Field(default="SPEC_VISITOR", description="워크플로우 스펙")
    end_date: str = Field(description="기준일 (YYYY-MM-DD)")
    stores: Union[str, List[str]] = Field(description="매장 목록 (문자열 콤마 구분 또는 리스트)")
    periods: Optional[List[int]] = Field(default=None, description="분석 기간 목록")
    user_prompt: Optional[str] = Field(default="방문 현황 요약 통계(HTML)", description="커스텀 프롬프트")

@app.post("/mcp/tools/workflow/visitor-summary-html", tags=["workflow"])
async def visitor_summary_html(request: VisitorSummaryRequest):
    """[VISITOR_SUMMARY] Generate a visitor summary HTML report"""
    logger.info(f"visitor_summary_html 호출: {request.end_date}")
    try:
        # Import and execute the actual workflow
        from mcp_tools.reports.visitor_summary_workflow import VisitorSummaryWorkflow
        
        workflow = VisitorSummaryWorkflow()
        
        # Convert stores to list if string
        stores_list = request.stores.split(",") if isinstance(request.stores, str) else request.stores
        
        # Run the workflow
        result = workflow.run(
            spec=request.spec or "visitor",
            end_date=request.end_date,
            stores=stores_list,
            periods=(request.periods[0] if request.periods else 1),
            user_prompt=request.user_prompt or "방문 현황 요약 통계(HTML)"
        )
        
        return {"result": f"HTML 보고서가 생성되었습니다: {result}"}
        
    except Exception as e:
        logger.error(f"visitor_summary_html 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ComparisonAnalysisRequest(BaseModel):
    stores: Union[str, List[str]] = Field(description="매장 목록 (문자열 콤마 구분 또는 리스트)")
    end_date: str = Field(description="기준일 (YYYY-MM-DD)")
    period: Optional[int] = Field(default=7, description="분석 기간 (일)")
    analysis_type: Optional[str] = Field(default="all", description="분석 타입 (daily_trends, customer_composition, time_age_pattern, all)")
    user_prompt: Optional[str] = Field(default="매장 비교 분석 리포트", description="커스텀 프롬프트")

@app.post("/mcp/tools/workflow/comparison-analysis-html", tags=["workflow"])
async def comparison_analysis_html(request: ComparisonAnalysisRequest):
    """[COMPARISON_ANALYSIS] Generate a comparison analysis HTML report for multiple stores"""
    logger.info(f"comparison_analysis_html 호출: {request.end_date}")
    try:
        # TODO: 실제 워크플로우 실행 구현
        stores_str = request.stores if isinstance(request.stores, str) else ", ".join(request.stores)
        result = f"매장 비교 분석 HTML 생성: {stores_str}, 기준일: {request.end_date}, 기간: {request.period}일, 유형: {request.analysis_type}"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= MCP 호환성 엔드포인트들 =============

@app.get("/mcp/tools", tags=["mcp"])
async def list_mcp_tools():
    """사용 가능한 모든 MCP 도구 목록을 반환합니다"""
    tools = []
    
    # 앱의 라우트들을 스캔해서 /mcp/tools/ 경로만 추출
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/mcp/tools/'):
            if hasattr(route, 'methods'):
                tool_name = route.path.replace('/mcp/tools/', '').replace('/', '_').replace('-', '_')
                tool = {
                    "name": tool_name,
                    "description": route.summary or f"Tool: {route.path}",
                    "path": route.path,
                    "methods": list(route.methods)
                }
                tools.append(tool)
    
    return {
        "tools": tools,
        "count": len(tools),
        "server_info": {
            "name": "report-mcp-server",
            "version": "3.0.0"
        }
    }

@app.get("/mcp/health", tags=["mcp"])
async def mcp_health():
    """MCP 서버 상태 확인"""
    # 도구 개수 계산
    tool_count = len([r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/mcp/tools/')])
    
    return {
        "status": "healthy",
        "version": "3.0.0", 
        "tools_count": tool_count,
        "capabilities": ["tool_discovery", "direct_rest_api", "openapi_schema"]
    }

@app.post("/mcp/tool-execution", tags=["mcp"])
async def execute_mcp_tool(tool_name: str, parameters: Dict[str, Any]):
    """MCP 도구 실행 호환성 엔드포인트"""
    return {
        "message": f"도구 '{tool_name}'을 실행하려면 해당 엔드포인트를 직접 호출하세요",
        "available_endpoints": [r.path for r in app.routes if hasattr(r, 'path') and r.path.startswith('/mcp/tools/')],
        "note": "이 서버는 REST API 방식으로 작동합니다. plus-agent가 자동으로 적절한 엔드포인트를 호출합니다."
    }

# Register MCP tool routes
mcp_diagnose_new.register_routes(app)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "report-mcp-server"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )