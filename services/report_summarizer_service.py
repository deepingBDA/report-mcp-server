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
                        "content": "당신은 편의점 매출 데이터 분석 전문가입니다. 데이터 리포트를 간결하고 핵심적으로 요약해주세요."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3
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
                temperature=0.3
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
다음은 편의점 {report_type} 보고서 내용입니다. 이 보고서를 분석하여 다음 형식으로 요약해주세요:

📊 **주요 지표 요약**
- 핵심 매출/방문자 수치
- 전일/전주 대비 증감률

🔍 **주목할 점**
- 가장 눈에 띄는 변화나 특이사항
- 성과가 좋은 부분과 개선이 필요한 부분

💡 **인사이트**
- 데이터에서 도출할 수 있는 비즈니스 통찰

---
보고서 내용:
{content}
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