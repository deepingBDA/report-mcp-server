"""
메인 통합 워크플로우

스펙에 따라 적절한 데이터 추출기와 워크플로우를 선택하고 실행합니다.
"""

from typing import Dict, List, Any, Optional, Union
from datetime import date
import os
from shutil import copyfile

from ..data_extractors import create_extractor
from ..workflows import create_workflow
from ..specs import get_spec_config, get_report_config, DataSpec, ReportType


class MainReportWorkflow:
    """메인 통합 워크플로우"""
    
    def __init__(self):
        """메인 워크플로우 초기화"""
        pass
    
    def run(
        self,
        *,
        data_spec: str,
        end_date: str,
        stores: Union[str, List[str]],
        periods: Optional[List[int]] = None,
        report_types: Optional[List[str]] = None,
        user_prompt: str = "데이터 분석 리포트"
    ) -> Dict[str, Any]:
        """
        메인 워크플로우를 실행합니다.
        
        Args:
            data_spec: 데이터 스펙 (visitor, touch_point, dwelling_time, sales)
            end_date: 기준일 (YYYY-MM-DD)
            stores: 매장 목록 (문자열 콤마 구분 또는 리스트)
            periods: 분석 기간 리스트 (예: [7, 30])
            report_types: 리포트 타입 리스트 (예: ["summary", "comparison"])
            user_prompt: 사용자 프롬프트
            
        Returns:
            워크플로우 실행 결과
        """
        # 1. 입력 정규화
        if isinstance(stores, str):
            stores_list = [s.strip() for s in stores.replace("，", ",").split(",") if s.strip()]
        else:
            stores_list = [str(s).strip() for s in stores if str(s).strip()]
        
        if not stores_list:
            raise ValueError("stores가 비어 있습니다")
        
        # 기본값 설정
        if periods is None:
            spec_config = get_spec_config(data_spec)
            periods = spec_config.get("periods", [7, 30])
        
        if report_types is None:
            report_types = ["summary"]  # 기본값은 요약 통계
        
        # 2. 데이터 추출기 생성
        try:
            extractor = create_extractor(data_spec)
        except ValueError as e:
            return {"error": str(e), "status": "failed"}
        
        # 3. 각 워크플로우 실행
        results = {}
        for report_type in report_types:
            try:
                workflow = create_workflow(report_type, extractor)
                workflow_result = workflow.run(stores_list, end_date, periods)
                results[report_type] = workflow_result
            except Exception as e:
                results[report_type] = {"error": str(e), "status": "failed"}
        
        # 4. 최종 결과 통합
        final_result = self._generate_final_result(
            data_spec=data_spec,
            end_date=end_date,
            stores=stores_list,
            periods=periods,
            report_types=report_types,
            results=results,
            user_prompt=user_prompt
        )
        
        # 5. HTML 파일 저장 (기존 visitor_summary_workflow.py와 동일한 경로)
        if final_result.get("main_html"):
            self._save_html_file(final_result["main_html"], end_date, data_spec)
        
        return final_result
    
    def _save_html_file(self, html_content: str, end_date: str, data_spec: str) -> None:
        """HTML 파일을 기존 visitor_summary_workflow.py와 동일한 경로에 저장"""
        try:
            # 저장 경로 통일: chat/report/weekly (기존과 동일)
            out_dir = os.path.abspath(os.path.join("/Users/junho/DA-agent", "chat", "report", "weekly"))
            os.makedirs(out_dir, exist_ok=True)
            
            # 파일명 생성 (기존과 동일한 형식)
            if data_spec == "visitor":
                out_path = os.path.join(out_dir, f"visitor_summary_{end_date}.html")
            else:
                out_path = os.path.join(out_dir, f"{data_spec}_summary_{end_date}.html")
            
            latest_path = os.path.join(out_dir, "latest.html")
            
            # HTML 파일 저장
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # latest.html로 복사
            try:
                copyfile(out_path, latest_path)
            except Exception:
                pass
                
        except Exception as e:
            print(f"HTML 파일 저장 실패: {e}")
    
    def _generate_final_result(
        self,
        data_spec: str,
        end_date: str,
        stores: List[str],
        periods: List[int],
        report_types: List[str],
        results: Dict[str, Any],
        user_prompt: str
    ) -> Dict[str, Any]:
        """최종 결과를 통합하여 생성"""
        
        # 성공한 워크플로우 결과 수집
        successful_results = {}
        failed_results = {}
        
        for report_type, result in results.items():
            if "error" not in result:
                successful_results[report_type] = result
            else:
                failed_results[report_type] = result
        
        # 메인 HTML 콘텐츠 (첫 번째 성공한 워크플로우의 HTML 사용)
        main_html = ""
        if successful_results:
            first_success = list(successful_results.values())[0]
            main_html = first_success.get("html_content", "")
        
        # 상태 요약
        status_summary = {
            "total_workflows": len(report_types),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "success_rate": len(successful_results) / len(report_types) * 100
        }
        
        # 최종 결과 구성
        final_result = {
            "status": "success" if successful_results else "failed",
            "data_spec": data_spec,
            "end_date": end_date,
            "stores": stores,
            "periods": periods,
            "report_types": report_types,
            "user_prompt": user_prompt,
            "status_summary": status_summary,
            "workflow_results": results,
            "main_html": main_html,
            "timestamp": date.today().isoformat()
        }
        
        return final_result
    
    def get_available_specs(self) -> List[str]:
        """사용 가능한 데이터 스펙 목록 반환"""
        return list(DataSpec.__members__.keys())
    
    def get_available_report_types(self) -> List[str]:
        """사용 가능한 리포트 타입 목록 반환"""
        return list(ReportType.__members__.keys())
    
    def get_spec_info(self, data_spec: str) -> Dict[str, Any]:
        """스펙 정보 반환"""
        return get_spec_config(data_spec)
    
    def get_report_info(self, report_type: str) -> Dict[str, Any]:
        """리포트 타입 정보 반환"""
        return get_report_config(report_type) 