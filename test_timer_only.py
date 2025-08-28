#!/usr/bin/env python3
"""
타이머 기능만 테스트
"""

import time
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.simple_timer import timer, print_timer_summary, reset_timers


def test_timer():
    print("🚀 타이머 기능 테스트")
    
    reset_timers()
    
    with timer("첫번째_작업"):
        print("첫번째 작업 실행 중...")
        time.sleep(1.0)
    
    with timer("두번째_작업"):
        print("두번째 작업 실행 중...")
        time.sleep(0.5)
    
    with timer("세번째_작업"):
        print("세번째 작업 실행 중...")
        time.sleep(1.5)
    
    print("\n✅ 모든 작업 완료!")
    print_timer_summary()


if __name__ == "__main__":
    test_timer()