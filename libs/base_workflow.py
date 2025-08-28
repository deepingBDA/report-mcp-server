"""
Base Workflow 클래스
워크플로우의 기본 구조만 제공하는 추상 베이스 클래스
"""

import os
import sys
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, TypedDict, Generic, TypeVar, Optional, Tuple
from shutil import copyfile

from langgraph.graph import StateGraph


# Generic State Type
StateType = TypeVar('StateType', bound='BaseState')


class BaseState(TypedDict):
    """
    모든 워크플로우의 기본 상태 정의
    최소한의 공통 필드만 포함
    """
    user_prompt: str        # 사용자 요청
    workflow_id: str        # 워크플로우 고유 ID
    timestamp: str          # 실행 시작 시간


class BaseWorkflow(ABC, Generic[StateType]):
    """
    모든 워크플로우의 기본 클래스
    핵심 구조만 제공하고 구체적 구현은 하위 클래스에 위임
    """
    
    def __init__(self, workflow_name: str = "base"):
        """
        Args:
            workflow_name: 워크플로우 이름 (로깅에 사용)
        """
        self.workflow_name = workflow_name
        
        # 로깅 설정
        self.logger = self._setup_logging()
        self.logger.info(f"{workflow_name} 워크플로우 초기화")
        
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정 (내부 메서드)"""
        log_dir = Path("results/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{self.workflow_name}_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger = logging.getLogger(self.workflow_name)
        logger.info(f"로그 파일 생성: {log_file}")
        return logger
    


    def create_initial_state(self, user_prompt: str, **kwargs) -> StateType:
        """
        초기 상태 생성
        하위 클래스에서 오버라이드하여 추가 필드 설정 가능
        """
        base_state = {
            "user_prompt": user_prompt,
            "workflow_id": f"{self.workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
        }
        return base_state  # type: ignore
    

        
    @abstractmethod
    def run(self, user_prompt: str, **kwargs) -> str:
        """
        워크플로우 실행 메서드
        하위 클래스에서 반드시 구현해야 합니다.
        """
        pass

    @abstractmethod 
    def _build_workflow(self) -> StateGraph:
        """
        LangGraph 워크플로우 구성
        하위 클래스에서 반드시 구현해야 합니다.
        """
        pass
    
    def save_html(self, html_content: str, report_type: str, end_date: str, 
                  use_unified: bool = False) -> Tuple[str, str]:
        """
        HTML 파일을 저장하는 공통 메서드
        
        Args:
            html_content: HTML 내용
            report_type: 리포트 타입 ('visitor_daily', 'visitor_weekly', 'comparison', etc.)
            end_date: 종료 날짜 (YYYY-MM-DD)
            use_unified: 통합 디렉토리 사용 여부
            
        Returns:
            (full_path, latest_path) 튜플
        """
        try:
            # config 모듈 임포트
            mcp_tools_path = Path(__file__).parent
            if str(mcp_tools_path) not in sys.path:
                sys.path.insert(0, str(mcp_tools_path))
            
            from libs.html_output_config import get_full_html_path
            
            # 경로 가져오기
            out_path, latest_path = get_full_html_path(
                report_type=report_type,
                end_date=end_date,
                use_unified=use_unified
            )
            
            # HTML 파일 저장
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # latest.html 동기화
            try:
                copyfile(out_path, latest_path)
            except Exception as e:
                self.logger.warning(f"latest.html 복사 실패: {e}")
            
            self.logger.info(f"HTML 리포트 저장 완료: {out_path}")
            return out_path, latest_path
            
        except Exception as e:
            self.logger.error(f"HTML 저장 실패: {e}")
            raise
    
    def generate_llm_summary(self, prompt_template: str, data: Any, 
                           llm_model: Optional[Any] = None) -> str:
        """
        LLM을 사용하여 요약을 생성하는 공통 메서드
        
        Args:
            prompt_template: 프롬프트 템플릿
            data: 요약할 데이터
            llm_model: LLM 모델 (없으면 기본 모델 사용)
            
        Returns:
            생성된 요약 텍스트
        """
        try:
            if llm_model is None:
                # 기본 모델 사용
                from langchain_openai import ChatOpenAI
                llm_model = ChatOpenAI(model="gpt-4o", temperature=0.1)
            
            # 프롬프트 생성
            prompt = prompt_template.format(data=data)
            
            # LLM 호출
            response = llm_model.invoke(prompt)
            
            # 응답 추출
            if hasattr(response, 'content'):
                return response.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            self.logger.error(f"LLM 요약 생성 실패: {e}")
            return f"요약 생성 중 오류 발생: {str(e)}"
    
    def format_error_response(self, error: Exception) -> str:
        """
        에러를 포맷된 응답으로 변환하는 공통 메서드
        
        Args:
            error: 발생한 예외
            
        Returns:
            포맷된 에러 메시지
        """
        error_msg = f"❌ {self.workflow_name} 워크플로우 실행 중 오류 발생:\n{str(error)}"
        self.logger.error(error_msg, exc_info=True)
        return error_msg
    
    def validate_input(self, **kwargs) -> bool:
        """
        입력 데이터 유효성 검사
        하위 클래스에서 오버라이드 가능
        
        Returns:
            유효성 검사 통과 여부
        """
        return True