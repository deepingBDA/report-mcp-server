"""Report generator service for handling report generation logic."""

import os
import logging
from typing import Dict, List, Union, Any

logger = logging.getLogger(__name__)


class ReportGeneratorService:
    """Service class for report generation operations."""
    
    @staticmethod
    def normalize_stores_list(stores: Union[str, List[str]]) -> List[str]:
        """Convert stores to normalized list format."""
        if isinstance(stores, str):
            # "all" 특별 처리
            if stores.lower().strip() == "all":
                from libs.database import get_all_sites
                print(f"🔍 normalize_stores_list: 'all' 매장 파라미터 감지, 전체 매장 목록 조회 중...")
                stores_list = get_all_sites()
                print(f"🏪 normalize_stores_list: 조회된 매장 목록: {stores_list}")
                
                # 망우혜원점 제외 (접근 불가)
                if "망우혜원점" in stores_list:
                    stores_list.remove("망우혜원점")
                    print(f"⚠️ normalize_stores_list: 망우혜원점 제외됨 (접근 불가)")
                
                if not stores_list:
                    print("❌ normalize_stores_list: 사용 가능한 매장이 없습니다")
                    raise ValueError("사용 가능한 매장이 없습니다")
                print(f"✅ normalize_stores_list: {len(stores_list)}개 매장으로 설정됨: {stores_list}")
                return stores_list
            else:
                return [s.strip() for s in stores.split(",") if s.strip()]
        return [str(s).strip() for s in stores if str(s).strip()]
    
    @staticmethod
    def generate_summary_report(
        data_type: str,
        end_date: str,
        stores: List[str],
        periods: int
    ) -> Dict[str, Any]:
        """Generate summary report."""
        try:
            logger.info("📊 Using modular summary report generator")
            from report_generators.summary_report import SummaryReportGenerator
            generator = SummaryReportGenerator()
            
            # Generate the report
            try:
                logger.info(f"🔧 Starting generator.run() with: {len(stores)} stores, periods={periods}")
                report_result = generator.run(
                    data_type=data_type,
                    end_date=end_date,
                    stores=stores,
                    periods=periods
                )
                logger.info(f"✅ generator.run() completed successfully")
            except Exception as gen_error:
                logger.error(f"❌ generator.run() failed with error: {gen_error}")
                import traceback
                logger.error(f"❌ Full traceback: {traceback.format_exc()}")
                raise
            
            # Try to read the generated HTML file
            try:
                from libs.html_output_config import get_full_html_path, save_html_report, cleanup_old_reports
                
                # Determine report type based on periods
                report_type = 'visitor_daily' if periods == 1 else 'visitor_weekly'
                
                # Get the file path
                _, latest_path = get_full_html_path(report_type, end_date, only_latest=True)
                
                if os.path.exists(latest_path):
                    with open(latest_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Save both dated file and latest.html for better file management
                    try:
                        save_result = save_html_report(html_content, report_type, end_date, save_both=True)
                        logger.info(f"Saved report files: {save_result['saved_files']}")
                        
                        # Clean up old reports (keep last 30)
                        cleanup_old_reports(report_type, max_files=30)
                        
                    except Exception as e:
                        logger.warning(f"Failed to save dated report file: {e}")
                        # Continue anyway since we have the HTML content
                    
                    return {
                        "result": "success",
                        "html_content": html_content
                    }
                else:
                    return {
                        "result": "failed",
                        "html_content": None
                    }
                    
            except Exception as e:
                logger.error(f"HTML 파일 읽기 실패: {e}")
                return {
                    "result": "failed",
                    "html_content": None
                }
                
        except Exception as e:
            logger.error(f"Summary report generation 실행 실패: {e}")
            raise
    
    @staticmethod
    def generate_comparison_analysis(
        stores: List[str],
        end_date: str,
        period: int,
        analysis_type: str
    ) -> Dict[str, Any]:
        """Generate comparison analysis report."""
        try:
            from report_generators.comparison_analysis import ComparisonAnalysisGenerator
            
            generator = ComparisonAnalysisGenerator()
            
            # Generate the report
            report_result = generator.run(
                stores=stores,
                end_date=end_date,
                period=period,
                analysis_type=analysis_type
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
                        "result": "success",
                        "html_content": html_content
                    }
                else:
                    return {
                        "result": "failed",
                        "html_content": None
                    }
                    
            except Exception as e:
                logger.error(f"HTML 파일 읽기 실패: {e}")
                return {
                    "result": "failed",
                    "html_content": None
                }
            
        except Exception as e:
            logger.error(f"Comparison analysis generation 실행 실패: {e}")
            raise