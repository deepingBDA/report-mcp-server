"""
Summary Report 빌더 클래스
"""

from __future__ import annotations
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .data_extractors import create_extractor, SummaryDataExtractor
from .chart_generators import (
    SparklineChartGenerator,
    ScatterPlotGenerator, 
    PerformanceTableGenerator,
    TrendSummaryGenerator,
    ActionItemGenerator,
    NextActionsGenerator,
    ExplanationGenerator
)
from .card_composers import get_cards_for_period, create_card_composer
from .constants import *


class SummaryReportBuilder:
    """Summary Report 빌더 클래스"""
    
    def __init__(self, data_type: str):
        self.data_type = data_type
        self.extractor = create_extractor(data_type)
        self.chart_generators = self._init_chart_generators()
        self.card_composers = self._init_card_composers()
    
    def _init_chart_generators(self) -> Dict:
        """차트 생성기 초기화"""
        return {
            "sparkline": SparklineChartGenerator(),
            "scatter": ScatterPlotGenerator(),
            "table": PerformanceTableGenerator(),
            "summary": TrendSummaryGenerator(),
            "action": ActionItemGenerator(),
            "next_actions": NextActionsGenerator(),
            "explanation": ExplanationGenerator(),
        }
    
    def _init_card_composers(self) -> Dict:
        """카드 구성기 초기화"""
        composers = {}
        for card_type in ["summary", "action", "table", "scatter", "next_actions", "explanation"]:
            composers[card_type] = create_card_composer(card_type, self.chart_generators)
        return composers
    
    def _fetch_single_period_data(self, end_date: str, stores: List[str], period: int) -> Dict:
        """단일 period 데이터 수집 (간소화)"""
        period_data = {}
        
        # 병렬 처리로 매장별 데이터 수집
        with ThreadPoolExecutor(max_workers=len(stores)) as executor:
            future_to_store = {
                executor.submit(self._fetch_store_data, store, end_date, period): store
                for store in stores
            }
            
            for future in as_completed(future_to_store):
                store = future_to_store[future]
                try:
                    store_data = future.result()
                    period_data[store] = store_data
                except Exception as exc:
                    print(f"Store {store} generated an exception: {exc}")
                    period_data[store] = self._get_empty_store_data()
        
        return period_data
    
    def _fetch_store_data(self, store: str, end_date: str, period: int) -> Dict:
        """매장별 데이터 수집"""
        return {
            "rates": self.extractor.extract_period_rates(store, end_date, period),
            "series": self._fetch_series_for_period(store, end_date, period)
        }
    
    def _fetch_series_for_period(self, store: str, end_date: str, period: int) -> Dict:
        """기간별 시리즈 데이터 수집"""
        if period == 1:
            # 1일 모드
            return {
                "daily": self.extractor.extract_daily_series(store, end_date),
                "same_weekday": self.extractor.extract_same_weekday_series(store, end_date)
            }
        else:
            # 7일 이상 모드
            return {
                "weekly": self.extractor.extract_weekly_series(store, end_date)
            }
    
    def _get_empty_store_data(self) -> Dict:
        """빈 매장 데이터 반환 (에러 시 사용)"""
        return {
            "rates": {},
            "series": {}
        }
    
    def build_report(self, end_date: str, stores: List[str], periods: List[int]) -> str:
        """리포트 생성 (현재는 period 하나만 처리)"""
        # periods는 하나의 값만 들어옴 (예: [1] 또는 [7])
        period = periods[0] if periods else 7
        
        # 1. 데이터 수집 (단일 period)
        data = self._fetch_single_period_data(end_date, stores, period)
        
        # 2. 카드들 생성
        cards = self._build_cards(period, data)
        
        # 3. HTML 페이지 생성 (섹션 래핑 없이)
        title = self._generate_title(end_date, [period])
        return self._build_simple_html_page(title, cards)
    
    def _build_cards(self, period: int, data: Dict) -> List[str]:
        """카드들 생성 (단일 period)"""
        cards = []
        card_types = get_cards_for_period(period)
        
        for card_type in card_types:
            try:
                card_html = self.card_composers[card_type].compose(
                    title=f"{period}일 {card_type}",
                    content=data,
                    period=period
                )
                cards.append(card_html)
            except Exception as exc:
                print(f"Card {card_type} generation failed: {exc}")
                # 에러 시 기본 카드 생성
                cards.append(self._get_error_card(card_type, str(exc)))
        
        return cards
    
    def _get_error_card(self, card_type: str, error: str) -> str:
        """에러 카드 생성"""
        return f"""
<section class="card">
    <h3>{card_type.title()} Card Error</h3>
    <p class="muted">Error generating {card_type}: {error}</p>
</section>
"""
    
    def _generate_title(self, end_date: str, periods: List[int]) -> str:
        """리포트 타이틀 생성"""
        period = periods[0] if periods else 7
        period_str = f"{period}일" if period == 1 else f"{period}일간"
        return f"{self.data_type.title()} Summary Report ({period_str}) - {end_date}"
    
    def _build_simple_html_page(self, title: str, cards: List[str]) -> str:
        """
        HTML 페이지 생성 (단일 period용 간단한 구조)
        """
        body_html = ''.join(cards)
        
        return f"""
<!doctype html>
<html lang="ko">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', Arial, sans-serif; margin: 0; background: #fafafa; color: #111; }}
        .container {{ max-width: 1080px; margin: 24px auto; padding: 0 16px; }}
        .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
        .card h2, .card h3 {{ margin: 0 0 8px; font-size: 18px; }}
        .muted {{ color: #6b7280; font-size: 13px; }}
        .pct-pos {{ color: #dc2626; }}
        .pct-neg {{ color: #1d4ed8; }}
        .pct-zero {{ color: #374151; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="page-header">
            <h1>{title}</h1>
            <p class="desc">Generated at {self._get_current_timestamp()}</p>
        </header>
        
        {body_html}
    </div>
</body>
</html>
"""
    
    def _get_current_timestamp(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")