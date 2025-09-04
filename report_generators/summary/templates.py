"""
Summary Report HTML 템플릿 정의
기존 summary_report.py의 HTML 구조를 완전 보존
"""

# 메인 페이지 템플릿 (기존 _build_html_page 함수에서 추출)
MAIN_PAGE_TEMPLATE = '''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', Arial, sans-serif; margin: 0; background: #fafafa; color: #111; }}
    .container {{ max-width: 1080px; margin: 24px auto; padding: 0 16px; }}
    header.page-header {{ margin-bottom: 16px; }}
    header.page-header h1 {{ font-size: 22px; margin: 0 0 4px; }}
    .desc {{ color: #666; font-size: 13px; }}
    .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
    .card h2, .card h3 {{ margin: 0 0 8px; font-size: 18px; }}
    .card-header {{ margin-bottom: 16px; }}
    .card-header h3 {{ margin: 0 0 4px; font-size: 18px; color: #111; }}
    .card-subtitle {{ margin: 0; color: #6b7280; font-size: 13px; line-height: 1.4; }}
    .muted {{ color: #6b7280; font-size: 13px; }}
    .bullets {{ margin: 8px 0 8px 16px; padding: 0; }}
    .bullets li {{ margin: 4px 0; }}
    .table-wrap {{ overflow-x: auto; }}
    table.table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    table.table th, table.table td {{ border-top: 1px solid #f3f4f6; padding: 8px 10px; text-align: center; }}
    table.table th {{ background: #f9fafb; color: #374151; font-weight: 600; }}
    td.num {{ text-align: center; }}
    th.sep-left, td.sep-left {{ border-left: 1px solid #e5e7eb; }}
    th.sep-right, td.sep-right {{ border-right: 1px solid #e5e7eb; }}
    td.sep-left, th.sep-left {{ padding-left: 10px; }}
    td.sep-right, th.sep-right {{ padding-right: 10px; }}
    .pct-with-chart {{ display: inline-flex; align-items: center; gap: 8px; }}
    .pct-with-chart .spark {{ display: inline-flex; align-items: center; gap: 6px; padding: 2px 0; border: none; background: transparent; }}
    .pct-with-chart .spark svg {{ display: block; }}
    .col-note {{ font-size: 10px; color: #6b7280; font-weight: 400; margin-top: 2px; }}
    .pct-pos {{ color: #dc2626; }}
    .pct-neg {{ color: #1d4ed8; }}
    .pct-zero {{ color: #374151; }}
    .tabs {{ display: flex; gap: 8px; margin: 8px 0 16px; }}
    .tab-label {{ padding: 8px 12px; background: #eef2ff; color: #3730a3; border-radius: 8px; cursor: pointer; user-select: none; }}
    .tab-label:hover {{ background: #e0e7ff; }}
    input[type="radio"].tab-input {{ display: none; }}
    .tab-section {{ display: block; }}
    {css_rules}
    /* Summary readability */
    .summary-list {{ margin: 0; padding: 0 0 0 20px; line-height: 1.6; }}
    .summary-list li {{ margin: 4px 0; text-align: left; display: list-item; }}
    .action-list {{ margin: 0; padding: 0 0 0 20px; line-height: 1.6; }}
    .action-list li {{ margin: 4px 0; text-align: left; display: list-item; }}
    
    /* 프롬프트 기반 요약 스타일 */
    .trend-red {{ color: #7f1d1d; }}
    .badge {{ 
        display: inline-block;
        background: #fee2e2; 
        border-left: 3px solid #ef4444; 
        color: #7f1d1d;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 500;
    }}
    
    /* Pair recommendations */
    .pair-list {{ list-style: none; padding: 0; margin: 8px 0; display: grid; grid-template-columns: 1fr; gap: 10px; }}
    @media (min-width: 720px) {{ .pair-list {{ grid-template-columns: 1fr 1fr; }} }}
    .pair-item {{ border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 12px; background: #fff; }}
    .pair-head {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
    .pair-names {{ font-weight: 600; font-size: 14px; color: #111; }}
    .criteria-badge {{ font-size: 11px; color: #3730a3; background: #eef2ff; border: 1px solid #e0e7ff; padding: 2px 8px; border-radius: 999px; white-space: nowrap; }}
    .pair-note {{ margin-top: 6px; color: #374151; font-size: 13px; line-height: 1.5; }}
    .pair-question {{ display: block; margin-top: 6px; color: #6b7280; font-size: 12px; }}
  </style>
  <!-- section:head -->
</head>
<body>
  <div class="container">
    <header class="page-header">
      <h1>{title}</h1>
    </header>
    <div class="sections">
      {body_html}
    </div>
  </div>
</body>
</html>'''

# 1일 모드 섹션 템플릿 (기존 _build_tab_section_html에서 추출)
DAILY_SECTION_TEMPLATE = '''<section id="{section_id}" class="tab-section" data-period="{section_id}">
  {summary}
  {action}
  {table}
  {scatter}
</section>'''

# 7일 모드 섹션 템플릿
WEEKLY_SECTION_TEMPLATE = '''<section id="{section_id}" class="tab-section" data-period="{section_id}">
  {summary}
  {table}
  {scatter}
  {next}
  {explain}
</section>'''

# Summary 카드 템플릿 (기존 _build_summary_card_html에서 추출)
SUMMARY_CARD_TEMPLATE = '''<section class="card"> 
  <h3 style="margin: 0 0 8px 0;">요약</h3>
  <div style="margin-top: 0;">
    {content}
  </div>
  <!-- section:summary -->
</section>'''

# Action 카드 템플릿 (기존 _build_action_card_html에서 추출)
ACTION_CARD_TEMPLATE = '''<section class="card">
  <h3 style="margin: 0 0 8px 0;">액션</h3>
  <div style="margin-top: 0;">
    {content}
  </div>
  <!-- section:action -->
</section>'''

# LLM 응답이 없을 때의 기본 Summary 콘텐츠
SUMMARY_DEFAULT_CONTENT = '''
<div style="text-align: center; padding: 12px; color: #6b7280;">
  <p style="margin: 0; font-size: 14px;">📊 <strong>AI 분석 요약</strong></p>
  <p style="margin: 6px 0 0 0; font-size: 12px;">매장별 방문 데이터를 분석하여<br>핵심 인사이트를 제공합니다</p>
</div>'''

# LLM 응답이 없을 때의 기본 Action 콘텐츠  
ACTION_DEFAULT_CONTENT = '''
<div style="text-align: center; padding: 12px; color: #6b7280;">
  <p style="margin: 0; font-size: 14px;">📋 <strong>권장 액션</strong></p>
  <p style="margin: 6px 0 0 0; font-size: 12px;">당일 데이터 기반<br>즉시 실행 가능한 액션을 제공합니다</p>
</div>'''

# 테이블 카드 템플릿들 (1일 모드)
TABLE_DAILY_HEADER_TEMPLATE = '''<section class="card">
  <div class="card-header">
    <h3>방문객 증감 요약</h3>
    <p class="card-subtitle">당일과 전주 동일 요일 대비를 비교해 매장별 방문 추세를 한눈에 파악합니다.</p>
  </div>
  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th>매장명</th>
          <th>당일 방문객<div class="col-note">{curr_range}</div></th>
          <th>전주 동일 요일 방문객<div class="col-note">{prev_range}</div></th>
          <th>증감률</th>
          <th>주간 증감률 추이<br><div class="col-note">(전주 동일 요일 대비 방문 증감률 기준)</div></th>
        </tr>
      </thead>
      <tbody>'''

# 테이블 카드 템플릿들 (7일 모드)  
TABLE_WEEKLY_HEADER_TEMPLATE = '''<section class="card">
  <div class="card-header">
    <h3>방문객 증감 요약</h3>
    <p class="card-subtitle">최근 {days}일과 전 기간 대비를 비교해 매장별 방문 추세와 최근 4주의 변동을 한눈에 파악합니다.</p>
  </div>
  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th>매장명</th>
          <th>최근7일 방문객<div class="col-note">{curr_range}</div></th>
          <th>전주7일 방문객<div class="col-note">{prev_range}</div></th>
          <th>평일<br>증감률</th>
          <th>주말<br>증감률</th>
          <th>총<br>증감률</th>
          <th class="sep-left">주차별 평일<br>증감률<div class="col-note">max: {wd_max}%<br>min: {wd_min}%</div></th>
          <th>주차별 주말<br>증감률<div class="col-note">max: {we_max}%<br>min: {we_min}%</div></th>
          <th>주차별 총<br>증감률<div class="col-note">max: {tot_max}%<br>min: {tot_min}%</div></th>
        </tr>
      </thead>
      <tbody>'''

# 테이블 행 템플릿들
TABLE_DAILY_ROW_TEMPLATE = '''        <tr>
          <td>{site}</td>
          <td class="num">{curr}</td>
          <td class="num">{prev}</td>
          <td class="num"><b><span class="{tot_cls}">{tot}</span></b></td>
          <td class="num"><div class="pct-with-chart"><span class="spark">{spark_daily}</span></div></td>
        </tr>'''

TABLE_WEEKLY_ROW_TEMPLATE = '''        <tr>
          <td>{site}</td>
          <td class="num">{curr}</td>
          <td class="num">{prev}</td>
          <td class="num"><span class="{wd_cls}">{wd}</span></td>
          <td class="num"><span class="{we_cls}">{we}</span></td>
          <td class="num sep-right"><b><span class="{tot_cls}">{tot}</span></b></td>
          <td class="num sep-left"><div class="pct-with-chart"><span class="spark">{spark_wd}</span></div></td>
          <td class="num"><div class="pct-with-chart"><span class="spark">{spark_we}</span></div></td>
          <td class="num"><div class="pct-with-chart"><span class="spark">{spark_tot}</span></div></td>
        </tr>'''

# 테이블 끝부분
TABLE_FOOTER_TEMPLATE = '''      </tbody>
    </table>
  </div>
  <!-- section:table -->
</section>'''

# Scatter plot 카드 템플릿
SCATTER_CARD_TEMPLATE = '''<section class="card"> 
  {scatter_content}
</section>'''

SCATTER_NO_DATA_TEMPLATE = '''<p class="muted">표시할 데이터가 부족합니다.</p>'''