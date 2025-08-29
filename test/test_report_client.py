#!/usr/bin/env python3
"""
Report MCP Server 클라이언트 테스트
서버 헬스체크, 보고서 생성, 서버 URL로 보고서 열기 테스트
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
    
    def generate_summary_report(self, data_type="visitor", end_date="2025-08-29", stores="all", periods=[1], report_type="daily"):
        """Summary Report 생성 및 서버 URL로 열기"""
        url = f"{self.server_url}/mcp/tools/report-generator/summary-report-html"
        
        payload = {
            "data_type": data_type,
            "end_date": end_date,
            "stores": stores,
            "periods": periods
        }
        
        print(f"📤 {report_type.title()} Summary Report 요청 중...")
        print(f"   URL: {url}")
        print(f"   Data: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, timeout=200)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('result') == 'success':
                print(f"✅ 응답 성공: {result['result']}")
                
                # 서버에 저장된 보고서 URL로 브라우저에서 열기
                period_type = "daily" if periods[0] == 1 else "weekly"
                server_url = f"{self.server_url}/reports/visitor/{period_type}/latest.html"
                
                print(f"🌐 서버 보고서 URL: {server_url}")
                webbrowser.open(server_url)
                print(f"📊 브라우저에서 서버 보고서를 열었습니다!")
                
                # 로컬 백업 파일도 저장
                if result.get('html_content'):
                    filename = f"summary_{data_type}_{period_type}_{end_date}.html"
                    file_path = self.output_dir / filename
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(result['html_content'])
                    
                    print(f"💾 로컬 백업 저장: {file_path}")
                
                return server_url
            else:
                print(f"❌ 응답 실패: {result['result']}")
                return None
                
        except Exception as e:
            print(f"❌ Summary Report 생성 실패: {e}")
            return None
    
    def generate_comparison_report(self, stores=["망우혜원점", "수원영통점"], end_date="2025-08-29", period=7):
        """Comparison Report 생성 및 서버 URL로 열기"""
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
            
            if result.get('result') == 'success':
                print(f"✅ 응답 성공: {result['result']}")
                
                # 서버에 저장된 보고서 URL로 브라우저에서 열기
                server_url = f"{self.server_url}/reports/comparison/latest.html"
                
                print(f"🌐 서버 보고서 URL: {server_url}")
                webbrowser.open(server_url)
                print(f"📊 브라우저에서 서버 보고서를 열었습니다!")
                
                # 로컬 백업 파일도 저장
                if result.get('html_content'):
                    stores_str = "_".join([store.replace(" ", "") for store in stores[:2]])
                    filename = f"comparison_{stores_str}_{end_date}.html"
                    file_path = self.output_dir / filename
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(result['html_content'])
                    
                    print(f"💾 로컬 백업 저장: {file_path}")
                
                return server_url
            else:
                print(f"❌ 응답 실패: {result['result']}")
                return None
                
        except Exception as e:
            print(f"❌ Comparison Report 생성 실패: {e}")
            return None
    
    def test_reports_list(self):
        """보고서 목록 API 테스트"""
        url = f"{self.server_url}/api/reports/list"
        
        print(f"📤 보고서 목록 조회 중...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"✅ 보고서 목록 조회 성공")
            print(f"📊 총 {result.get('total_files', 0)}개의 보고서 파일")
            
            for report_type, files in result.get('reports', {}).items():
                print(f"   - {report_type}: {len(files)}개")
            
            return True
            
        except Exception as e:
            print(f"❌ 보고서 목록 조회 실패: {e}")
            return False
    
    def test_latest_redirect(self, report_type):
        """최신 보고서 리다이렉트 테스트"""
        url = f"{self.server_url}/api/reports/latest/{report_type}"
        
        print(f"📤 최신 {report_type} 보고서 리다이렉트 테스트...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, timeout=30, allow_redirects=False)
            
            if response.status_code == 307:
                redirect_url = response.headers.get('location')
                print(f"✅ 리다이렉트 성공: {redirect_url}")
                
                # 실제 보고서 파일 존재 확인
                final_url = f"{self.server_url}{redirect_url}"
                final_response = requests.get(final_url, timeout=30)
                
                if final_response.status_code == 200:
                    print(f"✅ 보고서 파일 접근 성공")
                    return True
                else:
                    print(f"❌ 보고서 파일 접근 실패: {final_response.status_code}")
                    return False
            else:
                print(f"❌ 리다이렉트 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 리다이렉트 테스트 실패: {e}")
            return False


def main():
    print("🚀 Report MCP Server 종합 테스트 시작")
    print("=" * 60)
    
    client = ReportClient()
    test_date = "2025-08-29"
    results = {}
    
    # 1. 헬스체크
    print("🔍 1. 서버 헬스체크")
    if not client.test_health():
        print("❌ 서버 연결 실패. 종료합니다.")
        return
    results['health'] = True
    
    print("\n" + "=" * 60)
    
    # 2. Daily Summary Report 테스트
    print(f"📊 2. Daily Summary Report 테스트 (기준일: {test_date})")
    daily_url = client.generate_summary_report(
        data_type="visitor",
        end_date=test_date,
        stores="all",
        periods=[1],  # 1일
        report_type="daily"
    )
    results['daily_summary'] = daily_url is not None
    
    print("\n" + "=" * 60)
    
    # 3. Weekly Summary Report 테스트
    print(f"📊 3. Weekly Summary Report 테스트 (기준일: {test_date})")
    weekly_url = client.generate_summary_report(
        data_type="visitor",
        end_date=test_date,
        stores="all",
        periods=[7],  # 7일
        report_type="weekly"
    )
    results['weekly_summary'] = weekly_url is not None
    
    print("\n" + "=" * 60)
    
    # 4. Comparison Report 테스트
    print(f"📊 4. Comparison Report 테스트 (기준일: {test_date})")
    comparison_url = client.generate_comparison_report(
        stores=["망우혜원점", "수원영통점"],
        end_date=test_date,
        period=7
    )
    results['comparison'] = comparison_url is not None
    
    print("\n" + "=" * 60)
    
    # 5. 보고서 목록 API 테스트
    print("📋 5. 보고서 목록 API 테스트")
    results['reports_list'] = client.test_reports_list()
    
    print("\n" + "=" * 60)
    
    # 6. 최신 보고서 리다이렉트 테스트
    print("🔄 6. 최신 보고서 리다이렉트 테스트")
    results['redirect_daily'] = client.test_latest_redirect("visitor_daily")
    results['redirect_weekly'] = client.test_latest_redirect("visitor_weekly")
    results['redirect_comparison'] = client.test_latest_redirect("comparison")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("🎉 테스트 결과 요약")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"   {test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    print(f"\n📊 전체 결과: {success_count}/{total_count} 테스트 통과")
    
    if success_count == total_count:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")
    
    print(f"📁 로컬 백업 파일들은 '{client.output_dir}' 폴더에 저장되었습니다.")


if __name__ == "__main__":
    main()