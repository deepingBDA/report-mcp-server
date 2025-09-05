"""Report summarizer service for summarizing HTML/JSON reports using OpenAI."""

import os
import logging
from typing import Dict, Any, Optional
import json
import re
from bs4 import BeautifulSoup

from openai import OpenAI

logger = logging.getLogger(__name__)


class ReportSummarizerService:
    """Service class for summarizing reports using OpenAI GPT."""
    
    def __init__(self):
        """Initialize the summarizer service."""
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def summarize_html_report(
        self, 
        html_content: str,
        report_type: str = "daily_report",
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Summarize HTML report content using OpenAI GPT.
        
        Args:
            html_content: The HTML content to summarize
            report_type: Type of report (daily_report, weekly_report, etc.)
            max_tokens: Maximum tokens for the summary
            
        Returns:
            Dict containing success status, summary text, and metadata
        """
        try:
            # Extract meaningful content from HTML
            extracted_content = self._extract_content_from_html(html_content)
            
            if not extracted_content:
                raise ValueError("HTML content에서 텍스트를 추출할 수 없습니다")
            
            # Create prompt for summarization
            prompt = self._create_summarization_prompt(extracted_content, report_type)
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 데이터 기반 편의점 운영 분석가입니다. 매장 간 성과를 상대적으로 비교하고, 숨겨진 패턴을 발견하며, 추가 탐구가 필요한 질문을 제시하는 것이 당신의 역할입니다. 전체 시장 트렌드(시그널)를 파악하고, 개별 매장의 상대적 성과를 분석하며, 호기심을 자극하는 인사이트를 제공해주세요."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info(f"Successfully summarized {report_type} report")
            
            return {
                "success": True,
                "summary": summary,
                "report_type": report_type,
                "original_content_length": len(html_content),
                "extracted_content_length": len(extracted_content),
                "tokens_used": response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"Report summarization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": None,
                "report_type": report_type
            }
    
    def summarize_json_data(
        self,
        json_data: Dict[str, Any],
        report_type: str = "daily_report",
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Summarize JSON report data using OpenAI GPT.
        
        Args:
            json_data: The JSON data to summarize
            report_type: Type of report
            max_tokens: Maximum tokens for the summary
            
        Returns:
            Dict containing success status, summary text, and metadata
        """
        try:
            # Convert JSON to readable text
            json_text = json.dumps(json_data, ensure_ascii=False, indent=2)
            
            # Create prompt for summarization
            prompt = self._create_json_summarization_prompt(json_text, report_type)
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 편의점 매출 데이터 분석 전문가입니다. JSON 데이터를 분석하여 핵심 인사이트를 제공해주세요."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content.strip()
            
            logger.info(f"Successfully summarized JSON {report_type}")
            
            return {
                "success": True,
                "summary": summary,
                "report_type": report_type,
                "data_size": len(json_text),
                "tokens_used": response.usage.total_tokens if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"JSON summarization failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": None,
                "report_type": report_type
            }
    
    def _extract_content_from_html(self, html_content: str) -> str:
        """Extract meaningful text content from HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            text = soup.get_text()
            
            # Clean up whitespace and empty lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = '\n'.join(lines)
            
            # Limit content length to avoid token limits
            max_content_length = 8000  # Approximate limit for context
            if len(cleaned_text) > max_content_length:
                cleaned_text = cleaned_text[:max_content_length] + "..."
                logger.warning(f"Content truncated to {max_content_length} characters")
            
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Failed to extract content from HTML: {e}")
            return ""
    
    def _create_summarization_prompt(self, content: str, report_type: str) -> str:
        """
        Summarization prompt: Global avg & ±10%p band → Only outlier stores (good/bad).
        Focus on 매출 방향 → 풋폴 추론 → 액션/검증.
        """
        return f"""
    너는 편의점 {report_type} 일일 리포트를 요약하는 리테일 분석 코파일럿이다.
    최종 출력은 이메일 본문에 그대로 붙일 "일반 텍스트"여야 한다. 
    마크다운 문법(#, **, -, 등)은 절대 쓰지 말고, 오직 이모지와 구분선(----)만 사용하라.
    반말 톤으로 간결하고 실행지향적으로 써라.

    목표:
    1) 전체 매장 평균 증감률 계산, ±10%p 범위를 기준으로 "일상 변동"과 "아웃라이어"를 구분
    2) 아웃라이어(평균 대비 +10%p 초과 또는 -10%p 초과) 매장에 대해서만 상세 카드 생성
    3) 카드 안에서는 "매출 방향 판정 → 풋폴 방향 추론 → 오늘의 액션 → 검증/측정"을 정리
    4) 수치·날짜·단위 표준화, 불확실성은 명확히 표기(N/A, 추정, 신뢰도)

    ==================== 출력 형식 ====================

    🌐 전체 개요
    - 기준일과 비교 기준을 한 줄로 명시(예: 2025-09-05, 전주 동요일 기준)
    - 전체 평균 증감률 한 줄 요약(예: 전체 평균 +3%)
    - 외생 요인(날씨/이벤트/계절성 등)이 명확하다면 한 줄 추정

    📊 평균 대비 성과 분포
    - 평균 ±10%p 이내: "일상 변동 범위"로만 간단히 언급
    - 평균 +10%p 초과(상위 아웃라이어): 매장명과 (평균 대비 +x%p) 3개 이내
    - 평균 -10%p 초과(하위 아웃라이어): 매장명과 (평균 대비 -x%p) 3개 이내

    🧠 호기심 유발 포인트
    - 상위 아웃라이어: 왜 이렇게 잘 나왔는지 가설 1~2개(상품/시간대/프로모션/동선 등)
    - 하위 아웃라이어: 왜 급락했는지 가설 1~2개(수요/전환율/객단가/경쟁 등)
    - 각 가설은 근거 수치가 있으면 괄호로 짧게 표기

    ----
    이후, 아웃라이어 매장만 카드 생성(±10%p 벗어난 매장).
    각 카드에 아래 섹션 포함:

    🧭 매장/기간
    - 매장명, 기준일, 비교 기준 한 줄
    - 날짜/지표 불일치 시 "참고/추정"으로 표시

    📊 매출 방향 판정
    - up / down / flat / unknown 중 하나
    - 핵심 근거 1~2개만 숫자로 (예: 전주 대비 +12%p)
    - 거래수/영수증 수, AOV 있으면 함께, 없으면 N/A

    👣 풋폴(방문) 방향 추론
    - up / down / flat / unknown + 신뢰도(low/medium/high)
    - 거래수·AOV 없으면 최소 2개 가설로 설명

    🎯 오늘의 액션(2–3개)
    - 발주/진열/프로모션/스태핑 중 필요한 것만
    - 각 조치 옆에 근거 수치를 괄호로 1줄 표기

    🧪 검증/측정(1개 이상)
    - 1주 내 검증 가능한 미니 실험: 무엇을/언제/어떻게 측정할지 한 줄

    ⚠ 데이터 공백/품질 메모
    - N/A 항목, 이상치, 날짜 불일치 등 한 줄

    ----
    보고서 원문:
    {content}

    **중요:** 
    - 평균 ±10%p 이내 매장은 카드로 만들지 말고, "일상 변동"으로만 전체 개요에서 언급. 
    - 상세 카드는 아웃라이어 매장만 생성.
    - 마크다운 금지, 이모지/구분선만 허용.
    """


def _create_json_summarization_prompt(self, json_text: str, report_type: str) -> str:
    """Create a prompt for JSON data summarization aligned with sales trend → footfall inference → actions."""
    return f"""
다음은 편의점 {report_type}의 JSON 데이터다. 매장별로 "매출 방향 → 풋폴 방향 → 실행/검증" 순서로 요약해줘.

출력 규칙(이메일 본문용 일반 텍스트):
- 마크다운 문법 금지(#, **, -, 등). 이모지와 구분선(----)만 사용.
- 매장별 카드 반복. 조치 옆에 근거 수치 괄호 표기.
- 거래수/AOV/풋폴 값이 없으면 N/A로 표기하고 가설 복수 제시(신뢰도는 low).

필수 섹션(매장별):
🧭 매장/기간 정렬
📊 매출 방향 판정(up/down/flat/unknown + 근거 수치)
👣 풋폴 방향 추론(up/down/flat/unknown + 신뢰도)
🎯 오늘의 액션(2–4개, 발주/진열/프로모션/스태핑)
🧪 검증/측정(실험·지표·성공기준)
⚠ 데이터 공백/품질 메모

단위 표준화: 금액(원), 수량(개), 방문(명), 거래(건), 시간(KST)

---
JSON 데이터:
{json_text}
"""