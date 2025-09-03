# 배포 가이드 - Report MCP Server

## 🚀 프로덕션 배포

### 시스템 요구사항
- **OS**: Ubuntu 20.04 LTS 이상
- **메모리**: 최소 4GB, 권장 8GB
- **CPU**: 최소 2 코어, 권장 4 코어
- **디스크**: 최소 20GB 여유 공간
- **네트워크**: 인터넷 연결 (OpenAI API, AWS SES)

### 전체 시스템 배포 순서

#### 1. Plus Agent LLM Server 배포
```bash
# Plus Agent 서버 배포
cd /opt/plus-agent-llm-server
docker-compose up -d

# 서비스 확인
curl http://localhost:32770/health
```

#### 2. Report MCP Server 배포
```bash
# Report 서버 배포
cd /opt/report-mcp-server
docker-compose up -d

# 서비스 확인
curl http://localhost:8002/health
```

#### 3. 네트워크 연결 설정
```bash
# 두 서비스 간 네트워크 연결
docker network connect plus-agent-llm-server_plus-agent-network report-mcp-server
```

### 환경 변수 설정

#### `.env` 파일 구성
```bash
# Report MCP Server/.env
OPENAI_API_KEY=sk-proj-xxx...
CONFIG_DB_HOST=clickhouse-server
CONFIG_DB_PORT=8123
CONFIG_DB_NAME=cu_base
CLICKHOUSE_USER=your_username
CLICKHOUSE_PASSWORD=your_password

# Scheduler Settings
SCHEDULER_ENABLED=true
DAILY_REPORT_TIME=08:00
DAILY_REPORT_STORES=all
PLUS_AGENT_URL=http://plus-agent-llm-server:8000
```

### 서비스 헬스체크

#### 자동 모니터링 스크립트
```bash
#!/bin/bash
# healthcheck.sh

echo "=== Report MCP Server Health Check ==="

# 1. Report Server 상태
echo "1. Report Server Status:"
curl -s http://localhost:8002/health | jq .

# 2. Plus Agent 연결
echo "2. Plus Agent Connection:"
curl -s http://localhost:32770/health | jq .

# 3. 스케줄러 상태
echo "3. Scheduler Status:"
curl -s http://localhost:8002/mcp/tools/scheduler/status | jq .

# 4. 데일리 리포트 서비스
echo "4. Daily Report Service:"
curl -s http://localhost:8002/mcp/tools/daily-report-status | jq .

# 5. 테스트 이메일
echo "5. Test Email:"
curl -s -X POST http://localhost:8002/mcp/tools/scheduler/send-test-email | jq .
```

### 로그 관리

#### 로그 로테이션 설정
```bash
# /etc/logrotate.d/report-mcp-server
/var/log/report-mcp-server/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 0644 root root
    postrotate
        docker kill -s USR1 report-mcp-server 2>/dev/null || true
    endscript
}
```

#### 로그 모니터링
```bash
# 실시간 로그 모니터링
tail -f /var/log/report-mcp-server/app.log

# 에러 로그만 필터링
docker logs report-mcp-server 2>&1 | grep -i error
```

### 백업 및 복구

#### 설정 백업
```bash
#!/bin/bash
# backup_config.sh

BACKUP_DIR="/backup/report-mcp-server/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 설정 파일 백업
cp -r /opt/report-mcp-server/.env $BACKUP_DIR/
cp -r /opt/report-mcp-server/docker-compose.yml $BACKUP_DIR/
cp -r /opt/report-mcp-server/config/ $BACKUP_DIR/

echo "Configuration backed up to $BACKUP_DIR"
```

### 성능 최적화

#### Docker 리소스 제한
```yaml
# docker-compose.yml
services:
  report-mcp-server:
    # ... 기존 설정
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

#### 데이터베이스 연결 풀링
```python
# config/database.py 최적화 권장사항
CONNECTION_POOL_SIZE = 10
CONNECTION_TIMEOUT = 30
QUERY_TIMEOUT = 120
```

### 보안 설정

#### 방화벽 설정
```bash
# UFW 방화벽 설정
sudo ufw allow 8002/tcp    # Report Server
sudo ufw allow 32770/tcp   # Plus Agent (외부 접근 필요시)
sudo ufw enable
```

#### SSL/TLS 인증서 (선택사항)
```bash
# Let's Encrypt 인증서 설정
certbot certonly --standalone -d your-domain.com
```

### 모니터링 및 알림

#### Prometheus 메트릭 (선택사항)
```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```

#### 슬랙 알림 설정 (선택사항)
```python
# config/notification.py
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/xxx"
ALERT_CHANNELS = ["#operations", "#reports"]
```

### 자동 업데이트

#### CI/CD 파이프라인 예시
```bash
#!/bin/bash
# deploy.sh

# 1. 소스 코드 업데이트
git pull origin main

# 2. 서비스 다운타임 최소화 롤링 업데이트
docker-compose pull
docker-compose up -d --no-deps report-mcp-server

# 3. 헬스체크
sleep 30
if curl -f http://localhost:8002/health; then
    echo "Deployment successful"
else
    echo "Deployment failed, rolling back..."
    docker-compose rollback
    exit 1
fi
```

### 문제 해결

#### 일반적인 문제 및 해결 방법

1. **컨테이너 시작 실패**
```bash
# 로그 확인
docker logs report-mcp-server --tail 50

# 디스크 공간 확인
df -h

# 메모리 사용량 확인
free -h
```

2. **네트워크 연결 문제**
```bash
# Docker 네트워크 상태 확인
docker network ls
docker network inspect plus-agent-llm-server_plus-agent-network

# 컨테이너 간 연결 테스트
docker exec -it report-mcp-server ping plus-agent-llm-server
```

3. **스케줄러 작동 안함**
```bash
# 스케줄러 로그 확인
docker logs report-mcp-server | grep -i scheduler

# 시간대 설정 확인
docker exec -it report-mcp-server date
```

### 성능 모니터링

#### 주요 메트릭
- API 응답 시간
- 메모리 사용률
- CPU 사용률
- 디스크 I/O
- 이메일 전송 성공률
- 스케줄러 실행 성공률

#### 모니터링 스크립트
```bash
#!/bin/bash
# monitor.sh

echo "=== Performance Metrics ==="
echo "CPU Usage:"
docker stats report-mcp-server --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo "Disk Usage:"
df -h /opt/report-mcp-server

echo "Network Connections:"
netstat -tuln | grep -E "(8002|32770)"
```

### 데이터 백업

#### 정기 백업 스크립트
```bash
#!/bin/bash
# daily_backup.sh

BACKUP_DIR="/backup/daily/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 생성된 리포트 백업
cp -r /opt/report-mcp-server/data/reports $BACKUP_DIR/

# 로그 백업  
cp -r /opt/report-mcp-server/data/logs $BACKUP_DIR/

# 설정 백업
cp /opt/report-mcp-server/.env $BACKUP_DIR/
cp /opt/report-mcp-server/docker-compose.yml $BACKUP_DIR/

# 오래된 백업 삭제 (30일 이상)
find /backup/daily -type d -mtime +30 -exec rm -rf {} \;
```

### Crontab 설정

```bash
# crontab -e
# 매일 오전 1시 백업
0 1 * * * /opt/scripts/daily_backup.sh

# 매 시간 헬스체크
0 * * * * /opt/scripts/healthcheck.sh >> /var/log/healthcheck.log

# 매주 월요일 로그 정리
0 2 * * 1 docker system prune -f
```

---

이 가이드를 따라하시면 안정적인 프로덕션 환경에서 Report MCP Server를 운영할 수 있습니다.