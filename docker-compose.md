# Docker 배포 가이드

## 사전 준비

1. **환경 변수 설정**
   ```bash
   cp .env.example .env
   # .env 파일을 열어서 OPENAI_API_KEY 등 필요한 값들 입력
   ```

2. **프로젝트 구조**
   ```
   report-mcp-server/
   ├── docker-compose.yml
   ├── Dockerfile  
   ├── .env
   └── app/
   ```

## 실행 방법

### 서버 시작
```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드로 실행하려면
docker-compose up -d --build
```

### 서비스 제어
```bash
# 서비스 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

### 서비스 종료
```bash
# 서비스 종료
docker-compose down

# 볼륨까지 삭제하려면
docker-compose down -v
```

## 서비스 확인

### Health Check
```bash
curl http://localhost:8002/health
```

### API 테스트
```bash
# MCP 도구 목록 확인
curl http://localhost:8002/api/tools

# MCP 프로토콜 테스트
curl -X POST http://localhost:8002/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'

# 특정 도구 실행 예시
curl -X POST http://localhost:8002/api/tools/mcp_example_tool \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World"}'
```

## 네트워크 구성

- **HTTP API**: http://localhost:8002
- **MCP Protocol**: http://localhost:8002/mcp
- **Health Check**: http://localhost:8002/health

## 트러블슈팅

### 포트 충돌
```bash
# 포트 8002 사용 중인 프로세스 확인
lsof -i :8002

# 기존 서비스 종료 후 다시 실행
docker-compose down && docker-compose up --build
```

### 서비스 문제
```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f

# 컨테이너 내부 접속
docker-compose exec report-mcp-server bash
```

### 개발 모드
```bash
# 코드 변경시 재빌드 필요
docker-compose up --build
```

## 프로덕션 배포

1. **환경 변수 보안**
   - `.env` 파일을 Git에 커밋하지 마세요
   - 프로덕션에서는 환경 변수를 안전하게 관리하세요

2. **포트 설정**
   - 필요시 docker-compose.yml에서 포트 변경
   - 외부 접근을 위한 방화벽 설정

3. **모니터링**
   - Health check 엔드포인트를 통한 상태 모니터링
   - 로그 수집 및 분석 시스템 구축

간단하게 `docker-compose up --build` 로 서버가 실행됩니다! 🐳