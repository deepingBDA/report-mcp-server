"""Table 카드 생성기 (기존 _build_table_html 로직 이관)."""

from __future__ import annotations

from typing import List, Tuple

from libs.svg_renderer import svg_sparkline
from libs.weekly_domain import to_pct_series

from ..models import StoreRowDict, RenderSeries, fmt_int, fmt_pct, get_pct_class
from ..templates import (
    TABLE_DAILY_HEADER_TEMPLATE,
    TABLE_WEEKLY_HEADER_TEMPLATE,
    TABLE_DAILY_ROW_TEMPLATE,
    TABLE_WEEKLY_ROW_TEMPLATE,
    TABLE_FOOTER_TEMPLATE,
)
from ..data.extractors import fetch_same_weekday_series, fetch_weekly_series


class TableCardGenerator:
    """Table 카드 생성기 (기존 _build_table_html 로직 이관)."""
    
    def generate(self, rows: List[StoreRowDict], end_iso: str, days: int, state_data: dict) -> str:
        """테이블 카드 HTML 생성."""
        # 공통 스케일 계산을 위해 모든 시리즈 수집 (기존 로직 완전 보존)
        collected: List[Tuple[StoreRowDict, RenderSeries]] = []
        minmax = {
            "wd_min": None, "wd_max": None,
            "we_min": None, "we_max": None,
            "tot_min": None, "tot_max": None,
        }  # type: ignore

        for r in rows:
            site = str(r.get("site", ""))
            try:
                if days == 1:
                    # 1일 모드: 같은 요일 데이터만 가져와서 스파크라인 생성
                    weekly = fetch_same_weekday_series(site, end_iso, weeks=5)
                    s_tot = to_pct_series(weekly.get("total", []))[-4:] if len(weekly.get("total", [])) >= 4 else [0] * 4
                    s_wd = [0] * 4  # 1일 모드에서는 평일/주말 스파크라인 없음
                    s_we = [0] * 4
                    # 4포인트 보장
                    while len(s_tot) < 4:
                        s_tot.insert(0, 0.0)
                    s_tot = s_tot[-4:]
                else:
                    # 7일 모드: 기존 주간 데이터 사용
                    weekly = fetch_weekly_series(site, end_iso, weeks=5)
                    s_wd = to_pct_series(weekly.get("weekday", []))[-4:]
                    s_we = to_pct_series(weekly.get("weekend", []))[-4:]
                    s_tot = to_pct_series(weekly.get("total", []))[-4:]
                    # 최소 4포인트 보장
                    while len(s_wd) < 4:
                        s_wd.insert(0, 0.0)
                    while len(s_we) < 4:
                        s_we.insert(0, 0.0)
                    while len(s_tot) < 4:
                        s_tot.insert(0, 0.0)
            except Exception:
                if days == 1:
                    s_wd = [0.0] * 7
                    s_we = [0.0] * 7
                    s_tot = [0.0] * 7
                else:
                    s_wd = [0.0, 0.0, 0.0, 0.0]
                    s_we = [0.0, 0.0, 0.0, 0.0]
                    s_tot = [0.0, 0.0, 0.0, 0.0]

            collected.append((r, RenderSeries(s_wd, s_we, s_tot)))
            for label, series in (("wd", s_wd), ("we", s_we), ("tot", s_tot)):
                for v in series:
                    key_min = f"{label}_min"
                    key_max = f"{label}_max"
                    if minmax[key_min] is None or v < minmax[key_min]:
                        minmax[key_min] = v
                    if minmax[key_max] is None or v > minmax[key_max]:
                        minmax[key_max] = v

        # 날짜 범위 계산 (기존 로직 유지)
        from datetime import date, timedelta
        
        end_date = date.fromisoformat(end_iso)
        if state_data.get("compare_lag") == 1 and days == 1:
            # 1일 모드: 전주 같은 요일과 비교
            weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][end_date.weekday()]
            curr_range = f"{end_date.strftime('%Y-%m-%d')}({weekday_kr})"
            prev_date = end_date - timedelta(days=7)
            prev_weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][prev_date.weekday()]
            prev_range = f"{prev_date.strftime('%Y-%m-%d')}({prev_weekday_kr})"
        else:
            # 다른 모드: 기간별 비교
            curr_start = end_date - timedelta(days=(days-1))
            prev_start = end_date - timedelta(days=(2*days-1))
            prev_end = end_date - timedelta(days=days)
            curr_range = f"{curr_start.strftime('%Y-%m-%d')}<br>~ {end_date.strftime('%Y-%m-%d')}"
            prev_range = f"{prev_start.strftime('%Y-%m-%d')}<br>~ {prev_end.strftime('%Y-%m-%d')}"

        # 헤더 생성
        if state_data.get("compare_lag") == 1 and days == 1:
            # 1일 모드
            header_html = TABLE_DAILY_HEADER_TEMPLATE
        else:
            # 7일 모드
            header_html = TABLE_WEEKLY_HEADER_TEMPLATE

        # 템플릿 변수 치환
        header = header_html.replace("{curr_range}", curr_range).replace("{prev_range}", prev_range).replace(
            "{period_label}", state_data.get("period_label", "금주")).replace("{prev_label}", state_data.get("prev_label", "전주")).replace("{days}", str(days))
        
        # 주간 모드일 때만 min/max 값 치환
        if not (state_data.get("compare_lag") == 1 and days == 1):
            header = header.replace(
                "{wd_min}", f"{(minmax['wd_min'] or 0):.1f}"
            ).replace("{wd_max}", f"{(minmax['wd_max'] or 0):.1f}").replace(
                "{we_min}", f"{(minmax['we_min'] or 0):.1f}"
            ).replace("{we_max}", f"{(minmax['we_max'] or 0):.1f}").replace(
                "{tot_min}", f"{(minmax['tot_min'] or 0):.1f}"
            ).replace("{tot_max}", f"{(minmax['tot_max'] or 0):.1f}")

        # 바디 생성
        body_rows: List[str] = []
        for r, ser in collected:
            if days == 1:
                # 일자별 모드: 총 증감률 + 7일 스파크라인 표시
                row_html = TABLE_DAILY_ROW_TEMPLATE
                body_rows.append(
                    row_html
                    .replace("{site}", str(r.get("site", "")))
                    .replace("{curr}", fmt_int(r.get("curr_total")))
                    .replace("{prev}", fmt_int(r.get("prev_total")))
                    .replace("{tot}", fmt_pct(r.get("total_delta_pct")))
                    .replace("{tot_cls}", get_pct_class(r.get("total_delta_pct")))
                    .replace("{spark_daily}", svg_sparkline(ser.total))  # 7일간 총 증감률 사용
                )
            else:
                # 주간 모드: 기존 전체 컬럼 표시
                row_html = TABLE_WEEKLY_ROW_TEMPLATE
                body_rows.append(
                    row_html
                    .replace("{site}", str(r.get("site", "")))
                    .replace("{curr}", fmt_int(r.get("curr_total")))
                    .replace("{prev}", fmt_int(r.get("prev_total")))
                    .replace("{wd}", fmt_pct(r.get("weekday_delta_pct")))
                    .replace("{wd_cls}", get_pct_class(r.get("weekday_delta_pct")))
                    .replace("{we}", fmt_pct(r.get("weekend_delta_pct")))
                    .replace("{we_cls}", get_pct_class(r.get("weekend_delta_pct")))
                    .replace("{tot}", fmt_pct(r.get("total_delta_pct")))
                    .replace("{tot_cls}", get_pct_class(r.get("total_delta_pct")))
                    .replace("{spark_wd}", svg_sparkline(ser.weekday))
                    .replace("{spark_we}", svg_sparkline(ser.weekend))
                    .replace("{spark_tot}", svg_sparkline(ser.total))
                )

        # 전체 조립
        return header + "".join(body_rows) + TABLE_FOOTER_TEMPLATE