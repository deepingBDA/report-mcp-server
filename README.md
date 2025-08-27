# Report MCP Server

FastAPI 기반 HTTP 서버로, DA-agent MCP 도구들을 REST API로 제공하는 리테일 분석 서버입니다.

## 주요 기능

- **✅ 매장 관리**: 7개 매장의 기본 정보 및 검증 기능 
- **🔗 ClickHouse 연결**: 데이터베이스 연결 및 기본 쿼리 지원
- **📊 MCP 프로토콜**: 34개 도구 엔드포인트 (일부 구현 진행 중)
- **🔍 진단 도구**: 방문객 분석 등 데이터 품질 검사 (개발 중)
- **📈 리포트 생성**: HTML 리포트 워크플로우 (개발 중)
- **🐳 Docker 지원**: 컨테이너 기반 배포 완료

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

## API 엔드포인트 현황

### ✅ 현재 작동 중인 기능

#### 기본 정보 및 상태 확인
- `GET /health` - 서버 상태 확인
- `GET /mcp/health` - MCP 서버 상태 및 도구 수 확인  
- `GET /mcp/tools` - 모든 MCP 도구 목록 조회 (34개 도구)

#### 매장 관리 기능  
- `GET /mcp/tools/available-sites` - 사용 가능한 매장 목록 (7개 매장)
- `GET /mcp/tools/system-info` - 시스템 정보 및 기능 목록
- `POST /mcp/tools/validate-site` - 매장명 유효성 검증

**사용 예시:**
```bash
# 매장 목록 확인
curl http://192.168.49.157:8002/mcp/tools/available-sites

# 매장 검증
curl -X POST http://192.168.49.157:8002/mcp/tools/validate-site \
  -H "Content-Type: application/json" \
  -d '{"site": "역삼점"}'
```

### ⚠️ 부분 작동 중인 기능 (데이터베이스 테이블 구성 필요)

#### POS 데이터 분석
- `POST /mcp/tools/pos/receipt-ranking` - 영수증 건수 비중 Top 5
- `POST /mcp/tools/pos/sales-ranking` - 매출 비중 Top 5

**현재 상태:** ClickHouse 연결 성공, `cu_revenue_total` 테이블 생성 필요

**에러 예시:**
```json
{
  "detail": "Table plusinsight.cu_revenue_total does not exist. (UNKNOWN_TABLE)"
}
```

### 🚧 구현 중인 기능

#### 진단 도구 (개발 진행 중)
- `POST /mcp/tools/diagnose/avg-visitors` - 일평균 방문객 진단 (구현 완료)
- `POST /mcp/tools/diagnose/avg-sales` - 일평균 판매 건수 진단
- `POST /mcp/tools/diagnose/zero-visits` - 방문객수 데이터 이상 조회  
- `POST /mcp/tools/diagnose/purchase-conversion` - 구매전환율 진단

#### 워크플로우 (개발 진행 중)
- `POST /mcp/tools/workflow/visitor-summary-html` - 방문 현황 HTML 리포트 생성
- `POST /mcp/tools/workflow/comparison-analysis-html` - 매장 비교 분석 HTML 리포트

#### 이메일 기능 (구현 예정)
- `GET /mcp/tools/email/config` - 이메일 설정 조회
- `GET /mcp/tools/email/test-connection` - SMTP 연결 테스트
- `POST /mcp/tools/email/send-html-report` - HTML 리포트 이메일 발송

### 📊 현재 등록된 매장
- 금천프라임점
- 마천파크점  
- 만촌힐스테이트점
- 망우혜원점
- 신촌르메이에르점
- 역삼점
- 타워팰리스점

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