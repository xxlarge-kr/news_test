"""
Streamlit 메인 애플리케이션
나만의 IT 뉴스룸 (My IT Newsroom)
"""
import streamlit as st
from datetime import datetime, timedelta
from github_manager import GithubManager
from rss_parser import collect_news_from_feeds, remove_duplicate_news, test_rss_feed
from gemini_analyzer import analyze_news_batch, generate_daily_briefing
from utils import (
    get_today_date, format_date_for_display, update_visitor_stats,
    get_cached_data, clear_cache, clean_old_news_data
)
from config import get_admin_password, get_default_feeds
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="나만의 IT 뉴스룸",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# GitHub Manager 초기화 (세션당 한 번만)
if 'github_manager' not in st.session_state:
    try:
        st.session_state.github_manager = GithubManager()
    except Exception as e:
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

github_manager = st.session_state.github_manager


def main_page():
    """메인 화면 (Newsroom)"""
    st.title("📰 나만의 IT 뉴스룸")
    
    # 접속자 통계 업데이트
    update_visitor_stats(github_manager)
    
    # 날짜 선택
    today = get_today_date()
    default_date = datetime.strptime(today, "%Y-%m-%d")
    
    selected_date = st.date_input(
        "날짜 선택",
        value=default_date,
        max_value=default_date
    )
    
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # 뉴스 데이터 로드
    with st.spinner("뉴스 데이터를 불러오는 중..."):
        news_data = get_cached_data("news_data", github_manager, "news_data.json", {})
    
    if date_str in news_data:
        date_news = news_data[date_str]
        
        # AI 브리핑 표시
        st.markdown("---")
        st.subheader(f"🤖 {format_date_for_display(date_str)} IT 주요 뉴스 브리핑")
        
        summary = date_news.get("summary", "브리핑이 없습니다.")
        st.markdown(summary)
        
        # 주요 뉴스 리스트
        st.markdown("---")
        st.subheader("📋 주요 뉴스 리스트")
        
        news_list = date_news.get("news", [])
        if news_list:
            for i, news in enumerate(news_list, 1):
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{i}. {news.get('title', '제목 없음')}**")
                        if news.get('summary'):
                            st.caption(news.get('summary', '')[:150] + "...")
                    with col2:
                        st.link_button("원문 보기", news.get('link', ''), use_container_width=True)
                    st.markdown("---")
        else:
            st.info("해당 날짜에 수집된 뉴스가 없습니다.")
    else:
        st.info(f"{format_date_for_display(date_str)}에 수집된 뉴스 데이터가 없습니다.")
        st.caption("관리자 대시보드에서 뉴스 수집을 실행해주세요.")


def admin_dashboard():
    """관리자 대시보드"""
    st.title("⚙️ 관리자 대시보드")
    
    # 접근 제어
    admin_password = get_admin_password()
    if admin_password:
        if 'admin_authenticated' not in st.session_state:
            st.session_state.admin_authenticated = False
        
        if not st.session_state.admin_authenticated:
            password = st.text_input("관리자 비밀번호", type="password")
            if st.button("로그인"):
                if password == admin_password:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("비밀번호가 올바르지 않습니다.")
            st.stop()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📊 접속자 통계", "🔗 RSS 피드 관리", "📥 데이터 수집"])
    
    # 탭 1: 접속자 통계
    with tab1:
        st.subheader("접속자 통계")
        
        try:
            stats = get_cached_data("stats", github_manager, "stats.json", {})
            
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("누적 접속자 수", f"{stats.get('total_visitors', 0):,}명")
                with col2:
                    today = get_today_date()
                    today_visitors = stats.get('daily_visitors', {}).get(today, 0)
                    st.metric("오늘 접속자 수", f"{today_visitors}명")
                
                # 일별 방문자 추이 그래프
                daily_visitors = stats.get('daily_visitors', {})
                if daily_visitors:
                    df = pd.DataFrame([
                        {"날짜": date, "방문자 수": count}
                        for date, count in sorted(daily_visitors.items())
                    ])
                    st.line_chart(df.set_index("날짜"))
            else:
                st.info("통계 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"통계 데이터 로드 실패: {e}")
    
    # 탭 2: RSS 피드 관리
    with tab2:
        st.subheader("RSS 피드 관리")
        
        try:
            feeds_data = get_cached_data("feeds", github_manager, "feeds.json", {})
            
            if not feeds_data or "feeds" not in feeds_data:
                # 초기 피드 설정
                feeds_data = {"feeds": get_default_feeds()}
                github_manager.write_json("feeds.json", feeds_data, "초기 RSS 피드 설정")
                clear_cache("feeds")
                st.rerun()
            
            feeds = feeds_data.get("feeds", [])
            
            # RSS 피드 목록 표시
            if feeds:
                st.markdown("### 등록된 RSS 피드")
                df = pd.DataFrame(feeds)
                st.dataframe(df, use_container_width=True)
                
                # RSS 추가
                st.markdown("### RSS 피드 추가")
                with st.form("add_feed_form"):
                    new_name = st.text_input("피드 이름")
                    new_url = st.text_input("RSS URL")
                    new_enabled = st.checkbox("활성화", value=True)
                    
                    if st.form_submit_button("추가"):
                        if new_name and new_url:
                            # URL 유효성 테스트
                            test_result = test_rss_feed(new_url)
                            if test_result["valid"]:
                                feeds.append({
                                    "name": new_name,
                                    "url": new_url,
                                    "enabled": new_enabled
                                })
                                feeds_data["feeds"] = feeds
                                github_manager.write_json("feeds.json", feeds_data, f"RSS 피드 추가: {new_name}")
                                clear_cache("feeds")
                                st.success(f"RSS 피드가 추가되었습니다: {new_name}")
                                st.rerun()
                            else:
                                st.error(f"RSS 피드 유효성 검증 실패: {test_result.get('error', 'Unknown error')}")
                        else:
                            st.warning("이름과 URL을 모두 입력해주세요.")
                
                # RSS 삭제
                st.markdown("### RSS 피드 삭제")
                if feeds:
                    feed_names = [f"{f['name']} ({f['url'][:50]}...)" for f in feeds]
                    selected_feed = st.selectbox("삭제할 피드 선택", feed_names)
                    
                    if st.button("삭제"):
                        selected_index = feed_names.index(selected_feed)
                        removed_feed = feeds.pop(selected_index)
                        feeds_data["feeds"] = feeds
                        github_manager.write_json("feeds.json", feeds_data, f"RSS 피드 삭제: {removed_feed['name']}")
                        clear_cache("feeds")
                        st.success(f"RSS 피드가 삭제되었습니다: {removed_feed['name']}")
                        st.rerun()
            
        except Exception as e:
            st.error(f"RSS 피드 관리 오류: {e}")
    
    # 탭 3: 데이터 수집
    with tab3:
        st.subheader("데이터 수집 및 분석")
        
        if st.button("🔄 뉴스 수집 및 분석 시작", type="primary", use_container_width=True):
            try:
                # 피드 로드
                feeds_data = get_cached_data("feeds", github_manager, "feeds.json", {})
                feeds = feeds_data.get("feeds", [])
                
                if not feeds:
                    st.error("등록된 RSS 피드가 없습니다. RSS 피드 관리에서 피드를 추가해주세요.")
                    st.stop()
                
                enabled_feeds = [f for f in feeds if f.get("enabled", True)]
                if not enabled_feeds:
                    st.error("활성화된 RSS 피드가 없습니다.")
                    st.stop()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.container()
                
                # 1. RSS 크롤링
                status_text.text("1/5 단계: RSS 피드에서 뉴스 수집 중...")
                progress_bar.progress(0.2)
                
                all_news = collect_news_from_feeds(enabled_feeds, max_age_hours=24)
                log_container.info(f"✅ {len(all_news)}개의 뉴스 수집 완료")
                
                if not all_news:
                    st.warning("수집된 뉴스가 없습니다.")
                    st.stop()
                
                # 2. 중복 제거
                status_text.text("2/5 단계: 중복 뉴스 제거 중...")
                progress_bar.progress(0.4)
                
                unique_news = remove_duplicate_news(all_news)
                log_container.info(f"✅ 중복 제거 완료: {len(unique_news)}개 뉴스")
                
                # 3. Gemini 분석
                status_text.text("3/5 단계: Gemini API로 뉴스 분석 중... (시간이 걸릴 수 있습니다)")
                progress_bar.progress(0.5)
                
                analyzed_news = analyze_news_batch(unique_news, batch_size=15)
                log_container.info(f"✅ 뉴스 분석 완료: {len(analyzed_news)}개")
                
                # 4. 일일 브리핑 생성
                status_text.text("4/5 단계: 일일 브리핑 생성 중...")
                progress_bar.progress(0.8)
                
                briefing = generate_daily_briefing(analyzed_news)
                
                # 5. 데이터 저장
                status_text.text("5/5 단계: GitHub에 데이터 저장 중...")
                progress_bar.progress(0.9)
                
                today = get_today_date()
                news_data = get_cached_data("news_data", github_manager, "news_data.json", {})
                
                news_data[today] = {
                    "date": today,
                    "summary": briefing,
                    "news": analyzed_news,
                    "collected_at": datetime.now().isoformat()
                }
                
                # 오래된 데이터 정리 (선택적)
                news_data = clean_old_news_data(news_data, days_to_keep=30)
                
                github_manager.write_json(
                    "news_data.json",
                    news_data,
                    f"뉴스 수집 및 분석: {today} ({len(analyzed_news)}개 뉴스)"
                )
                
                clear_cache("news_data")
                progress_bar.progress(1.0)
                status_text.text("✅ 완료!")
                
                st.success(f"✅ 뉴스 수집 및 분석이 완료되었습니다! ({len(analyzed_news)}개 뉴스)")
                st.balloons()
                
            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())


# 사이드바 네비게이션
st.sidebar.title("📰 나만의 IT 뉴스룸")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "메뉴 선택",
    ["📰 뉴스룸", "⚙️ 관리자 대시보드"],
    label_visibility="collapsed"
)

# 페이지 라우팅
if page == "📰 뉴스룸":
    main_page()
elif page == "⚙️ 관리자 대시보드":
    admin_dashboard()

# 사이드바 푸터
st.sidebar.markdown("---")
st.sidebar.caption("Made with ❤️ using Streamlit & Gemini")

