"""
Summary Report용 카드 구성 클래스들
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .chart_generators import (
    ChartGenerator, 
    PerformanceTableGenerator, 
    ScatterPlotGenerator,
    TrendSummaryGenerator,
    ActionItemGenerator,
    NextActionsGenerator,
    ExplanationGenerator
)


class CardComposer(ABC):
    """카드 구성 베이스 클래스"""
    
    @abstractmethod
    def compose(self, title: str, content: Dict, period: int) -> str:
        """카드 HTML 생성"""
        pass


class SummaryCard(CardComposer):
    """요약 카드"""
    
    def __init__(self, summary_generator: TrendSummaryGenerator):
        self.summary_generator = summary_generator
    
    def compose(self, title: str, content: Dict, period: int) -> str:
        """
        요약 카드 생성
        기존 _build_summary_card_html 로직을 이관
        """
        # TODO: 기존 _build_summary_card_html 함수 내용 이관
        # LLM 요약을 HTML로 렌더링
        pass


class ActionCard(CardComposer):
    """액션 카드 (1일 모드)"""
    
    def __init__(self, action_generator: ActionItemGenerator):
        self.action_generator = action_generator
    
    def compose(self, title: str, content: Dict, period: int) -> str:
        """
        액션 카드 생성 (1일 모드용)
        기존 _build_action_card_html 로직을 이관
        """
        # TODO: 기존 _build_action_card_html 함수 내용 이관
        pass


class TableCard(CardComposer):
    """테이블 카드"""
    
    def __init__(self, table_generator: PerformanceTableGenerator):
        self.table_generator = table_generator
    
    def compose(self, title: str, content: Dict, period: int) -> str:
        """
        테이블 카드 생성
        period에 따라 다른 테이블 구조 적용
        """
        # period 정보를 config로 전달
        config = {"period": period}
        table_html = self.table_generator.generate(content, config)
        
        # period에 따른 테이블 제목
        if period == 1:
            table_title = "일별 방문 증감률 (전주 같은 요일 대비)"
        else:
            table_title = "주간 방문 증감률 (평일/주말/총)"
        
        return f"""
<section class="card">
    <h3>{table_title}</h3>
    {table_html}
    <!-- section:table -->
</section>
"""


class ScatterCard(CardComposer):
    """산점도 카드"""
    
    def __init__(self, scatter_generator: ScatterPlotGenerator):
        self.scatter_generator = scatter_generator
    
    def compose(self, title: str, content: Dict, period: int) -> str:
        """
        산점도 카드 생성
        """
        scatter_html = self.scatter_generator.generate(content)
        
        return f"""
<section class="card">
    <h3>매장 성과</h3>
    {scatter_html}
    <!-- section:scatter -->
</section>
"""


class NextActionsCard(CardComposer):
    """다음 액션 카드 (7일 모드)"""
    
    def __init__(self, next_actions_generator: NextActionsGenerator):
        self.next_actions_generator = next_actions_generator
    
    def compose(self, title: str, content: Dict, period: int) -> str:
        """
        다음 액션 카드 생성 (7일 모드용)
        """
        next_actions_html = self.next_actions_generator.generate(content)
        
        return f"""
<section class="card">
    <h3>다음 액션</h3>
    {next_actions_html}
    <!-- section:next-actions -->
</section>
"""


class ExplanationCard(CardComposer):
    """설명 카드"""
    
    def __init__(self, explanation_generator: ExplanationGenerator):
        self.explanation_generator = explanation_generator
    
    def compose(self, title: str, content: Dict, period: int) -> str:
        """
        설명 카드 생성
        """
        explanation_html = self.explanation_generator.generate(content)
        
        return f"""
<section class="card">
    <h2>지표 설명</h2>
    {explanation_html}
    <!-- section:explanation -->
</section>
"""


def get_cards_for_period(period: int) -> List[str]:
    """기간별 필요한 카드 목록 반환"""
    if period == 1:
        # 1일 모드: 요약, 액션, 테이블, 산점도
        return ["summary", "action", "table", "scatter"]
    elif period == 7:
        # 7일 모드: 요약, 테이블, 산점도, 다음단계, 지표설명
        return ["summary", "table", "scatter", "next_actions", "explanation"]
    else:
        # 기타 기간
        return ["summary", "table", "scatter", "next_actions", "explanation"]


def create_card_composer(card_type: str, chart_generators: Dict) -> CardComposer:
    """카드 타입에 따른 CardComposer 팩토리"""
    composers = {
        "summary": lambda: SummaryCard(chart_generators["summary"]),
        "action": lambda: ActionCard(chart_generators["action"]),
        "table": lambda: TableCard(chart_generators["table"]),
        "scatter": lambda: ScatterCard(chart_generators["scatter"]),
        "next_actions": lambda: NextActionsCard(chart_generators["next_actions"]),
        "explanation": lambda: ExplanationCard(chart_generators["explanation"]),
    }
    
    if card_type not in composers:
        raise ValueError(f"Unknown card_type: {card_type}")
    
    return composers[card_type]()