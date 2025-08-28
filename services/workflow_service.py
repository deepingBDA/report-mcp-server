"""Workflow service for handling workflow execution logic."""

import os
import logging
from typing import Dict, List, Union, Any

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service class for workflow operations."""
    
    @staticmethod
    def normalize_stores_list(stores: Union[str, List[str]]) -> List[str]:
        """Convert stores to normalized list format."""
        if isinstance(stores, str):
            return [s.strip() for s in stores.split(",") if s.strip()]
        return [str(s).strip() for s in stores if str(s).strip()]
    
    @staticmethod
    def execute_summary_report(
        data_type: str,
        end_date: str,
        stores: List[str],
        periods: int,
        user_prompt: str
    ) -> Dict[str, Any]:
        """Execute summary report workflow."""
        try:
            from workflows.summary_report import SummaryReportWorkflow
            
            workflow = SummaryReportWorkflow()
            
            # Run the workflow
            workflow_result = workflow.run(
                data_type=data_type,
                end_date=end_date,
                stores=stores,
                periods=periods,
                user_prompt=user_prompt
            )
            
            # Try to read the generated HTML file
            try:
                from libs.html_output_config import get_full_html_path
                
                # Determine report type based on periods
                report_type = 'visitor_daily' if periods == 1 else 'visitor_weekly'
                
                # Get the file path
                _, latest_path = get_full_html_path(report_type, end_date, only_latest=True)
                
                if os.path.exists(latest_path):
                    with open(latest_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    return {
                        "result": "HTML 보고서 생성 및 반환 완료",
                        "html_content": html_content,
                        "file_path": latest_path,
                        "workflow_summary": workflow_result
                    }
                else:
                    return {
                        "result": workflow_result,
                        "html_content": None,
                        "file_path": None,
                        "workflow_summary": "HTML 파일을 찾을 수 없음"
                    }
                    
            except Exception as e:
                logger.error(f"HTML 파일 읽기 실패: {e}")
                return {
                    "result": workflow_result,
                    "html_content": None,
                    "file_path": None,
                    "workflow_summary": f"HTML 파일 처리 오류: {e}"
                }
                
        except Exception as e:
            logger.error(f"Summary report workflow 실행 실패: {e}")
            raise
    
    @staticmethod
    def execute_comparison_analysis(
        stores: List[str],
        end_date: str,
        period: int,
        analysis_type: str,
        user_prompt: str
    ) -> Dict[str, Any]:
        """Execute comparison analysis workflow."""
        try:
            from workflows.comparison_analysis import ComparisonAnalysisWorkflow
            
            workflow = ComparisonAnalysisWorkflow()
            
            # Run the workflow
            workflow_result = workflow.run(
                stores=stores,
                end_date=end_date,
                period=period,
                analysis_type=analysis_type,
                user_prompt=user_prompt
            )
            
            # Try to read the generated HTML file
            try:
                from libs.html_output_config import get_full_html_path
                
                # Get the file path for comparison reports
                _, latest_path = get_full_html_path("comparison", end_date, only_latest=True)
                
                if os.path.exists(latest_path):
                    with open(latest_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    return {
                        "result": "HTML 비교 분석 보고서 생성 및 반환 완료",
                        "html_content": html_content,
                        "file_path": latest_path,
                        "workflow_summary": workflow_result
                    }
                else:
                    return {
                        "result": workflow_result,
                        "html_content": None,
                        "file_path": None,
                        "workflow_summary": "HTML 파일을 찾을 수 없음"
                    }
                    
            except Exception as e:
                logger.error(f"HTML 파일 읽기 실패: {e}")
                return {
                    "result": workflow_result,
                    "html_content": None,
                    "file_path": None,
                    "workflow_summary": f"HTML 파일 처리 오류: {e}"
                }
            
        except Exception as e:
            logger.error(f"Comparison analysis workflow 실행 실패: {e}")
            raise