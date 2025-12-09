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
import os
import logging
from logging.handlers import RotatingFileHandler

# 로깅 설정
def setup_logging():
    """로깅 설정 초기화"""
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 로그 파일 경로
    log_file = os.path.join(logs_dir, "app.log")
    
    # 로거 설정
    logger = logging.getLogger("newsroom_app")
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()
    
    # 파일 핸들러 (회전 로그 파일, 최대 10MB, 5개 파일 보관)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 로거 초기화
app_logger = setup_logging()

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
        app_logger.info("GitHub Manager 초기화 시작")
        st.session_state.github_manager = GithubManager()
        app_logger.info("GitHub Manager 초기화 완료")
    except Exception as e:
        app_logger.error(f"GitHub 연결 실패: {e}", exc_info=True)
        st.error(f"GitHub 연결 실패: {e}")
        st.stop()

github_manager = st.session_state.github_manager


def main_page():
    """메인 화면 (Newsroom)"""
    app_logger.info("메인 페이지 접속")
    st.title("📰 나만의 IT 뉴스룸")
    
    # 접속자 통계 업데이트
    try:
        app_logger.debug("접속자 통계 업데이트 시작")
        update_visitor_stats(github_manager)
        app_logger.debug("접속자 통계 업데이트 완료")
    except Exception as e:
        app_logger.error(f"접속자 통계 업데이트 실패: {e}", exc_info=True)
    
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
        
        # AI 브리핑 표시 - Top 3 뉴스
        st.markdown("---")
        st.subheader(f"🤖 {format_date_for_display(date_str)} IT 주요 뉴스 브리핑")
        
        # Top 3 뉴스 데이터 확인
        briefing_data = date_news.get("briefing", {})
        top3_news = briefing_data.get("top3_news", [])
        markdown_text = briefing_data.get("markdown", date_news.get("summary", ""))
        
        if top3_news:
            # Top 3 뉴스를 카드 형태로 표시
            for idx, news in enumerate(top3_news, 1):
                with st.container():
                    # 카드 스타일
                    st.markdown(f"""
                    <div style="
                        border: 2px solid #e0e0e0;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 15px 0;
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    ">
                        <h3 style="color: #2c3e50; margin-top: 0;">🏆 Top {idx}: {news.get('title', '제목 없음')}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 핵심 요약
                    st.markdown("#### 📋 핵심 요약")
                    st.info(news.get('summary', '요약 없음'))
                    
                    # 인사이트
                    st.markdown("#### 💡 인사이트")
                    st.markdown(news.get('insights', '인사이트 없음'))
                    
                    # 연관 기술 (배지 형태)
                    related_tech = news.get('related_tech', [])
                    if related_tech:
                        st.markdown("#### 🔖 연관 기술")
                        tech_badges = " ".join([f"`{tech}`" for tech in related_tech])
                        st.markdown(tech_badges)
                    
                    # 원문 링크
                    if news.get('link'):
                        st.link_button("🔗 원문 보기", news.get('link'), use_container_width=True, type="primary")
                    
                    st.markdown("---")
        else:
            # 기존 마크다운 형식 표시 (하위 호환성)
            st.markdown(markdown_text)
        
        # 전체 뉴스 리스트 (접을 수 있게)
        with st.expander("📋 전체 뉴스 리스트 보기", expanded=False):
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
            log_start_time = datetime.now()
            app_logger.info("=" * 80)
            app_logger.info(f"뉴스 수집 및 분석 시작 - {log_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            app_logger.info("=" * 80)
            
            try:
                # 피드 로드
                app_logger.debug("RSS 피드 목록 로드 시작")
                feeds_data = get_cached_data("feeds", github_manager, "feeds.json", {})
                feeds = feeds_data.get("feeds", [])
                app_logger.info(f"등록된 RSS 피드 수: {len(feeds)}")
                
                if not feeds:
                    app_logger.warning("등록된 RSS 피드가 없습니다")
                    st.error("등록된 RSS 피드가 없습니다. RSS 피드 관리에서 피드를 추가해주세요.")
                    st.stop()
                
                enabled_feeds = [f for f in feeds if f.get("enabled", True)]
                app_logger.info(f"활성화된 RSS 피드 수: {len(enabled_feeds)}")
                
                if not enabled_feeds:
                    app_logger.warning("활성화된 RSS 피드가 없습니다")
                    st.error("활성화된 RSS 피드가 없습니다.")
                    st.stop()
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.container()
                
                # 1. RSS 크롤링
                app_logger.info("1/5 단계: RSS 피드에서 뉴스 수집 시작")
                status_text.text("1/5 단계: RSS 피드에서 뉴스 수집 중...")
                progress_bar.progress(0.2)
                
                all_news = collect_news_from_feeds(enabled_feeds, max_age_hours=24)
                app_logger.info(f"✅ {len(all_news)}개의 뉴스 수집 완료")
                log_container.info(f"✅ {len(all_news)}개의 뉴스 수집 완료")
                
                if not all_news:
                    app_logger.warning("수집된 뉴스가 없습니다")
                    st.warning("수집된 뉴스가 없습니다.")
                    st.stop()
                
                # 2. 중복 제거
                app_logger.info("2/5 단계: 중복 뉴스 제거 시작")
                status_text.text("2/5 단계: 중복 뉴스 제거 중...")
                progress_bar.progress(0.4)
                
                unique_news = remove_duplicate_news(all_news)
                app_logger.info(f"✅ 중복 제거 완료: {len(unique_news)}개 뉴스 (제거: {len(all_news) - len(unique_news)}개)")
                log_container.info(f"✅ 중복 제거 완료: {len(unique_news)}개 뉴스")
                
                # 3. Top 3 뉴스 선별 및 분석 (모든 뉴스를 한 번에 분석)
                app_logger.info(f"3/4 단계: 모든 뉴스를 묶어서 Top 3 선별 및 분석 시작 (총 {len(unique_news)}개)")
                status_text.text("3/4 단계: 참신한 Top 3 뉴스 선별 및 분석 중... (시간이 걸릴 수 있습니다)")
                progress_bar.progress(0.6)
                
                log_container.info(f"📊 {len(unique_news)}개의 뉴스를 한 번에 분석하여 Top 3를 선별합니다...")
                
                briefing_result = generate_daily_briefing(unique_news)
                top3_count = len(briefing_result.get('top3_news', []))
                app_logger.info(f"✅ Top 3 뉴스 선별 및 분석 완료: {top3_count}개")
                log_container.info(f"✅ Top 3 뉴스 선별 완료: {top3_count}개")
                
                # 분석 결과 표시
                if top3_count > 0:
                    st.markdown("---")
                    st.subheader("📰 선별된 Top 3 뉴스")
                    analysis_results_container = st.container()
                    
                    with analysis_results_container:
                        for idx, news in enumerate(briefing_result.get('top3_news', []), 1):
                            with st.expander(f"🏆 Top {idx}: {news.get('title', '제목 없음')}", expanded=(idx == 1)):
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    st.markdown("**📋 핵심 요약**")
                                    summary = news.get('summary', '요약 없음')
                                    if summary:
                                        st.info(summary)
                                    else:
                                        st.warning("요약 없음")
                                
                                with col2:
                                    st.markdown("**💡 인사이트**")
                                    insights = news.get('insights', '인사이트 없음')
                                    if insights:
                                        st.markdown(insights)
                                    else:
                                        st.info("인사이트 없음")
                                
                                # 연관 기술 배지
                                related_tech = news.get('related_tech', [])
                                if related_tech:
                                    st.markdown("**🔖 연관 기술**")
                                    tech_badges = " ".join([f"`{tech}`" for tech in related_tech])
                                    st.markdown(tech_badges)
                                
                                if news.get('link'):
                                    st.link_button("🔗 원문 보기", news.get('link'), use_container_width=True, type="primary")
                                
                                st.markdown("---")
                
                # 분석된 뉴스는 원본 뉴스 리스트 사용 (개별 분석 없음)
                analyzed_news = unique_news
                
                # 4. 데이터 저장
                app_logger.info("4/4 단계: GitHub에 데이터 저장 시작")
                status_text.text("4/4 단계: GitHub에 데이터 저장 중...")
                progress_bar.progress(0.9)
                
                today = get_today_date()
                news_data = get_cached_data("news_data", github_manager, "news_data.json", {})
                
                news_data[today] = {
                    "date": today,
                    "summary": briefing_result.get("markdown", ""),  # 하위 호환성 유지
                    "briefing": briefing_result,  # Top 3 뉴스 정보 포함
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
                
                # 최종 로그
                log_end_time = datetime.now()
                duration = (log_end_time - log_start_time).total_seconds()
                app_logger.info(f"✅ 전체 프로세스 완료 (소요 시간: {duration:.1f}초)")
                app_logger.info("=" * 80)
                
                st.success(f"✅ 뉴스 수집 및 분석이 완료되었습니다! ({len(analyzed_news)}개 뉴스, 소요 시간: {duration:.1f}초)")
                
                # 로그 파일 정보 표시
                log_file_path = os.path.join("logs", "app.log")
                if os.path.exists(log_file_path):
                    st.info(f"📄 로그 파일: `{log_file_path}`")
                    with open(log_file_path, "r", encoding="utf-8") as f:
                        log_content = f.read()
                        # 최근 로그만 표시 (마지막 100줄)
                        recent_logs = "\n".join(log_content.split("\n")[-100:])
                        st.download_button(
                            label="📥 최근 로그 다운로드 (최근 100줄)",
                            data=recent_logs,
                            file_name=f"recent_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                            mime="text/plain"
                        )
                
                st.balloons()
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                app_logger.error(f"뉴스 수집 및 분석 중 오류 발생: {e}", exc_info=True)
                app_logger.error(f"상세 오류 추적:\n{error_trace}")
                st.error(f"❌ 오류 발생: {e}")
                st.code(error_trace)


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

