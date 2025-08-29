"""Report viewer and management API routes."""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, FileResponse

from libs.html_output_config import HTML_OUTPUT_ROOT, HTML_OUTPUT_PATHS, get_html_output_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/list")
async def list_reports() -> Dict[str, Any]:
    """생성된 리포트 목록을 조회합니다."""
    try:
        reports = {}
        
        # 각 리포트 타입별로 파일 목록 조회
        for report_type, path in HTML_OUTPUT_PATHS.items():
            if report_type == 'unified':
                continue
                
            report_dir = Path(path)
            if not report_dir.exists():
                reports[report_type] = []
                continue
                
            files = []
            for file_path in report_dir.glob("*.html"):
                try:
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "path": str(file_path.relative_to(Path(HTML_OUTPUT_ROOT))),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "url": f"/reports/{file_path.relative_to(Path(HTML_OUTPUT_ROOT))}"
                    })
                except Exception as e:
                    logger.warning(f"Failed to get info for {file_path}: {e}")
                    continue
            
            # 수정 시간으로 정렬 (최신순)
            files.sort(key=lambda x: x["modified"], reverse=True)
            reports[report_type] = files
        
        return {
            "result": "success",
            "reports": reports,
            "total_files": sum(len(files) for files in reports.values())
        }
        
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {e}")


@router.get("/latest/{report_type}")
async def get_latest_report(report_type: str):
    """특정 타입의 최신 리포트로 리다이렉트합니다."""
    try:
        if report_type not in HTML_OUTPUT_PATHS:
            raise HTTPException(status_code=404, detail="Invalid report type")
        
        report_dir = Path(get_html_output_path(report_type))
        latest_file = report_dir / "latest.html"
        
        if not latest_file.exists():
            raise HTTPException(status_code=404, detail="No reports found")
        
        # Static files URL로 리다이렉트
        relative_path = latest_file.relative_to(Path(HTML_OUTPUT_ROOT))
        return RedirectResponse(url=f"/reports/{relative_path}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest report: {e}")


@router.get("/view/{report_type}/{filename}")
async def view_report(report_type: str, filename: str):
    """특정 리포트 파일을 반환합니다."""
    try:
        if report_type not in HTML_OUTPUT_PATHS:
            raise HTTPException(status_code=404, detail="Invalid report type")
        
        report_dir = Path(get_html_output_path(report_type))
        file_path = report_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        
        if not file_path.suffix.lower() == '.html':
            raise HTTPException(status_code=400, detail="Only HTML files are supported")
        
        return FileResponse(
            path=str(file_path),
            media_type="text/html",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to view report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to view report: {e}")


@router.get("/types")
async def get_report_types():
    """사용 가능한 리포트 타입 목록을 반환합니다."""
    return {
        "result": "success",
        "report_types": {
            "visitor_daily": {
                "name": "일일 방문객 리포트",
                "description": "1일 기준 방문객 데이터 분석 및 AI 인사이트",
                "path": "/api/reports/latest/visitor_daily"
            },
            "visitor_weekly": {
                "name": "주간 방문객 리포트", 
                "description": "7일 기준 방문객 트렌드 분석",
                "path": "/api/reports/latest/visitor_weekly"
            },
            "comparison": {
                "name": "매장간 비교 분석",
                "description": "매장별 성과 비교 및 분석 리포트",
                "path": "/api/reports/latest/comparison"
            }
        }
    }