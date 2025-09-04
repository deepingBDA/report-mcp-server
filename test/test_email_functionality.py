#!/usr/bin/env python3
"""Email functionality integration tests.

Tests the AWS SES email functionality by sending actual emails.
Requires proper AWS SES credentials and recipients configuration.
"""

import asyncio
import json
import logging
from datetime import datetime

import pytest
import requests

# Setup logging for test output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEmailFunctionality:
    """Test suite for email functionality."""

    BASE_URL = 'http://localhost:8002'

    def test_email_config_status(self):
        """Test email configuration status endpoint."""
        url = f'{self.BASE_URL}/mcp/tools/email-config'
        
        try:
            response = requests.get(url, timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            logger.info(f"Email config status: {data}")
            
            # Check configuration
            assert data['smtp_configured'] is True
            assert data['recipients_count'] > 0
            assert data['sender_email'] is not None
            assert data['smtp_server'] is not None
            
            logger.info("✅ Email configuration is properly set up")
            
        except requests.exceptions.ConnectionError:
            pytest.skip('Server not running at http://localhost:8002')

    def test_send_test_email(self):
        """Test sending a simple test email."""
        url = f'{self.BASE_URL}/mcp/tools/test-email'
        
        payload = {
            'message': '테스트 이메일입니다. 시스템이 정상 작동 중입니다.'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            logger.info(f"Test email response status: {response.status_code}")
            logger.info(f"Test email response: {response.text}")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'recipients' in data
            assert len(data['recipients']) > 0
            
            logger.info(f"✅ Test email sent successfully to {len(data['recipients'])} recipients")
            logger.info(f"Recipients: {data['recipients']}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip('Server not running at http://localhost:8002')

    def test_send_html_email(self):
        """Test sending HTML email via MCP tools."""
        url = f'{self.BASE_URL}/mcp/tools/send-email'
        
        payload = {
            'topic': '📧 HTML 이메일 테스트',
            'content': '''
            <h2>HTML 이메일 테스트</h2>
            <p>이것은 <strong>HTML 형식</strong>의 테스트 이메일입니다.</p>
            <ul>
                <li>✅ AWS SES 연동 확인</li>
                <li>✅ HTML 렌더링 확인</li>
                <li>✅ 한글 인코딩 확인</li>
            </ul>
            <p><em>테스트 시간:</em> {}</p>
            '''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'sender_name': 'Email Test Bot',
            'content_type': 'html'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            logger.info(f"HTML email response status: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            logger.info(f"HTML email response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            assert data['success'] is True
            assert data['content_type'] == 'html'
            assert 'sent_at' in data
            
            logger.info(f"✅ HTML email sent successfully to {len(data['recipients'])} recipients")
            
        except requests.exceptions.ConnectionError:
            pytest.skip('Server not running at http://localhost:8002')

    def test_send_plain_text_email(self):
        """Test sending plain text email."""
        url = f'{self.BASE_URL}/mcp/tools/send-email'
        
        payload = {
            'topic': '📝 Plain Text 이메일 테스트',
            'content': '''Plain Text 이메일 테스트

이것은 일반 텍스트 형식의 테스트 이메일입니다.

특징:
- AWS SES 연동 확인
- 텍스트 형식 확인  
- 한글 인코딩 확인

테스트 시간: {}

감사합니다.
Email Test Bot'''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'sender_name': 'Email Test Bot',
            'content_type': 'text'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            logger.info(f"Plain text email response status: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert data['content_type'] == 'text'
            
            logger.info(f"✅ Plain text email sent successfully to {len(data['recipients'])} recipients")
            
        except requests.exceptions.ConnectionError:
            pytest.skip('Server not running at http://localhost:8002')

    def test_send_daily_report_email(self):
        """Test sending daily report format email."""
        url = f'{self.BASE_URL}/mcp/tools/send-daily-report'
        
        summary = """📊 데일리 리포트 테스트 요약

주요 지표:
- 총 방문자: 1,234명
- 매출: ₩2,345,678
- 전환율: 3.45%

분석 결과:
✅ 전일 대비 방문자 12% 증가
✅ 매출 목표 달성률 108%
⚠️  모바일 전환율 개선 필요

이것은 테스트 리포트입니다."""

        payload = {
            'summary': summary,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'sender_name': 'Daily Report Test Bot'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            logger.info(f"Daily report email response status: {response.status_code}")
            
            assert response.status_code == 200
            
            data = response.json()
            logger.info(f"Daily report email response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            assert data['success'] is True
            assert '데일리 리포트' in data['subject']
            
            logger.info(f"✅ Daily report email sent successfully")
            logger.info(f"Subject: {data['subject']}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip('Server not running at http://localhost:8002')


def run_email_tests():
    """Run all email tests manually."""
    logger.info("=" * 60)
    logger.info("🧪 Email Functionality Tests")
    logger.info("=" * 60)
    
    test = TestEmailFunctionality()
    
    tests = [
        ("Email Configuration Status", test.test_email_config_status),
        ("Send Test Email", test.test_send_test_email),
        ("Send HTML Email", test.test_send_html_email),
        ("Send Plain Text Email", test.test_send_plain_text_email),
        ("Send Daily Report Email", test.test_send_daily_report_email),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            test_func()
            results.append((test_name, "✅ PASSED"))
            logger.info(f"✅ {test_name} - PASSED")
        except Exception as e:
            results.append((test_name, f"❌ FAILED: {e}"))
            logger.error(f"❌ {test_name} - FAILED: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("📋 Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, result in results:
        logger.info(f"{result}")
    
    passed = len([r for r in results if "PASSED" in r[1]])
    total = len(results)
    
    logger.info(f"\n📊 Total: {total} tests, Passed: {passed}, Failed: {total - passed}")
    
    if passed == total:
        logger.info("🎉 All email tests passed!")
    else:
        logger.warning("⚠️  Some email tests failed. Check configuration.")


if __name__ == '__main__':
    # For standalone execution
    run_email_tests()