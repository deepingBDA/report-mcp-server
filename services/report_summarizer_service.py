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
        """Create a prompt for HTML content summarization."""
        return f"""
다음은 편의점 {report_type} 보고서 내용입니다. 이 보고서를 분석하여 다음 관점으로 요약해주세요:

📊 **시그널 분석 (전체 트렌드)**
- 전체 매장들의 평균 증감률을 계산하여 이번 주/일의 전반적인 시장 상황을 파악해주세요
- 날씨, 이벤트, 계절적 요인 등이 모든 매장에 공통으로 미친 영향을 추정해주세요
- 전체 시장이 움직인 방향성 (상승/하락/혼조)

🎯 **상대적 성과 분석 (평균 대비)**  
- 평균 증감률 대비 TOP 성과 매장들 (평균보다 얼마나 더 좋은지 %p로 표현)
- 평균 증감률 대비 저조한 성과 매장들 (평균보다 얼마나 나쁜지 %p로 표현)
- 예시 형식: "전체 평균 +3%인데 A매장은 +15% (평균 대비 +12%p 초과 달성)"

📈 **추세의 지속성 파악**
- 최근 몇 주간 지속적으로 상승 중인 매장 (연속 상승 패턴)
- 최근 몇 주간 지속적으로 하락 중인 매장 (연속 하락 패턴)
- 변동성이 큰 매장 (불안정한 패턴)

🔍 **호기심을 유발하는 탐구 질문들**
- "왜 같은 조건에서 이 매장들은 다른 결과를 보였을까?"
- "상위 매장의 성공 비결은 무엇일까? 무엇이 다를까?"
- "하위 매장에서 무슨 일이 일어나고 있을까? 어떤 변화가 있었나?"
- "이런 차이를 만든 근본 원인은 무엇일까?"

💡 **다음 단계 탐구 제안**
- 추가로 확인해봐야 할 데이터나 정보 (프로모션, 경쟁점, 공사 등)
- 심층 분석이 필요한 매장과 그 이유
- 벤치마킹하거나 케이스 스터디할 만한 우수/부진 사례
- 실무진이 현장에서 확인해봐야 할 구체적 액션

---
보고서 내용:
{content}

**중요:** 위 내용을 이메일 본문에 적합한 일반 텍스트 형태로 작성해주세요. 
- 마크다운 문법(#, **, -, 등) 사용하지 마세요
- 이모지와 구분선(----)만 사용해주세요  
- 섹션은 이모지로 구분하고 줄바꿈으로 정리해주세요
- 읽기 쉬운 일반 텍스트 형태로 작성해주세요
"""
    
    def _create_json_summarization_prompt(self, json_text: str, report_type: str) -> str:
        """Create a prompt for JSON data summarization."""
        return f"""
다음은 편의점 {report_type}의 JSON 데이터입니다. 이 데이터를 분석하여 핵심 내용을 요약해주세요:

📈 **데이터 하이라이트**
- 주요 수치와 지표
- 변화 추이

🎯 **핵심 포인트**
- 가장 중요한 발견사항
- 주의깊게 봐야 할 부분

---
JSON 데이터:
{json_text}
"""