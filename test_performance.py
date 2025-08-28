#!/usr/bin/env python3
"""
성능 측정 테스트 - 로컬에서 직접 실행
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from report_generators.summary_report import SummaryReportGenerator


def test_local_performance():
    print("🚀 로컬 성능 측정 테스트 시작")
    print("=" * 60)
    
    try:
        generator = SummaryReportGenerator()
        
        # 작은 규모 테스트 (2개 매장, 7일)
        print("📊 Summary Report 테스트 (2개 매장, 7일)")
        result = generator.run(
            data_type="visitor",
            end_date="2025-04-30",
            stores=["금천프라임점", "마천파크점"],
            periods=7
        )
        print("✅ 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_local_performance()