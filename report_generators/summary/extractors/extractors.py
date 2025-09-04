"""Summary Report용 데이터 추출 클래스들."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Dict, List, Optional

from libs.database import get_site_client
from libs.weekly_domain import to_pct_series
from ..models import StoreRowDict, WeeklySeriesDict, DailySeriesDict, SameDaySeriesDict


def clamp_end_date_to_yesterday(end_date_iso: str) -> str:
    """종료 날짜를 어제로 제한 (기존 함수 이관)."""
    req_date = date.fromisoformat(end_date_iso)
    yesterday = date.today() - timedelta(days=1)
    if req_date > yesterday:
        return yesterday.isoformat()
    return end_date_iso


class SummaryDataExtractor(ABC):
    """Summary Report용 데이터 추출 베이스 클래스."""
    
    @abstractmethod
    def extract_period_rates(self, site: str, end_date: str, days: int) -> StoreRowDict:
        """기간별 증감률 데이터 추출."""
        pass
    
    @abstractmethod
    def extract_daily_series(self, site: str, end_date: str, days: int = 7) -> DailySeriesDict:
        """일별 시리즈 데이터 추출 (1일 모드용)."""
        pass
    
    @abstractmethod
    def extract_weekly_series(self, site: str, end_date: str, weeks: int = 4) -> WeeklySeriesDict:
        """주별 시리즈 데이터 추출 (7일 모드용)."""
        pass
    
    @abstractmethod
    def extract_same_weekday_series(self, site: str, end_date: str, weeks: int = 4) -> SameDaySeriesDict:
        """같은 요일 시리즈 데이터 추출."""
        pass


class VisitorSummaryExtractor(SummaryDataExtractor):
    """방문자 데이터 추출기 (기존 함수들 이관)."""
    
    def _build_sql_period_agg(self, end_date_iso: str, days: int) -> str:
        """ClickHouse SQL: 주기(days) 단위로 최근/이전 동일기간 합계 및 평일/주말 분리 집계."""
        return f"""
WITH
  toDate('{end_date_iso}') AS req_end,
  if(req_end >= today(), addDays(today(), -1), req_end) AS target_end,
  {days} AS win,
  addDays(target_end, -(win-1))          AS curr_start,
  addDays(target_end, -(2*win-1))        AS prev_start,
  addDays(target_end, -win)              AS prev_end,

  base AS (
    SELECT lioi.date, lioi.person_seq
    FROM line_in_out_individual AS lioi
    INNER JOIN line AS l
      ON l.id = lioi.triggered_line_id
     AND l.entrance = 1
    WHERE lioi.date BETWEEN prev_start AND target_end
      AND lioi.is_staff = 0
      AND upper(lioi.in_out) = 'IN'
  ),
  daily AS (
    SELECT date, uniqExact(person_seq) AS uv
    FROM base
    GROUP BY date
  ),
  labeled AS (
    SELECT
      date,
      uv,
      if(date BETWEEN curr_start AND target_end, 1, 0) AS is_curr,
      if(date BETWEEN prev_start AND prev_end,   1, 0) AS is_prev,
      if(toDayOfWeek(date) IN (6, 7), 'weekend', 'weekday') AS day_type
    FROM daily
    WHERE date BETWEEN prev_start AND target_end
  ),
  agg AS (
    SELECT
      sumIf(uv, is_curr = 1)                                        AS curr_total,
      sumIf(uv, is_prev = 1)                                        AS prev_total,
      sumIf(uv, is_curr = 1 AND day_type = 'weekday')               AS curr_weekday_total,
      sumIf(uv, is_prev = 1 AND day_type = 'weekday')               AS prev_weekday_total,
      sumIf(uv, is_curr = 1 AND day_type = 'weekend')               AS curr_weekend_total,
      sumIf(uv, is_prev = 1 AND day_type = 'weekend')               AS prev_weekend_total
    FROM labeled
  )
SELECT
  curr_total,
  prev_total,
  curr_weekday_total,
  prev_weekday_total,
  curr_weekend_total,
  prev_weekend_total,
  if(prev_weekday_total = 0, NULL,
     (curr_weekday_total - prev_weekday_total) / prev_weekday_total * 100) AS weekday_delta_pct,
  if(prev_weekend_total = 0, NULL,
     (curr_weekend_total - prev_weekend_total) / prev_weekend_total * 100) AS weekend_delta_pct,
  if(prev_total = 0, NULL,
     (curr_total - prev_total) / prev_total * 100)                      AS total_delta_pct
FROM agg
"""

    def _build_sql_weekly_series(self, end_date_iso: str, num_weeks: int = 5) -> str:
        """ClickHouse SQL: 최근 주차별(week_idx 0=금주, 1=전주, ...) 합계 산출."""
        return f"""
WITH
  toDate('{end_date_iso}') AS req_end,
  if(req_end >= today(), addDays(today(), -1), req_end) AS target_end,
  {num_weeks} AS wcnt,
  base AS (
    SELECT lioi.date, lioi.person_seq
    FROM line_in_out_individual AS lioi
    INNER JOIN line AS l
      ON l.id = lioi.triggered_line_id
     AND l.entrance = 1
    WHERE lioi.date <= target_end
      AND lioi.date >= addDays(target_end, -90) -- 안전범위(약 3개월)로 제한
      AND lioi.is_staff = 0
      AND upper(lioi.in_out) = 'IN'
  ),
  daily AS (
    SELECT date, uniqExact(person_seq) AS uv
    FROM base
    GROUP BY date
  ),
  weekly AS (
    SELECT
      toYearWeek(date) AS yearweek,
      toStartOfWeek(date) AS week_start,
      sumIf(uv, toDayOfWeek(date) IN (6, 7)) AS weekend_total,
      sumIf(uv, toDayOfWeek(date) NOT IN (6, 7)) AS weekday_total,
      sum(uv) AS total_total
    FROM daily
    GROUP BY yearweek, week_start
  ),
  indexed AS (
    SELECT
      *,
      intDiv(dateDiff('day', week_start, target_end), 7) AS week_idx
    FROM weekly
    WHERE week_start <= target_end
  )
SELECT
  week_idx,
  weekday_total,
  weekend_total,
  total_total
FROM indexed
WHERE week_idx < wcnt
ORDER BY week_idx
"""

    def _build_sql_daily_same_weekday_agg(self, end_date_iso: str) -> str:
        """ClickHouse SQL: 같은 요일(전주 대비) 집계."""
        return f"""
WITH
  toDate('{end_date_iso}') AS req_end,
  if(req_end >= today(), addDays(today(), -1), req_end) AS target_end,
  toDayOfWeek(target_end) AS target_dow,
  base AS (
    SELECT lioi.date, lioi.person_seq
    FROM line_in_out_individual AS lioi
    INNER JOIN line AS l
      ON l.id = lioi.triggered_line_id
     AND l.entrance = 1
    WHERE lioi.date <= target_end
      AND lioi.date >= addDays(target_end, -21) -- 3주 범위
      AND toDayOfWeek(lioi.date) = target_dow
      AND lioi.is_staff = 0
      AND upper(lioi.in_out) = 'IN'
  ),
  daily AS (
    SELECT date, uniqExact(person_seq) AS uv
    FROM base
    GROUP BY date
  ),
  indexed AS (
    SELECT
      *,
      intDiv(dateDiff('day', date, target_end), 7) AS week_idx
    FROM daily
    WHERE date <= target_end
  )
SELECT
  week_idx,
  uv AS total
FROM indexed
WHERE week_idx < 4
ORDER BY week_idx
"""

    def _build_sql_daily_same_weekday_period(self, end_date_iso: str) -> str:
        """ClickHouse SQL: 전주 같은 요일 비교 (1일 모드 전용)."""
        return f"""
WITH
  toDate('{end_date_iso}') AS req_end,
  if(req_end >= today(), addDays(today(), -1), req_end) AS target_end,
  toDayOfWeek(target_end) AS target_dow,
  addDays(target_end, -7) AS prev_same_day,
  base AS (
    SELECT lioi.date, lioi.person_seq
    FROM line_in_out_individual AS lioi
    INNER JOIN line AS l
      ON l.id = lioi.triggered_line_id
     AND l.entrance = 1
    WHERE lioi.date IN (target_end, prev_same_day)
      AND lioi.is_staff = 0
      AND upper(lioi.in_out) = 'IN'
  ),
  daily AS (
    SELECT date, uniqExact(person_seq) AS uv
    FROM base
    GROUP BY date
  ),
  labeled AS (
    SELECT
      date,
      uv,
      if(date = target_end, 1, 0) AS is_curr,
      if(date = prev_same_day, 1, 0) AS is_prev
    FROM daily
  ),
  agg AS (
    SELECT
      sumIf(uv, is_curr = 1) AS curr_total,
      sumIf(uv, is_prev = 1) AS prev_total,
      curr_total AS curr_weekday_total, -- 1일 모드에서는 전체가 평일/주말 중 하나
      prev_total AS prev_weekday_total,
      0 AS curr_weekend_total, -- 미사용
      0 AS prev_weekend_total  -- 미사용
    FROM labeled
  )
SELECT
  curr_total,
  prev_total,
  curr_weekday_total,
  prev_weekday_total,
  curr_weekend_total,
  prev_weekend_total,
  if(prev_total = 0, NULL,
     (curr_total - prev_total) / prev_total * 100) AS weekday_delta_pct,
  NULL AS weekend_delta_pct, -- 1일 모드에서는 미사용
  if(prev_total = 0, NULL,
     (curr_total - prev_total) / prev_total * 100) AS total_delta_pct
FROM agg
"""

    def extract_period_rates(self, site: str, end_date: str, days: int) -> StoreRowDict:
        """기간별 증감률 데이터 추출 (기존 summarize_period_rates 함수 이관)."""
        try:
            client = get_site_client(site)
            end_clamped = clamp_end_date_to_yesterday(end_date)
            
            # 1일 모드에서는 전주 같은 요일 비교 쿼리 사용
            if days == 1:
                sql = self._build_sql_daily_same_weekday_period(end_clamped)
            else:
                sql = self._build_sql_period_agg(end_clamped, days)
            job = client.query(sql)
            # clickhouse-connect API 호환성 처리
            try:
                rows = list(job.result())
                use_dict_access = False
            except AttributeError:
                # 새로운 API 버전: named_results()로 딕셔너리 형태 반환
                rows = list(job.named_results())
                use_dict_access = True
            
            if not rows:
                return {"site": site}
            
            row = rows[0]
            if use_dict_access:
                # 딕셔너리 접근
                result: StoreRowDict = {
                    "site": site,
                    "curr_total": int(row["curr_total"]) if row.get("curr_total") is not None else None,
                    "prev_total": int(row["prev_total"]) if row.get("prev_total") is not None else None,
                    "weekday_delta_pct": float(row["weekday_delta_pct"]) if row.get("weekday_delta_pct") is not None else None,
                    "weekend_delta_pct": float(row["weekend_delta_pct"]) if row.get("weekend_delta_pct") is not None else None,
                    "total_delta_pct": float(row["total_delta_pct"]) if row.get("total_delta_pct") is not None else None,
                }
            else:
                # 속성 접근
                result: StoreRowDict = {
                    "site": site,
                    "curr_total": int(row.curr_total) if row.curr_total is not None else None,
                    "prev_total": int(row.prev_total) if row.prev_total is not None else None,
                    "weekday_delta_pct": float(row.weekday_delta_pct) if row.weekday_delta_pct is not None else None,
                    "weekend_delta_pct": float(row.weekend_delta_pct) if row.weekend_delta_pct is not None else None,
                    "total_delta_pct": float(row.total_delta_pct) if row.total_delta_pct is not None else None,
                }
            return result
            
        except Exception as exc:
            print(f"[extract_period_rates] {site} 에러: {exc}")
            return {"site": site}

    def extract_daily_series(self, site: str, end_date: str, days: int = 7) -> DailySeriesDict:
        """일별 시리즈 데이터 추출 (기존 fetch_daily_series 함수 이관)."""
        try:
            client = get_site_client(site)
            end_clamped = clamp_end_date_to_yesterday(end_date)
            
            # 기존 로직 유지: 7일간 일별 데이터
            sql = f"""
WITH
  toDate('{end_clamped}') AS req_end,
  if(req_end >= today(), addDays(today(), -1), req_end) AS target_end,
  base AS (
    SELECT lioi.date, lioi.person_seq
    FROM line_in_out_individual AS lioi
    INNER JOIN line AS l
      ON l.id = lioi.triggered_line_id
     AND l.entrance = 1
    WHERE lioi.date <= target_end
      AND lioi.date >= addDays(target_end, -{days-1})
      AND lioi.is_staff = 0
      AND upper(lioi.in_out) = 'IN'
  ),
  daily AS (
    SELECT date, uniqExact(person_seq) AS uv
    FROM base
    GROUP BY date
  )
SELECT
  date,
  if(toDayOfWeek(date) IN (6, 7), uv, 0) AS weekend_total,
  if(toDayOfWeek(date) NOT IN (6, 7), uv, 0) AS weekday_total,
  uv AS total_total
FROM daily
ORDER BY date
"""
            
            job = client.query(sql)
            # clickhouse-connect API 호환성 처리
            try:
                rows = list(job.result())
                use_dict_access = False
            except AttributeError:
                # 새로운 API 버전: named_results()로 딕셔너리 형태 반환
                rows = list(job.named_results())
                use_dict_access = True
            
            weekday_vals = []
            weekend_vals = []
            total_vals = []
            
            for row in rows:
                if use_dict_access:
                    weekday_vals.append(int(row["weekday_total"]))
                    weekend_vals.append(int(row["weekend_total"]))
                    total_vals.append(int(row["total_total"]))
                else:
                    weekday_vals.append(int(row.weekday_total))
                    weekend_vals.append(int(row.weekend_total))
                    total_vals.append(int(row.total_total))
            
            return {
                "weekday": weekday_vals,
                "weekend": weekend_vals,
                "total": total_vals,
            }
            
        except Exception as exc:
            print(f"[extract_daily_series] {site} 에러: {exc}")
            return {"weekday": [], "weekend": [], "total": []}

    def extract_weekly_series(self, site: str, end_date: str, weeks: int = 4) -> WeeklySeriesDict:
        """주별 시리즈 데이터 추출 (기존 fetch_weekly_series 함수 이관)."""
        try:
            client = get_site_client(site)
            end_clamped = clamp_end_date_to_yesterday(end_date)
            
            sql = self._build_sql_weekly_series(end_clamped, weeks)
            job = client.query(sql)
            # clickhouse-connect API 호환성 처리
            try:
                rows = list(job.result())
                use_dict_access = False
            except AttributeError:
                # 새로운 API 버전: named_results()로 딕셔너리 형태 반환
                rows = list(job.named_results())
                use_dict_access = True
            
            weekday_vals = []
            weekend_vals = []
            total_vals = []
            
            if use_dict_access:
                sorted_rows = sorted(rows, key=lambda r: r["week_idx"], reverse=True)
            else:
                sorted_rows = sorted(rows, key=lambda r: r.week_idx, reverse=True)
            
            for row in sorted_rows:
                if use_dict_access:
                    weekday_vals.append(int(row["weekday_total"]))
                    weekend_vals.append(int(row["weekend_total"]))
                    total_vals.append(int(row["total_total"]))
                else:
                    weekday_vals.append(int(row.weekday_total))
                    weekend_vals.append(int(row.weekend_total))
                    total_vals.append(int(row.total_total))
            
            return {
                "weekday": weekday_vals,
                "weekend": weekend_vals,
                "total": total_vals,
            }
            
        except Exception as exc:
            print(f"[extract_weekly_series] {site} 에러: {exc}")
            return {"weekday": [], "weekend": [], "total": []}

    def extract_same_weekday_series(self, site: str, end_date: str, weeks: int = 4) -> SameDaySeriesDict:
        """같은 요일 시리즈 데이터 추출 (원본 fetch_same_weekday_series와 동일)."""
        try:
            client = get_site_client(site)
            end_clamped = clamp_end_date_to_yesterday(end_date)
            
            # 원본과 동일한 SQL 구조 사용
            sql = f"""
WITH
  toDate('{end_clamped}') AS req_end,
  if(req_end >= today(), addDays(today(), -1), req_end) AS target_end,
  toDayOfWeek(target_end) AS target_weekday,
  
  -- 과거 4주간의 같은 요일 날짜들
  addDays(target_end, -7) AS prev_week_same_day,
  addDays(target_end, -14) AS prev2_week_same_day,
  addDays(target_end, -21) AS prev3_week_same_day,
  addDays(target_end, -28) AS prev4_week_same_day,
  base AS (
    SELECT lioi.date, lioi.person_seq
    FROM line_in_out_individual AS lioi
    INNER JOIN line AS l
      ON l.id = lioi.triggered_line_id
     AND l.entrance = 1
    WHERE lioi.date IN (target_end, prev_week_same_day, prev2_week_same_day, prev3_week_same_day, prev4_week_same_day)
      AND lioi.is_staff = 0
      AND upper(lioi.in_out) = 'IN'
  ),
  daily AS (
    SELECT date, uniqExact(person_seq) AS uv
    FROM base
    GROUP BY date
  ),
  agg AS (
    SELECT
      sumIf(uv, date = target_end) AS curr_total,
      sumIf(uv, date = prev_week_same_day) AS prev_total,
      sumIf(uv, date = prev2_week_same_day) AS prev2_total,
      sumIf(uv, date = prev3_week_same_day) AS prev3_total,
      sumIf(uv, date = prev4_week_same_day) AS prev4_total
    FROM daily
  )
SELECT
  curr_total, prev_total, prev2_total, prev3_total, prev4_total
FROM agg
"""
            
            job = client.query(sql)
            # clickhouse-connect API 호환성 처리
            try:
                rows = list(job.result())
                use_dict_access = False
            except AttributeError:
                # 새로운 API 버전: named_results()로 딕셔너리 형태 반환
                rows = list(job.named_results())
                use_dict_access = True
            
            if not rows:
                return {"total": [0, 0, 0, 0, 0]}
            
            row = rows[0]
            if use_dict_access:
                curr_total = int(row["curr_total"]) if row.get("curr_total") is not None else 0
                prev_total = int(row["prev_total"]) if row.get("prev_total") is not None else 0
                prev2_total = int(row["prev2_total"]) if row.get("prev2_total") is not None else 0
                prev3_total = int(row["prev3_total"]) if row.get("prev3_total") is not None else 0
                prev4_total = int(row["prev4_total"]) if row.get("prev4_total") is not None else 0
            else:
                curr_total = int(row.curr_total) if row.curr_total is not None else 0
                prev_total = int(row.prev_total) if row.prev_total is not None else 0
                prev2_total = int(row.prev2_total) if row.prev2_total is not None else 0
                prev3_total = int(row.prev3_total) if row.prev3_total is not None else 0
                prev4_total = int(row.prev4_total) if row.prev4_total is not None else 0
            
            # 과거부터 최신 순서로 정렬 (to_pct_series와 맞추기 위해)
            values_tot = [prev4_total, prev3_total, prev2_total, prev_total, curr_total]
            
            return {"total": values_tot}
            
        except Exception as exc:
            print(f"[extract_same_weekday_series] {site} 에러: {exc}")
            return {"total": [0, 0, 0, 0, 0]}


class TouchPointSummaryExtractor(SummaryDataExtractor):
    """터치포인트 데이터 추출기 (미래 확장용)."""
    
    def extract_period_rates(self, site: str, end_date: str, days: int) -> StoreRowDict:
        # TODO: 터치포인트 전용 쿼리 구현
        return {"site": site}
    
    def extract_daily_series(self, site: str, end_date: str, days: int = 7) -> DailySeriesDict:
        # TODO: 터치포인트 일별 시리즈 구현
        return {"weekday": [], "weekend": [], "total": []}
    
    def extract_weekly_series(self, site: str, end_date: str, weeks: int = 4) -> WeeklySeriesDict:
        # TODO: 터치포인트 주별 시리즈 구현
        return {"weekday": [], "weekend": [], "total": []}
    
    def extract_same_weekday_series(self, site: str, end_date: str, weeks: int = 4) -> SameDaySeriesDict:
        # TODO: 터치포인트 같은 요일 시리즈 구현
        return {"total": []}


class DwellingTimeSummaryExtractor(SummaryDataExtractor):
    """체류시간 데이터 추출기 (미래 확장용)."""
    
    def extract_period_rates(self, site: str, end_date: str, days: int) -> StoreRowDict:
        # TODO: 체류시간 전용 쿼리 구현
        return {"site": site}
    
    def extract_daily_series(self, site: str, end_date: str, days: int = 7) -> DailySeriesDict:
        # TODO: 체류시간 일별 시리즈 구현
        return {"weekday": [], "weekend": [], "total": []}
    
    def extract_weekly_series(self, site: str, end_date: str, weeks: int = 4) -> WeeklySeriesDict:
        # TODO: 체류시간 주별 시리즈 구현
        return {"weekday": [], "weekend": [], "total": []}
    
    def extract_same_weekday_series(self, site: str, end_date: str, weeks: int = 4) -> SameDaySeriesDict:
        # TODO: 체류시간 같은 요일 시리즈 구현
        return {"total": []}


def create_extractor(data_type: str) -> SummaryDataExtractor:
    """데이터 타입에 따른 Extractor 팩토리."""
    extractors = {
        "visitor": VisitorSummaryExtractor,
        "touch_point": TouchPointSummaryExtractor,
        "dwelling_time": DwellingTimeSummaryExtractor,
    }
    
    if data_type not in extractors:
        raise ValueError(f"Unknown data_type: {data_type}")
    
    return extractors[data_type]()


# 기존 함수들을 래퍼로 유지 (하위 호환성)
def summarize_period_rates(site: str, end_date_iso: str, days: int) -> StoreRowDict:
    """기존 함수 호환성 유지."""
    extractor = VisitorSummaryExtractor()
    return extractor.extract_period_rates(site, end_date_iso, days)


def fetch_daily_series(site: str, end_date_iso: str, days: int = 7) -> DailySeriesDict:
    """기존 함수 호환성 유지."""
    extractor = VisitorSummaryExtractor()
    return extractor.extract_daily_series(site, end_date_iso, days)


def fetch_weekly_series(site: str, end_date_iso: str, weeks: int = 4) -> WeeklySeriesDict:
    """기존 함수 호환성 유지."""
    extractor = VisitorSummaryExtractor()
    return extractor.extract_weekly_series(site, end_date_iso, weeks)


def fetch_same_weekday_series(site: str, end_date_iso: str, weeks: int = 4) -> SameDaySeriesDict:
    """기존 함수 호환성 유지."""
    extractor = VisitorSummaryExtractor()
    return extractor.extract_same_weekday_series(site, end_date_iso, weeks)