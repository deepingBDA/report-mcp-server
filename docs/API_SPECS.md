# Report MCP Server - API 스펙 문서

## 개요

Report MCP Server는 편의점 방문자 데이터를 분석하고 리포트를 생성하는 HTTP API 서버입니다.

### 주요 기능
- 📊 **리포트 생성**: 매장별 방문자 분석 리포트
- 🤖 **AI 요약**: GPT를 활용한 자동 리포트 요약
- 📧 **이메일 자동화**: 일일 리포트 자동 이메일 전송
- ⏰ **스케줄러**: 매일 자동 실행되는 리포트 생성

## API 엔드포인트

### 1. 리포트 생성 (Report Generator)
**Base URL**: `/mcp/tools/report-generator`

#### 1.1 요약 리포트 생성
```http
POST /summary-report-html
```

**Request Body**:
```json
{
  "data_type": "visitor",
  "end_date": "2025-09-02", 
  "stores": ["매장1", "매장2"] | "all",
  "periods": [1, 7, 30]
}
```

**Response**:
```json
{
  "result": "success",
  "html_content": "<html>...</html>",
  "execution_time": "0:00:05.123456"
}
```

#### 1.2 비교 분석 리포트
```http
POST /comparison-analysis-html
```

**Request Body**:
```json
{
  "stores": ["매장1", "매장2"] | "all",
  "end_date": "2025-09-02",
  "period": 7,
  "analysis_type": "all"
}
```

### 2. 리포트 요약 (Report Summarizer)
**Base URL**: `/mcp/tools/report-summarizer`

#### 2.1 HTML 리포트 요약
```http
POST /summarize-html-report
```

**Request Body**:
```json
{
  "html_content": "<html>...</html>",
  "report_type": "daily_report",
  "max_tokens": 500
}
```

**Response**:
```json
{
  "success": true,
  "summary": "리포트 요약 내용...",
  "tokens_used": 123,
  "model": "gpt-4o-mini"
}
```

### 3. 데일리 리포트 자동화 (Daily Report)
**Base URL**: `/mcp/tools`

#### 3.1 데일리 리포트 이메일 전송
```http
POST /daily-report-email?report_date=2025-09-02
```

**Response**:
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

#### 3.2 데일리 리포트 서비스 상태
```http
GET /daily-report-status
```

**Response**:
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

#### 3.3 데일리 리포트 테스트
```http
POST /daily-report-test?use_sample_data=true
```

**Response**:
```json
{
  "result": "success",
  "message": "테스트 모드: 샘플 데이터로 워크플로우 시뮬레이션 완료",
  "test_mode": true,
  "workflow_steps": {
    "1_report_generation": "✅ 샘플 HTML 리포트 생성됨",
    "2_gpt_summarization": "✅ GPT 요약 시뮬레이션 완료",
    "3_email_preparation": "✅ 이메일 내용 준비 완료 (전송 안됨)"
  }
}
```

### 4. 스케줄러 관리 (Scheduler)
**Base URL**: `/mcp/tools/scheduler`

#### 4.1 스케줄러 상태 확인
```http
GET /status
```

**Response**:
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
        "next_run_time": "2025-09-03T15:10:00+00:00",
        "trigger": "cron[hour='15', minute='10']"
      }
    ],
    "config": {
      "enabled": true,
      "daily_report_enabled": true,
      "daily_report_time": "15:10"
    }
  }
}
```

#### 4.2 수동 데일리 리포트 실행
```http
POST /test-daily-report
```

#### 4.3 테스트 이메일 전송
```http
POST /send-test-email
```

#### 4.4 다음 실행 시간 확인
```http
GET /next-execution
```

#### 4.5 스케줄러 설정 조회
```http
GET /config
```

### 5. 리포트 뷰어 (Report Viewer)
**Base URL**: `/mcp/tools/report-viewer`

#### 5.1 리포트 목록 조회
```http
GET /list-reports
```

#### 5.2 최근 리포트 조회
```http
GET /recent-reports?limit=10
```

## 에러 응답

모든 API는 일관된 에러 응답 형식을 사용합니다:

```json
{
  "result": "failed",
  "message": "에러 메시지",
  "error_details": "상세 에러 정보",
  "step_failed": "실패한 단계"
}
```

## 인증

현재 버전은 인증이 필요하지 않습니다.

## Rate Limiting

현재 Rate Limiting은 적용되지 않습니다.

## 문서 버전

- **버전**: 4.1.0
- **마지막 업데이트**: 2025-09-03
- **API 문서**: `http://localhost:8002/docs` (Swagger UI)
- **ReDoc**: `http://localhost:8002/redoc`