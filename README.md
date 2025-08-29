# Report MCP Server

**AI 기반 리테일 방문객 분석 및 리포트 생성 서버**

GPT-4o를 활용한 스마트 매장 분석과 시각적 리포트를 제공하는 FastAPI 기반 서버입니다.

## ✨ 주요 기능

- **🤖 AI 분석**: OpenAI GPT-4o 모델을 활용한 매장별 인사이트 및 액션 권장사항 생성
- **📊 요약 리포트**: 1일/7일 방문객 데이터 분석 및 HTML 시각화 리포트
- **🎨 시각적 출력**: CSS 스타일링, 불릿 포인트, 색상 코딩이 적용된 전문적인 HTML 리포트
- **📈 트렌드 분석**: 전주 대비 증감률, 매장별 성과 비교, 주요 지표 추적
- **🔗 ClickHouse 연결**: 실시간 데이터베이스 연동 및 매장 데이터 관리
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

## 🚀 API 엔드포인트

> **📖 상세한 API 문서**: [docs/api.md](docs/api.md) - 모든 API의 요청/응답 형식, 예시, 에러 처리 방법

### ✅ 현재 작동하는 기능

#### 📊 요약 리포트 (메인 기능)
- **`POST /mcp/tools/report-generator/summary-report-html`** - AI 기반 방문객 요약 리포트 생성

**주요 특징:**
- 🤖 **GPT-4o AI 분석**: 매장별 인사이트 및 액션 권장사항 자동 생성
- 📅 **1일/7일 모드**: 일별 상세 분석 또는 주간 트렌드 분석
- 🎨 **시각적 HTML**: 전문적인 스타일링이 적용된 완전한 HTML 리포트
- 📈 **실시간 분석**: 전주 대비 증감률, 매장별 성과 비교

**간단한 사용 예시:**
```bash
# 1일 모드 (AI 분석 포함)
curl -X POST http://localhost:8002/mcp/tools/report-generator/summary-report-html \
  -H "Content-Type: application/json" \
  -d '{"end_date": "2025-04-30", "stores": "all", "periods": [1]}'

# 응답
{
  "result": "success",
  "html_content": "<html>완전한 HTML 리포트...</html>"
}
```

#### 서버 상태 확인
- `GET /health` - 서버 상태 확인
- `GET /` - 서버 정보 및 엔드포인트 목록

### ⚠️ 구현 중인 기능

#### 비교 분석 리포트 (개발 중)
- `POST /mcp/tools/report-generator/comparison-analysis-html` - 매장간 비교 분석

**현재 상태:** API 존재하나 안정성 이슈로 디버깅 중

### 📊 현재 지원하는 매장
- **금천프라임점** - 저방문 고성장 매장
- **마천파크점** - 중간규모 증가세 매장  
- **만촌힐스테이트점** - 대형 안정형 매장
- **망우혜원점** - 지역 특화 매장
- **신촌르메이에르점** - 고성장 매장
- **역삼점** - 대형 핵심 매장
- **타워팰리스점** - 최대 규모 플래그십 매장

**매장 지정 방법:**
- `"all"` - 모든 매장 분석
- `["역삼점", "타워팰리스점"]` - 특정 매장만 선택
- `"역삼점,타워팰리스점"` - 콤마로 구분된 문자열

## 🧪 테스트 도구 사용법

프로젝트에는 자동화된 테스트 클라이언트가 포함되어 있습니다:

```bash
# Python 테스트 클라이언트 실행
python test/test_report_client.py

# 실행 결과:
# - 서버 상태 확인
# - 1일 모드 요약 리포트 생성
# - HTML 파일 자동 저장 (downloaded_reports/ 폴더)
# - 브라우저에서 자동 열기
```

**테스트 클라이언트 주요 기능:**
- 자동 health check
- 다양한 날짜/매장 조합 테스트
- HTML 파일 로컬 저장
- 브라우저 자동 실행
- 상세한 실행 로그

## 🤖 AI 분석 엔진

### GPT-4o 기반 스마트 분석
- **Few-shot 프롬프팅**: 일관된 출력 형식 보장
- **매장별 맞춤 분석**: 각 매장의 특성을 고려한 개별 인사이트
- **액션 권장사항**: 즉시 실행 가능한 구체적인 개선 방안 제시
- **트렌드 해석**: 복잡한 데이터 패턴을 이해하기 쉬운 언어로 설명

### 1일 모드 특별 기능
- **요약 섹션**: 주요 지표와 핵심 인사이트
- **액션 섹션**: 매장별 맞춤 개선 방안
- **시각적 강조**: 증가/감소 매장을 색상으로 구분
- **즉시 실행**: 당일 데이터 기반 즉각적인 의사결정 지원

## 🛠 기술 스택

- **웹 프레임워크**: FastAPI 4.0
- **AI/ML**: LangChain + OpenAI GPT-4o
- **데이터베이스**: ClickHouse
- **시각화**: Custom CSS + SVG Charts  
- **배포**: Docker + Docker Compose
- **언어**: Python 3.8+

## 환경 변수

`.env.example` 파일을 참고하여 다음 환경 변수들을 설정하세요:

- `HOST`: 서버 호스트 (기본값: 0.0.0.0)
- `PORT`: 서버 포트 (기본값: 8002)
- `DEBUG`: 디버그 모드 (기본값: False)
- 데이터베이스 연결 정보들

## 📈 사용 사례

### 일일 운영 관리
- 매일 아침 전일 성과 분석
- AI가 제안하는 당일 액션 아이템 실행
- 매장별 맞춤형 개선 방안 적용

### 주간 성과 리뷰  
- 주간 트렌드 분석 및 패턴 파악
- 매장간 성과 비교 및 베스트 프랙티스 공유
- 데이터 기반 의사결정 지원

### 전략적 분석
- 매장별 특성 파악 및 포지셔닝
- 성장 동력 분석 및 확산 전략 수립
- ROI 기반 투자 우선순위 결정

