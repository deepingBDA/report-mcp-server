"""
Summary Report용 차트 생성 클래스들
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from langchain_openai import ChatOpenAI
from libs.svg_renderer import svg_sparkline
from libs.weekly_domain import to_pct_series


class ChartGenerator(ABC):
    """차트 생성 베이스 클래스"""
    
    @abstractmethod
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """차트 HTML 생성"""
        pass


class SparklineChartGenerator(ChartGenerator):
    """스파크라인 차트 생성기"""
    
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """
        스파크라인 차트 생성
        기존 svg_sparkline 활용
        """
        # TODO: svg_sparkline을 활용한 스파크라인 생성
        # data에서 시리즈 데이터 추출 후 svg_sparkline 호출
        pass


class ScatterPlotGenerator(ChartGenerator):
    """산점도 차트 생성기"""
    
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """
        산점도 차트 생성
        기존 _build_scatter_card_html 로직을 이관
        """
        # TODO: 기존 _build_scatter_card_html 함수 내용 이관
        # x=금주 방문객(curr_total), y=총 증감률(total_delta_pct)
        pass


class PerformanceTableGenerator(ChartGenerator):
    """성과 테이블 생성기"""
    
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """
        성과 테이블 생성
        기존 _build_table_html 로직을 이관
        period에 따라 테이블 구조가 달라짐
        """
        period = config.get("period", 7) if config else 7
        
        if period == 1:
            # 1일 모드: 같은 요일 데이터 기반 테이블
            return self._generate_daily_table(data, config)
        else:
            # 7일 모드: 주간 데이터 기반 테이블  
            return self._generate_weekly_table(data, config)
    
    def _generate_daily_table(self, data: Dict, config: Optional[Dict] = None) -> str:
        """1일 모드 테이블 생성 (같은 요일 비교)"""
        # TODO: 1일 모드용 테이블 로직
        # - 전주 같은 요일과 비교
        # - 같은 요일 스파크라인 (4주간)
        pass
    
    def _generate_weekly_table(self, data: Dict, config: Optional[Dict] = None) -> str:
        """7일 모드 테이블 생성 (주간 비교)"""
        # TODO: 7일 모드용 테이블 로직
        # - 평일/주말/총 증감률
        # - 주간 스파크라인 (4주간)
        pass


class TrendSummaryGenerator(ChartGenerator):
    """LLM 기반 트렌드 요약 생성기"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        if llm is None:
            # 기본 LLM 설정
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        else:
            self.llm = llm
    
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """
        LLM을 활용한 트렌드 요약 생성
        기존 _summarize_node 로직을 이관
        """
        # TODO: 기존 _summarize_node 함수 내용 이관
        # LLM 프롬프트를 통한 요약 생성
        pass


class ActionItemGenerator(ChartGenerator):
    """액션 아이템 생성기 (1일 모드용)"""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        if llm is None:
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        else:
            self.llm = llm
    
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """
        액션 아이템 생성 (1일 모드용)
        """
        # TODO: 1일 모드용 액션 아이템 생성 로직
        pass


class NextActionsGenerator(ChartGenerator):
    """다음 액션 생성기 (7일 모드용)"""
    
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """
        다음 액션 생성 (7일 모드용)
        기존 _build_next_actions_card_html 로직을 이관
        """
        # TODO: 기존 _build_next_actions_card_html 함수 내용 이관
        pass


class ExplanationGenerator(ChartGenerator):
    """설명 생성기"""
    
    def generate(self, data: Dict, config: Optional[Dict] = None) -> str:
        """
        지표 설명 생성
        기존 _build_explanation_card_html 로직을 이관
        """
        # TODO: 기존 _build_explanation_card_html 함수 내용 이관
        pass