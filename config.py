"""
설정 관리 모듈
Streamlit Secrets에서 환경 변수를 가져옴
"""
import streamlit as st
from typing import Optional


def get_github_token() -> str:
    """GitHub Token 가져오기"""
    try:
        return st.secrets["GITHUB_TOKEN"]
    except KeyError:
        raise ValueError("GITHUB_TOKEN이 Streamlit Secrets에 설정되지 않았습니다.")


def get_repo_name() -> str:
    """GitHub Repository 이름 가져오기 (예: 'username/repo-name')"""
    try:
        return st.secrets["REPO_NAME"]
    except KeyError:
        raise ValueError("REPO_NAME이 Streamlit Secrets에 설정되지 않았습니다.")


def get_gemini_api_key() -> str:
    """Gemini API Key 가져오기"""
    try:
        return st.secrets["GEMINI_API_KEY"]
    except KeyError:
        raise ValueError("GEMINI_API_KEY이 Streamlit Secrets에 설정되지 않았습니다.")


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

