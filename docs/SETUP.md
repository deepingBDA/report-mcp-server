# 설치 및 설정 가이드

Report MCP Server의 설치와 초기 설정에 대한 완전한 가이드입니다.

## 📋 시스템 요구사항

### 최소 요구사항
- **OS**: Linux (Ubuntu 20.04+) 또는 macOS
- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **메모리**: 4GB 이상
- **디스크**: 10GB 여유 공간

### 외부 서비스 의존성
- **OpenAI API**: GPT-4o-mini 모델 사용
- **ClickHouse**: 방문자 데이터베이스
- **Plus Agent LLM Server**: AWS SES 이메일 전송

## 🚀 빠른 설치

### 1단계: Plus Agent LLM Server 먼저 설치

```bash
# Plus Agent 서버 실행 (AWS SES 설정 완료된 상태)
cd /path/to/plus-agent-llm-server
docker-compose up -d

# 서비스 확인
curl http://localhost:32770/health
```

### 2단계: Report MCP Server 설치

```bash
# 리포지토리 클론
git clone https://github.com/deepingBDA/report-mcp-server.git
cd report-mcp-server

# 환경 설정 파일 생성
cp .env.example .env
```

### 3단계: 환경 변수 설정

`.env` 파일을 편집하여 다음 정보를 입력:

```bash
# OpenAI API 설정
OPENAI_API_KEY=sk-proj-your-api-key-here

# ClickHouse 데이터베이스 설정
CONFIG_DB_HOST=your-clickhouse-host
CONFIG_DB_PORT=8123
CONFIG_DB_NAME=cu_base
CLICKHOUSE_USER=your-username
CLICKHOUSE_PASSWORD=your-password

# 서버 설정
HOST=0.0.0.0
PORT=8002
DEBUG=false
LOG_LEVEL=INFO
```

### 4단계: Docker 실행

```bash
# 컨테이너 빌드 및 실행
docker-compose up -d

# 서비스 상태 확인
curl http://localhost:8002/health
```

## 🔧 상세 설정

### Docker 네트워크 연결

Plus Agent와 Report Server 간 통신을 위한 네트워크 설정:

```bash
# 네트워크 확인
docker network ls

# 자동으로 연결되지 않은 경우 수동 연결
docker network connect plus-agent-llm-server_plus-agent-network report-mcp-server
```

### 스케줄러 설정

`config/scheduler_config.py`에서 실행 시간 설정:

```python
# 매일 오전 8시 실행
"daily_report_time": "08:00"

# 스케줄러 활성화
"enabled": True
"daily_report_enabled": True
```

환경 변수로도 설정 가능:
```bash
export SCHEDULER_ENABLED=true
export DAILY_REPORT_TIME=08:00
export DAILY_REPORT_STORES=all
```

### 시간대 설정

Docker 컨테이너는 자동으로 KST(Asia/Seoul) 시간대로 설정됩니다:

```yaml
# docker-compose.yml에 포함됨
environment:
  - TZ=Asia/Seoul
volumes:
  - /etc/localtime:/etc/localtime:ro
```

## 🧪 설치 확인

### 1. 기본 서비스 확인
```bash
# 서버 상태
curl http://localhost:8002/health

# Plus Agent 연결
curl http://localhost:32770/health

# 매장 데이터 접근
curl http://localhost:8002/mcp/tools/available-sites
```

### 2. 스케줄러 확인
```bash
# 스케줄러 상태
curl http://localhost:8002/mcp/tools/scheduler/status

# 다음 실행 시간
curl http://localhost:8002/mcp/tools/scheduler/next-execution
```

### 3. 이메일 연결 테스트
```bash
# 테스트 이메일 전송
curl -X POST http://localhost:8002/mcp/tools/scheduler/send-test-email
```

### 4. 전체 워크플로우 테스트
```bash
# 샘플 데이터로 테스트 (이메일 전송 없음)
curl -X POST "http://localhost:8002/mcp/tools/daily-report-test?use_sample_data=true"

# 실제 리포트 생성 및 이메일 전송
curl -X POST "http://localhost:8002/mcp/tools/daily-report-email?report_date=2025-09-02"
```

## 🛠️ 고급 설정

### 로그 레벨 설정
```bash
# .env 파일에서
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### 리포트 저장소 설정
```bash
# 생성된 리포트 파일 저장 위치
REPORTS_DIR=./data/reports
LOGS_DIR=./data/logs
```

### GPT 모델 설정
```python
# config/scheduler_config.py
"max_tokens": 500,  # GPT 응답 최대 토큰 수
"sender_name": "Daily Report Bot",  # 이메일 발신자명
```

### 매장 필터링
```bash
# 특정 매장만 포함
DAILY_REPORT_STORES="매장1,매장2,매장3"

# 모든 매장 포함
DAILY_REPORT_STORES=all
```

## 🔒 보안 설정

### API 키 보안
- `.env` 파일에 API 키 저장
- 파일 권한을 600으로 설정: `chmod 600 .env`
- Git에 .env 파일 커밋하지 않음 (`.gitignore`에 포함됨)

### 네트워크 보안
- 내부 서비스 통신은 Docker 네트워크 사용
- 필요한 포트만 외부 노출 (8002, 32770)
- ClickHouse 인증 정보 암호화 저장

### 방화벽 설정
```bash
# Ubuntu UFW 설정 예시
sudo ufw allow 8002/tcp
sudo ufw allow 32770/tcp  # Plus Agent (필요시만)
sudo ufw enable
```

## 📊 모니터링 설정

### 헬스체크 스크립트
```bash
#!/bin/bash
# healthcheck.sh

echo "=== System Health Check ==="

# 기본 서비스
curl -f http://localhost:8002/health || echo "❌ Report Server Down"
curl -f http://localhost:32770/health || echo "❌ Plus Agent Down"

# 스케줄러
curl -s http://localhost:8002/mcp/tools/scheduler/status | jq -r '.status.running' | grep -q true || echo "❌ Scheduler Not Running"

# 디스크 공간
df -h | grep -v tmpfs | awk 'NR>1 {if($5 > 90) print "⚠️ Disk space critical: " $0}'

echo "✅ Health check completed"
```

### 로그 모니터링
```bash
# 실시간 로그 모니터링
docker logs -f report-mcp-server

# 에러 로그만 필터링
docker logs report-mcp-server 2>&1 | grep -i error

# 스케줄러 실행 로그
docker logs report-mcp-server 2>&1 | grep -i "daily report"
```

## 🔄 업데이트

### 코드 업데이트
```bash
# 최신 코드 받기
git pull origin main

# 컨테이너 재빌드
docker-compose down
docker-compose up --build -d

# 서비스 확인
curl http://localhost:8002/health
```

### 환경 변수 업데이트
```bash
# .env 파일 수정 후
docker-compose restart

# 또는 전체 재시작
docker-compose down && docker-compose up -d
```

## 🆘 문제 해결

### 일반적인 문제들

#### 1. 컨테이너가 시작되지 않음
```bash
# 로그 확인
docker logs report-mcp-server

# 포트 충돌 확인
netstat -tuln | grep 8002

# 디스크 공간 확인
df -h
```

#### 2. Plus Agent 연결 실패
```bash
# 네트워크 연결 테스트
docker exec -it report-mcp-server curl http://plus-agent-llm-server:8000/health

# 네트워크 재연결
docker network disconnect plus-agent-llm-server_plus-agent-network report-mcp-server
docker network connect plus-agent-llm-server_plus-agent-network report-mcp-server
```

#### 3. 스케줄러가 실행되지 않음
```bash
# 시간대 확인
docker exec -it report-mcp-server date

# 스케줄러 로그 확인
docker logs report-mcp-server | grep -i scheduler

# 수동 테스트
curl -X POST http://localhost:8002/mcp/tools/scheduler/test-daily-report
```

#### 4. 데이터베이스 연결 실패
```bash
# ClickHouse 연결 테스트
curl "http://your-clickhouse-host:8123/ping"

# 환경 변수 확인
docker exec -it report-mcp-server env | grep -i clickhouse
```

### 로그 파일 위치
- **애플리케이션 로그**: `docker logs report-mcp-server`
- **저장된 리포트**: `./data/reports/`
- **설정 로그**: `./data/logs/`

---

문제가 해결되지 않으면 [GitHub Issues](https://github.com/deepingBDA/report-mcp-server/issues)에 로그와 함께 문의해주세요.