"""
워크플로우 중앙 설정 파일
모든 워크플로우에서 공통으로 사용하는 설정값들
"""

import os
from typing import Dict, Any


class WorkflowConfig:
    """워크플로우 설정 클래스"""
    
    # LLM 모델 설정
    LLM_MODELS = {
        'default': 'gpt-4o-mini',
        'comparison': 'gpt-5',  # 비교 분석용
        'summary': 'gpt-4o-mini',
        'advanced': 'gpt-4',
    }
    
    # LLM 파라미터
    LLM_PARAMS = {
        'temperature': 0.0,
        'max_tokens': 2000,
        'timeout': 30,
    }
    
    # 데이터베이스 설정
    DATABASE = {
        'default_database': 'plusinsight',
        'config_database': 'cu_base',
        'timeout': 60,
        'retry_count': 3,
    }
    
    # 차트 설정
    CHART = {
        'default_width': 1100,
        'default_height': 640,
        'padding': 100,
        'colors': {
            'primary': '#3467E2',
            'secondary': '#76CCCF',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
        }
    }
    
    # 프롬프트 템플릿
    PROMPTS = {
        'visitor_summary': """
당신은 리테일 방문 데이터 분석 전문가입니다. 아래 표형 텍스트를 근거로 한국어로 간결한 요약을 작성하세요.

[지침]
1. 가장 중요한 인사이트 3~5개를 도출하세요.
2. 각 항목은 25~50자로 작성하세요.
3. 증감률이 높은 매장과 낮은 매장을 구분하세요.
4. 마크다운 불릿 포인트로 작성하세요.

데이터:
{data}
""",
        
        'comparison_analysis': """
당신은 리테일 방문 데이터 비교 분석가입니다. 아래 표형 텍스트를 근거로 한국어로 간결한 비교 분석을 작성하세요.

[비교분석 요약 지침]
1. 매장 간 성과 차이: 금주 방문객 수와 증감률을 기준으로 매장별 성과 순위를 매기고 핵심 인사이트를 도출하세요.
2. 평일/주말 패턴 분석: 평일과 주말의 증감률 차이를 분석하여 매장별 특성을 파악하세요.
3. 성장/하락 추세: 증감률이 높은 매장과 낮은 매장을 구분하고, 각각의 특징을 요약하세요.
4. 개선점 제시: 성과가 낮은 매장의 개선 방향을 구체적으로 제시하세요.

[출력 형식]
- 불릿 5~7개, 각 항목 25~50자
- 각 항목을 "- "로 시작하는 마크다운 불릿 목록으로만 출력

데이터:
{data}
""",
    }
    
    # 로깅 설정
    LOGGING = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'log_dir': 'results/logs',
    }
    
    # 파일 경로 설정
    PATHS = {
        'results_dir': 'results',
        'logs_dir': 'results/logs',
        'html_output_root': os.environ.get('HTML_OUTPUT_ROOT', 'html_report'),
        'temp_dir': 'temp',
    }
    
    # 매장 정보
    STORES = {
        'all': [
            '금천프라임점',
            '마천파크점',
            '만촌힐스테이트점',
            '망우혜원점',
            '신촌르메이에르점',
            '역삼점',
            '타워팰리스점'
        ],
        'default_exclude': ['망우혜원점'],  # 기본적으로 제외할 매장
    }
    
    # 날짜 형식
    DATE_FORMATS = {
        'default': '%Y-%m-%d',
        'korean': '%Y년 %m월 %d일',
        'short': '%m/%d',
        'filename': '%Y%m%d',
    }
    
    @classmethod
    def get_llm_model(cls, model_type: str = 'default') -> str:
        """LLM 모델명을 반환합니다."""
        return cls.LLM_MODELS.get(model_type, cls.LLM_MODELS['default'])
    
    @classmethod
    def get_prompt_template(cls, prompt_type: str) -> str:
        """프롬프트 템플릿을 반환합니다."""
        return cls.PROMPTS.get(prompt_type, "")
    
    @classmethod
    def get_active_stores(cls) -> list:
        """활성 매장 목록을 반환합니다 (제외 매장 제거)."""
        all_stores = cls.STORES['all']
        exclude = cls.STORES['default_exclude']
        return [s for s in all_stores if s not in exclude]
    
    @classmethod
    def get_chart_config(cls) -> Dict[str, Any]:
        """차트 설정을 반환합니다."""
        return cls.CHART.copy()
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """데이터베이스 설정을 반환합니다."""
        return cls.DATABASE.copy()