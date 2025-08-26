#!/usr/bin/env python3
"""
MCP Email Sender Server
HTML 리포트를 이메일로 발송하는 MCP 서버
"""

import asyncio
import json
import os
import smtplib
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl
import mcp.types as types

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_sender_server")

server = Server("email-sender")

class EmailSender:
    def __init__(self):
        self.config_file = Path(__file__).parent / "config" / "email_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        if not self.config_file.exists():
            self.create_default_config()
            
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_default_config(self):
        """기본 설정 파일 생성"""
        self.config_file.parent.mkdir(exist_ok=True)
        
        default_config = {
            "smtp": {
                "host": "smtp-mail.outlook.com",
                "port": 587,
                "user": "your-email@outlook.com",
                "password": "your-app-password"
            },
            "email": {
                "to": ["recipient@company.com"],
                "cc": [],
                "subject_prefix": "[일일 리포트]"
            },
            "report": {
                "default_html_path": "/app/mcp_tools/html_report/daily/latest.html"
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    def extract_summary_from_html(self, html_content):
        """HTML에서 요약 정보 추출"""
        if not BeautifulSoup:
            return {
                'title': "일일 리포트",
                'items': []
            }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 제목 추출
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "일일 리포트"
            
            # 주요 헤더 찾기
            headers = soup.find_all(['h1', 'h2', 'h3'])[:5]
            summary_items = [header.get_text().strip() for header in headers if header.get_text().strip()]
            
            return {
                'title': title_text,
                'items': summary_items
            }
        except Exception as e:
            logger.warning(f"HTML 요약 추출 실패: {e}")
            return {
                'title': "일일 리포트",
                'items': []
            }
    
    def create_email_body(self, summary_info):
        """이메일 본문 생성"""
        today = datetime.now().strftime('%Y년 %m월 %d일')
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Malgun Gothic', Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ margin: 20px 0; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; }}
                ul {{ margin: 10px 0; padding-left: 20px; }}
                li {{ margin: 5px 0; }}
                .attachment-note {{ background-color: #e7f3ff; padding: 10px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 {summary_info['title']} - {today}</h2>
            </div>
            
            <div class="summary">
                <h3>주요 내용 요약</h3>
        """
        
        if summary_info['items']:
            html_body += "<ul>\n"
            for item in summary_info['items']:
                html_body += f"<li>{item}</li>\n"
            html_body += "</ul>\n"
        else:
            html_body += "<p>리포트가 생성되었습니다.</p>\n"
        
        html_body += f"""
            </div>
            
            <div class="attachment-note">
                <strong>📎 상세 내용은 첨부된 HTML 파일을 확인해주세요.</strong>
            </div>
            
            <div class="footer">
                발송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                MCP Email Sender Tool
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def send_email(self, html_file_path=None, to_emails=None, subject=None):
        """이메일 발송"""
        # HTML 파일 경로 결정
        if not html_file_path:
            html_file_path = self.config['report']['default_html_path']
        
        if not os.path.exists(html_file_path):
            raise FileNotFoundError(f"HTML 파일을 찾을 수 없습니다: {html_file_path}")
        
        # HTML 파일 읽기
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 요약 정보 추출
        summary_info = self.extract_summary_from_html(html_content)
        
        # 수신자 설정
        recipients = to_emails if to_emails else self.config['email']['to']
        if isinstance(recipients, str):
            recipients = [recipients]
        
        # 이메일 객체 생성
        msg = MIMEMultipart()
        today = datetime.now().strftime('%Y-%m-%d')
        
        if subject:
            msg['Subject'] = subject
        else:
            subject_prefix = self.config['email'].get('subject_prefix', '[리포트]')
            msg['Subject'] = f"{subject_prefix} {summary_info['title']} - {today}"
        
        msg['From'] = self.config['smtp']['user']
        msg['To'] = ', '.join(recipients)
        
        if self.config['email'].get('cc'):
            msg['Cc'] = ', '.join(self.config['email']['cc'])
        
        # 이메일 본문 생성
        html_body = self.create_email_body(summary_info)
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # HTML 파일 첨부
        with open(html_file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="daily_report_{today}.html"'
        )
        msg.attach(part)
        
        # 이메일 발송
        server_smtp = smtplib.SMTP(self.config['smtp']['host'], self.config['smtp']['port'])
        server_smtp.starttls()
        server_smtp.login(self.config['smtp']['user'], self.config['smtp']['password'])
        
        all_recipients = recipients + self.config['email'].get('cc', [])
        server_smtp.send_message(msg, to_addrs=all_recipients)
        server_smtp.quit()
        
        return {
            "success": True,
            "recipients": all_recipients,
            "subject": msg['Subject'],
            "file": html_file_path,
            "timestamp": datetime.now().isoformat()
        }

# MCP 서버 인스턴스 생성
email_sender = EmailSender()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """사용 가능한 도구 목록 반환"""
    return [
        types.Tool(
            name="send_html_report_email",
            description="HTML 리포트 파일을 이메일로 발송합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "html_file_path": {
                        "type": "string",
                        "description": "발송할 HTML 파일 경로 (선택사항, 기본값: 설정 파일의 경로 사용)"
                    },
                    "to_emails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "수신자 이메일 목록 (선택사항, 기본값: 설정 파일의 수신자 사용)"
                    },
                    "subject": {
                        "type": "string", 
                        "description": "이메일 제목 (선택사항, 기본값: 자동 생성)"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_email_config",
            description="현재 이메일 설정을 확인합니다",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """도구 호출 처리"""
    try:
        if name == "send_html_report_email":
            html_file_path = arguments.get("html_file_path")
            to_emails = arguments.get("to_emails")
            subject = arguments.get("subject")
            
            result = email_sender.send_email(html_file_path, to_emails, subject)
            
            return [types.TextContent(
                type="text",
                text=f"""✅ 이메일 발송 완료!

📧 발송 정보:
- 제목: {result['subject']}
- 수신자: {', '.join(result['recipients'])}
- 파일: {result['file']}
- 발송 시간: {result['timestamp']}
"""
            )]
            
        elif name == "get_email_config":
            config = email_sender.config.copy()
            # 비밀번호 마스킹
            if 'smtp' in config and 'password' in config['smtp']:
                config['smtp']['password'] = '*' * 8
            
            return [types.TextContent(
                type="text", 
                text=f"""📋 현재 이메일 설정:

SMTP 서버: {config['smtp']['host']}:{config['smtp']['port']}
발송자: {config['smtp']['user']}
기본 수신자: {', '.join(config['email']['to'])}
참조: {', '.join(config['email'].get('cc', []))}
제목 접두사: {config['email'].get('subject_prefix', '')}
기본 HTML 경로: {config['report']['default_html_path']}

설정 파일: {email_sender.config_file}
"""
            )]
            
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ 알 수 없는 도구: {name}"
            )]
            
    except Exception as e:
        logger.error(f"도구 실행 오류: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ 오류 발생: {str(e)}"
        )]

async def main():
    # stdin/stdout을 통한 MCP 서버 실행
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="email-sender",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())