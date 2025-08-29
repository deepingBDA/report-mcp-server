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


def save_html_report(html_content, report_type, end_date, prefix=None, use_unified=False, save_both=True):
    """
    HTML 리포트를 파일로 저장합니다. 날짜별 파일과 latest.html을 모두 저장할 수 있습니다.
    
    Args:
        html_content: HTML 내용
        report_type: 리포트 타입
        end_date: 종료 날짜
        prefix: 파일명 접두사
        use_unified: 통합 디렉토리 사용 여부
        save_both: True일 경우 날짜별 파일과 latest.html 모두 저장
    
    Returns:
        dict: {'dated_file': 날짜별_파일_경로, 'latest_file': latest.html_경로, 'saved_files': 저장된_파일_목록}
    """
    try:
        # 디렉토리 생성
        if use_unified:
            output_dir = get_html_output_path('unified')
        else:
            output_dir = get_html_output_path(report_type)
        
        saved_files = []
        result = {}
        
        if save_both:
            # 1. 날짜별 파일 저장
            dated_filename = get_html_filename(report_type, end_date, prefix)
            dated_path = os.path.join(output_dir, dated_filename)
            
            with open(dated_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            saved_files.append(dated_path)
            result['dated_file'] = dated_path
            
            # 2. latest.html 저장
            latest_path = os.path.join(output_dir, "latest.html")
            with open(latest_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            saved_files.append(latest_path)
            result['latest_file'] = latest_path
            
        else:
            # latest.html만 저장 (기존 동작)
            latest_path = os.path.join(output_dir, "latest.html")
            with open(latest_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            saved_files.append(latest_path)
            result['latest_file'] = latest_path
            result['dated_file'] = None
        
        result['saved_files'] = saved_files
        return result
        
    except Exception as e:
        raise Exception(f"Failed to save HTML report: {e}")


def cleanup_old_reports(report_type, max_files=30):
    """
    오래된 리포트 파일들을 정리합니다. latest.html은 제외하고 날짜별 파일만 정리합니다.
    
    Args:
        report_type: 리포트 타입
        max_files: 보관할 최대 파일 개수 (latest.html 제외)
    """
    try:
        output_dir = Path(get_html_output_path(report_type))
        if not output_dir.exists():
            return
        
        # HTML 파일 목록 (latest.html 제외)
        html_files = []
        for file_path in output_dir.glob("*.html"):
            if file_path.name != "latest.html":
                html_files.append(file_path)
        
        # 생성 시간으로 정렬 (오래된 순)
        html_files.sort(key=lambda x: x.stat().st_ctime)
        
        # max_files 개수를 초과하는 오래된 파일들 삭제
        if len(html_files) > max_files:
            files_to_delete = html_files[:-max_files]
            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                except Exception as e:
                    print(f"Warning: Failed to delete old report {file_path}: {e}")
                    
    except Exception as e:
        print(f"Warning: Failed to cleanup old reports: {e}")