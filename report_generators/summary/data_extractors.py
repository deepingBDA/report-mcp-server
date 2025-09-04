"""
Summary Report용 데이터 추출 클래스들
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import date, timedelta

from libs.database import get_site_client


class SummaryDataExtractor(ABC):
    """Summary Report용 데이터 추출 베이스 클래스"""
    
    @abstractmethod
    def extract_period_rates(self, store: str, end_date: str, days: int) -> Dict:
        """기간별 증감률 데이터 추출"""
        pass
    
    @abstractmethod
    def extract_daily_series(self, store: str, end_date: str, days: int = 7) -> Dict:
        """일별 시리즈 데이터 추출 (1일 모드용)"""
        pass
    
    @abstractmethod
    def extract_weekly_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        """주별 시리즈 데이터 추출 (7일 모드용)"""
        pass
    
    @abstractmethod
    def extract_same_weekday_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        """같은 요일 시리즈 데이터 추출"""
        pass


class VisitorSummaryExtractor(SummaryDataExtractor):
    """방문자 데이터 추출기"""
    
    def extract_period_rates(self, store: str, end_date: str, days: int) -> Dict:
        """
        지정된 기간에 대한 매장별 증감률 데이터를 가져온다
        기존 summarize_period_rates 로직을 이관
        """
        # TODO: 기존 summarize_period_rates 함수 내용 이관
        # 1일 모드에서는 전주 같은 요일과 비교
        # 다른 모드에서는 기간별 비교
        pass
    
    def extract_daily_series(self, store: str, end_date: str, days: int = 7) -> Dict:
        """
        일별 방문 합계 시리즈를 가져온다 (1일 모드용)
        기존 fetch_daily_series 로직을 이관
        """
        # TODO: 기존 fetch_daily_series 함수 내용 이관
        pass
    
    def extract_weekly_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        """
        주별 시리즈 데이터 추출 (7일 모드용)
        기존 fetch_weekly_series 로직을 이관
        """
        # TODO: 기존 fetch_weekly_series 함수 내용 이관
        pass
    
    def extract_same_weekday_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        """
        같은 요일 시리즈 데이터 추출
        기존 fetch_same_weekday_series 로직을 이관
        """
        # TODO: 기존 fetch_same_weekday_series 함수 내용 이관
        pass


class TouchPointSummaryExtractor(SummaryDataExtractor):
    """터치포인트 데이터 추출기"""
    
    def extract_period_rates(self, store: str, end_date: str, days: int) -> Dict:
        # TODO: 터치포인트 전용 쿼리 구현
        pass
    
    def extract_daily_series(self, store: str, end_date: str, days: int = 7) -> Dict:
        # TODO: 터치포인트 일별 시리즈 구현
        pass
    
    def extract_weekly_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        # TODO: 터치포인트 주별 시리즈 구현
        pass
    
    def extract_same_weekday_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        # TODO: 터치포인트 같은 요일 시리즈 구현
        pass


class DwellingTimeSummaryExtractor(SummaryDataExtractor):
    """체류시간 데이터 추출기"""
    
    def extract_period_rates(self, store: str, end_date: str, days: int) -> Dict:
        # TODO: 체류시간 전용 쿼리 구현
        pass
    
    def extract_daily_series(self, store: str, end_date: str, days: int = 7) -> Dict:
        # TODO: 체류시간 일별 시리즈 구현
        pass
    
    def extract_weekly_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        # TODO: 체류시간 주별 시리즈 구현
        pass
    
    def extract_same_weekday_series(self, store: str, end_date: str, weeks: int = 4) -> Dict:
        # TODO: 체류시간 같은 요일 시리즈 구현
        pass


def create_extractor(data_type: str) -> SummaryDataExtractor:
    """데이터 타입에 따른 Extractor 팩토리"""
    extractors = {
        "visitor": VisitorSummaryExtractor,
        "touch_point": TouchPointSummaryExtractor,
        "dwelling_time": DwellingTimeSummaryExtractor,
    }
    
    if data_type not in extractors:
        raise ValueError(f"Unknown data_type: {data_type}")
    
    return extractors[data_type]()