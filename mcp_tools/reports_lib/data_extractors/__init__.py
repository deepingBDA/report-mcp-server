"""
데이터 추출기 패키지

다양한 데이터 스펙에 대한 데이터 추출기를 제공합니다.
"""

from mcp_tools.reports.data_extractors.base_extractor import BaseDataExtractor
from mcp_tools.reports.data_extractors.comparison_extractor import ComparisonDataExtractor

__all__ = [
    "BaseDataExtractor",
    "ComparisonDataExtractor",
    "create_extractor",
]


def create_extractor(data_spec: str) -> BaseDataExtractor:
    """
    스펙에 맞는 데이터 추출기를 생성합니다.
    
    Args:
        data_spec: 데이터 스펙 (visitor, touch_point, dwelling_time, sales)
        
    Returns:
        해당 스펙의 데이터 추출기 인스턴스
        
    Raises:
        ValueError: 지원하지 않는 스펙인 경우
    """
    extractors = {
        "visitor": ComparisonDataExtractor,  # 임시로 ComparisonDataExtractor 사용
        # TODO: 추후 구현
        # "touch_point": TouchPointDataExtractor,
        # "dwelling_time": DwellingTimeDataExtractor,
        # "sales": SalesDataExtractor,
    }
    
    if data_spec not in extractors:
        available = ", ".join(extractors.keys())
        raise ValueError(f"지원하지 않는 스펙: {data_spec}. 사용 가능한 스펙: {available}")
    
    return extractors[data_spec]() 