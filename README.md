# Report MCP Server

FastAPI 기반 HTTP 서버로, DA-agent MCP 도구들을 REST API로 제공하는 리테일 분석 서버입니다.

## 주요 기능

- **📊 34개 MCP 도구**: POS 데이터 분석, 인사이트 분석, 진단 도구 등
- **🏪 멀티 매장 지원**: 여러 매장의 데이터를 동시에 분석 
- **🔍 실시간 분석**: ClickHouse 기반 실시간 데이터 조회
- **📈 리포트 생성**: HTML 리포트 자동 생성 및 이메일 발송
- **🐳 Docker 지원**: 컨테이너 기반 배포

## 빠른 시작

### 1. 환경 설정
```bash
cp .env.example .env
# .env 파일에 데이터베이스 연결 정보 입력
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
python main.py
# 서버가 http://localhost:8002 에서 실행됩니다
```

### 4. API 테스트
```bash
# 서버 상태 확인
curl http://localhost:8002/health

# 사용 가능한 매장 목록
curl http://localhost:8002/mcp/tools/available-sites

# MCP 도구 목록
curl http://localhost:8002/mcp/tools
```

## Docker 배포

```bash
# Docker로 빌드 및 실행
docker-compose up --build -d

# 로그 확인
docker-compose logs -f report-mcp-server
```

## 주요 API 엔드포인트

### 기본 정보
- `GET /health` - 서버 상태 확인
- `GET /mcp/health` - MCP 서버 상태 및 도구 수 확인
- `GET /mcp/tools` - 모든 MCP 도구 목록 조회

### 매장 및 시스템
- `GET /mcp/tools/available-sites` - 사용 가능한 매장 목록
- `GET /mcp/tools/system-info` - 시스템 정보 및 기능 목록
- `POST /mcp/tools/validate-site` - 매장명 유효성 검증

### POS 데이터 분석
- `POST /mcp/tools/pos/sales-statistics` - 매출 통계 요약
- `POST /mcp/tools/pos/receipt-ranking` - 영수증 건수 비중 Top 5
- `POST /mcp/tools/pos/sales-ranking` - 매출 비중 Top 5

### 인사이트 분석
- `POST /mcp/tools/insight/pickup-transition` - 픽업 구역 전환 분석
- `POST /mcp/tools/insight/sales-funnel` - 세일즈 퍼널 분석
- `POST /mcp/tools/insight/shelf-performance` - 선반 성과 분석
- `POST /mcp/tools/insight/customer-journey` - 고객 여정 분석

### 진단 도구
- `POST /mcp/tools/diagnose/avg-visitors` - 일평균 방문객 진단
- `POST /mcp/tools/diagnose/avg-sales` - 일평균 판매 건수 진단
- `POST /mcp/tools/diagnose/zero-visits` - 방문객수 데이터 이상 조회
- `POST /mcp/tools/diagnose/purchase-conversion` - 구매전환율 진단

### 워크플로우
- `POST /mcp/tools/workflow/visitor-summary-html` - 방문 현황 HTML 리포트 생성
- `POST /mcp/tools/workflow/comparison-analysis-html` - 매장 비교 분석 HTML 리포트

## 도구 추가 방법

새로운 MCP 도구를 추가하려면:

1. **간단한 도구**: `main.py`에 직접 FastAPI 엔드포인트 추가
```python
@app.post("/mcp/tools/category/tool-name", tags=["category"])
async def new_tool(request: RequestModel):
    """도구 설명"""
    try:
        # 도구 로직 구현
        result = "결과"
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **복잡한 도구**: `mcp_tools/` 폴더에 모듈 생성 후 import하여 사용
3. **Request 모델**: 필요시 새로운 Pydantic 모델 정의
4. **태그**: 관련 기능별로 태그 분류 (`pos`, `insight`, `diagnose` 등)

## 환경 변수

`.env.example` 파일을 참고하여 다음 환경 변수들을 설정하세요:

- `HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `PORT`: 서버 포트 (기본값: 8002)
- `DEBUG`: 디버그 모드 (기본값: False)
- 데이터베이스 연결 정보들

## 라이센스

이 프로젝트는 내부 사용을 위한 리테일 분석 도구입니다.