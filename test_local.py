#!/usr/bin/env python3
"""
로컬 환경에서 새로운 모듈화된 Summary Report 테스트

사용법:
1. .env.local 파일에서 SSH 및 DB 정보 설정
2. python test_local.py
"""

import os
import sys
from pathlib import Path
from datetime import date, timedelta

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 로컬 환경변수 로드
from dotenv import load_dotenv
load_dotenv(".env.local")

print("🔧 환경변수 로딩 완료")
print(f"SSH_HOST: {os.getenv('SSH_HOST')}")
print(f"CONFIG_DB_HOST: {os.getenv('CONFIG_DB_HOST')}")

# 모듈 import
try:
    from report_generators.summary import SummaryReportBuilder
    print("✅ SummaryReportBuilder import 성공")
except Exception as e:
    print(f"❌ SummaryReportBuilder import 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from libs.database import get_all_sites
    print("✅ get_all_sites import 성공")
except Exception as e:
    print(f"❌ get_all_sites import 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def test_summary_report():
    """Summary Report 테스트"""
    print("\n🧪 Summary Report 모듈 테스트 시작")
    
    # 1. Builder 생성
    print("📊 SummaryReportBuilder 생성 중...")
    try:
        builder = SummaryReportBuilder("visitor")
        print("✅ SummaryReportBuilder 생성 성공")
    except Exception as e:
        print(f"❌ SummaryReportBuilder 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 매장 목록 확인
    print("🏪 매장 목록 확인 중...")
    try:
        sites = get_all_sites()
        print(f"📋 전체 매장 개수: {len(sites) if sites else 0}")
        
        if not sites:
            print("❌ 매장 목록이 비어있습니다. DB 연결을 확인하세요.")
            return
        
        # sites가 문자열 리스트인지 딕셔너리 리스트인지 확인
        if sites and isinstance(sites[0], str):
            # 문자열 리스트인 경우
            store_names = sites  # 모든 매장 사용
            print(f"✅ 테스트할 매장들: {store_names}")
        elif sites and isinstance(sites[0], dict):
            # 딕셔너리 리스트인 경우
            store_names = [site["name"] for site in sites if site.get("enabled", True)]  # 모든 매장 사용
            print(f"✅ 테스트할 매장들: {store_names}")
        else:
            print(f"❓ sites 데이터 형식: {type(sites[0]) if sites else 'empty'}")
            store_names = sites if sites else []  # 모든 매장 사용
            print(f"✅ 테스트할 매장들: {store_names}")
        
    except Exception as e:
        print(f"❌ 매장 목록 조회 실패: {e}")
        print("💡 SSH 터널링 설정을 확인하세요:")
        print("   - .env.local에서 SSH_HOST, SSH_USERNAME, SSH_PASSWORD 확인")
        print("   - 네트워크 연결 및 방화벽 설정 확인")
        import traceback
        traceback.print_exc()
        return
    
    # 3. 테스트 날짜 설정
    test_date = "2025-04-30"  # 2025년 4월 30일로 테스트
    print(f"📅 테스트 날짜: {test_date}")
    
    # 출력 디렉토리 생성
    output_dir = Path("./local_test_output")
    output_dir.mkdir(exist_ok=True)
    print(f"📁 출력 디렉토리: {output_dir.absolute()}")
    
    # 4. 1일 모드 테스트
    print("\n🔬 1일 모드 테스트...")
    try:
        html_1day = builder.build_report(test_date, store_names, [1])
        
        output_file_1day = output_dir / f"summary_1day_{test_date}.html"
        with open(output_file_1day, 'w', encoding='utf-8') as f:
            f.write(html_1day)
        
        print(f"✅ 1일 모드 리포트 생성 성공: {output_file_1day}")
        print(f"   파일 크기: {len(html_1day):,} bytes")
        
    except Exception as e:
        print(f"❌ 1일 모드 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 7일 모드 테스트
    print("\n🔬 7일 모드 테스트...")
    try:
        html_7day = builder.build_report(test_date, store_names, [7])
        
        output_file_7day = output_dir / f"summary_7day_{test_date}.html"
        with open(output_file_7day, 'w', encoding='utf-8') as f:
            f.write(html_7day)
        
        print(f"✅ 7일 모드 리포트 생성 성공: {output_file_7day}")
        print(f"   파일 크기: {len(html_7day):,} bytes")
        
    except Exception as e:
        print(f"❌ 7일 모드 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 테스트 완료
    print("\n📊 테스트 완료!")
    print(f"📁 생성된 파일들: {output_dir.absolute()}")
    print("🌐 브라우저에서 HTML 파일을 열어서 확인하세요.")


def check_environment():
    """환경 설정 확인"""
    print("🔧 환경 설정 확인...")
    
    required_vars = [
        "SSH_HOST", "SSH_USERNAME", 
        "CONFIG_DB_HOST", "CONFIG_DB_PORT", "CONFIG_DB_NAME",
        "CLICKHOUSE_USER", "CLICKHOUSE_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # 비밀번호는 일부만 표시
            if "PASSWORD" in var:
                display_value = value[:3] + "*" * (len(value) - 3) if len(value) > 3 else "*" * len(value)
            else:
                display_value = value
            print(f"  {var}: {display_value}")
    
    if missing_vars:
        print(f"❌ 누락된 환경변수: {missing_vars}")
        print("💡 .env.local 파일을 확인하고 필요한 값들을 설정하세요.")
        return False
    
    print("✅ 모든 환경변수가 설정되어 있습니다.")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🏠 로컬 Summary Report 테스트")
    print("=" * 60)
    
    # 환경 확인
    if not check_environment():
        print("\n❌ 환경 설정 문제로 테스트를 중단합니다.")
        sys.exit(1)
    
    # 테스트 실행
    test_summary_report()
    
    print("\n" + "=" * 60)
    print("🎯 테스트 완료!")
    print("=" * 60)