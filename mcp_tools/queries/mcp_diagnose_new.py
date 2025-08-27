from fastapi import HTTPException
from pydantic import BaseModel, Field
import clickhouse_connect
import os
from dotenv import load_dotenv
import logging
import sys
import time
from pathlib import Path

from mcp_tools.utils import create_transition_data
from mcp_tools.utils.map_config import item2zone
from mcp_tools.utils.database_manager import get_site_client, get_site_connection_info
from mcp_tools.utils.mcp_utils import is_token_limit_exceeded, DEFAULT_MODEL
from typing import Optional

# Request models
class SiteRequest(BaseModel):
    site: str = Field(description="매장명")

class DateRangeRequest(BaseModel):
    start_date: str = Field(description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(description="종료 날짜 (YYYY-MM-DD)")
    site: str = Field(description="매장명")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_routes(app):
    
    @app.post("/mcp/tools/diagnose/db-name", tags=["diagnose"])
    async def get_db_name_endpoint(request: SiteRequest):
        """특정 매장의 데이터베이스명 조회"""
        try:
            connection_info = get_site_connection_info(request.site)
            if not connection_info:
                return {"result": f"❌ {request.site} 매장 정보를 찾을 수 없습니다."}
            
            db_name = connection_info.get('db_name', 'plusinsight')
            result = f"📋 **{request.site} 매장 정보:**\\n데이터베이스명: {db_name}"
            return {"result": result}
        except Exception as e:
            return {"result": f"❌ {request.site} 매장 DB명 조회 실패: {e}"}

    @app.post("/mcp/tools/diagnose/avg-visitors", tags=["diagnose"])
    async def diagnose_avg_visitors_endpoint(request: DateRangeRequest):
        """방문객 진단 - 일평균 방문객수와 관련 트렌드 분석"""
        logger.info(f"diagnose_avg_visitors 호출: {request.site}, {request.start_date}~{request.end_date}")
        
        try:
            client = get_site_client(request.site, 'plusinsight')
            if not client:
                raise HTTPException(status_code=500, detail=f"❌ {request.site} 매장 연결 실패")
            
            query = f"""
            WITH
        df AS (
            SELECT
                li.date AS visit_date,
                li.timestamp,
                li.person_seq AS visitor_id,
                if(toDayOfWeek(li.date) IN (1,2,3,4,5), 'weekday', 'weekend')                     AS day_type,
                multiIf(
                    toHour(li.timestamp) IN (22,23,0,1), '22-01',
                    toHour(li.timestamp) BETWEEN 2  AND 5 , '02-05',
                    toHour(li.timestamp) BETWEEN 6  AND 9 , '06-09',
                    toHour(li.timestamp) BETWEEN 10 AND 13, '10-13',
                    toHour(li.timestamp) BETWEEN 14 AND 17, '14-17',
                    '18-21'
                ) AS time_range,
                multiIf(
                    dt.age BETWEEN 0  AND  9 , '10대 미만',
                    dt.age BETWEEN 10 AND 19, '10대',
                    dt.age BETWEEN 20 AND 29, '20대',
                    dt.age BETWEEN 30 AND 39, '30대',
                    dt.age BETWEEN 40 AND 49, '40대',
                    dt.age BETWEEN 50 AND 59, '50대',
                    dt.age >= 60           , '60대 이상',
                    'Unknown'
                ) AS age_group,
                if(dt.gender = '0', '남성', if(dt.gender='1','여성','Unknown'))                   AS gender
            FROM line_in_out_individual li
            LEFT JOIN detected_time dt ON li.person_seq = dt.person_seq
            LEFT JOIN line          l  ON li.triggered_line_id = l.id
            WHERE li.date BETWEEN '{request.start_date}' AND '{request.end_date}'
              AND li.is_staff = 0
              AND li.in_out   = 'IN'
              AND l.entrance  = 1
        ),
        daily_all     AS (SELECT visit_date, uniqExact(visitor_id) AS ucnt FROM df GROUP BY visit_date),
        avg_all       AS (SELECT toUInt64(round(avg(ucnt))) AS avg_cnt FROM daily_all),
        daily_dayType AS (SELECT visit_date, day_type, uniqExact(visitor_id) AS ucnt FROM df GROUP BY visit_date, day_type),
        avg_dayType   AS (SELECT day_type, toUInt64(round(avg(ucnt))) AS avg_cnt FROM daily_dayType GROUP BY day_type),
        daily_gender  AS (SELECT visit_date, gender, uniqExact(visitor_id) AS ucnt FROM df GROUP BY visit_date, gender),
        avg_gender    AS (SELECT gender, toUInt64(round(avg(ucnt))) AS avg_cnt FROM daily_gender GROUP BY gender),
        daily_age     AS (SELECT visit_date, age_group, uniqExact(visitor_id) AS ucnt FROM df GROUP BY visit_date, age_group),
        avg_age       AS (SELECT age_group, toUInt64(round(avg(ucnt))) AS avg_cnt FROM daily_age GROUP BY age_group),
        rank_age      AS (SELECT *, row_number() OVER (ORDER BY avg_cnt DESC) AS rk FROM avg_age),
        overall_cnt   AS (SELECT avg_cnt AS cnt FROM avg_all),
        range_cnt AS (
            SELECT day_type, time_range, uniqExact(visitor_id) AS visit_cnt
            FROM df GROUP BY day_type, time_range
        ),
        tot_cnt   AS (SELECT day_type, sum(visit_cnt) AS total_cnt FROM range_cnt GROUP BY day_type),
        range_pct AS (
            SELECT r.day_type, r.time_range, r.visit_cnt,
                   toUInt64(round(
                       CASE 
                           WHEN t.total_cnt > 0 THEN r.visit_cnt / t.total_cnt * 100
                           ELSE 0
                       END
                   )) AS pct
            FROM range_cnt r JOIN tot_cnt t USING(day_type)
        ),
        rank_slot AS (
            SELECT *, row_number() OVER (PARTITION BY day_type ORDER BY pct DESC) AS rk
            FROM range_pct
        ),
        final AS (
            SELECT '일평균' AS section, '전체' AS label,
                   avg_cnt AS value_cnt, CAST(NULL AS Nullable(UInt64)) AS value_pct, 0 AS ord
            FROM avg_all
            UNION ALL
            SELECT '일평균', '평일', avg_cnt, CAST(NULL AS Nullable(UInt64)), 1
            FROM avg_dayType WHERE day_type='weekday'
            UNION ALL
            SELECT '일평균', '주말', avg_cnt, CAST(NULL AS Nullable(UInt64)), 2
            FROM avg_dayType WHERE day_type='weekend'
            UNION ALL
            SELECT '성별경향', gender, avg_cnt,
                   toUInt64(round(
                       CASE 
                           WHEN (SELECT cnt FROM overall_cnt) > 0 THEN avg_cnt / (SELECT cnt FROM overall_cnt) * 100
                           ELSE 0
                       END
                   )) AS value_pct,
                   10 + if(gender='남성',0,1) AS ord
            FROM avg_gender WHERE gender IN ('남성','여성')
            UNION ALL
            SELECT '연령대경향',
                   concat(toString(rk),'위_',age_group)                         AS label,
                   avg_cnt,
                   toUInt64(round(
                       CASE 
                           WHEN (SELECT cnt FROM overall_cnt) > 0 THEN avg_cnt / (SELECT cnt FROM overall_cnt) * 100
                           ELSE 0
                       END
                   )) AS value_pct,
                   20 + rk AS ord
            FROM rank_age WHERE rk<=3
            UNION ALL
            SELECT '시간대경향',
                   concat('평일_',toString(rk),'_',time_range)                 AS label,
                   visit_cnt, pct, 30 + rk
            FROM rank_slot WHERE day_type='weekday' AND rk<=3
            UNION ALL
            SELECT '시간대경향',
                   concat('주말_',toString(rk),'_',time_range),
                   visit_cnt, pct, 40 + rk
            FROM rank_slot WHERE day_type='weekend' AND rk<=3
        )
        SELECT section, label, value_cnt, value_pct
        FROM final
        ORDER BY ord
        """
            
            result = client.query(query)
            
            if len(result.result_rows) > 0:
                # 섹션별로 데이터 분류
                sections = {
                    '일평균': [],
                    '성별경향': [],
                    '연령대경향': [],
                    '시간대경향': []
                }
                
                for row in result.result_rows:
                    section, label, value_cnt, value_pct = row
                    sections[section].append((label, value_cnt, value_pct))
                
                # 표 형태로 포맷팅
                answer = f"=== {request.site} ===\\n"
                
                # 1. 일평균 방문객수
                answer += "일평균 방문객수\\n"
                for label, cnt, _ in sections['일평균']:
                    answer += f"  {label}: {cnt}명\\n"
                
                # 2. 성별경향
                answer += "\\n성별경향\\n"
                for label, cnt, pct in sections['성별경향']:
                    gender_display = 'M' if label == '남성' else 'F'
                    answer += f"  {gender_display}: {pct}%\\n"
                
                # 3. 연령대별 순위 (상위 3개)
                answer += "\\n연령대별 순위\\n"
                for label, cnt, pct in sections['연령대경향']:
                    rank = label.split('위_')[0]
                    age_group = label.split('위_')[1]
                    answer += f"  {rank}: {age_group} - {pct}%\\n"
                
                # 4. 주요 방문시간대
                answer += "\\n주요 방문시간대\\n"
                
                # 시간대 명칭 매핑
                time_names = {
                    '22-01': '심야',
                    '02-05': '새벽',
                    '06-09': '아침',
                    '10-13': '낮',
                    '14-17': '오후',
                    '18-21': '저녁'
                }
                    
                # 평일 시간대 분리
                weekday_slots = [item for item in sections['시간대경향'] if '평일_' in item[0]]
                weekend_slots = [item for item in sections['시간대경향'] if '주말_' in item[0]]
                
                answer += "  평일:\\n"
                for label, cnt, pct in weekday_slots:
                    rank = label.split('_')[1]
                    time_range = label.split('_')[2]
                    time_name = time_names.get(time_range, time_range)
                    answer += f"    {rank}: {time_name}({time_range}) - {pct}%\\n"
                
                answer += "  주말:\\n"
                for label, cnt, pct in weekend_slots:
                    rank = label.split('_')[1]
                    time_range = label.split('_')[2]
                    time_name = time_names.get(time_range, time_range)
                    answer += f"    {rank}: {time_name}({time_range}) - {pct}%\\n"
            else:
                answer = f"⚠️ {request.site}: 데이터가 없습니다."
                
            return {"result": answer}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"diagnose_avg_visitors 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/mcp/tools/diagnose/avg-sales", tags=["diagnose"])
    async def diagnose_avg_sales_endpoint(request: DateRangeRequest):
        """일평균 판매 건수 진단"""
        logger.info(f"diagnose_avg_sales 호출: {request.site}")
        try:
            # TODO: 실제 로직 구현 (기존 mcp_diagnose.py에서 가져와야 함)
            result = f"판매 건수 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
            return {"result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # 나머지 진단 도구들도 같은 방식으로 추가...
    @app.post("/mcp/tools/diagnose/zero-visits", tags=["diagnose"])
    async def check_zero_visits_endpoint(request: DateRangeRequest):
        """방문객수 데이터 이상 조회"""
        try:
            result = f"방문객수 데이터 이상 조회 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
            return {"result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/mcp/tools/diagnose/purchase-conversion", tags=["diagnose"])
    async def diagnose_purchase_conversion_endpoint(request: DateRangeRequest):
        """구매전환율 진단"""
        try:
            result = f"구매전환율 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
            return {"result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/mcp/tools/diagnose/exploratory-tendency", tags=["diagnose"])
    async def diagnose_exploratory_tendency_endpoint(request: DateRangeRequest):
        """탐색 경향성 진단"""
        try:
            result = f"탐색 경향성 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
            return {"result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/mcp/tools/diagnose/shelf", tags=["diagnose"])
    async def diagnose_shelf_endpoint(request: DateRangeRequest):
        """진열대 진단"""
        try:
            result = f"진열대 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
            return {"result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/mcp/tools/diagnose/table-occupancy", tags=["diagnose"])
    async def diagnose_table_occupancy_endpoint(request: DateRangeRequest):
        """시식대 혼잡도 진단"""
        try:
            result = f"시식대 혼잡도 진단 호출됨: {request.site} 매장, {request.start_date}~{request.end_date}"
            return {"result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))