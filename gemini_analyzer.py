"""
Gemini API 분석 모듈
Google Gemini API를 사용하여 뉴스 요약 및 분석
"""
import google.generativeai as genai
from typing import List, Dict, Any
import time
import logging
from config import get_gemini_api_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini API 초기화 플래그
_api_configured = False


def _configure_api():
    """Gemini API 초기화 (지연 초기화)"""
    global _api_configured
    if not _api_configured:
        try:
            genai.configure(api_key=get_gemini_api_key())
            _api_configured = True
        except Exception as e:
            logger.error(f"Gemini API 초기화 실패: {e}")
            raise


def analyze_news_batch(news_list: List[Dict[str, Any]], batch_size: int = 15) -> List[Dict[str, Any]]:
    """
    뉴스 배치를 Gemini API로 분석
    
    Args:
        news_list: 분석할 뉴스 리스트
        batch_size: 한 번에 처리할 뉴스 개수 (기본값: 15)
        
    Returns:
        분석 결과가 추가된 뉴스 리스트
    """
    _configure_api()
    model = genai.GenerativeModel('gemini-pro')
    analyzed_news = []
    
    # 배치로 나누기
    for i in range(0, len(news_list), batch_size):
        batch = news_list[i:i + batch_size]
        logger.info(f"뉴스 배치 분석 중: {i+1}-{min(i+batch_size, len(news_list))}/{len(news_list)}")
        
        for news in batch:
            try:
                analyzed_item = analyze_single_news(news, model)
                analyzed_news.append(analyzed_item)
                
                # Rate Limit 방지를 위한 지연
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"뉴스 분석 실패 ({news.get('title', 'Unknown')}): {e}")
                # 분석 실패해도 기본 정보는 유지
                analyzed_news.append({
                    **news,
                    "summary": "분석 중 오류가 발생했습니다.",
                    "insights": ""
                })
    
    return analyzed_news


def analyze_single_news(news: Dict[str, Any], model=None) -> Dict[str, Any]:
    """
    단일 뉴스 분석
    
    Args:
        news: 뉴스 딕셔너리
        model: Gemini 모델 (None이면 새로 생성)
        
    Returns:
        분석 결과가 추가된 뉴스 딕셔너리
    """
    _configure_api()
    if model is None:
        model = genai.GenerativeModel('gemini-pro')
    
    title = news.get("title", "")
    description = news.get("description", "")
    
    # 프롬프트 구성
    prompt = f"""다음 IT 뉴스를 IT 트렌드 관점에서 분석해주세요.

제목: {title}
내용: {description[:500]}  # 내용이 길면 500자로 제한

다음 형식으로 응답해주세요:
1. 핵심 내용 3줄 요약 (각 줄은 간결하게)
2. IT 트렌드 관점에서의 인사이트 (2-3문장)

응답 형식:
요약:
- [첫 번째 핵심 내용]
- [두 번째 핵심 내용]
- [세 번째 핵심 내용]

인사이트:
[IT 트렌드 관점에서의 인사이트를 2-3문장으로 작성]
"""
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                }
            )
            
            # 응답 파싱
            result_text = response.text
            
            # 요약과 인사이트 분리
            summary_lines = []
            insights = ""
            
            lines = result_text.split('\n')
            in_summary = False
            in_insights = False
            
            for line in lines:
                line = line.strip()
                if '요약' in line or 'Summary' in line:
                    in_summary = True
                    in_insights = False
                    continue
                elif '인사이트' in line or 'Insight' in line:
                    in_summary = False
                    in_insights = True
                    continue
                
                if in_summary and line and (line.startswith('-') or line.startswith('•')):
                    summary_lines.append(line.lstrip('- •').strip())
                elif in_insights and line:
                    insights += line + " "
            
            summary = "\n".join(summary_lines) if summary_lines else result_text[:200]
            insights = insights.strip() if insights else "인사이트를 생성할 수 없습니다."
            
            return {
                **news,
                "summary": summary,
                "insights": insights
            }
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # 지수 백오프
                logger.warning(f"API 호출 실패, {wait_time}초 후 재시도 ({retry_count}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"뉴스 분석 최종 실패 ({title}): {e}")
                raise
    
    # 모든 재시도 실패
    return {
        **news,
        "summary": "분석 중 오류가 발생했습니다.",
        "insights": ""
    }


def generate_daily_briefing(news_list: List[Dict[str, Any]]) -> str:
    """
    일일 브리핑 마크다운 생성
    
    Args:
        news_list: 분석된 뉴스 리스트
        
    Returns:
        마크다운 형식의 브리핑 텍스트
    """
    if not news_list:
        return "오늘 수집된 뉴스가 없습니다."
    
    _configure_api()
    model = genai.GenerativeModel('gemini-pro')
    
    # 뉴스 요약 정보 구성
    news_summaries = []
    for i, news in enumerate(news_list[:20], 1):  # 최대 20개만 사용
        news_summaries.append(f"{i}. {news.get('title', '제목 없음')}")
        if news.get('summary'):
            news_summaries.append(f"   요약: {news.get('summary', '')[:100]}")
    
    news_text = "\n".join(news_summaries)
    
    prompt = f"""다음은 오늘 수집된 IT 뉴스 목록입니다. 이를 바탕으로 "오늘의 IT 주요 뉴스 브리핑"을 마크다운 형식으로 작성해주세요.

뉴스 목록:
{news_text}

요구사항:
1. 전체적인 IT 트렌드와 주요 이슈를 파악하여 종합적인 브리핑 작성
2. 마크다운 형식 사용 (제목, 리스트, 강조 등)
3. 3-5개의 주요 섹션으로 구성
4. 각 섹션은 간결하고 명확하게 작성
5. 한국어로 작성

마크다운 형식으로 응답해주세요:
"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 1500,
            }
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"브리핑 생성 실패: {e}")
        return f"""# 오늘의 IT 주요 뉴스 브리핑

오늘 {len(news_list)}개의 뉴스가 수집되었습니다.

## 주요 뉴스
{chr(10).join([f"- {news.get('title', '제목 없음')}" for news in news_list[:10]])}
"""

