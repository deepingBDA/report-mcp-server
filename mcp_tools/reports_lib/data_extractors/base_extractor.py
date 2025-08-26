"""
데이터 추출기 부모 클래스

모든 데이터 추출기가 구현해야 하는 공통 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import date, timedelta

# from mcp_tools.reports.specs import get_db_config, DataSpec  # TODO: specs 모듈 구현 필요


class BaseDataExtractor(ABC):
    """데이터 추출기 부모 클래스"""
    
    def __init__(self, data_spec: str):
        """
        Args:
            data_spec: 데이터 스펙 (visitor, touch_point, dwelling_time, sales)
        """
        self.data_spec = data_spec
        # self.db_config = get_db_config(data_spec)  # TODO: specs 모듈 구현 필요
        # self.spec_config = get_db_config(data_spec)  # TODO: specs 모듈 구현 필요
        self.db_config = {}
        self.spec_config = {}
    
    @abstractmethod
    def extract_period_data(self, site: str, end_date: str, days: int) -> Dict[str, Any]:
        """
        지정된 기간에 대한 데이터를 추출합니다.
        
        Args:
            site: 매장명
            end_date: 기준일 (YYYY-MM-DD)
            days: 분석 기간 (일)
            
        Returns:
            기간별 데이터 딕셔너리
        """
        pass
    
    @abstractmethod
    def extract_series_data(self, site: str, end_date: str, weeks: int = 4) -> Dict[str, List[float]]:
        """
        시리즈 데이터를 추출합니다.
        
        Args:
            site: 매장명
            end_date: 기준일 (YYYY-MM-DD)
            weeks: 분석 주차 수
            
        Returns:
            시리즈 데이터 딕셔너리
        """
        pass
    
    def extract_multiple_sites(self, sites: List[str], end_date: str, days: int) -> List[Dict[str, Any]]:
        """
        여러 매장의 데이터를 일괄 추출합니다.
        
        Args:
            sites: 매장명 리스트
            end_date: 기준일 (YYYY-MM-DD)
            days: 분석 기간 (일)
            
        Returns:
            매장별 데이터 리스트
        """
        results = []
        for site in sites:
            try:
                data = self.extract_period_data(site, end_date, days)
                results.append(data)
            except Exception as e:
                # 에러 발생 시 기본값으로 대체
                results.append(self._create_fallback_data(site, end_date))
        
        return results
    
    def _create_fallback_data(self, site: str, end_date: str) -> Dict[str, Any]:
        """에러 발생 시 기본 데이터 생성"""
        return {
            "site": site,
            "end_date": end_date,
            "curr_total": None,
            "prev_total": None,
            "weekday_delta_pct": None,
            "weekend_delta_pct": None,
            "total_delta_pct": None,
        }
    
    def _clamp_end_date_to_yesterday(self, end_date_iso: str) -> str:
        """기준일이 오늘이거나 미래인 경우 어제로 조정"""
        end_d = date.fromisoformat(end_date_iso)
        today = date.today()
        if end_d >= today:
            return (today - timedelta(days=1)).isoformat()
        return end_date_iso
    
    def get_spec_name(self) -> str:
        """스펙의 표시 이름 반환"""
        return self.spec_config.get("name", self.data_spec)
    
    def get_supported_periods(self) -> List[int]:
        """지원하는 분석 기간 반환"""
        return self.spec_config.get("periods", [7, 30, 90])
    
    def get_default_period(self) -> int:
        """기본 분석 기간 반환"""
        return self.spec_config.get("default_period", 7)
    
    def get_table_columns(self) -> List[str]:
        """테이블 컬럼명 반환"""
        return self.spec_config.get("table_columns", [])
    
    def get_chart_type(self) -> str:
        """차트 타입 반환"""
        return self.spec_config.get("chart_type", "scatter")
    
    def get_color_scheme(self) -> Dict[str, str]:
        """색상 스키마 반환"""
        return self.spec_config.get("color_scheme", {})
    
    def validate_spec(self) -> bool:
        """스펙 유효성 검증"""
        # return self.data_spec in DataSpec.__members__  # TODO: specs 모듈 구현 필요
        return self.data_spec in ["visitor", "touch_point", "dwelling_time", "sales"] 