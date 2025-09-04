"""
Summary Report Workflow (Modular Version)
"""

from __future__ import annotations
import sys
from pathlib import Path

# 📁 절대경로 import 방법들:

# 방법 1: sys.path에 프로젝트 루트 추가 (추천)
PROJECT_ROOT = Path(__file__).parent.parent  # report-mcp-server 디렉토리
sys.path.insert(0, str(PROJECT_ROOT))

# 방법 2: PYTHONPATH 환경변수 사용 (실행 시 설정)
# export PYTHONPATH=/Users/junho/report-mcp-server:$PYTHONPATH

# 방법 3: 패키지 설치 (pip install -e .)
# pyproject.toml이나 setup.py 만들어서 개발 모드로 설치

# 이제 절대 경로로 import 가능
from libs.base_workflow import BaseWorkflow, BaseState
from libs.database import get_all_sites
from report_generators.summary import SummaryReportBuilder

from typing import Any, Dict, List, Optional, Sequence
from datetime import date


class SummaryReportState(BaseState):
    data_type: str
    end_date: str
    stores: List[str] 
    periods: List[int]
    html: Optional[str] = None


class SummaryReportGenerator:
    """모듈화된 Summary Report Generator"""
    
    def __init__(self) -> None:
        pass
    
    def run(
        self,
        data_type: str = "visitor",
        end_date: Optional[str] = None,
        stores: Optional[Sequence[str]] = None,
        periods: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Summary Report 실행"""
        
        # 기본값 설정
        if end_date is None:
            end_date = date.today().isoformat()
        
        if stores is None:
            all_sites = get_all_sites()
            # get_all_sites가 문자열 리스트를 반환하는 경우 처리
            if all_sites and isinstance(all_sites[0], str):
                stores = all_sites
            elif all_sites and isinstance(all_sites[0], dict):
                stores = [site["name"] for site in all_sites if site.get("enabled", True)]
            else:
                stores = all_sites if all_sites else []
            
            # 망우혜원점 제외 (접근 불가)
            if "망우혜원점" in stores:
                stores.remove("망우혜원점")
        
        if periods is None:
            periods = [1, 7]  # 기본 1일, 7일
        
        # ReportBuilder를 사용한 단순한 구조
        builder = SummaryReportBuilder(data_type)
        
        try:
            # 리포트 생성
            html = builder.build_report(end_date, list(stores), periods)
            
            # HTML을 기존 경로에 저장 (PDF 변환 등을 위해)
            try:
                from libs.html_output_config import save_html_report
                # periods[0]를 사용하여 리포트 타입 결정
                report_type = 'visitor_daily' if periods[0] == 1 else 'visitor_weekly'
                save_result = save_html_report(html, report_type, end_date, save_both=True)
                print(f"✅ HTML 파일 저장 성공: {save_result.get('saved_files', [])}")
            except Exception as save_error:
                print(f"❌ HTML 파일 저장 실패: {save_error}")
                # 저장 실패해도 HTML은 반환 (기본 기능은 유지)
            
            return {
                "status": "success",
                "html": html,
                "data_type": data_type,
                "end_date": end_date,
                "stores": list(stores),
                "periods": periods
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "data_type": data_type,
                "end_date": end_date,
                "stores": list(stores),
                "periods": periods
            }


# 사용 예시
if __name__ == "__main__":
    # 테스트용 코드
    builder = SummaryReportBuilder("visitor")
    print("✅ SummaryReportBuilder created successfully!")
    
    generator = SummaryReportGenerator()
    print("✅ SummaryReportGenerator created successfully!")