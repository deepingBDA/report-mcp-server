"""
비교분석 워크플로우

매장 간 비교 분석을 위한 워크플로우입니다:
1. 매장별 일별 방문추이 (전주 vs 금주) - 막대그래프 + 꺾은선그래프
2. 고객 구성 차이 (성별, 연령대 비중) - 파이 차트 + 막대그래프
3. 시간대/연령대별 방문 패턴 히트맵
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Dict, List, Any, Union, Sequence
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START

from libs.base_workflow import BaseWorkflow, BaseState
from libs.comparison_extractor import ComparisonDataExtractor
from libs.chart_renderer import ChartRenderer


class ComparisonAnalysisState(BaseState):
    """비교분석 워크플로우 전용 상태"""
    stores: List[str]
    end_date: str
    period: int  # 분석 기간 (일)
    analysis_type: str  # "daily_trends", "customer_composition", "time_age_pattern", "all"
    
    # 데이터 저장
    daily_trends_data: Dict[str, Dict[str, Any]]
    customer_composition_data: Dict[str, Dict[str, Any]]
    time_age_pattern_data: Dict[str, Dict[str, Any]]
    
    # 차트 저장
    daily_trends_charts: Dict[str, str]
    customer_composition_charts: Dict[str, str]
    time_age_pattern_charts: Dict[str, str]
    
    # HTML 콘텐츠
    html_content: str
    final_result: str


@dataclass
class AnalysisResult:
    """분석 결과 데이터 클래스"""
    store: str
    period: int
    data: Dict[str, Any]
    chart: str


class ComparisonAnalysisGenerator(BaseWorkflow[ComparisonAnalysisState]):
    """비교분석 리포트 생성기 클래스"""

    def __init__(self):
        super().__init__(workflow_name="comparison_analysis")
        
        # 환경변수 로드 및 LLM 설정
        load_dotenv()
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        # 데이터 추출기 및 차트 렌더러
        self.extractor = ComparisonDataExtractor()
        self.chart_renderer = ChartRenderer()
        
        # 워크플로우 앱 빌드
        self.workflow_app = self._build_workflow()

    def run(
        self,
        *,
        stores: Union[str, Sequence[str]],
        end_date: str,
        period: int = 7,
        analysis_type: str = "all",
    ) -> str:
        """
        비교분석 워크플로우 실행
        
        Args:
            stores: 매장 목록 (문자열 콤마 구분 또는 리스트)
            end_date: 기준일 (YYYY-MM-DD)
            period: 분석 기간 (일)
            analysis_type: 분석 타입 ("daily_trends", "customer_composition", "time_age_pattern", "all")
        """
        # 입력 정규화
        if isinstance(stores, str):
            stores_list = [s.strip() for s in stores.replace("，", ",").split(",") if s.strip()]
        else:
            stores_list = [str(s).strip() for s in stores if str(s).strip()]
        
        if not stores_list:
            raise ValueError("stores가 비어 있습니다")
        
        # 기준일 조정 (오늘이거나 미래인 경우 어제로)
        end_iso = self._clamp_end_date_to_yesterday(end_date)
        
        # 초기 상태 생성
        initial_state: ComparisonAnalysisState = {
            "workflow_id": f"{self.workflow_name}_{end_iso}",
            "timestamp": date.today().isoformat(),
            "stores": stores_list,
            "end_date": end_iso,
            "period": period,
            "analysis_type": analysis_type,
            "daily_trends_data": {},
            "customer_composition_data": {},
            "time_age_pattern_data": {},
            "daily_trends_charts": {},
            "customer_composition_charts": {},
            "time_age_pattern_charts": {},
            "html_content": "",
            "final_result": "",
        }  # type: ignore
        
        # 워크플로우 실행
        result = self.workflow_app.invoke(initial_state)
        return result.get("final_result", "워크플로우 실행 완료")

    def _build_workflow(self) -> StateGraph:
        """워크플로우 그래프 구성"""
        builder = StateGraph(ComparisonAnalysisState)
        
        # 노드 추가
        builder.add_node("extract_data", self._extract_data_node)
        builder.add_node("generate_charts", self._generate_charts_node)
        builder.add_node("generate_html", self._generate_html_node)
        builder.add_node("save", self._save_node)
        
        # 엣지 연결
        builder.add_edge(START, "extract_data")
        builder.add_edge("extract_data", "generate_charts")
        builder.add_edge("generate_charts", "generate_html")
        builder.add_edge("generate_html", "save")
        builder.add_edge("save", END)
        
        return builder.compile()

    def _extract_data_node(self, state: ComparisonAnalysisState) -> ComparisonAnalysisState:
        """데이터 추출 노드 (병렬 처리)"""
        stores = state["stores"]
        end_date = state["end_date"]
        period = state["period"]
        analysis_type = state["analysis_type"]
        
        self.logger.info(f"병렬 데이터 추출 시작: {len(stores)}개 매장, {period}일")
        
        # 병렬 처리를 위한 워커 수 설정 (매장 수와 CPU 코어 수 중 작은 값)
        max_workers = min(len(stores), os.cpu_count() or 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 1. 일별 방문추이 데이터
            if analysis_type in ["daily_trends", "all"]:
                state["daily_trends_data"] = self._extract_parallel(
                    executor, stores, self.extractor.extract_daily_trends, 
                    end_date, period, "일별 방문추이"
                )
            
            # 2. 고객 구성 데이터
            if analysis_type in ["customer_composition", "all"]:
                state["customer_composition_data"] = self._extract_parallel(
                    executor, stores, self.extractor.extract_customer_composition,
                    end_date, period, "고객 구성"
                )
            
            # 3. 시간대/연령대 패턴 데이터
            if analysis_type in ["time_age_pattern", "all"]:
                state["time_age_pattern_data"] = self._extract_parallel(
                    executor, stores, self.extractor.extract_time_age_pattern,
                    end_date, period, "시간대/연령대 패턴"
                )
        
        self.logger.info("병렬 데이터 추출 완료")
        return state

    def _extract_parallel(
        self, 
        executor: ThreadPoolExecutor, 
        stores: List[str], 
        extract_func: callable, 
        end_date: str, 
        period: int, 
        data_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """병렬로 매장별 데이터 추출"""
        self.logger.info(f"{data_type} 데이터 병렬 추출 시작: {len(stores)}개 매장")
        
        # 모든 매장에 대한 Future 객체 생성
        future_to_store = {
            executor.submit(extract_func, store, end_date, period): store 
            for store in stores
        }
        
        results = {}
        completed_count = 0
        
        # as_completed를 사용하여 완료되는 대로 결과 수집
        for future in as_completed(future_to_store):
            store = future_to_store[future]
            completed_count += 1
            
            try:
                data = future.result()
                results[store] = data
                self.logger.info(f"{data_type} 데이터 추출 완료 ({completed_count}/{len(stores)}): {store}")
            except Exception as e:
                self.logger.error(f"{data_type} 데이터 추출 실패 ({completed_count}/{len(stores)}): {store}, {e}")
                results[store] = {"error": str(e)}
        
        self.logger.info(f"{data_type} 데이터 병렬 추출 완료: {len(results)}개 매장")
        return results

    def _generate_charts_node(self, state: ComparisonAnalysisState) -> ComparisonAnalysisState:
        """차트 생성 노드"""
        analysis_type = state["analysis_type"]
        
        self.logger.info("차트 생성 시작")
        
        # 1. 일별 방문추이 차트
        if analysis_type in ["daily_trends", "all"]:
            state["daily_trends_charts"] = {}
            for store, data in state["daily_trends_data"].items():
                if "error" not in data:
                    try:
                        chart = self.chart_renderer.render_daily_trends_chart(
                            data["daily_data"], width=800, height=400
                        )
                        state["daily_trends_charts"][store] = chart
                    except Exception as e:
                        self.logger.error(f"일별 방문추이 차트 생성 실패: {store}, {e}")
                        state["daily_trends_charts"][store] = f"차트 생성 실패: {e}"
        
        # 2. 고객 구성 차트
        if analysis_type in ["customer_composition", "all"]:
            state["customer_composition_charts"] = {}
            for store, data in state["customer_composition_data"].items():
                if "error" not in data:
                    try:
                        chart = self.chart_renderer.render_customer_composition_chart(
                            data["gender_distribution"], 
                            data["age_distribution"], 
                            width=800, height=400
                        )
                        state["customer_composition_charts"][store] = chart
                    except Exception as e:
                        self.logger.error(f"고객 구성 차트 생성 실패: {store}, {e}")
                        state["customer_composition_charts"][store] = f"차트 생성 실패: {e}"
        
        # 3. 시간대/연령대 패턴 히트맵
        if analysis_type in ["time_age_pattern", "all"]:
            state["time_age_pattern_charts"] = {}
            for store, data in state["time_age_pattern_data"].items():
                if "error" not in data:
                    try:
                        chart = self.chart_renderer.render_heatmap_chart(
                            data["heatmap_data"], width=800, height=500
                        )
                        state["time_age_pattern_charts"][store] = chart
                    except Exception as e:
                        self.logger.error(f"히트맵 차트 생성 실패: {store}, {e}")
                        state["time_age_pattern_charts"][store] = f"차트 생성 실패: {e}"
        
        self.logger.info("차트 생성 완료")
        return state

    def _generate_html_node(self, state: ComparisonAnalysisState) -> ComparisonAnalysisState:
        """HTML 생성 노드"""
        end_date = state["end_date"]
        period = state["period"]
        stores = state["stores"]
        analysis_type = state["analysis_type"]
        
        self.logger.info("HTML 생성 시작")
        
        # HTML 페이지 구성
        html_content = self._build_html_page(
            title=f"매장 비교 분석 리포트 (기준일: {end_date}, 기간: {period}일)",
            stores=stores,
            analysis_type=analysis_type,
            state=state
        )
        
        state["html_content"] = html_content
        self.logger.info("HTML 생성 완료")
        return state

    def _save_node(self, state: ComparisonAnalysisState) -> ComparisonAnalysisState:
        """저장 노드"""
        html = state.get("html_content", "")
        if not html:
            state["final_result"] = "HTML 콘텐츠가 없음"
            return state
        
        try:
            from libs.html_output_config import get_full_html_path
            
            # comparison 타입으로 저장
            out_path, latest_path = get_full_html_path("comparison", state['end_date'], only_latest=True)
            
            # 디렉토리 생성
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            # 파일 저장
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            # latest.html 동기화
            try:
                from shutil import copyfile
                copyfile(out_path, latest_path)
            except Exception:
                pass
            
            state["final_result"] = (
                "📊 매장 비교 분석 리포트 생성 완료!\n\n"
                f"📁 파일 경로: {out_path}\n\n"
                f"📈 분석 내용:\n"
                f"• 매장별 일별 방문추이 (전주 vs 금주)\n"
                f"• 고객 구성 차이 (성별, 연령대)\n"
                f"• 시간대/연령대별 방문 패턴 히트맵"
            )
            
        except Exception as e:
            self.logger.error(f"HTML 저장 실패: {e}")
            state["final_result"] = f"HTML 저장 실패: {e}"
        
        return state

    def _build_html_page(
        self, 
        title: str, 
        stores: List[str], 
        analysis_type: str, 
        state: ComparisonAnalysisState
    ) -> str:
        """HTML 페이지 구성"""
        # 탭 구성
        tabs_html = self._build_tabs(analysis_type)
        
        # 섹션 구성
        sections_html = self._build_sections(analysis_type, state)
        
        return f"""
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans KR', Arial, sans-serif; margin: 0; background: #fafafa; color: #111; }}
    .container {{ max-width: 1200px; margin: 24px auto; padding: 0 16px; }}
    header.page-header {{ margin-bottom: 16px; }}
    header.page-header h1 {{ font-size: 22px; margin: 0 0 4px; }}
    .desc {{ color: #666; font-size: 13px; }}
    .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; margin: 12px 0; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
    .card h2, .card h3 {{ margin: 0 0 8px; font-size: 18px; }}
    .tabs {{ display: flex; gap: 8px; margin: 8px 0 16px; }}
    .tab-label {{ padding: 8px 12px; background: #eef2ff; color: #3730a3; border-radius: 8px; cursor: pointer; user-select: none; }}
    .tab-label:hover {{ background: #e0e7ff; }}
    input[type="radio"].tab-input {{ display: none; }}
    .tab-section {{ display: none; }}
    .store-section {{ margin-bottom: 24px; }}
    .store-header {{ background: #f9fafb; padding: 12px; border-radius: 8px; margin-bottom: 16px; }}
    .store-name {{ font-size: 16px; font-weight: 600; color: #374151; }}
    .chart-container {{ text-align: center; margin: 16px 0; }}
    .chart-container svg {{ max-width: 100%; height: auto; }}
    .error-message {{ color: #dc2626; background: #fef2f2; padding: 12px; border-radius: 8px; border: 1px solid #fecaca; }}
  </style>
</head>
<body>
  <div class="container">
    <header class="page-header">
      <h1>{title}</h1>
      <div class="desc">매장 간 비교 분석을 통해 인사이트를 도출합니다</div>
    </header>
    
    {tabs_html}
    
    <div class="sections">
      {sections_html}
    </div>
  </div>
  
  <script>
    // 탭 전환 기능
    document.querySelectorAll('input[name="tabs"]').forEach(input => {{
      input.addEventListener('change', function() {{
        // 모든 섹션 숨기기
        document.querySelectorAll('.tab-section').forEach(section => {{
          section.style.display = 'none';
        }});
        
        // 선택된 섹션 보이기
        const targetSection = document.getElementById('section-' + this.value);
        if (targetSection) {{
          targetSection.style.display = 'block';
        }}
      }});
    }});
    
    // 첫 번째 탭 활성화
    document.querySelector('input[name="tabs"]').checked = true;
    document.querySelector('input[name="tabs"]').dispatchEvent(new Event('change'));
  </script>
</body>
</html>
"""

    def _build_tabs(self, analysis_type: str) -> str:
        """탭 구성"""
        tabs = []
        inputs = []
        css_rules = []
        
        if analysis_type in ["daily_trends", "all"]:
            tabs.append('<label for="tab-daily" class="tab-label">일별 방문추이</label>')
            inputs.append('<input id="tab-daily" class="tab-input" type="radio" name="tabs" checked />')
            css_rules.append('#tab-daily:checked ~ .sections #section-daily { display: block; }')
        
        if analysis_type in ["customer_composition", "all"]:
            tabs.append('<label for="tab-composition" class="tab-label">고객 구성</label>')
            inputs.append('<input id="tab-composition" class="tab-input" type="radio" name="tabs" />')
            css_rules.append('#tab-composition:checked ~ .sections #section-composition { display: block; }')
        
        if analysis_type in ["time_age_pattern", "all"]:
            tabs.append('<label for="tab-pattern" class="tab-label">시간대/연령대 패턴</label>')
            inputs.append('<input id="tab-pattern" class="tab-input" type="radio" name="tabs" />')
            css_rules.append('#tab-pattern:checked ~ .sections #section-pattern { display: block; }')
        
        # 첫 번째 탭을 기본으로 설정
        if inputs:
            inputs[0] = inputs[0].replace(' />', ' checked />')
        
        return f"""
        <div class="tabs">{''.join(tabs)}</div>
        {''.join(inputs)}
        <style>{''.join(css_rules)}</style>
        """

    def _build_sections(self, analysis_type: str, state: ComparisonAnalysisState) -> str:
        """섹션 구성"""
        sections = []
        
        # 1. 일별 방문추이 섹션
        if analysis_type in ["daily_trends", "all"]:
            sections.append(self._build_daily_trends_section(state))
        
        # 2. 고객 구성 섹션
        if analysis_type in ["customer_composition", "all"]:
            sections.append(self._build_customer_composition_section(state))
        
        # 3. 시간대/연령대 패턴 섹션
        if analysis_type in ["time_age_pattern", "all"]:
            sections.append(self._build_time_age_pattern_section(state))
        
        return '\n'.join(sections)

    def _build_daily_trends_section(self, state: ComparisonAnalysisState) -> str:
        """일별 방문추이 섹션"""
        stores = state["stores"]
        period = state["period"]
        
        store_sections = []
        for store in stores:
            data = state["daily_trends_data"].get(store, {})
            chart = state["daily_trends_charts"].get(store, "")
            
            if "error" in data:
                content = f'<div class="error-message">데이터 추출 실패: {data["error"]}</div>'
            elif chart and "차트 생성 실패" not in chart:
                content = f'<div class="chart-container">{chart}</div>'
            else:
                content = '<div class="error-message">차트 생성 실패</div>'
            
            store_sections.append(f"""
              <div class="store-section">
                <div class="store-header">
                  <div class="store-name">{store}</div>
                </div>
                {content}
              </div>
            """)
        
        return f"""
        <section id="section-daily" class="tab-section">
          <div class="card">
            <h2>일별 방문추이 분석</h2>
            <p class="desc">전주와 금주 {period}일간의 방문객 수 비교 및 증감률 추이</p>
          </div>
          {''.join(store_sections)}
        </section>
        """

    def _build_customer_composition_section(self, state: ComparisonAnalysisState) -> str:
        """고객 구성 섹션"""
        stores = state["stores"]
        
        store_sections = []
        for store in stores:
            data = state["customer_composition_data"].get(store, {})
            chart = state["customer_composition_charts"].get(store, "")
            
            if "error" in data:
                content = f'<div class="error-message">데이터 추출 실패: {data["error"]}</div>'
            elif chart and "차트 생성 실패" not in chart:
                content = f'<div class="chart-container">{chart}</div>'
            else:
                content = '<div class="error-message">차트 생성 실패</div>'
            
            store_sections.append(f"""
              <div class="store-section">
                <div class="store-header">
                  <div class="store-name">{store}</div>
                </div>
                {content}
              </div>
            """)
        
        return f"""
        <section id="section-composition" class="tab-section">
          <div class="card">
            <h2>고객 구성 분석</h2>
            <p class="desc">성별 및 연령대별 고객 분포 비교</p>
          </div>
          {''.join(store_sections)}
        </section>
        """

    def _build_time_age_pattern_section(self, state: ComparisonAnalysisState) -> str:
        """시간대/연령대 패턴 섹션"""
        stores = state["stores"]
        
        store_sections = []
        for store in stores:
            data = state["time_age_pattern_data"].get(store, {})
            chart = state["time_age_pattern_charts"].get(store, "")
            
            if "error" in data:
                content = f'<div class="error-message">데이터 추출 실패: {data["error"]}</div>'
            elif chart and "차트 생성 실패" not in chart:
                content = f'<div class="chart-container">{chart}</div>'
            else:
                content = '<div class="error-message">차트 생성 실패</div>'
            
            store_sections.append(f"""
              <div class="store-section">
                <div class="store-header">
                  <div class="store-name">{store}</div>
                </div>
                {content}
              </div>
            """)
        
        return f"""
        <section id="section-pattern" class="tab-section">
          <div class="card">
            <h2>시간대/연령대별 방문 패턴</h2>
            <p class="desc">24시간 기준 시간대별, 연령대별 방문 패턴 히트맵</p>
          </div>
          {''.join(store_sections)}
        </section>
        """

    def _clamp_end_date_to_yesterday(self, end_date_iso: str) -> str:
        """기준일이 오늘이거나 미래인 경우 어제로 조정"""
        end_d = date.fromisoformat(end_date_iso)
        today = date.today()
        if end_d >= today:
            return (today - timedelta(days=1)).isoformat()
        return end_date_iso


# ----------------------------- FastMCP Tool -----------------------------
from fastmcp import FastMCP

mcp = FastMCP("comparison_analysis")


@mcp.tool()
def comparison_analysis_html(
    *,
    stores: str | list[str],
    end_date: str,
    period: int = 7,
    analysis_type: str = "all",
) -> str:
    """
    [COMPARISON_ANALYSIS] Generate a comparison analysis HTML report for multiple stores.

    Parameters
    ----------
    - stores: 매장 목록(문자열 콤마 구분 또는 리스트)
    - end_date: 기준일(YYYY-MM-DD)
    - period: 분석 기간(일, 기본값: 7)
    - analysis_type: 분석 타입 ("daily_trends", "customer_composition", "time_age_pattern", "all")
    """
    generator = ComparisonAnalysisGenerator()
    return generator.run(
        stores=stores,
        end_date=end_date,
        period=period,
        analysis_type=analysis_type,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Comparison Analysis Workflow Runner")
    parser.add_argument("--stores", required=True, help="콤마로 구분된 매장 문자열")
    parser.add_argument("--end", required=True, help="기준일(YYYY-MM-DD)")
    parser.add_argument("--period", type=int, default=7, help="분석 기간(일)")
    parser.add_argument("--type", default="all", help="분석 타입 (daily_trends, customer_composition, time_age_pattern, all)")
    parser.add_argument("--cli", action="store_true", help="FastMCP 서버 대신 1회 실행")
    args = parser.parse_args()

    if args.cli:
        generator = ComparisonAnalysisGenerator()
        result = generator.run(
            stores=args.stores,
            end_date=args.end,
            period=args.period,
            analysis_type=args.type
        )
        print(result)
    else:
        print("FastMCP 서버 시작 - comparison_analysis")
        mcp.run() 