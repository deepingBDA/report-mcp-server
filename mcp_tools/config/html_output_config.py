"""
HTML 출력 경로 설정
모든 워크플로우에서 사용하는 중앙 집중식 HTML 출력 경로 관리
"""

import os
from pathlib import Path

# 기본 HTML 출력 루트 디렉토리
HTML_OUTPUT_ROOT = os.environ.get('HTML_OUTPUT_ROOT', 'html_report')

# 각 워크플로우별 서브 디렉토리
HTML_OUTPUT_PATHS = {
    'visitor_daily': os.path.join(HTML_OUTPUT_ROOT, 'visitor', 'daily'),
    'visitor_weekly': os.path.join(HTML_OUTPUT_ROOT, 'visitor', 'weekly'),
    'comparison': os.path.join(HTML_OUTPUT_ROOT, 'comparison'),
    'diagnosis': os.path.join(HTML_OUTPUT_ROOT, 'diagnosis'),
    # 통합 경로 (모든 리포트를 한 곳에 저장하고 싶을 때)
    'unified': HTML_OUTPUT_ROOT
}

def get_html_output_path(report_type='unified'):
    """
    HTML 출력 경로를 반환합니다.
    
    Args:
        report_type: 리포트 타입 ('visitor_daily', 'visitor_weekly', 'comparison', 'diagnosis', 'unified')
    
    Returns:
        str: HTML 출력 디렉토리 경로
    """
    path = HTML_OUTPUT_PATHS.get(report_type, HTML_OUTPUT_ROOT)
    # 디렉토리가 없으면 생성
    Path(path).mkdir(parents=True, exist_ok=True)
    return os.path.abspath(path)

def get_html_filename(report_type, end_date, prefix=None):
    """
    표준화된 HTML 파일명을 생성합니다.
    
    Args:
        report_type: 리포트 타입
        end_date: 종료 날짜 (YYYY-MM-DD 형식)
        prefix: 파일명 접두사 (선택사항)
    
    Returns:
        str: HTML 파일명
    """
    if prefix:
        return f"{prefix}_{end_date}.html"
    
    filename_map = {
        'visitor_daily': f"visitor_daily_{end_date}.html",
        'visitor_weekly': f"visitor_weekly_{end_date}.html",
        'comparison': f"comparison_{end_date}.html",
        'diagnosis': f"diagnosis_{end_date}.html",
    }
    
    return filename_map.get(report_type, f"report_{end_date}.html")

def get_full_html_path(report_type, end_date, prefix=None, use_unified=False, only_latest=True):
    """
    전체 HTML 파일 경로를 반환합니다.
    
    Args:
        report_type: 리포트 타입
        end_date: 종료 날짜
        prefix: 파일명 접두사
        use_unified: True일 경우 통합 디렉토리 사용
        only_latest: True일 경우 latest.html만 반환 (날짜별 파일 생성 안함)
    
    Returns:
        tuple: (full_path, latest_path)
    """
    # 통합 디렉토리 사용 옵션
    if use_unified:
        output_dir = get_html_output_path('unified')
    else:
        output_dir = get_html_output_path(report_type)
    
    # latest.html만 사용
    if only_latest:
        full_path = os.path.join(output_dir, "latest.html")
        latest_path = full_path  # 동일한 파일
    else:
        filename = get_html_filename(report_type, end_date, prefix)
        full_path = os.path.join(output_dir, filename)
        latest_path = os.path.join(output_dir, "latest.html")
    
    return full_path, latest_path