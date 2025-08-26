"""
숫자 및 날짜 포맷팅 유틸리티
"""

from typing import Optional, Union
from datetime import datetime, date, timedelta
import locale


def format_number(value: Union[int, float, None], decimal_places: int = 0) -> str:
    """숫자를 천 단위 콤마를 포함한 문자열로 포맷합니다.
    
    Args:
        value: 포맷할 숫자
        decimal_places: 소수점 자리수
    
    Returns:
        포맷된 문자열
    """
    if value is None:
        return ""
    
    try:
        if decimal_places == 0:
            return f"{int(value):,}"
        else:
            return f"{value:,.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(
    value: Union[float, None], 
    decimal_places: int = 1,
    include_sign: bool = True,
    include_percent: bool = True
) -> str:
    """백분율을 포맷합니다.
    
    Args:
        value: 백분율 값
        decimal_places: 소수점 자리수
        include_sign: 양수일 때 + 기호 포함 여부
        include_percent: % 기호 포함 여부
    
    Returns:
        포맷된 백분율 문자열
    """
    if value is None:
        return ""
    
    try:
        formatted = f"{value:.{decimal_places}f}"
        
        if include_sign and value > 0:
            formatted = "+" + formatted
        
        if include_percent:
            formatted += "%"
            
        return formatted
    except (ValueError, TypeError):
        return str(value)


def format_date(date_value: Union[str, date, datetime], format_str: str = "%Y-%m-%d") -> str:
    """날짜를 지정된 형식으로 포맷합니다.
    
    Args:
        date_value: 날짜 값
        format_str: 날짜 포맷 문자열
    
    Returns:
        포맷된 날짜 문자열
    """
    if date_value is None:
        return ""
    
    try:
        if isinstance(date_value, str):
            # ISO 형식 문자열을 datetime으로 변환
            if "T" in date_value:
                dt = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(date_value, "%Y-%m-%d")
        elif isinstance(date_value, datetime):
            dt = date_value
        elif isinstance(date_value, date):
            dt = datetime.combine(date_value, datetime.min.time())
        else:
            return str(date_value)
        
        return dt.strftime(format_str)
    except Exception:
        return str(date_value)


def format_date_korean(date_value: Union[str, date, datetime]) -> str:
    """날짜를 한국어 형식으로 포맷합니다 (예: 2024년 1월 15일).
    
    Args:
        date_value: 날짜 값
    
    Returns:
        한국어 형식의 날짜 문자열
    """
    if date_value is None:
        return ""
    
    try:
        if isinstance(date_value, str):
            dt = datetime.strptime(date_value, "%Y-%m-%d")
        elif isinstance(date_value, datetime):
            dt = date_value
        elif isinstance(date_value, date):
            dt = datetime.combine(date_value, datetime.min.time())
        else:
            return str(date_value)
        
        return f"{dt.year}년 {dt.month}월 {dt.day}일"
    except Exception:
        return str(date_value)


def format_weekday(date_value: Union[str, date, datetime]) -> str:
    """날짜의 요일을 한국어로 반환합니다.
    
    Args:
        date_value: 날짜 값
    
    Returns:
        요일 문자열 (예: "월", "화")
    """
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    
    try:
        if isinstance(date_value, str):
            dt = datetime.strptime(date_value, "%Y-%m-%d")
        elif isinstance(date_value, datetime):
            dt = date_value
        elif isinstance(date_value, date):
            dt = datetime.combine(date_value, datetime.min.time())
        else:
            return ""
        
        return weekdays[dt.weekday()]
    except Exception:
        return ""


def format_date_range(start_date: Union[str, date], end_date: Union[str, date]) -> str:
    """날짜 범위를 포맷합니다.
    
    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
    
    Returns:
        포맷된 날짜 범위 문자열
    """
    start_str = format_date_korean(start_date)
    end_str = format_date_korean(end_date)
    
    if start_str and end_str:
        return f"{start_str} ~ {end_str}"
    elif start_str:
        return start_str
    elif end_str:
        return end_str
    else:
        return ""


def format_time(hour: int) -> str:
    """시간을 포맷합니다.
    
    Args:
        hour: 시간 (0-23)
    
    Returns:
        포맷된 시간 문자열 (예: "오전 9시", "오후 3시")
    """
    if hour < 0 or hour > 23:
        return f"{hour}시"
    
    if hour == 0:
        return "자정"
    elif hour == 12:
        return "정오"
    elif hour < 12:
        return f"오전 {hour}시"
    else:
        return f"오후 {hour - 12}시"


def format_duration(seconds: float) -> str:
    """시간 간격을 사람이 읽기 쉬운 형식으로 포맷합니다.
    
    Args:
        seconds: 초 단위 시간
    
    Returns:
        포맷된 시간 문자열 (예: "2시간 30분")
    """
    if seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}분"
    else:
        hours = seconds / 3600
        if hours < 24:
            return f"{hours:.1f}시간"
        else:
            days = hours / 24
            return f"{days:.1f}일"


def calculate_percentage_change(old_value: float, new_value: float) -> Optional[float]:
    """두 값 사이의 백분율 변화를 계산합니다.
    
    Args:
        old_value: 이전 값
        new_value: 새 값
    
    Returns:
        백분율 변화 (None if old_value is 0)
    """
    if old_value == 0:
        return None
    
    return ((new_value - old_value) / old_value) * 100


def format_large_number(value: Union[int, float]) -> str:
    """큰 숫자를 읽기 쉬운 형식으로 포맷합니다.
    
    Args:
        value: 숫자 값
    
    Returns:
        포맷된 문자열 (예: "1.2만", "3.5억")
    """
    if value is None:
        return ""
    
    try:
        abs_value = abs(value)
        sign = "-" if value < 0 else ""
        
        if abs_value >= 100000000:  # 1억 이상
            return f"{sign}{abs_value/100000000:.1f}억"
        elif abs_value >= 10000:  # 1만 이상
            return f"{sign}{abs_value/10000:.1f}만"
        elif abs_value >= 1000:  # 1천 이상
            return f"{sign}{abs_value/1000:.1f}천"
        else:
            return f"{sign}{int(abs_value)}"
    except (ValueError, TypeError):
        return str(value)