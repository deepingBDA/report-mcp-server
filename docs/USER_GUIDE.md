# Report MCP Server - 사용 가이드

## 📖 목차

1. [시스템 개요](#시스템-개요)
2. [설치 및 초기 설정](#설치-및-초기-설정)
3. [데일리 리포트 자동화](#데일리-리포트-자동화)
4. [스케줄러 관리](#스케줄러-관리)
5. [수동 리포트 생성](#수동-리포트-생성)
6. [문제 해결](#문제-해결)
7. [고급 설정](#고급-설정)

## 시스템 개요

Report MCP Server는 편의점 방문자 데이터를 분석하여 자동으로 리포트를 생성하고 이메일로 전송하는 시스템입니다.

### 🔄 워크플로우
```
데이터베이스 조회 → 리포트 생성 → GPT 요약 → 이메일 전송
```

### 🏗️ 아키텍처
- **Report MCP Server** (Port 8002): 메인 리포트 생성 서버
- **Plus Agent LLM Server** (Port 32770): 이메일 전송 서비스
- **ClickHouse Database**: 방문자 데이터 저장소

## 설치 및 초기 설정

### 1. 필수 요구사항
- Docker & Docker Compose
- OpenAI API 키
- Plus Agent LLM Server (AWS SES 설정 완료)

### 2. Plus Agent 서버 먼저 실행
```bash
cd /path/to/plus-agent-llm-server
docker-compose up -d
```

### 3. Report Server 실행
```bash
cd /path/to/report-mcp-server
docker-compose up -d
```

### 4. 초기 설정 확인
```bash
# 서버 상태 확인
curl http://localhost:8002/health

# 데일리 리포트 서비스 상태 확인
curl http://localhost:8002/mcp/tools/daily-report-status

# 스케줄러 상태 확인
curl http://localhost:8002/mcp/tools/scheduler/status
```

## 데일리 리포트 자동화

### 🎯 핵심 기능: 원클릭 데일리 리포트

이 시스템의 가장 중요한 기능은 **하나의 API 호출로 전체 워크플로우를 실행**하는 것입니다.

```bash
# 어제 데이터로 리포트 생성 + GPT 요약 + 이메일 전송
curl -X POST "http://localhost:8002/mcp/tools/daily-report-email"

# 특정 날짜로 실행
curl -X POST "http://localhost:8002/mcp/tools/daily-report-email?report_date=2025-09-02"
```

### 📧 이메일 리포트 내용
수신되는 이메일에는 다음 내용이 포함됩니다:

1. **AI 요약**: GPT-4o-mini가 생성한 핵심 인사이트
2. **상세 HTML 리포트**: 차트와 그래프가 포함된 전체 분석
3. **매장별 성과**: 각 매장의 성과 및 비교 분석
4. **액션 아이템**: AI가 권장하는 개선 사항

### 🧪 테스트 모드
실제 이메일 전송 없이 워크플로우 테스트:

```bash
curl -X POST "http://localhost:8002/mcp/tools/daily-report-test?use_sample_data=true"
```

## 스케줄러 관리

### ⏰ 자동 실행 설정

스케줄러는 매일 지정된 시간에 자동으로 데일리 리포트를 생성합니다.

#### 현재 설정 확인
```bash
curl http://localhost:8002/mcp/tools/scheduler/status
```

**응답 예시:**
```json
{
  "result": "success",
  "status": {
    "running": true,
    "timezone": "Asia/Seoul",
    "jobs": [
      {
        "id": "daily_report",
        "name": "Daily Report Generation and Email",
        "next_run_time": "2025-09-04T08:00:00+00:00",
        "trigger": "cron[hour='8', minute='0']"
      }
    ]
  }
}
```

#### 다음 실행 시간 확인
```bash
curl http://localhost:8002/mcp/tools/scheduler/next-execution
```

#### 수동 테스트 실행
```bash
# 스케줄러가 실제로 실행할 워크플로우를 수동으로 테스트
curl -X POST http://localhost:8002/mcp/tools/scheduler/test-daily-report
```

### 🔧 실행 시간 변경

실행 시간을 변경하려면 `config/scheduler_config.py` 파일을 수정:

```python
"daily_report_time": os.getenv("DAILY_REPORT_TIME", "08:00"),  # 원하는 시간으로 변경
```

또는 환경 변수로 설정:
```bash
export DAILY_REPORT_TIME="15:30"  # 오후 3:30
```

## 수동 리포트 생성

### 📊 개별 컴포넌트 실행

필요시 워크플로우의 각 단계를 개별적으로 실행할 수 있습니다.

#### 1. HTML 리포트만 생성
```bash
curl -X POST http://localhost:8002/mcp/tools/report-generator/summary-report-html \\
  -H "Content-Type: application/json" \\
  -d '{
    "data_type": "visitor",
    "end_date": "2025-09-02",
    "stores": "all",
    "periods": [1, 7]
  }'
```

#### 2. GPT 요약만 생성
```bash
curl -X POST http://localhost:8002/mcp/tools/report-summarizer/summarize-html-report \\
  -H "Content-Type: application/json" \\
  -d '{
    "html_content": "<html>리포트 내용</html>",
    "report_type": "daily_report",
    "max_tokens": 500
  }'
```

#### 3. 비교 분석 리포트
```bash
curl -X POST http://localhost:8002/mcp/tools/report-generator/comparison-analysis-html \\
  -H "Content-Type: application/json" \\
  -d '{
    "stores": ["매장1", "매장2"],
    "end_date": "2025-09-02",
    "period": 7
  }'
```

## 문제 해결

### 🚨 일반적인 문제들

#### 1. 이메일이 전송되지 않음
```bash
# 이메일 서비스 연결 테스트
curl -X POST http://localhost:8002/mcp/tools/scheduler/send-test-email

# Plus Agent 서버 상태 확인
curl http://localhost:32770/health

# 네트워크 연결 확인
docker exec -it report-mcp-server curl http://plus-agent-llm-server:8000/health
```

#### 2. 스케줄러가 실행되지 않음
```bash
# 스케줄러 상태 확인
curl http://localhost:8002/mcp/tools/scheduler/status

# 로그 확인
docker logs report-mcp-server
```

#### 3. 데이터베이스 연결 실패
```bash
# 매장 목록 조회로 DB 연결 테스트
curl http://localhost:8002/mcp/tools/available-sites

# ClickHouse 연결 정보 확인
docker logs report-mcp-server | grep -i clickhouse
```

### 📋 체크리스트

데일리 리포트 시스템이 정상 작동하는지 확인하는 체크리스트:

- [ ] Report Server 실행 중 (`curl http://localhost:8002/health`)
- [ ] Plus Agent Server 실행 중 (`curl http://localhost:32770/health`)  
- [ ] 두 컨테이너 간 네트워크 연결 정상
- [ ] 스케줄러 활성화 및 다음 실행 시간 설정됨
- [ ] 테스트 이메일 전송 성공
- [ ] 샘플 데이터로 워크플로우 테스트 성공

## 고급 설정

### 🔧 환경 변수 설정

#### 스케줄러 설정
```bash
SCHEDULER_ENABLED=true
DAILY_REPORT_TIME=08:00
DAILY_REPORT_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Seoul
```

#### 데일리 리포트 설정
```bash
DAILY_REPORT_STORES=all
DAILY_REPORT_DATA_TYPE=visitor
DAILY_REPORT_MAX_TOKENS=500
DAILY_REPORT_SENDER_NAME="Daily Report Bot"
```

#### 이메일 설정
```bash
PLUS_AGENT_URL=http://plus-agent-llm-server:8000
```

### 🐳 Docker 네트워크 최적화

두 서비스가 다른 Docker 네트워크에 있는 경우:

```bash
# 네트워크 확인
docker network ls

# Report Server를 Plus Agent 네트워크에 연결
docker network connect plus-agent-llm-server_plus-agent-network report-mcp-server
```

### 📊 모니터링 및 로깅

#### 실시간 로그 모니터링
```bash
# Report Server 로그
docker logs -f report-mcp-server

# Plus Agent 로그  
docker logs -f plus-agent-llm-server
```

#### API 성능 모니터링
```bash
# 응답 시간 측정
time curl -X POST "http://localhost:8002/mcp/tools/daily-report-email"
```

### 🔒 보안 설정

#### API 키 관리
- OpenAI API 키는 환경 변수로만 설정
- AWS SES 자격 증명은 Plus Agent에서 관리
- ClickHouse 인증 정보 보안 유지

#### 네트워크 보안
- 내부 서비스는 Docker 네트워크로 통신
- 외부 포트는 필요한 것만 노출 (8002, 32770)

---

## 🎯 요약

1. **시작하기**: Plus Agent → Report Server 순으로 실행
2. **테스트**: 샘플 데이터로 워크플로우 검증
3. **자동화**: 스케줄러 설정으로 매일 자동 실행
4. **모니터링**: 로그와 API 상태 정기 확인

**핵심 API**: `POST /mcp/tools/daily-report-email` - 원클릭으로 전체 워크플로우 실행

더 자세한 정보는 [API 스펙 문서](API_SPECS.md)를 참조하세요.