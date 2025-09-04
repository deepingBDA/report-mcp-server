"""Summary 카드 생성기 (LLM 기반 요약 및 액션)."""

from __future__ import annotations

from typing import List, Optional

from langchain_openai import ChatOpenAI

from ..models import StoreRowDict, process_llm_content
from ..templates import (
    SUMMARY_CARD_TEMPLATE,
    ACTION_CARD_TEMPLATE,
    SUMMARY_DEFAULT_CONTENT,
    ACTION_DEFAULT_CONTENT,
)


class SummaryCardGenerator:
    """Summary 카드 생성기 (기존 _build_summary_card_html 로직 이관)."""
    
    def generate(self, rows: List[StoreRowDict], llm_summary: str) -> str:
        """Summary 카드 HTML 생성."""
        # 디버깅을 위한 로그 추가 (기존 코드 유지)
        print(f"DEBUG: _build_summary_card_html 호출됨")
        print(f"DEBUG: llm_summary 길이: {len(llm_summary) if llm_summary else 0}")
        print(f"DEBUG: llm_summary 내용: {llm_summary[:200] if llm_summary else 'None'}...")
        
        # LLM 요약을 HTML로 렌더링 (기존 로직 완전 보존)
        if llm_summary and llm_summary.strip():
            content = process_llm_content(llm_summary, "summary-list")
            print(f"DEBUG: LLM 요약을 HTML로 변환")
        else:
            content = SUMMARY_DEFAULT_CONTENT
            print(f"DEBUG: 기본 안내문 사용")

        return SUMMARY_CARD_TEMPLATE.format(content=content)


class ActionCardGenerator:
    """Action 카드 생성기 (1일 모드 전용, 기존 _build_action_card_html 로직 이관)."""
    
    def generate(self, rows: List[StoreRowDict], llm_action: str) -> str:
        """Action 카드 HTML 생성 (1일 모드 전용)."""
        # LLM 액션을 HTML로 렌더링 (기존 로직 완전 보존)
        if llm_action and llm_action.strip():
            content = process_llm_content(llm_action, "action-list")
        else:
            content = ACTION_DEFAULT_CONTENT

        return ACTION_CARD_TEMPLATE.format(content=content)


class NextActionsGenerator:
    """다음 액션 카드 생성기 (7일 모드용)."""
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        if llm is None:
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        else:
            self.llm = llm
    
    def generate(self, rows: List[StoreRowDict], llm_summary: str, end_iso: Optional[str] = None) -> str:
        """다음 액션 카드 생성 (기존 _build_next_actions_card_html 로직 이관)."""
        # 기존 _pair_prompt_tpl 사용
        pair_prompt_tpl = """
            [다음 단계 지침 + 스타일]

            당신의 작업:
            - 주간 리포트 테이블을 바탕으로 매장 성과 매트릭스를 분석하여 "매장 페어"를 선정하고 HTML 카드로 출력한다.

            선정 규칙:
            1) 테이블의 "금주 방문객" 컬럼 기준으로 방문객 수가 유사한 두 매장을 페어로 묶는다.
            • **유사성 기준**: 두 매장의 금주 방문객 수 차이가 평균 대비 30% 이하인 경우
            • [평균 방문객수] = (매장 A 금주 방문객 + 매장 B 금주 방문객) / 2
            • **중요**: 테이블에서 "금주 방문객" 컬럼의 값을 읽어야 함
            • 이 값은 반드시 양의 정수여야 하며, 소수점이 있으면 반올림
            2) 전주 대비 총 증감률이 반대 흐름(한쪽 증가, 한쪽 감소)이면 → "전주 대비 방문객 증감률 반대 흐름"
            3) 두 매장 모두 증가(또는 감소)이지만 증감 폭 차이가 크면 → "전주 대비 방문객 증감 폭 차이 큼"

            출력 형식 (HTML):
            <ul class="pair-list">
            <li class="pair-item">
                <div class="pair-head">
                <div class="pair-names">매장A vs 매장B</div>
                <span class="criteria-badge">선정 기준 요약</span>
                </div>
                <div class="pair-note">두 매장 평균 방문객: <span class="pct-pos"><b>[평균 방문객수]명</b></span>, [선정 기준 상세 설명]</div>
            </li>
            … (페어 개수만큼 반복)
            </ul>

            스타일 규칙:
            - [평균 방문객수]명은 <span class="pct-pos"><b>…</b></span>로 감싸 파란색 + 볼드 처리
            - 불필요한 설명/코드블록 없이 오직 <ul class="pair-list"> … </ul> 구조만 출력한다.


            데이터:
            {table_text}
            """
        
        # 테이블 텍스트 생성 (기존 로직 유지)
        table_lines = []
        for r in rows:
            site = r.get("site", "")
            curr = r.get("curr_total", 0) or 0
            total_pct = r.get("total_delta_pct")
            if total_pct is not None:
                table_lines.append(f"{site}: {curr}명, {total_pct:+.1f}%")
            else:
                table_lines.append(f"{site}: {curr}명, N/A")
        
        table_text = "\n".join(table_lines)
        
        try:
            # LLM 호출
            prompt = pair_prompt_tpl.replace("{table_text}", table_text)
            response = self.llm.invoke(prompt)
            pair_content = response.content if hasattr(response, 'content') else str(response)
            
            # 코드펜스 제거
            if pair_content.startswith("```") and pair_content.endswith("```"):
                pair_content = "\n".join(pair_content.splitlines()[1:-1])
            
            pair_content = pair_content.strip()
            
        except Exception as exc:
            print(f"[NextActionsGenerator] LLM 호출 실패: {exc}")
            pair_content = """
            <div style="text-align: center; padding: 12px; color: #6b7280;">
              <p style="margin: 0; font-size: 14px;">⚡ <strong>다음 단계 분석</strong></p>
              <p style="margin: 6px 0 0 0; font-size: 12px;">매장 성과 데이터를 분석하여<br>개선 방향을 제안합니다</p>
            </div>
            """
        
        return f"""
<section class="card">
  <h3>다음 단계</h3>
  <div style="margin-top: 8px;">
    {pair_content}
  </div>
  <!-- section:next-actions -->
</section>
"""


class ExplanationGenerator:
    """지표 설명 생성기."""
    
    def generate(self, title_suffix: str) -> str:
        """지표 설명 카드 생성 (기존 _build_explanation_card_html 로직 이관)."""
        return f"""
<section class="card">
  <h2>지표 설명</h2>
  <p class="muted">이 표는 각 매장의 평일 증감률, 주말 증감률, 그리고 전체 기간(총) 증감률을 나타냅니다.</p>
  <ul class="bullets">
    <li><b>평일 증감률</b>: 해당 매장의 평일 방문자 수가 전 기간 대비 얼마나 증가 감소했는지를 백분율로 표시</li>
    <li><b>주말 증감률</b>: 주말(토·일) 방문자 수의 변동률</li>
    <li><b>총 증감률</b>: 평일과 주말을 합산한 전체 기간 대비 변동률</li>
    <li><b>주차별 평일/주말/총 증감률</b>: 최근 4주(금주 포함)의 전주 대비 방문율을 주차별로 비교</li>
  </ul>
  <p class="muted">매장별 상승·하락 추세를 진단하고, 최근 4주간의 증감률 변화를 통해 해당 추세가 일시적인지, 지속적인지 판단할 수 있습니다.</p>
  <p class="muted">지속적인 추세를 보이는 매장은 면밀히 관찰이 필요합니다.</p>
  <!-- section:explanation -->
</section>
"""