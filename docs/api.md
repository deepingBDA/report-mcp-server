# API 명세서

Report MCP Server의 모든 API 엔드포인트에 대한 상세한 명세입니다.

## 🌐 기본 정보

- **Base URL**: `http://localhost:8002`
- **API 문서**: `http://localhost:8002/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8002/redoc`

## 📊 데일리 리포트 자동화 API

### POST /mcp/tools/daily-report-email
**전체 워크플로우를 한번에 실행하는 메인 API**

```http
POST /mcp/tools/daily-report-email?report_date=2025-09-02
```

**Query Parameters:**
- `report_date` (optional): 리포트 날짜 (YYYY-MM-DD). 기본값: 어제 날짜

**Response:**
```json
{
  "result": "success",
  "message": "2025-09-02 데일리 리포트가 성공적으로 생성되고 이메일로 전송되었습니다",
  "report_date": "2025-09-02",
  "execution_time": "0:00:12.482549",
  "details": {
    "summary_length": 495,
    "html_length": 17313,
    "email_recipients": ["user@example.com"]
  }
}
```

### GET /mcp/tools/daily-report-status
**데일리 리포트 서비스 상태 확인**

```json
{
  "result": "success",
  "status": "healthy",
  "service": "daily-report-email",
  "configuration": {
    "data_type": "visitor",
    "max_tokens": 500,
    "sender_name": "Daily Report Bot",
    "include_html": true
  }
}
```

### POST /mcp/tools/daily-report-test
**테스트 모드 실행 (이메일 전송 없음)**

```http
POST /mcp/tools/daily-report-test?use_sample_data=true
```

## ⏰ 스케줄러 관리 API

### GET /mcp/tools/scheduler/status
**스케줄러 상태 및 다음 실행 시간 확인**

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
        "next_run_time": "2025-09-04T08:00:00+09:00",
        "trigger": "cron[hour='8', minute='0']"
      }
    ],
    "config": {
      "enabled": true,
      "daily_report_enabled": true,
      "daily_report_time": "08:00"
    }
  }
}
```

### POST /mcp/tools/scheduler/test-daily-report
**스케줄러 수동 실행 테스트**

### POST /mcp/tools/scheduler/send-test-email
**테스트 이메일 전송**

### GET /mcp/tools/scheduler/next-execution
**다음 실행 시간만 조회**

### GET /mcp/tools/scheduler/config
**스케줄러 설정 조회**

## 📈 리포트 생성 API

### POST /mcp/tools/report-generator/summary-report-html
**요약 리포트 HTML 생성**

```json
{
  "data_type": "visitor",
  "end_date": "2025-09-02",
  "stores": ["매장1", "매장2"] || "all",
  "periods": [1, 7, 30]
}
```

### POST /mcp/tools/report-generator/comparison-analysis-html
**비교 분석 리포트 생성**

```json
{
  "stores": ["매장1", "매장2"] || "all",
  "end_date": "2025-09-02",
  "period": 7,
  "analysis_type": "all"
}
```

## 🤖 AI 요약 API

### POST /mcp/tools/report-summarizer/summarize-html-report
**GPT를 활용한 리포트 요약**

```json
{
  "html_content": "<html>...</html>",
  "report_type": "daily_report",
  "max_tokens": 500
}
```

**Response:**
```json
{
  "success": true,
  "summary": "AI가 생성한 요약 내용...",
  "tokens_used": 123,
  "model": "gpt-4o-mini"
}
```

## 🔍 리포트 뷰어 API

### GET /mcp/tools/report-viewer/list-reports
**생성된 리포트 목록 조회**

### GET /mcp/tools/report-viewer/recent-reports
**최근 리포트 목록**

```http
GET /mcp/tools/report-viewer/recent-reports?limit=10
```

## 🏪 매장 정보 API

### GET /mcp/tools/available-sites
**사용 가능한 매장 목록**

### GET /mcp/tools
**모든 MCP 도구 목록**

### GET /health
**서버 상태 확인**

## ❌ 에러 응답 형식

모든 API는 일관된 에러 응답을 사용합니다:

```json
{
  "result": "failed",
  "message": "에러 메시지",
  "error_details": "상세 에러 정보",
  "step_failed": "실패한 단계",
  "report_date": "2025-09-02"
}
```

## 🔐 인증

현재 버전은 인증이 필요하지 않습니다.

## 📝 요청 예시

### cURL 사용
```bash
# 데일리 리포트 즉시 실행
curl -X POST "http://localhost:8002/mcp/tools/daily-report-email?report_date=2025-09-02"

# 스케줄러 상태 확인
curl "http://localhost:8002/mcp/tools/scheduler/status"

# 테스트 모드 실행
curl -X POST "http://localhost:8002/mcp/tools/daily-report-test?use_sample_data=true"
```

### Python 사용
```python
import httpx

async def send_daily_report():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/mcp/tools/daily-report-email",
            params={"report_date": "2025-09-02"}
        )
        return response.json()
```

## 🚀 성능 고려사항

- **타임아웃**: API 호출은 최대 5분 소요될 수 있습니다
- **동시성**: 동시에 여러 리포트 생성 요청은 권장하지 않습니다
- **리소스**: GPT 요약 시 OpenAI API 사용량이 발생합니다

---

더 자세한 사용 예시는 [USAGE.md](USAGE.md)를 참조하세요.