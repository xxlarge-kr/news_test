"""
설정 관리 모듈
Streamlit Secrets에서 환경 변수를 가져옴
"""
import streamlit as st
from typing import Optional


def get_github_token() -> str:
    """GitHub Token 가져오기"""
    try:
        # Streamlit Cloud 또는 로컬 secrets.toml에서 읽기
        if "GITHUB_TOKEN" in st.secrets:
            return st.secrets["GITHUB_TOKEN"]
        else:
            raise ValueError("GITHUB_TOKEN이 Streamlit Secrets에 설정되지 않았습니다.\n로컬 실행 시: .streamlit/secrets.toml 파일을 확인하세요.\nStreamlit Cloud 실행 시: Streamlit Cloud의 Secrets 설정에서 GITHUB_TOKEN을 추가하세요.")
    except AttributeError:
        raise ValueError("Streamlit이 초기화되지 않았습니다. Streamlit 앱 내에서만 사용할 수 있습니다.")
    except KeyError:
        raise ValueError("GITHUB_TOKEN이 Streamlit Secrets에 설정되지 않았습니다.\n로컬 실행 시: .streamlit/secrets.toml 파일을 확인하세요.\nStreamlit Cloud 실행 시: Streamlit Cloud의 Secrets 설정에서 GITHUB_TOKEN을 추가하세요.")


def get_repo_name() -> str:
    """GitHub Repository 이름 가져오기 (예: 'username/repo-name')"""
    try:
        if "REPO_NAME" in st.secrets:
            return st.secrets["REPO_NAME"]
        else:
            raise ValueError("REPO_NAME이 Streamlit Secrets에 설정되지 않았습니다.\n로컬 실행 시: .streamlit/secrets.toml 파일을 확인하세요.\nStreamlit Cloud 실행 시: Streamlit Cloud의 Secrets 설정에서 REPO_NAME을 추가하세요.")
    except AttributeError:
        raise ValueError("Streamlit이 초기화되지 않았습니다. Streamlit 앱 내에서만 사용할 수 있습니다.")
    except KeyError:
        raise ValueError("REPO_NAME이 Streamlit Secrets에 설정되지 않았습니다.\n로컬 실행 시: .streamlit/secrets.toml 파일을 확인하세요.\nStreamlit Cloud 실행 시: Streamlit Cloud의 Secrets 설정에서 REPO_NAME을 추가하세요.")


def get_gemini_api_key() -> str:
    """Gemini API Key 가져오기"""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
        else:
            raise ValueError("GEMINI_API_KEY이 Streamlit Secrets에 설정되지 않았습니다.\n로컬 실행 시: .streamlit/secrets.toml 파일을 확인하세요.\nStreamlit Cloud 실행 시: Streamlit Cloud의 Secrets 설정에서 GEMINI_API_KEY을 추가하세요.")
    except AttributeError:
        raise ValueError("Streamlit이 초기화되지 않았습니다. Streamlit 앱 내에서만 사용할 수 있습니다.")
    except KeyError:
        raise ValueError("GEMINI_API_KEY이 Streamlit Secrets에 설정되지 않았습니다.\n로컬 실행 시: .streamlit/secrets.toml 파일을 확인하세요.\nStreamlit Cloud의 Secrets 설정에서 GEMINI_API_KEY을 추가하세요.")


def get_admin_password() -> Optional[str]:
    """관리자 비밀번호 가져오기 (선택사항)"""
    try:
        return st.secrets.get("ADMIN_PASSWORD", None)
    except Exception:
        return None


def get_default_feeds() -> list:
    """
    초기 RSS 피드 목록
    한국어 IT 뉴스 RSS 예시
    """
    return [
        {
            "name": "GeekNews",
            "url": "https://feeds.feedburner.com/geeknews",
            "enabled": True
        },
        {
            "name": "Naver IT News",
            "url": "https://news.naver.com/main/rss/section.naver?sid=105",
            "enabled": True
        },
        {
            "name": "TechCrunch Korea",
            "url": "https://kr.techcrunch.com/feed/",
            "enabled": True
        }
    ]

