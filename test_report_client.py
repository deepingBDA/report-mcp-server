#!/usr/bin/env python3
"""
Report MCP Server 클라이언트 테스트
로컬에서 서버를 호출해서 HTML 보고서를 저장하고 브라우저에서 열기
"""

import requests
import json
import os
from datetime import datetime, date, timedelta
import webbrowser
from pathlib import Path


class ReportClient:
    def __init__(self, server_url="http://192.168.49.157:8002"):
        self.server_url = server_url
        self.output_dir = Path("downloaded_reports")
        self.output_dir.mkdir(exist_ok=True)
    
    def test_health(self):
        """헬스체크"""
        try:
            response = requests.get(f"{self.server_url}/health")
            print(f"🔍 Health Check: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health Check 실패: {e}")
            return False
    
    def generate_summary_report(self, data_type="visitor", end_date="2024-04-30", stores="all", periods=[7]):
        """Summary Report 생성 및 저장"""
        url = f"{self.server_url}/mcp/tools/report-generator/summary-report-html"
        
        payload = {
            "data_type": data_type,
            "end_date": end_date,
            "stores": stores,
            "periods": periods
        }
        
        print(f"📤 Summary Report 요청 중...")
        print(f"   URL: {url}")
        print(f"   Data: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, timeout=200)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 응답 성공: {result['result']}")
            
            # DEBUG: 응답 구조 확인
            print(f"🔍 응답 키들: {list(result.keys())}")
            
            # 성능 데이터 출력
            if result.get('performance'):
                perf = result['performance']
                print(f"\n⏱️  성능 측정 결과:")
                print(f"   총 소요 시간: {perf['total_time']}초")
                for measurement in perf['measurements']:
                    print(f"   {measurement['name']:<25} {measurement['duration']:6.2f}초 ({measurement['percentage']:5.1f}%)")
                print()
            else:
                print(f"⚠️  성능 데이터 없음: {result.get('performance')}")
            
            if result.get('html_content'):
                # HTML 파일 저장
                filename = f"summary_report_{data_type}_{end_date}_{'all' if stores == 'all' else 'custom'}.html"
                file_path = self.output_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result['html_content'])
                
                print(f"💾 HTML 파일 저장: {file_path}")
                
                # 브라우저에서 열기
                webbrowser.open(f"file://{file_path.absolute()}")
                print(f"🌐 브라우저에서 열었습니다!")
                
                return file_path
            else:
                print("❌ HTML 내용이 없습니다")
                return None
                
        except Exception as e:
            print(f"❌ Summary Report 생성 실패: {e}")
            return None
    
    def generate_comparison_report(self, stores=["망우혜원점", "수원영통점"], end_date="2024-04-30", period=7):
        """Comparison Report 생성 및 저장"""
        url = f"{self.server_url}/mcp/tools/report-generator/comparison-analysis-html"
        
        payload = {
            "stores": stores,
            "end_date": end_date,
            "period": period,
            "analysis_type": "all"
        }
        
        print(f"📤 Comparison Report 요청 중...")
        print(f"   URL: {url}")
        print(f"   Data: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, timeout=200)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 응답 성공: {result['result']}")
            
            if result.get('html_content'):
                # HTML 파일 저장
                stores_str = "_".join(stores[:2])  # 처음 2개 매장만
                filename = f"comparison_report_{stores_str}_{end_date}.html"
                file_path = self.output_dir / filename
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(result['html_content'])
                
                print(f"💾 HTML 파일 저장: {file_path}")
                
                # 브라우저에서 열기
                webbrowser.open(f"file://{file_path.absolute()}")
                print(f"🌐 브라우저에서 열었습니다!")
                
                return file_path
            else:
                print("❌ HTML 내용이 없습니다")
                return None
                
        except Exception as e:
            print(f"❌ Comparison Report 생성 실패: {e}")
            return None


def main():
    print("🚀 Report MCP Server 클라이언트 테스트 시작")
    print("=" * 60)
    
    client = ReportClient()
    
    # 1. 헬스체크
    if not client.test_health():
        print("❌ 서버 연결 실패. 종료합니다.")
        return
    
    print("\n" + "=" * 60)
    
    # 2. Summary Report 테스트 (2025-04-30 기준, 모든 매장) - 1일 모드
    test_date = "2025-04-30"
    print(f"📊 Visitor Summary Report 생성 테스트 (All stores - 기준일: {test_date}) - 1일 모드")
    summary_file = client.generate_summary_report(
        data_type="visitor",
        end_date=test_date,
        stores="all",
        periods=[1]  # 1일 모드로 테스트
    )
    
    print("\n" + "=" * 60)
    print("🎉 테스트 완료!")
    
    if summary_file:
        print(f"📄 Summary Report: {summary_file}")
    else:
        print("❌ Summary Report 생성 실패")
    
    print(f"📁 모든 파일은 '{client.output_dir}' 폴더에 저장되었습니다.")


if __name__ == "__main__":
    main()