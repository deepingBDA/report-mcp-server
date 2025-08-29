# Report MCP Server - API Documentation

**Version:** 4.0.0 (GPT-4o Integration)  
**Base URL:** `http://localhost:8002`

---

## 📋 Table of Contents

1. [Server Status](#server-status)
2. [Summary Report API](#summary-report-api)
3. [Comparison Analysis API](#comparison-analysis-api-development)
4. [Response Formats](#response-formats)
5. [Error Handling](#error-handling)

---

## Server Status

### GET /health
서버 상태 확인

**Request:**
```bash
curl http://localhost:8002/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Report MCP Server is running"
}
```

### GET /
서버 정보 및 사용 가능한 엔드포인트 목록

**Request:**
```bash
curl http://localhost:8002/
```

**Response:**
```json
{
  "message": "Report MCP Server",
  "version": "4.0.0",
  "endpoints": [
    "/mcp/tools/report-generator/summary-report-html",
    "/mcp/tools/report-generator/comparison-analysis-html"
  ]
}
```

---

## Summary Report API

### POST /mcp/tools/report-generator/summary-report-html

**🤖 AI 기반 방문객 요약 리포트 생성**

GPT-4o를 활용하여 매장별 방문 데이터를 분석하고, 인사이트 및 액션 권장사항을 포함한 시각적 HTML 리포트를 생성합니다.

#### Request Format

**Method:** `POST`  
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "data_type": "visitor",           // string, optional (default: "visitor")
  "end_date": "2025-04-30",        // string, required (YYYY-MM-DD)
  "stores": "all",                 // string|array, required
  "periods": [1]                   // array<int>, optional (default: [7])
}
```

**Parameters:**
- **`data_type`** *(string, optional)*: 데이터 타입. 현재 `"visitor"`만 지원 (기본값: `"visitor"`)
- **`end_date`** *(string, required)*: 분석 기준일. YYYY-MM-DD 형식
- **`stores`** *(string|array, required)*: 분석할 매장 목록
  - `"all"`: 모든 매장
  - `["역삼점", "타워팰리스점"]`: 특정 매장 배열
  - `"역삼점,타워팰리스점"`: 콤마로 구분된 문자열
- **`periods`** *(array<int>, optional)*: 분석 기간 목록 (기본값: `[7]`)
  - `[1]`: 1일 모드 - AI 요약 + 액션 권장사항
  - `[7]`: 7일 모드 - 주간 트렌드 분석

#### 지원 매장 목록
- **금천프라임점** - 저방문 고성장 매장
- **마천파크점** - 중간규모 증가세 매장  
- **만촌힐스테이트점** - 대형 안정형 매장
- **망우혜원점** - 지역 특화 매장
- **신촌르메이에르점** - 고성장 매장
- **역삼점** - 대형 핵심 매장
- **타워팰리스점** - 최대 규모 플래그십 매장

#### Response Format

**Success (HTTP 200):**
```json
{
  "result": "success",
  "html_content": "<html>...</html>"
}
```

**Response Fields:**
- **`result`** *(string)*: 처리 결과 (`"success"` | `"failed"`)
- **`html_content`** *(string|null)*: 생성된 완전한 HTML 리포트 내용

#### Request Examples

**1일 모드 - AI 요약 및 액션 포함:**
```bash
curl -X POST http://localhost:8002/mcp/tools/report-generator/summary-report-html \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "visitor",
    "end_date": "2025-04-30",
    "stores": "all",
    "periods": [1]
  }'
```

**7일 모드 - 주간 트렌드 분석:**
```bash
curl -X POST http://localhost:8002/mcp/tools/report-generator/summary-report-html \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "visitor",
    "end_date": "2025-04-30",
    "stores": "all",
    "periods": [7]
  }'
```

**특정 매장만 분석:**
```bash
curl -X POST http://localhost:8002/mcp/tools/report-generator/summary-report-html \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "visitor",
    "end_date": "2025-04-30",
    "stores": ["역삼점", "타워팰리스점"],
    "periods": [1]
  }'
```

#### Features

**🤖 AI 분석 (1일 모드):**
- GPT-4o 기반 매장별 성과 분석
- 전주 동일 요일 대비 증감률 해석
- 매장별 맞춤 액션 권장사항 생성
- 즉시 실행 가능한 구체적 개선 방안

**🎨 시각적 리포트:**
- CSS 스타일링 및 색상 코딩
- 증가/감소 매장 시각적 구분
- 불릿 포인트 및 구조화된 레이아웃
- 브라우저에서 바로 열기 가능한 완전한 HTML

**📈 데이터 분석:**
- 방문객 수 및 증감률 추적
- 매장별 성과 비교 및 랭킹
- 주간 트렌드 및 패턴 분석

---

## Comparison Analysis API (Development)

### POST /mcp/tools/report-generator/comparison-analysis-html

**⚠️ 현재 개발 중** - API는 존재하나 안정성 이슈로 디버깅 중

**Purpose:** 매장간 성과 비교 및 분석 리포트 생성

**Request Format:**
```json
{
  "stores": ["역삼점", "타워팰리스점"],
  "end_date": "2025-04-30",
  "period": 7,
  "analysis_type": "all"
}
```

**Status:** Under development - 추후 업데이트 예정

---

## Response Formats

### Success Response
모든 성공적인 API 호출은 다음 형식을 따릅니다:

```json
{
  "result": "success",
  "html_content": "<html>...</html>"
}
```

### Failed Response
처리 중 오류가 발생한 경우:

```json
{
  "result": "failed",
  "html_content": null
}
```

---

## Error Handling

### HTTP Status Codes

- **200 OK**: 요청 성공
- **500 Internal Server Error**: 서버 오류

### Error Response Format

```json
{
  "detail": "리포트 생성 실패: [오류 메시지]"
}
```

### Common Errors

**Invalid Date Format:**
```json
{
  "detail": "리포트 생성 실패: Invalid date format. Use YYYY-MM-DD"
}
```

**Invalid Store Name:**
```json
{
  "detail": "리포트 생성 실패: Unknown store name"
}
```

**Database Connection Error:**
```json
{
  "detail": "리포트 생성 실패: Database connection failed"
}
```

---

## Usage Tips

1. **HTML 응답 처리**: `html_content`는 완전한 HTML 문서이므로 파일로 저장하거나 직접 렌더링 가능
2. **1일 vs 7일 모드**: 1일 모드는 AI 분석이 포함되어 더 상세한 인사이트 제공
3. **매장 선택**: "all" 사용 시 모든 매장 분석, 특정 매장만 원할 경우 배열로 지정
4. **날짜 형식**: 반드시 YYYY-MM-DD 형식 사용
5. **브라우저 렌더링**: 생성된 HTML은 CSS와 스타일이 모두 포함되어 바로 표시 가능

---

**Last Updated:** 2025-08-29  
**API Version:** 4.0.0