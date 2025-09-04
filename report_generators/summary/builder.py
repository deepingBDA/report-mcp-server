"""Summary Report 빌더 (전체 오케스트레이션)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI

from .models import StoreRowDict
from .templates import (
    MAIN_PAGE_TEMPLATE,
    DAILY_SECTION_TEMPLATE,
    WEEKLY_SECTION_TEMPLATE,
)
from .data.extractors import create_extractor
from .generators.summary import (
    SummaryCardGenerator,
    ActionCardGenerator,
    NextActionsGenerator,
    ExplanationGenerator,
)
from .generators.table import TableCardGenerator
from .generators.scatter import ScatterCardGenerator


class SummaryReportBuilder:
    """Summary Report 빌더 클래스 (기존 로직 통합)."""
    
    def __init__(self, data_type: str):
        self.data_type = data_type
        self.extractor = create_extractor(data_type)
        
        # LLM 초기화
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # 생성기들 초기화
        self.summary_generator = SummaryCardGenerator()
        self.action_generator = ActionCardGenerator()
        self.table_generator = TableCardGenerator()
        self.scatter_generator = ScatterCardGenerator()
        self.next_actions_generator = NextActionsGenerator(self.llm)
        self.explanation_generator = ExplanationGenerator()
        
        # LLM 프롬프트들 (기존과 동일)
        self._summary_prompt_tpl = """
주어진 데이터를 바탕으로 정확히 아래 예시 형식을 따라 출력하세요.

[출력 예시]

예시 입력 데이터:
마천파크점: +24.8%, 역삼점: +8.6%, 금천프라임점: +7.0%, 타워팰리스점: +4.9%
신촌르메이에르점: -1.7%, 만촌힐스테이트점: -1.2%

올바른 출력:
<li class="trend-red"><span class="badge">지속 감소 매장: 만촌힐스테이트점 (총·4주 연속)</span></li>
<li><span class="pct-pos">▲증가 매장</span>: 마천파크점(<span class="pct-pos">+24.8%</span>), 역삼점(<span class="pct-pos">+8.6%</span>), 금천프라임점(<span class="pct-pos">+7.0%</span>), 타워팰리스점(<span class="pct-pos">+4.9%</span>)</li>
<li><span class="pct-neg">▼감소 매장</span>: 신촌르메이에르점(<span class="pct-neg">-1.7%</span>), 만촌힐스테이트점(<span class="pct-neg">-1.2%</span>)</li>

[핵심 규칙]
1. 지속 감소 매장: 별도의 <li> (가장 위에)
2. 증가 매장들: 모든 증가 매장을 하나의 <li>에 콤마로 연결
3. 감소 매장들: 모든 감소 매장을 하나의 <li>에 콤마로 연결
4. 절대 각 매장마다 별도의 <li> 만들지 마세요

데이터:
{table_text}
"""
        
        self._summary_daily_prompt_tpl = """
1일(일자별) 데이터를 바탕으로 정확히 아래 예시 형식을 따라 bullet 형식으로 작성하세요.

[출력 예시]

예시 입력 데이터:
타워팰리스점: 12,197명, +5.2%
마천파크점: 4,727명, +18.5% 
역삼점: 6,819명, +12.3%
신촌르메이에르점: 6,727명, -2.1%
금천프라임점: 3,794명, -0.8%

올바른 출력:
<li>전주 동일 요일 대비 증감률이 가장 높은 매장은 <span class="pct-pos">마천파크점 (+18.5%)</span>, 가장 낮은 매장은 <span class="pct-neg">신촌르메이에르점 (-2.1%)</span> 입니다.</li>
<li>주차별 증감률 추이에 따르면 타워팰리스점은 증가세이나 증가폭이 둔화되고 있으며, 신촌르메이에르점은 증가 추세를 보이고 있습니다.</li>
<li>금일 방문객 수 상위 2개 매장은 타워팰리스점 (12,197명), 역삼점 (6,819명)이고 하위 2개 매장은 금천프라임점 (3,794명), 마천파크점 (4,727명)입니다.</li>

[핵심 규칙]
1. 전주 동일 요일 대비 증감률이 가장 높은 매장은 <span class="pct-pos">, 가장 낮은 매장은 <span class="pct-neg"> CSS 클래스 사용
2. 주차별 증감률 추이를 증가세, 감소세, 증가폭 둔화 등으로 간단히 기술
3. 금일 방문객 수 상위 2개, 하위 2개 매장을 괄호 안에 명수 표시
4. bullet 형식으로 각 항목마다 <li> 태그 사용

데이터:
{table_text}
"""

    def build_report(self, end_date: str, stores: List[str], periods: List[int]) -> str:
        """리포트 생성 (현재는 period 하나만 처리)."""
        # periods는 하나의 값만 들어옴 (예: [1] 또는 [7])
        period = periods[0] if periods else 7
        
        # 1. 데이터 수집 (병렬 처리)
        rows = self._fetch_period_data(end_date, stores, period)
        
        # 2. LLM 요약 생성 (병렬로)
        llm_summary, llm_action = self._generate_llm_content(rows, period)
        
        # 3. 상태 데이터 구성
        state_data = self._build_state_data(end_date, period)
        
        # 4. 카드들 생성
        cards = self._build_cards(rows, end_date, period, state_data, llm_summary, llm_action)
        
        # 5. HTML 페이지 생성
        title = self._generate_title(end_date, period)
        section_html = self._build_section_html(period, cards)
        
        return MAIN_PAGE_TEMPLATE.format(
            title=title,
            body_html=section_html,
            css_rules=""
        )

    def _fetch_period_data(self, end_date: str, stores: List[str], period: int) -> List[StoreRowDict]:
        """병렬로 매장별 데이터 수집."""
        rows = []
        
        with ThreadPoolExecutor(max_workers=len(stores)) as executor:
            future_to_store = {
                executor.submit(self._fetch_store_data, store, end_date, period): store
                for store in stores
            }
            
            for future in as_completed(future_to_store):
                store = future_to_store[future]
                try:
                    store_data = future.result()
                    rows.append(store_data)
                except Exception as exc:
                    print(f"Store {store} generated an exception: {exc}")
                    rows.append({"site": store})
        
        # 증감률 기준으로 정렬 (None 값은 뒤로)
        return sorted(rows, key=lambda r: (
            0 if r.get("total_delta_pct") is not None else 1, 
            -(r.get("total_delta_pct") or 0)
        ))

    def _fetch_store_data(self, store: str, end_date: str, period: int) -> StoreRowDict:
        """매장별 데이터 수집."""
        return self.extractor.extract_period_rates(store, end_date, period)

    def _generate_llm_content(self, rows: List[StoreRowDict], period: int) -> tuple[str, str]:
        """LLM 요약 및 액션 생성."""
        # 테이블 텍스트 생성
        table_lines = []
        for r in rows:
            site = r.get("site", "")
            curr = r.get("curr_total", 0) or 0
            total_pct = r.get("total_delta_pct")
            if total_pct is not None:
                table_lines.append(f"{site}: {curr:,}명, {total_pct:+.1f}%")
            else:
                table_lines.append(f"{site}: {curr:,}명, N/A")
        
        table_text = "\\n".join(table_lines)
        
        # 병렬로 LLM 호출
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Summary 생성
            if period == 1:
                summary_prompt = self._summary_daily_prompt_tpl.replace("{table_text}", table_text)
            else:
                summary_prompt = self._summary_prompt_tpl.replace("{table_text}", table_text)
            
            summary_future = executor.submit(self._call_llm, summary_prompt)
            
            # Action 생성 (1일 모드에만)
            if period == 1:
                action_prompt = f"""
다음 데이터(매장별 방문객 수, 전주 동일 요일 대비 증감률, 주차별 추이)를 바탕으로 대시보드용 액션을 작성해줘.
"액션" 블록에서도 bullet 형식으로 작성하고, 각 매장 상황에 따른 권장 액션을 간단히 정리해:
- 주간 증감률추이와 타매장 대비 방문객수를 지표로 삼으면 돼
- 증감률이 증가하고 있는 매장은 원인(핵심 상품, 마케팅 효과 등)을 확인하고 확산 여부 검토
- 증감률 둔화나 감소세 매장은 원인 분석 및 개선 전략 필요
- 방문객 수는 높지만 증감률이 낮은 매장은 고객 유지 전략 필요
- 방문객 수가 저조한 매장은 지역 맞춤 마케팅/이벤트 강화 필요
[출력 형식]
- 매장명: 액션 요약내용 텍스트
매장명과 액션 요약 텍스트를 제외하고는 다른 내용은 추가하지 않음
데이터:
{table_text}"""
                action_future = executor.submit(self._call_llm, action_prompt)
            else:
                action_future = None
            
            # 결과 수집
            try:
                llm_summary = summary_future.result()
            except Exception as exc:
                print(f"[LLM Summary] 생성 실패: {exc}")
                llm_summary = ""
            
            if action_future:
                try:
                    llm_action = action_future.result()
                except Exception as exc:
                    print(f"[LLM Action] 생성 실패: {exc}")
                    llm_action = ""
            else:
                llm_action = ""
        
        return llm_summary, llm_action

    def _call_llm(self, prompt: str) -> str:
        """LLM 호출 헬퍼."""
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)

    def _build_state_data(self, end_date: str, period: int) -> dict:
        """상태 데이터 구성."""
        if period == 1:
            return {
                "compare_lag": 1,
                "period_label": "금일",
                "prev_label": "전주 동일 요일",
            }
        else:
            return {
                "compare_lag": period,
                "period_label": "금주" if period == 7 else f"최근 {period}일",
                "prev_label": "전주" if period == 7 else f"이전 {period}일",
            }

    def _build_cards(self, rows: List[StoreRowDict], end_date: str, period: int, 
                     state_data: dict, llm_summary: str, llm_action: str) -> Dict[str, str]:
        """카드들 생성."""
        cards = {}
        
        # Summary 카드 (항상 생성)
        cards["summary"] = self.summary_generator.generate(rows, llm_summary)
        
        # Action 카드 (1일 모드만)
        if period == 1:
            cards["action"] = self.action_generator.generate(rows, llm_action)
        
        # Table 카드 (항상 생성)
        cards["table"] = self.table_generator.generate(rows, end_date, period, state_data)
        
        # Scatter 카드 (항상 생성)
        cards["scatter"] = self.scatter_generator.generate(rows)
        
        # Next Actions 카드 (7일 모드만)
        if period != 1:
            cards["next"] = self.next_actions_generator.generate(rows, llm_summary, end_date)
        
        # Explanation 카드 (7일 모드만)
        if period != 1:
            title_suffix = f"{period}일" if period != 7 else "주간"
            cards["explain"] = self.explanation_generator.generate(title_suffix)
        
        return cards

    def _build_section_html(self, period: int, cards: Dict[str, str]) -> str:
        """섹션 HTML 생성."""
        section_id = f"section-{period}"
        
        if period == 1:
            # 1일 모드 템플릿
            return DAILY_SECTION_TEMPLATE.format(
                section_id=section_id,
                summary=cards["summary"],
                action=cards["action"],
                table=cards["table"],
                scatter=cards["scatter"]
            )
        else:
            # 7일+ 모드 템플릿
            return WEEKLY_SECTION_TEMPLATE.format(
                section_id=section_id,
                summary=cards["summary"],
                table=cards["table"],
                scatter=cards["scatter"],
                next=cards["next"],
                explain=cards["explain"]
            )

    def _generate_title(self, end_date: str, period: int) -> str:
        """리포트 타이틀 생성."""
        from datetime import date
        
        end_date_obj = date.fromisoformat(end_date)
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        weekday_name = weekdays[end_date_obj.weekday()]
        
        if period == 1:
            return f"방문 현황 요약 통계({end_date} {weekday_name})"
        else:
            return f"방문 현황 요약 통계({end_date} 기준 {period}일)"

    def get_current_timestamp(self) -> str:
        """현재 시간 반환."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")