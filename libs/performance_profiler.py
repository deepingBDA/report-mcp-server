"""
성능 측정 프로파일러

제거하기 쉽게 설계된 성능 측정 도구:
1. 컨텍스트 매니저 방식으로 기존 코드 변경 최소화
2. 환경변수로 활성화/비활성화 제어
3. 단일 파일 삭제로 완전 제거 가능
"""

import time
import os
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MeasurementResult:
    """측정 결과 데이터 클래스"""
    section: str
    duration: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceProfiler:
    """성능 측정 프로파일러 - 쉬운 제거를 위한 단일 파일 설계"""
    
    _instance: Optional['PerformanceProfiler'] = None
    
    def __init__(self):
        self.measurements: Dict[str, List[MeasurementResult]] = {}
        self.enabled = os.getenv('ENABLE_PERFORMANCE_PROFILER', 'true').lower() == 'true'
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @classmethod
    def get_instance(cls) -> 'PerformanceProfiler':
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @contextmanager
    def measure(self, section_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        컨텍스트 매니저 방식 시간 측정
        
        사용법:
        with profiler.measure("데이터_추출", {"store_count": 5}):
            # 측정할 코드
            extract_data()
        """
        if not self.enabled:
            yield
            return
            
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            result = MeasurementResult(
                section=section_name,
                duration=duration,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            if section_name not in self.measurements:
                self.measurements[section_name] = []
            self.measurements[section_name].append(result)
            
            # 즉시 로그 출력
            meta_str = f" ({metadata})" if metadata else ""
            print(f"⏱️  {section_name}: {duration:.2f}초{meta_str}")
    
    def get_summary(self) -> Dict[str, Any]:
        """측정 결과 요약 반환"""
        if not self.enabled or not self.measurements:
            return {"enabled": False, "message": "성능 측정이 비활성화되었거나 데이터가 없습니다"}
        
        summary = {
            "session": self.current_session,
            "enabled": True,
            "sections": [],
            "total_sections": len(self.measurements),
            "total_measurements": sum(len(results) for results in self.measurements.values())
        }
        
        total_time = 0
        for section, results in self.measurements.items():
            times = [r.duration for r in results]
            section_total = sum(times)
            total_time += section_total
            
            summary["sections"].append({
                "name": section,
                "count": len(times),
                "total_time": section_total,
                "avg_time": section_total / len(times),
                "min_time": min(times),
                "max_time": max(times),
                "latest": results[-1].timestamp.isoformat()
            })
        
        # 시간 비중 계산
        for section in summary["sections"]:
            section["percentage"] = (section["total_time"] / total_time * 100) if total_time > 0 else 0
        
        # 시간순 정렬 (가장 오래 걸리는 구간부터)
        summary["sections"].sort(key=lambda x: x["total_time"], reverse=True)
        summary["total_time"] = total_time
        
        return summary
    
    def print_report(self):
        """콘솔에 성능 리포트 출력"""
        summary = self.get_summary()
        
        if not summary["enabled"]:
            print(summary["message"])
            return
        
        print("\n" + "=" * 80)
        print(f"🔍 성능 측정 리포트 (세션: {summary['session']})")
        print("=" * 80)
        print(f"총 측정 구간: {summary['total_sections']}개")
        print(f"총 측정 횟수: {summary['total_measurements']}회")
        print(f"전체 소요 시간: {summary['total_time']:.2f}초")
        print("\n📊 구간별 성능 (느린 순):")
        print("-" * 80)
        
        for i, section in enumerate(summary["sections"], 1):
            print(f"{i:2d}. {section['name']:<30} "
                  f"총:{section['total_time']:6.2f}초 "
                  f"평균:{section['avg_time']:6.2f}초 "
                  f"횟수:{section['count']:2d} "
                  f"비중:{section['percentage']:5.1f}%")
        
        print("-" * 80)
        
        # 상위 3개 병목 구간 강조
        if summary["sections"]:
            print("\n🚨 주요 병목 구간:")
            for i, section in enumerate(summary["sections"][:3], 1):
                print(f"   {i}. {section['name']} - {section['percentage']:.1f}% ({section['total_time']:.2f}초)")
        
        print("\n")
    
    def save_report(self, filepath: Optional[str] = None):
        """JSON 형태로 상세 리포트 저장"""
        if not self.enabled:
            return
            
        if not filepath:
            filepath = f"performance_report_{self.current_session}.json"
        
        detailed_data = {
            "summary": self.get_summary(),
            "raw_measurements": {}
        }
        
        # 상세 측정 데이터 포함
        for section, results in self.measurements.items():
            detailed_data["raw_measurements"][section] = [
                {
                    "duration": r.duration,
                    "timestamp": r.timestamp.isoformat(),
                    "metadata": r.metadata
                }
                for r in results
            ]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 상세 리포트 저장됨: {filepath}")
    
    def reset(self):
        """측정 데이터 초기화"""
        self.measurements.clear()
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        print("🔄 성능 측정 데이터가 초기화되었습니다")


# 전역 인스턴스 - 쉬운 사용을 위해
profiler = PerformanceProfiler.get_instance()


# 비활성화용 더미 클래스 (필요시 사용)
class DummyProfiler:
    """성능 측정 비활성화 시 사용하는 더미 클래스"""
    
    @contextmanager
    def measure(self, section_name: str, metadata=None):
        yield
    
    def get_summary(self):
        return {"enabled": False}
    
    def print_report(self):
        pass
    
    def save_report(self, filepath=None):
        pass
    
    def reset(self):
        pass


# 환경변수에 따른 프로파일러 선택
if os.getenv('ENABLE_PERFORMANCE_PROFILER', 'true').lower() == 'false':
    profiler = DummyProfiler()