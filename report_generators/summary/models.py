"""Summary Report 데이터 모델 정의."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict, Any

from libs.base_workflow import BaseState


class SummaryReportState(BaseState):
    """Summary Report Workflow 상태."""
    
    data_type: str
    end_date: str
    stores: List[str]
    periods: List[int]  # 예: [7, 30]
    compare_lag: int
    period_label: str
    prev_label: str
    rows_by_period: Dict[int, List[Dict[str, Optional[float]]]]
    html_content: str
    llm_summary: str
    llm_action: str
    final_result: str


@dataclass
class RenderSeries:
    """시계열 데이터 렌더링용 클래스."""
    
    weekday: List[float]
    weekend: List[float]
    total: List[float]


# 기존 Dict 구조를 유지하면서 타입 힌트만 추가
class StoreRowDict(TypedDict, total=False):
    """매장별 행 데이터 (기존 Dict 구조 유지)."""
    
    site: str
    curr_total: Optional[int]
    prev_total: Optional[int]
    weekday_delta_pct: Optional[float]
    weekend_delta_pct: Optional[float]
    total_delta_pct: Optional[float]


class WeeklySeriesDict(TypedDict, total=False):
    """주간 시리즈 데이터 (기존 Dict 구조 유지)."""
    
    weekday: List[int]
    weekend: List[int]
    total: List[int]


class DailySeriesDict(TypedDict, total=False):
    """일간 시리즈 데이터 (기존 Dict 구조 유지)."""
    
    weekday: List[int]
    weekend: List[int]
    total: List[int]


class SameDaySeriesDict(TypedDict, total=False):
    """같은 요일 시리즈 데이터 (기존 Dict 구조 유지)."""
    
    total: List[int]


# 유틸리티 함수들 (기존 코드에서 사용되는 것들)
def fmt_int(value: Optional[int]) -> str:
    """정수 포맷팅 (기존 _fmt_int 함수와 동일)."""
    if value is None:
        return "N/A"
    return f"{value:,}"


def fmt_pct(value: Optional[float]) -> str:
    """퍼센트 포맷팅 (기존 _fmt_pct 함수와 동일)."""
    if value is None:
        return "N/A"
    return f"{value:+.1f}%"


def get_pct_class(value: Optional[float]) -> str:
    """퍼센트 값에 따른 CSS 클래스 반환."""
    if value is None:
        return "pct-zero"
    if value > 0:
        return "pct-pos"
    elif value < 0:
        return "pct-neg"
    else:
        return "pct-zero"


def escape_html(text: str) -> str:
    """HTML 이스케이프 (기존 _escape_html 함수와 동일)."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def process_llm_content(llm_content: str, list_class: str = "summary-list") -> str:
    """LLM 출력을 HTML로 변환 (기존 로직 완전 보존)."""
    if not llm_content or not llm_content.strip():
        return ""
    
    raw = llm_content.strip()
    
    # 코드펜스 제거
    if raw.startswith("```") and raw.endswith("```"):
        raw = "\n".join(raw.splitlines()[1:-1]).strip()
    
    # HTML 그대로 사용
    if "<ul" in raw and "<li" in raw:
        return raw
    elif raw.startswith("<li") and "</li>" in raw:
        return f'<ul class="{list_class}">{raw}</ul>'
    else:
        # 마크다운 불릿을 HTML li 태그로 변환
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        items = []
        for ln in lines:
            if ln.startswith("- "):
                items.append(ln[2:].strip())
            else:
                items.append(ln)
        li_html = "\n".join(f"<li>{escape_html(it)}</li>" for it in items)
        return f'<ul class="{list_class}">{li_html}</ul>'