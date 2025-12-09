# Role
너는 Python 및 Streamlit 전문가이자, AI 기반 뉴스 큐레이션 서비스 개발자야.

# Project Goal
"나만의 IT 뉴스룸(My IT Newsroom)"이라는 Streamlit 웹 애플리케이션을 만들고 싶어.
이 앱은 국내 IT 뉴스 RSS를 수집하고, Google Gemini API를 이용해 날짜별로 뉴스를 요약/분석하여 브리핑해 주는 서비스야.

# Tech Stack & Constraints
1. **Language:** Python 3.10+
2. **Framework:** Streamlit
3. **External Libraries:**
   - `streamlit`: 웹 UI 구성
   - `feedparser`: RSS 피드 파싱
   - `google-generativeai`: Gemini API 사용 (뉴스 요약 및 분석)
   - `PyGithub`: GitHub 리포지토리에 JSON 파일을 직접 읽고 쓰기 위함 (Database 대용)
   - `pandas`: 데이터 처리
4. **Data Storage (Crucial):**
   - 별도의 DB(MySQL 등)를 절대 사용하지 않음.
   - 모든 데이터(RSS 목록, 수집된 뉴스, 통계)는 **JSON 파일**로 관리함.
   - **중요:** Streamlit Cloud 배포 환경을 고려하여, 로컬 파일 시스템이 아닌 **GitHub Repository에 있는 JSON 파일을 PyGithub 라이브러리를 통해 직접 읽고(Read) 업데이트(Write/Commit)하는 방식**으로 구현해야 함.
   - **제약사항 및 고려사항:**
     - GitHub API Rate Limit: 시간당 5,000회 요청 제한 (인증된 사용자 기준)
     - 동시성 문제: 여러 사용자가 동시에 수정 시 충돌 가능성 → 최신 파일을 읽은 후 업데이트하는 방식으로 처리
     - JSON 파일 크기: 파일이 커질 경우 성능 저하 가능 → 날짜별로 분리하거나 최신 데이터만 유지하는 전략 고려
5. **Deployment:** Streamlit Cloud
6. **Security & Configuration:**
   - Streamlit Cloud Secrets 설정 필요: `GITHUB_TOKEN`, `REPO_NAME`, `GEMINI_API_KEY`, `ADMIN_PASSWORD` (선택)
   - GitHub Token 권한: `repo` 권한 필요 (파일 읽기/쓰기/커밋)
   - 관리자 대시보드 접근 제어: 간단한 비밀번호 인증 또는 Streamlit Secrets의 `ADMIN_PASSWORD` 사용

# Key Features

## 1. Data Structure (JSON Files in GitHub Repo)

### `feeds.json` 구조
```json
{
  "feeds": [
    {
      "name": "GeekNews",
      "url": "https://feeds.feedburner.com/geeknews",
      "enabled": true
    }
  ]
}
```

### `news_data.json` 구조
```json
{
  "2024-01-15": {
    "date": "2024-01-15",
    "summary": "Gemini가 생성한 마크다운 브리핑 텍스트",
    "news": [
      {
        "title": "뉴스 제목",
        "link": "https://...",
        "published": "2024-01-15T10:00:00",
        "summary": "Gemini가 생성한 3줄 요약",
        "insights": "인사이트 텍스트"
      }
    ],
    "collected_at": "2024-01-15T12:00:00"
  }
}
```

### `stats.json` 구조
```json
{
  "daily_visitors": {
    "2024-01-15": 42,
    "2024-01-16": 38
  },
  "total_visitors": 1200,
  "last_updated": "2024-01-16T09:00:00"
}
```

**참고:** `stats.json`은 세션 시작 시 자동으로 업데이트되며, 중복 방문자는 세션 ID 기반으로 추적함.

## 2. Page Structure (Streamlit Sidebar Menu)

### A. 메인 화면 (Newsroom)
- **날짜 선택:** 사용자가 날짜를 선택할 수 있음 (기본값: 오늘).
- **AI 브리핑:** 선택한 날짜에 저장된 `news_data.json` 데이터를 불러와서 Gemini가 작성한 "오늘의 IT 주요 뉴스 브리핑"을 마크다운 형태로 깔끔하게 보여줌.
- **주요 뉴스 리스트:** 브리핑 아래에 해당 날짜의 주요 뉴스 헤드라인과 원문 링크를 리스트업.

### B. 관리자 대시보드 (Admin Dashboard)
- **접근 제어:** 비밀번호 입력 후 접근 가능 (Streamlit Secrets의 `ADMIN_PASSWORD` 사용)
- **접속자 통계:**
  - `stats.json`을 시각화하여 일별 방문자 추이 그래프 표시 (Streamlit Chart 사용)
  - 누적 접속자 수 표시
  - 통계는 메인 화면 접속 시 자동으로 업데이트됨
- **RSS 피드 관리:**
  - 현재 등록된 RSS 목록 표시 (테이블 형태)
  - RSS 추가/삭제/활성화 토글 기능 (GitHub에 `feeds.json` 업데이트)
  - RSS 피드 테스트 기능 (URL 유효성 검증)
- **데이터 수집 및 분석 실행 (Action Button):**
  - [뉴스 수집 및 분석 시작] 버튼 배치.
  - 버튼 클릭 시:
    1. 등록된 RSS에서 최신 뉴스 크롤링 (최근 24시간 내 뉴스만 수집)
    2. 중복 뉴스 제거 (URL 기반)
    3. Gemini API로 뉴스 내용을 분석 및 요약 (프롬프트: "IT 트렌드 관점에서 핵심 내용 3줄 요약 및 인사이트 도출")
    4. 배치 처리: 뉴스가 많을 경우 청크 단위로 나누어 API 호출 (비용 및 Rate Limit 고려)
    5. 결과를 `news_data.json`에 저장하고 GitHub에 Commit/Push
  - 진행 상황을 `st.progress` 바와 로그로 표시
  - 완료 후 성공/실패 메시지 표시

# Implementation Steps
다음 단계에 따라 코드를 작성해줘.

**Step 1: 환경 설정 및 GitHub 연동 모듈 (GithubManager)**
- `secrets.toml`에서 GITHUB_TOKEN, REPO_NAME, GEMINI_API_KEY, ADMIN_PASSWORD를 가져옴.
- `PyGithub`를 사용하여 리포지토리의 JSON 파일을 읽고(decode), 수정하여 커밋(update)하는 Helper Class (`GithubManager`)를 먼저 작성해줘.
- **핵심 기능:**
  - `read_json(file_path)`: GitHub에서 JSON 파일 읽기 및 파싱
  - `write_json(file_path, data)`: JSON 데이터를 GitHub에 커밋 및 푸시
  - 동시성 처리: 최신 파일을 읽은 후 업데이트 (충돌 방지)
  - 에러 처리: Rate Limit, 네트워크 오류 등 예외 처리

**Step 2: RSS 파싱 및 Gemini 분석 로직**
- `feedparser`로 뉴스 가져오는 함수 (최근 24시간 내 뉴스만 필터링).
- 중복 뉴스 제거 로직 (URL 기반).
- Gemini Pro 모델을 사용하여 뉴스 리스트를 입력받아 마크다운 리포트를 생성하는 함수.
- **성능 최적화:**
  - 배치 처리: 뉴스가 많을 경우 10-20개씩 청크로 나누어 API 호출
  - 재시도 로직: API 호출 실패 시 최대 3회 재시도
  - 타임아웃 설정: API 호출 타임아웃 30초

**Step 3: Streamlit UI 구현**
- 사이드바 네비게이션 구현 (메인 화면, 관리자 대시보드).
- 메인 화면과 대시보드 화면 레이아웃 구성.
- **추가 기능:**
  - 세션 기반 캐싱: 같은 세션 내에서는 GitHub에서 한 번만 읽고 메모리에 캐시
  - 접속자 통계 자동 업데이트: 메인 화면 접속 시 `stats.json` 업데이트
  - 로딩 상태 표시: 데이터 로딩 중 스피너 및 진행 상황 표시

# Important Notes

## 코드 구조
- 코드는 모듈화하여 가독성 있게 작성해줘:
  - `github_manager.py`: GitHub 연동 로직
  - `rss_parser.py`: RSS 파싱 및 중복 제거
  - `gemini_analyzer.py`: Gemini API 호출 및 분석
  - `utils.py`: 공통 유틸리티 함수
  - `app.py`: Streamlit 메인 애플리케이션
  - `config.py`: 설정 관리

## 에러 처리
- RSS 파싱 실패: 개별 피드 실패 시 로그만 남기고 계속 진행
- API 호출 제한: Rate Limit 도달 시 대기 후 재시도 또는 사용자에게 알림
- GitHub API 오류: 네트워크 오류, 인증 오류 등 상세한 에러 메시지 표시
- JSON 파싱 오류: 파일 손상 시 기본값 반환 및 로그 기록

## 성능 최적화
- 세션 캐싱: `st.session_state`를 활용하여 같은 세션 내 중복 API 호출 방지
- 배치 처리: Gemini API 호출 시 여러 뉴스를 한 번에 처리하여 비용 절감
- 비동기 처리: 가능한 경우 비동기 방식으로 여러 RSS 피드 동시 수집

## 데이터 관리
- 중복 뉴스 처리: URL 기반으로 중복 제거
- 오래된 데이터 정리: 30일 이상 된 뉴스 데이터는 자동으로 삭제 (선택적)
- 백업: 중요한 업데이트 전에 기존 데이터 백업 고려

## 초기 설정
- 한국어 IT 뉴스 RSS 예시:
  - GeekNews: `https://feeds.feedburner.com/geeknews`
  - Naver IT News: `https://news.naver.com/main/rss/section.naver?sid=105`
  - 테크크런치 한국어: `https://kr.techcrunch.com/feed/`
  - 위 예시 URL을 `feeds.json` 초기 데이터로 사용할 수 있게 코드에 주석으로 남겨줘.

## 배포 전 체크리스트
- [ ] Streamlit Cloud Secrets 설정 완료
- [ ] GitHub Token 권한 확인 (repo 권한)
- [ ] Gemini API 키 유효성 확인
- [ ] 초기 JSON 파일들 GitHub 리포지토리에 생성
- [ ] RSS 피드 URL 유효성 테스트