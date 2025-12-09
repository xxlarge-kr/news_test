"""
RSS 파싱 모듈
feedparser를 사용하여 RSS 피드에서 뉴스 수집 및 중복 제거
"""
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_rss_feed(feed_url: str, max_age_hours: int = 24) -> List[Dict[str, Any]]:
    """
    RSS 피드에서 뉴스 파싱
    
    Args:
        feed_url: RSS 피드 URL
        max_age_hours: 수집할 최대 뉴스 나이 (시간 단위, 기본값: 24시간)
        
    Returns:
        뉴스 아이템 리스트
    """
    try:
        # RSS 피드 파싱
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"RSS 피드 파싱 경고 ({feed_url}): {feed.bozo_exception}")
        
        news_items = []
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        for entry in feed.entries:
            try:
                # 발행 시간 파싱
                published_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_time = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published_time = datetime(*entry.updated_parsed[:6])
                else:
                    # 발행 시간이 없으면 현재 시간으로 설정
                    published_time = datetime.now()
                
                # 최근 뉴스만 수집
                if published_time < cutoff_time:
                    continue
                
                # 뉴스 아이템 생성
                news_item = {
                    "title": entry.get("title", "제목 없음"),
                    "link": entry.get("link", ""),
                    "published": published_time.isoformat(),
                    "description": entry.get("description", ""),
                    "source": feed.feed.get("title", "Unknown")
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                logger.error(f"뉴스 아이템 파싱 오류 ({feed_url}): {e}")
                continue
        
        logger.info(f"RSS 피드에서 {len(news_items)}개의 뉴스 수집: {feed_url}")
        return news_items
        
    except Exception as e:
        logger.error(f"RSS 피드 파싱 실패 ({feed_url}): {e}")
        return []


def collect_news_from_feeds(feeds: List[Dict[str, Any]], max_age_hours: int = 24) -> List[Dict[str, Any]]:
    """
    여러 RSS 피드에서 뉴스 수집
    
    Args:
        feeds: RSS 피드 목록 (각 피드는 'name', 'url', 'enabled' 키를 가짐)
        max_age_hours: 수집할 최대 뉴스 나이 (시간 단위)
        
    Returns:
        모든 피드에서 수집한 뉴스 리스트
    """
    all_news = []
    
    for feed in feeds:
        if not feed.get("enabled", True):
            continue
        
        feed_url = feed.get("url", "")
        if not feed_url:
            logger.warning(f"RSS 피드 URL이 없습니다: {feed.get('name', 'Unknown')}")
            continue
        
        try:
            news_items = parse_rss_feed(feed_url, max_age_hours)
            all_news.extend(news_items)
        except Exception as e:
            logger.error(f"피드 수집 실패 ({feed.get('name', 'Unknown')}): {e}")
            continue
    
    return all_news


def remove_duplicate_news(news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    URL 기반으로 중복 뉴스 제거
    
    Args:
        news_list: 뉴스 리스트
        
    Returns:
        중복이 제거된 뉴스 리스트
    """
    seen_urls = set()
    unique_news = []
    
    for news in news_list:
        url = news.get("link", "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_news.append(news)
    
    removed_count = len(news_list) - len(unique_news)
    if removed_count > 0:
        logger.info(f"중복 뉴스 {removed_count}개 제거")
    
    return unique_news


def test_rss_feed(feed_url: str) -> Dict[str, Any]:
    """
    RSS 피드 유효성 테스트
    
    Args:
        feed_url: 테스트할 RSS 피드 URL
        
    Returns:
        테스트 결과 딕셔너리 (valid, title, item_count, error)
    """
    result = {
        "valid": False,
        "title": "",
        "item_count": 0,
        "error": None
    }
    
    try:
        feed = feedparser.parse(feed_url)
        
        if feed.bozo and feed.bozo_exception:
            result["error"] = str(feed.bozo_exception)
            return result
        
        if not feed.entries:
            result["error"] = "RSS 피드에 항목이 없습니다"
            return result
        
        result["valid"] = True
        result["title"] = feed.feed.get("title", "Unknown")
        result["item_count"] = len(feed.entries)
        
    except Exception as e:
        result["error"] = str(e)
    
    return result

