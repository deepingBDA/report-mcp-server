"""
HTML 관련 유틸리티 함수들
워크플로우에서 공통으로 사용되는 HTML 생성 및 처리 함수
"""

from typing import Optional, Dict, Any, List


def escape_html(text: str) -> str:
    """HTML 특수문자를 이스케이프합니다."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def create_base_html_template(
    title: str, 
    body_content: str,
    additional_styles: str = "",
    additional_scripts: str = ""
) -> str:
    """기본 HTML 템플릿을 생성합니다."""
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape_html(title)}</title>
    <style>
        {get_default_styles()}
        {additional_styles}
    </style>
    {additional_scripts}
</head>
<body>
    {body_content}
</body>
</html>
"""


def get_default_styles() -> str:
    """모든 리포트에서 사용하는 기본 스타일을 반환합니다."""
    return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', Arial, sans-serif;
            margin: 0;
            background: #fafafa;
            color: #111;
        }
        .container {
            max-width: 1080px;
            margin: 24px auto;
            padding: 0 16px;
        }
        .page-title {
            margin: 0 0 6px;
            font-size: 24px;
            font-weight: 700;
        }
        .page-subtitle {
            margin: 0 0 16px;
            color: #6b7280;
            font-size: 14px;
        }
        .card {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 16px;
            margin: 12px 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .card h3 {
            margin: 0 0 8px;
            font-size: 18px;
        }
        .placeholder {
            color: #9ca3af;
            font-size: 13px;
            text-align: center;
            padding: 20px;
        }
        .chart-container {
            text-align: center;
            margin: 16px auto;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .chart-container svg {
            width: 100%;
            height: auto;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            display: block;
            margin: 0 auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        th {
            background: #f9fafb;
            font-weight: 600;
        }
        .pct-pos {
            color: #10b981;
            font-weight: 600;
        }
        .pct-neg {
            color: #ef4444;
            font-weight: 600;
        }
        .pct-zero {
            color: #6b7280;
        }
        .summary-list {
            margin: 8px 0 0 16px;
            padding-left: 16px;
            line-height: 1.6;
        }
        .summary-list li {
            margin: 6px 0;
            text-align: left;
            list-style: disc;
        }
        .trend-red {
            color: #dc2626;
        }
        .badge {
            background: #fef2f2;
            color: #dc2626;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
    """


def create_card(title: str, content: str, card_class: str = "card") -> str:
    """카드 섹션을 생성합니다."""
    return f"""
<section class="{card_class}">
    <h3>{escape_html(title)}</h3>
    {content}
</section>
"""


def create_table(
    headers: List[str],
    rows: List[List[Any]],
    table_class: str = "",
    format_funcs: Optional[Dict[int, callable]] = None
) -> str:
    """HTML 테이블을 생성합니다.
    
    Args:
        headers: 테이블 헤더 리스트
        rows: 테이블 행 데이터
        table_class: 테이블 CSS 클래스
        format_funcs: 컬럼별 포맷팅 함수 딕셔너리 {column_index: format_function}
    """
    format_funcs = format_funcs or {}
    
    # 헤더 생성
    header_html = "<tr>" + "".join(f"<th>{escape_html(h)}</th>" for h in headers) + "</tr>"
    
    # 행 생성
    rows_html = []
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            if i in format_funcs:
                formatted = format_funcs[i](cell)
                cells.append(f"<td>{formatted}</td>")
            else:
                cells.append(f"<td>{escape_html(str(cell) if cell is not None else '')}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")
    
    class_attr = f'class="{table_class}"' if table_class else ""
    return f"""
<table {class_attr}>
    <thead>{header_html}</thead>
    <tbody>{''.join(rows_html)}</tbody>
</table>
"""


def create_percentage_span(value: float, include_sign: bool = True) -> str:
    """백분율 값을 스타일이 적용된 span으로 변환합니다."""
    if value > 0:
        sign = "+" if include_sign else ""
        return f'<span class="pct-pos">{sign}{value:.1f}%</span>'
    elif value < 0:
        return f'<span class="pct-neg">{value:.1f}%</span>'
    else:
        return f'<span class="pct-zero">0.0%</span>'


def create_summary_list(items: List[str]) -> str:
    """요약 리스트를 생성합니다."""
    if not items:
        return '<p class="placeholder">요약 정보가 없습니다.</p>'
    
    list_items = "\n".join(f"<li>{escape_html(item)}</li>" for item in items)
    return f'<ul class="summary-list">\n{list_items}\n</ul>'


def parse_markdown_bullets_to_list(markdown_text: str) -> List[str]:
    """마크다운 불릿 포인트를 리스트로 변환합니다."""
    if not markdown_text:
        return []
    
    lines = [ln.strip() for ln in markdown_text.splitlines() if ln.strip()]
    items = []
    for line in lines:
        if line.startswith('- '):
            items.append(line[2:].strip())
        elif line.startswith('* '):
            items.append(line[2:].strip())
        elif line.startswith('• '):
            items.append(line[2:].strip())
        else:
            # 불릿이 없는 라인도 포함
            items.append(line)
    
    return items


def create_container_div(content: str, container_class: str = "container") -> str:
    """컨테이너 div를 생성합니다."""
    return f'<div class="{container_class}">\n{content}\n</div>'


def create_flex_container(items: List[str], gap: str = "24px") -> str:
    """플렉스 컨테이너를 생성합니다."""
    items_html = "\n".join(f'<div style="flex:1;">\n{item}\n</div>' for item in items)
    return f'<div style="display:flex; gap:{gap}; align-items:flex-start;">\n{items_html}\n</div>'