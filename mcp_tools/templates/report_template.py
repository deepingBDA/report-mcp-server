"""
리포트 HTML 템플릿
"""

from typing import List, Dict, Any, Optional
from ..utils.html_utils import escape_html, get_default_styles


class ReportTemplate:
    """리포트 HTML 템플릿 클래스"""
    
    def __init__(self, title: str, subtitle: str = ""):
        """
        Args:
            title: 리포트 제목
            subtitle: 리포트 부제목
        """
        self.title = title
        self.subtitle = subtitle
        self.cards = []
        self.additional_styles = ""
        self.additional_scripts = ""
    
    def add_card(self, title: str, content: str, card_class: str = "card"):
        """카드를 추가합니다.
        
        Args:
            title: 카드 제목
            content: 카드 내용 (HTML)
            card_class: 카드 CSS 클래스
        """
        self.cards.append({
            'title': title,
            'content': content,
            'class': card_class
        })
    
    def add_styles(self, styles: str):
        """추가 스타일을 설정합니다."""
        self.additional_styles = styles
    
    def add_scripts(self, scripts: str):
        """추가 스크립트를 설정합니다."""
        self.additional_scripts = scripts
    
    def render(self) -> str:
        """템플릿을 렌더링합니다."""
        # 카드들을 HTML로 변환
        cards_html = []
        for card in self.cards:
            card_html = f"""
<section class="{card['class']}">
    <h3>{escape_html(card['title'])}</h3>
    {card['content']}
</section>
"""
            cards_html.append(card_html)
        
        # 페이지 본문 생성
        body_content = f"""
<div class="container">
    <h2 class="page-title">{escape_html(self.title)}</h2>
    {'<div class="page-subtitle">' + escape_html(self.subtitle) + '</div>' if self.subtitle else ''}
    
    {''.join(cards_html)}
</div>
"""
        
        # 전체 HTML 생성
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape_html(self.title)}</title>
    <style>
        {get_default_styles()}
        {self.additional_styles}
    </style>
    {self.additional_scripts}
</head>
<body>
    {body_content}
</body>
</html>
"""


class TabTemplate:
    """탭 형식의 템플릿"""
    
    def __init__(self, title: str):
        """
        Args:
            title: 페이지 제목
        """
        self.title = title
        self.tabs = []
    
    def add_tab(self, tab_id: str, tab_label: str, content: str, is_active: bool = False):
        """탭을 추가합니다.
        
        Args:
            tab_id: 탭 ID
            tab_label: 탭 라벨
            content: 탭 내용
            is_active: 활성 탭 여부
        """
        self.tabs.append({
            'id': tab_id,
            'label': tab_label,
            'content': content,
            'active': is_active
        })
    
    def render(self) -> str:
        """탭 템플릿을 렌더링합니다."""
        if not self.tabs:
            return ""
        
        # 탭 버튼 생성
        tab_buttons = []
        for tab in self.tabs:
            active_class = "active" if tab['active'] else ""
            button_html = f"""
<button class="tab-button {active_class}" 
        onclick="openTab(event, '{tab['id']}')">{escape_html(tab['label'])}</button>
"""
            tab_buttons.append(button_html)
        
        # 탭 컨텐츠 생성
        tab_contents = []
        for tab in self.tabs:
            display_style = "block" if tab['active'] else "none"
            content_html = f"""
<div id="{tab['id']}" class="tab-content" style="display: {display_style};">
    {tab['content']}
</div>
"""
            tab_contents.append(content_html)
        
        # 탭 스타일
        tab_styles = """
.tab {
    overflow: hidden;
    border: 1px solid #e5e7eb;
    background-color: #f9fafb;
    border-radius: 8px 8px 0 0;
}

.tab button {
    background-color: inherit;
    float: left;
    border: none;
    outline: none;
    cursor: pointer;
    padding: 14px 24px;
    transition: 0.3s;
    font-size: 16px;
    font-weight: 500;
    color: #6b7280;
}

.tab button:hover {
    background-color: #e5e7eb;
}

.tab button.active {
    background-color: white;
    color: #111827;
    font-weight: 600;
    border-bottom: 2px solid #3b82f6;
}

.tab-content {
    padding: 20px;
    border: 1px solid #e5e7eb;
    border-top: none;
    background: white;
    border-radius: 0 0 8px 8px;
}
"""
        
        # 탭 스크립트
        tab_script = """
<script>
function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    
    // Hide all tab content
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    
    // Remove active class from all buttons
    tablinks = document.getElementsByClassName("tab-button");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    
    // Show selected tab and add active class to button
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}
</script>
"""
        
        # 전체 HTML 생성
        return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape_html(self.title)}</title>
    <style>
        {get_default_styles()}
        {tab_styles}
    </style>
    {tab_script}
</head>
<body>
    <div class="container">
        <h2 class="page-title">{escape_html(self.title)}</h2>
        
        <div class="tab">
            {''.join(tab_buttons)}
        </div>
        
        {''.join(tab_contents)}
    </div>
</body>
</html>
"""


class ComparisonTemplate(ReportTemplate):
    """비교 분석 전용 템플릿"""
    
    def __init__(self, store_a: str, store_b: str, end_date: str):
        """
        Args:
            store_a: A 매장명
            store_b: B 매장명
            end_date: 분석 종료 날짜
        """
        title = f"매장별 방문객 추이 비교 분석: {store_a} vs {store_b}"
        subtitle = f"분석 기준일: {end_date}"
        super().__init__(title, subtitle)
        
        self.store_a = store_a
        self.store_b = store_b
        self.end_date = end_date
    
    def add_summary_card(self, llm_analysis: str):
        """요약 카드를 추가합니다."""
        # 마크다운 불릿을 HTML 리스트로 변환
        lines = [ln.strip() for ln in llm_analysis.splitlines() if ln.strip()]
        items = []
        
        for line in lines:
            if line.startswith('- '):
                items.append(line[2:].strip())
            elif line.startswith('* '):
                items.append(line[2:].strip())
            else:
                items.append(line)
        
        if items:
            li_html = "\n".join(f"<li>{escape_html(item)}</li>" for item in items)
            content = f'<ul class="summary-list">{li_html}</ul>'
        else:
            content = '<p class="placeholder">분석 결과가 없습니다.</p>'
        
        self.add_card("요약카드", content)
    
    def add_daily_trends_card(self, chart_svg: str):
        """일별 방문 추이 카드를 추가합니다."""
        content = f'<div class="chart-container">{chart_svg}</div>'
        self.add_card("매장별 일별 방문 추이 비교", content)
    
    def add_customer_composition_card(self, chart_svg: str):
        """고객 구성 카드를 추가합니다."""
        content = f'<div class="chart-container">{chart_svg}</div>'
        self.add_card("고객 구성 변화", content)
    
    def add_time_age_pattern_card(self, chart_svg: str):
        """시간대 연령대별 패턴 카드를 추가합니다."""
        content = f'<div class="chart-container">{chart_svg}</div>'
        self.add_card("시간대 연령대별 방문 패턴", content)