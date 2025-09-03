# 사용법 가이드

Report MCP Server의 일상적인 사용법과 운영 가이드입니다.

## 🎯 핵심 기능: 원클릭 데일리 리포트

가장 중요한 기능은 **하나의 API 호출로 전체 프로세스를 실행**하는 것입니다.

```bash
# 어제 데이터로 자동 리포트 생성 + GPT 요약 + 이메일 전송
curl -X POST "http://localhost:8002/mcp/tools/daily-report-email"

# 특정 날짜로 실행
curl -X POST "http://localhost:8002/mcp/tools/daily-report-email?report_date=2025-09-02"
```

### 📧 수신되는 이메일 내용

데일리 리포트 이메일에는 다음 내용이 포함됩니다:

1. **AI 요약 섹션**: GPT-4o-mini가 생성한 핵심 인사이트
2. **상세 HTML 리포트**: 차트와 그래프가 포함된 전체 분석
3. **매장별 성과 비교**: 각 매장의 성과 지표
4. **개선 권장사항**: AI가 제안하는 액션 아이템

### 📊 리포트 내용 예시

```
📊 편의점 데일리 리포트

🔍 요약 분석
어제(2025-09-02) 전체 매장 방문자 수는 1,234명으로 전주 대비 5.2% 증가했습니다.
- 🏆 최고 성과: 강남점 (234명, +12.3%)
- ⚠️ 주의 필요: 홍대점 (89명, -8.1%)
- 💡 권장사항: 오후 2-4시 시간대 마케팅 강화 필요

📈 상세 리포트
[HTML 차트 및 상세 분석 내용]
```

## ⏰ 자동 스케줄러 관리

### 스케줄러 상태 확인
```bash
# 현재 스케줄러 상태 및 다음 실행 시간
curl "http://localhost:8002/mcp/tools/scheduler/status"
```

**응답 예시:**
```json
{
  "status": {
    "running": true,
    "next_run_time": "2025-09-04T08:00:00+09:00",
    "trigger": "cron[hour='8', minute='0']"
  }
}
```

### 수동 실행 테스트
```bash
# 스케줄러가 실행할 워크플로우를 수동으로 테스트
curl -X POST "http://localhost:8002/mcp/tools/scheduler/test-daily-report"

# 테스트 이메일 전송 (연결 확인용)
curl -X POST "http://localhost:8002/mcp/tools/scheduler/send-test-email"
```

### 실행 시간 변경

#### 방법 1: 환경 변수 설정
```bash
# .env 파일에 추가
DAILY_REPORT_TIME=09:30  # 오전 9시 30분으로 변경

# 컨테이너 재시작
docker-compose restart
```

#### 방법 2: 설정 파일 수정
```python
# config/scheduler_config.py 파일 수정
"daily_report_time": "07:00"  # 오전 7시로 변경
```

## 🧪 테스트 및 검증

### 샘플 데이터로 테스트
```bash
# 실제 이메일 전송 없이 워크플로우만 테스트
curl -X POST "http://localhost:8002/mcp/tools/daily-report-test?use_sample_data=true"
```

### 단계별 테스트

#### 1. 서비스 상태 확인
```bash
# 메인 서버 상태
curl "http://localhost:8002/health"

# 데일리 리포트 서비스 상태
curl "http://localhost:8002/mcp/tools/daily-report-status"

# Plus Agent (이메일 서비스) 상태  
curl "http://localhost:32770/health"
```

#### 2. 데이터베이스 연결 테스트
```bash
# 사용 가능한 매장 목록 (ClickHouse 연결 확인)
curl "http://localhost:8002/mcp/tools/available-sites"
```

#### 3. 리포트 생성만 테스트
```bash
curl -X POST "http://localhost:8002/mcp/tools/report-generator/summary-report-html" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "visitor",
    "end_date": "2025-09-02",
    "stores": "all",
    "periods": [1]
  }'
```

## 📈 개별 기능 사용법

### 리포트 생성

#### 요약 리포트
```bash
curl -X POST "http://localhost:8002/mcp/tools/report-generator/summary-report-html" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "visitor",
    "end_date": "2025-09-02",
    "stores": ["매장1", "매장2"],
    "periods": [1, 7, 30]
  }'
```

#### 비교 분석 리포트
```bash
curl -X POST "http://localhost:8002/mcp/tools/report-generator/comparison-analysis-html" \
  -H "Content-Type: application/json" \
  -d '{
    "stores": ["강남점", "홍대점"],
    "end_date": "2025-09-02", 
    "period": 7,
    "analysis_type": "all"
  }'
```

### GPT 요약

```bash
curl -X POST "http://localhost:8002/mcp/tools/report-summarizer/summarize-html-report" \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<html>리포트 내용...</html>",
    "report_type": "daily_report",
    "max_tokens": 500
  }'
```

### 생성된 리포트 조회

```bash
# 최근 리포트 목록
curl "http://localhost:8002/mcp/tools/report-viewer/recent-reports?limit=10"

# 모든 리포트 목록
curl "http://localhost:8002/mcp/tools/report-viewer/list-reports"
```

## 🎛️ 설정 커스터마이징

### 매장 필터링
```bash
# 특정 매장만 포함
export DAILY_REPORT_STORES="강남점,홍대점,신촌점"

# 모든 매장 포함 (기본값)
export DAILY_REPORT_STORES=all
```

### GPT 요약 설정
```python
# config/scheduler_config.py
{
    "max_tokens": 800,  # 더 긴 요약 원할 때
    "sender_name": "AI Report Bot",  # 발신자명 변경
}
```

### 이메일 설정
```bash
# HTML 첨부 여부
export EMAIL_INCLUDE_HTML=true  # 상세 리포트 포함
export EMAIL_INCLUDE_HTML=false  # 요약만 포함
```

## 📊 모니터링 및 운영

### 성능 모니터링
```bash
# API 응답 시간 측정
time curl -X POST "http://localhost:8002/mcp/tools/daily-report-email"

# 메모리 사용량
docker stats report-mcp-server --no-stream

# 디스크 사용량
du -sh ./data/reports/
```

### 로그 모니터링
```bash
# 실시간 로그 확인
docker logs -f report-mcp-server

# 스케줄러 실행 로그만
docker logs report-mcp-server | grep -i "daily report"

# 에러 로그만
docker logs report-mcp-server | grep -i error

# 특정 날짜 로그
docker logs report-mcp-server | grep "2025-09-02"
```

### 주요 메트릭 확인
```bash
# 최근 실행 결과
curl "http://localhost:8002/mcp/tools/scheduler/status" | jq '.status.jobs[0].next_run_time'

# 서비스 상태 요약
curl "http://localhost:8002/mcp/tools/daily-report-status" | jq '.status'
```

## 🔧 문제 해결

### 일반적인 문제들

#### 이메일이 도착하지 않음
```bash
# 1. Plus Agent 연결 확인
curl "http://localhost:32770/health"

# 2. 테스트 이메일 전송
curl -X POST "http://localhost:8002/mcp/tools/scheduler/send-test-email"

# 3. 네트워크 연결 확인  
docker exec -it report-mcp-server curl http://plus-agent-llm-server:8000/health
```

#### 스케줄러가 실행되지 않음
```bash
# 1. 스케줄러 상태 확인
curl "http://localhost:8002/mcp/tools/scheduler/status"

# 2. 시간대 확인
docker exec -it report-mcp-server date

# 3. 수동 테스트
curl -X POST "http://localhost:8002/mcp/tools/scheduler/test-daily-report"
```

#### 리포트 생성 실패
```bash
# 1. 데이터베이스 연결 확인
curl "http://localhost:8002/mcp/tools/available-sites"

# 2. 샘플 데이터로 테스트
curl -X POST "http://localhost:8002/mcp/tools/daily-report-test?use_sample_data=true"

# 3. 로그에서 에러 확인
docker logs report-mcp-server | tail -50
```

### 디버깅 팁

#### 로그 레벨 변경
```bash
# .env 파일에서 DEBUG 모드 활성화
LOG_LEVEL=DEBUG

# 컨테이너 재시작
docker-compose restart
```

#### 상세 에러 정보 확인
```bash
# API 응답에서 에러 정보 확인
curl -X POST "http://localhost:8002/mcp/tools/daily-report-email" | jq '.error_details'

# 실행 과정별 로그 확인
docker logs report-mcp-server | grep -E "(Step [1-3]|ERROR|FAILED)"
```

## 🚀 고급 사용법

### Python 스크립트로 자동화
```python
import httpx
import asyncio
from datetime import datetime, timedelta

async def send_daily_report(report_date=None):
    if not report_date:
        report_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "http://localhost:8002/mcp/tools/daily-report-email",
            params={"report_date": report_date}
        )
        return response.json()

# 실행
result = asyncio.run(send_daily_report("2025-09-02"))
print(f"Status: {result['result']}")
```

### 배치 처리 (여러 날짜)
```bash
#!/bin/bash
# 최근 7일간의 리포트를 일괄 생성

for i in {1..7}; do
  date=$(date -d "$i days ago" +%Y-%m-%d)
  echo "Generating report for $date"
  curl -X POST "http://localhost:8002/mcp/tools/daily-report-email?report_date=$date"
  sleep 30  # API 부하 방지
done
```

### 헬스체크 자동화
```bash
#!/bin/bash
# healthcheck.sh - crontab으로 정기 실행

STATUS=$(curl -s "http://localhost:8002/health" | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
  echo "❌ Report Server is down!" | mail -s "Alert: Service Down" admin@company.com
else
  echo "✅ All services running normally"
fi
```

## 📱 웹 인터페이스 활용

### Swagger UI
- **URL**: http://localhost:8002/docs
- **기능**: 모든 API를 웹에서 직접 테스트
- **사용법**: 브라우저에서 접속하여 "Try it out" 버튼으로 API 실행

### ReDoc
- **URL**: http://localhost:8002/redoc  
- **기능**: 읽기 좋은 API 문서
- **사용법**: API 명세 확인 및 예시 코드 참고

### 리포트 뷰어
- **URL**: http://localhost:8002/reports/
- **기능**: 생성된 HTML 리포트 파일 목록
- **사용법**: 브라우저에서 과거 리포트 확인

---

더 자세한 API 명세는 [API.md](API.md)를, 설치 문제는 [SETUP.md](SETUP.md)를 참조하세요.