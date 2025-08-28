"""
간단한 시간 측정 유틸리티 - 제거하기 쉽게 설계
"""

import time
import logging
from contextlib import contextmanager
from typing import List, Tuple

# 성능 측정용 로거 - database.py와 동일한 방식으로
logger = logging.getLogger(__name__)


class TimerCollector:
    """시간 측정 결과를 수집하는 클래스"""
    def __init__(self):
        self.measurements: List[Tuple[str, float]] = []
    
    def add_measurement(self, name: str, duration: float):
        """측정 결과 추가"""
        self.measurements.append((name, duration))
    
    def print_summary(self):
        """수집된 모든 측정 결과 출력 (파일 저장 + 로거)"""
        if not self.measurements:
            return
            
        total_time = sum(duration for _, duration in self.measurements)
        
        # 결과 텍스트 생성
        lines = []
        lines.append("=" * 50)
        lines.append("⏱️  성능 측정 결과")
        lines.append("-" * 50)
        
        for name, duration in self.measurements:
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            lines.append(f"{name:<25} {duration:6.2f}초 ({percentage:5.1f}%)")
        
        lines.append("-" * 50)
        lines.append(f"{'총 소요 시간':<25} {total_time:6.2f}초")
        lines.append("=" * 50)
        
        result_text = "\n".join(lines)
        
        # 로거로 출력
        for line in lines:
            logger.info(line)
        
        # 파일로 저장
        try:
            import os
            from datetime import datetime
            
            # data/logs 디렉토리 생성
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            # 타임스탬프 포함한 파일명
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_{timestamp}.txt"
            filepath = os.path.join(log_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result_text)
            
            logger.info(f"📄 성능 측정 결과 파일 저장: {filepath}")
            print(f"📄 성능 측정 결과 파일 저장: {filepath}")  # 콘솔에도 출력
            
        except Exception as e:
            logger.error(f"성능 측정 결과 파일 저장 실패: {e}")
            print(f"❌ 성능 측정 결과 파일 저장 실패: {e}")
    
    def reset(self):
        """측정 결과 초기화"""
        self.measurements.clear()


# 전역 타이머 수집기
_timer_collector = TimerCollector()


@contextmanager
def timer(name: str):
    """
    간단한 시간 측정 컨텍스트 매니저 (결과는 나중에 일괄 출력)
    
    사용법:
    with timer("데이터 추출"):
        # 측정할 코드
        do_something()
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        duration = end_time - start_time
        _timer_collector.add_measurement(name, duration)


def print_timer_summary():
    """수집된 모든 타이머 결과 출력"""
    _timer_collector.print_summary()


def reset_timers():
    """타이머 결과 초기화"""
    _timer_collector.reset()


def get_timer_results():
    """타이머 결과를 딕셔너리로 반환 (JSON 응답용)"""
    if not _timer_collector.measurements:
        return None
    
    total_time = sum(duration for _, duration in _timer_collector.measurements)
    
    results = {
        "total_time": round(total_time, 2),
        "measurements": []
    }
    
    for name, duration in _timer_collector.measurements:
        percentage = (duration / total_time * 100) if total_time > 0 else 0
        results["measurements"].append({
            "name": name,
            "duration": round(duration, 2),
            "percentage": round(percentage, 1)
        })
    
    return results