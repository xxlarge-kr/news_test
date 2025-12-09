"""
공통 유틸리티 함수
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import streamlit as st


def get_today_date() -> str:
    """오늘 날짜를 YYYY-MM-DD 형식으로 반환"""
    return datetime.now().strftime("%Y-%m-%d")


def format_date_for_display(date_str: str) -> str:
    """날짜 문자열을 표시용 형식으로 변환"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y년 %m월 %d일")
    except:
        return date_str


def update_visitor_stats(github_manager) -> None:
    """
    접속자 통계 업데이트
    
    Args:
        github_manager: GithubManager 인스턴스
    """
    try:
        # 세션 ID 확인 (중복 방문 방지)
        if 'visitor_tracked' not in st.session_state:
            st.session_state.visitor_tracked = True
            
            # stats.json 읽기
            stats = github_manager.read_json("stats.json")
            
            if not stats:
                stats = {
                    "daily_visitors": {},
                    "total_visitors": 0,
                    "last_updated": ""
                }
            
            # 오늘 날짜
            today = get_today_date()
            
            # 일일 방문자 수 증가
            if today not in stats["daily_visitors"]:
                stats["daily_visitors"][today] = 0
            stats["daily_visitors"][today] += 1
            
            # 누적 방문자 수 증가
            stats["total_visitors"] = stats.get("total_visitors", 0) + 1
            stats["last_updated"] = datetime.now().isoformat()
            
            # GitHub에 저장
            github_manager.write_json("stats.json", stats, f"방문자 통계 업데이트: {today}")
            
    except Exception as e:
        # 통계 업데이트 실패해도 앱은 계속 동작
        st.error(f"통계 업데이트 실패: {e}")


def get_cached_data(key: str, github_manager, file_path: str, default: Any = None) -> Any:
    """
    세션 캐시를 활용한 데이터 가져오기
    
    Args:
        key: 캐시 키
        github_manager: GithubManager 인스턴스
        file_path: GitHub 파일 경로
        default: 기본값
        
    Returns:
        캐시된 데이터 또는 GitHub에서 읽은 데이터
    """
    cache_key = f"cache_{key}"
    
    # 캐시 확인
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # GitHub에서 읽기
    try:
        data = github_manager.read_json(file_path)
        if not data:
            data = default if default is not None else {}
        
        # 캐시에 저장
        st.session_state[cache_key] = data
        return data
        
    except Exception as e:
        st.error(f"데이터 로드 실패 ({file_path}): {e}")
        return default if default is not None else {}


def clear_cache(key: Optional[str] = None) -> None:
    """
    캐시 클리어
    
    Args:
        key: 특정 키만 클리어 (None이면 모든 캐시 클리어)
    """
    if key:
        cache_key = f"cache_{key}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
    else:
        # 모든 캐시 클리어
        keys_to_remove = [k for k in st.session_state.keys() if k.startswith("cache_")]
        for k in keys_to_remove:
            del st.session_state[k]


def clean_old_news_data(news_data: Dict[str, Any], days_to_keep: int = 30) -> Dict[str, Any]:
    """
    오래된 뉴스 데이터 정리
    
    Args:
        news_data: 뉴스 데이터 딕셔너리
        days_to_keep: 유지할 일수 (기본값: 30일)
        
    Returns:
        정리된 뉴스 데이터
    """
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")
    
    cleaned_data = {}
    for date_str, data in news_data.items():
        if date_str >= cutoff_str:
            cleaned_data[date_str] = data
    
    return cleaned_data

