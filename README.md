# 나만의 IT 뉴스룸 (My IT Newsroom)

Streamlit과 Google Gemini API를 활용한 AI 기반 IT 뉴스 큐레이션 서비스입니다.

## 주요 기능

- 📰 **RSS 피드 수집**: 국내 IT 뉴스 RSS 피드에서 최신 뉴스 자동 수집
- 🤖 **AI 브리핑**: Google Gemini API를 활용한 일일 IT 뉴스 요약 및 분석
- 📊 **통계 대시보드**: 일별 방문자 통계 시각화
- ⚙️ **관리자 기능**: RSS 피드 관리 및 데이터 수집 제어
- 💾 **GitHub 기반 저장소**: 별도 DB 없이 GitHub Repository를 데이터베이스로 활용

## 기술 스택

- **Python 3.10+**
- **Streamlit**: 웹 UI
- **feedparser**: RSS 피드 파싱
- **google-generativeai**: Gemini API 연동
- **PyGithub**: GitHub Repository 파일 관리
- **pandas**: 데이터 처리

## 설치 및 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd 1209_test03
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.streamlit/secrets.toml` 파일을 생성하고 다음 내용을 입력하세요:

```toml
GITHUB_TOKEN = "your_github_personal_access_token"
REPO_NAME = "username/repository-name"
GEMINI_API_KEY = "your_gemini_api_key"
ADMIN_PASSWORD = "your_admin_password"  # 선택사항
```

#### GitHub Token 생성 방법

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. `repo` 권한 선택
4. 토큰 생성 후 복사

#### Gemini API Key 발급 방법

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. API Key 생성
3. 키 복사

### 4. GitHub Repository 초기 설정

데이터 저장을 위한 JSON 파일들을 GitHub Repository에 생성해야 합니다:

- `feeds.json`: RSS 피드 목록
- `news_data.json`: 수집된 뉴스 데이터
- `stats.json`: 접속자 통계

앱을 처음 실행하면 자동으로 초기 파일이 생성됩니다.

## 실행 방법

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하세요.

## 배포 (Streamlit Cloud)

1. GitHub에 코드 푸시
2. [Streamlit Cloud](https://streamlit.io/cloud)에서 앱 연결
3. Secrets 설정:
   - `GITHUB_TOKEN`
   - `REPO_NAME`
   - `GEMINI_API_KEY`
   - `ADMIN_PASSWORD` (선택사항)

## 사용 방법

### 메인 화면 (뉴스룸)

- 날짜를 선택하여 해당 날짜의 AI 브리핑과 주요 뉴스를 확인할 수 있습니다.
- 기본값은 오늘 날짜입니다.

### 관리자 대시보드

1. **접속자 통계**: 일별 방문자 추이 그래프 및 누적 접속자 수 확인
2. **RSS 피드 관리**: 
   - RSS 피드 추가/삭제
   - 피드 활성화/비활성화
   - 피드 URL 유효성 테스트
3. **데이터 수집**: 
   - "뉴스 수집 및 분석 시작" 버튼 클릭
   - 최근 24시간 내 뉴스 자동 수집
   - Gemini API로 분석 및 요약
   - 결과를 GitHub에 저장

## 파일 구조

```
.
├── app.py                 # Streamlit 메인 애플리케이션
├── config.py              # 설정 관리
├── github_manager.py      # GitHub 연동 모듈
├── rss_parser.py          # RSS 파싱 모듈
├── gemini_analyzer.py     # Gemini API 분석 모듈
├── utils.py               # 공통 유틸리티 함수
├── requirements.txt       # Python 의존성
├── .streamlit/
│   └── secrets.toml       # 환경 변수 (Git에 커밋하지 않음)
└── README.md              # 이 파일
```

## 주의사항

- GitHub API Rate Limit: 시간당 5,000회 요청 제한 (인증된 사용자 기준)
- Gemini API 사용량에 따라 비용이 발생할 수 있습니다.
- RSS 피드 URL이 변경되거나 접근 불가능할 경우 수집이 실패할 수 있습니다.

## 라이선스

MIT License

