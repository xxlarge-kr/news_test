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


def analyze_news_batch(news_list: List[Dict[str, Any]], batch_size: int = 15, progress_callback=None, result_callback=None) -> List[Dict[str, Any]]:
    """
    뉴스 배치를 Gemini API로 분석
    
    Args:
        news_list: 분석할 뉴스 리스트
        batch_size: 한 번에 처리할 뉴스 개수 (기본값: 15)
        progress_callback: 진행 상황 콜백 함수 (current, total) -> None
        
    Returns:
        분석 결과가 추가된 뉴스 리스트
    """
    _configure_api()
    model = genai.GenerativeModel('gemini-2.5-flash')
    analyzed_news = []
    total_news = len(news_list)
    
    # 배치로 나누기
    for i in range(0, len(news_list), batch_size):
        batch = news_list[i:i + batch_size]
        logger.info(f"뉴스 배치 분석 중: {i+1}-{min(i+batch_size, len(news_list))}/{len(news_list)}")
        
        for idx, news in enumerate(batch):
            try:
                current_index = i + idx + 1
                logger.debug(f"뉴스 분석 시작 [{current_index}/{total_news}]: {news.get('title', 'Unknown')[:50]}")
                
                if progress_callback:
                    progress_callback(current_index, total_news)
                
                analyzed_item = analyze_single_news(news, model)
                
                # 분석 결과 검증
                if analyzed_item.get("summary", "").startswith("분석 중 오류가 발생했습니다"):
                    error_msg = analyzed_item.get("error", "알 수 없는 오류")
                    logger.warning(f"뉴스 분석 실패 - 제목: {news.get('title', 'Unknown')[:50]}, 오류: {error_msg}")
                    # 오류 정보를 포함한 결과 반환
                    analyzed_item["error"] = error_msg
                else:
                    logger.debug(f"뉴스 분석 성공 [{current_index}/{total_news}]: {news.get('title', 'Unknown')[:50]}")
                
                analyzed_news.append(analyzed_item)
                
                # 분석 결과 콜백 호출
                if result_callback:
                    result_callback(analyzed_item, current_index, total_news)
                
                # Rate Limit 방지를 위한 지연
                time.sleep(0.5)
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"뉴스 분석 중 예외 발생 [{current_index}/{total_news}] - 제목: {news.get('title', 'Unknown')[:50]}")
                logger.error(f"오류 타입: {type(e).__name__}, 메시지: {str(e)}")
                logger.debug(f"상세 오류:\n{error_trace}")
                # 분석 실패해도 기본 정보는 유지하되, 상세 오류 정보 포함
                analyzed_news.append({
                    **news,
                    "summary": f"분석 중 오류가 발생했습니다: {str(e)}",
                    "insights": "",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "error_trace": error_trace
                })
                current_index = i + idx + 1
                if progress_callback:
                    progress_callback(current_index, total_news)
        
        logger.info(f"배치 분석 완료: {i+1}-{min(i+batch_size, len(news_list))}/{len(news_list)}")
    
    logger.info(f"전체 뉴스 분석 완료: {len(analyzed_news)}/{total_news}개")
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
        model = genai.GenerativeModel('gemini-2.5-flash')
    
    title = news.get("title", "") or "제목 없음"
    description = news.get("description", "") or news.get("summary", "") or ""
    
    # description이 너무 길면 제한
    if description:
        description = description[:1000]  # 1000자로 제한
    else:
        description = "내용 없음"
    
    # 프롬프트 구성
    prompt = f"""다음 IT 뉴스를 IT 트렌드 관점에서 분석해주세요.

제목: {title}
내용: {description}

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
            logger.debug(f"Gemini API 호출 시도 {retry_count + 1}/{max_retries} - 제목: {title[:50]}")
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 500,
                }
            )
            
            # 응답 파싱 - 안전하게 처리
            if not response:
                raise ValueError("Gemini API 응답이 없습니다")
            
            # response.text가 없을 수 있으므로 안전하게 처리
            try:
                result_text = response.text
            except AttributeError:
                # response.candidates를 확인
                if hasattr(response, 'candidates') and response.candidates:
                    if hasattr(response.candidates[0], 'content'):
                        if hasattr(response.candidates[0].content, 'parts') and response.candidates[0].content.parts:
                            result_text = response.candidates[0].content.parts[0].text
                        else:
                            raise ValueError("응답 파트가 없습니다")
                    else:
                        raise ValueError("응답에서 텍스트를 추출할 수 없습니다")
                else:
                    raise ValueError("응답 후보가 없습니다")
            
            if not result_text or not result_text.strip():
                raise ValueError("Gemini API 응답이 비어있습니다")
            
            logger.debug(f"Gemini API 응답 수신 성공 - 길이: {len(result_text)}자")
            
            # 요약과 인사이트 분리 - 더 유연한 파싱
            summary_lines = []
            insights = ""
            
            lines = result_text.split('\n')
            in_summary = False
            in_insights = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 섹션 헤더 감지
                if '요약' in line or 'Summary' in line or 'summary' in line.lower():
                    in_summary = True
                    in_insights = False
                    continue
                elif '인사이트' in line or 'Insight' in line or 'insight' in line.lower():
                    in_summary = False
                    in_insights = True
                    continue
                
                # 요약 부분 파싱
                if in_summary:
                    # 다양한 불릿 포인트 형식 지원
                    if line.startswith('-') or line.startswith('•') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                        clean_line = line.lstrip('- •*1234567890. ').strip()
                        if clean_line:
                            summary_lines.append(clean_line)
                    elif line and not line.startswith('인사이트') and not line.startswith('Insight'):
                        # 불릿 포인트가 없어도 내용이 있으면 추가
                        if len(summary_lines) < 3:
                            summary_lines.append(line)
                
                # 인사이트 부분 파싱
                elif in_insights:
                    if line and not line.startswith('요약') and not line.startswith('Summary'):
                        insights += line + " "
            
            # 요약이 없으면 전체 텍스트에서 추출 시도
            if not summary_lines:
                # 전체 텍스트를 문장 단위로 나누어 처음 3개 사용
                sentences = result_text.split('.')[:3]
                summary_lines = [s.strip() for s in sentences if s.strip()]
            
            summary = "\n".join(summary_lines[:3]) if summary_lines else result_text[:300]
            insights = insights.strip() if insights else "IT 트렌드 관점에서의 인사이트를 생성했습니다."
            
            logger.debug(f"뉴스 분석 완료 - 제목: {title[:50]}, 요약 길이: {len(summary)}, 인사이트 길이: {len(insights)}")
            
            return {
                **news,
                "summary": summary,
                "insights": insights
            }
            
        except Exception as e:
            retry_count += 1
            import traceback
            error_trace = traceback.format_exc()
            
            if retry_count < max_retries:
                wait_time = min(2 ** retry_count, 10)  # 최대 10초로 제한
                logger.warning(f"API 호출 실패 ({title[:50]}), {wait_time}초 후 재시도 ({retry_count}/{max_retries})")
                logger.warning(f"오류 타입: {type(e).__name__}, 메시지: {str(e)}")
                time.sleep(wait_time)
            else:
                logger.error(f"뉴스 분석 최종 실패 - 제목: {title[:50]}")
                logger.error(f"오류 타입: {type(e).__name__}")
                logger.error(f"오류 메시지: {str(e)}")
                logger.debug(f"상세 오류:\n{error_trace}")
                # 예외를 raise하지 않고 오류 정보를 포함한 결과 반환
                return {
                    **news,
                    "summary": f"분석 중 오류가 발생했습니다: {str(e)}",
                    "insights": "",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "error_trace": error_trace
                }
    
    # 모든 재시도 실패 (이 부분은 도달하지 않아야 함)
    logger.error(f"뉴스 분석 실패 - 예상치 못한 오류 (제목: {title[:50]})")
    return {
        **news,
        "summary": "분석 중 오류가 발생했습니다: 예상치 못한 오류",
        "insights": "",
        "error": "예상치 못한 오류",
        "error_type": "UnknownError"
    }


def parse_top3_news(markdown_text: str, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    마크다운 텍스트에서 Top 3 뉴스 정보 파싱
    
    Args:
        markdown_text: Gemini가 생성한 마크다운 텍스트
        news_list: 원본 뉴스 리스트 (링크 매칭용)
        
    Returns:
        Top 3 뉴스 리스트
    """
    top3_news = []
    
    # Top 1, 2, 3 섹션 분리
    sections = []
    for i in range(1, 4):
        pattern = f"## Top {i}:"
        if pattern in markdown_text:
            start_idx = markdown_text.find(pattern)
            if i < 3:
                next_pattern = f"## Top {i+1}:"
                end_idx = markdown_text.find(next_pattern)
                if end_idx == -1:
                    end_idx = len(markdown_text)
            else:
                end_idx = len(markdown_text)
            
            sections.append(markdown_text[start_idx:end_idx])
    
    for section in sections:
        news_item = {}
        
        # 제목 추출
        title_match = section.split('\n')[0].replace('## Top', '').replace(':', '').strip()
        if title_match:
            news_item['title'] = title_match
        
        # 핵심 요약 추출
        if '**핵심 요약:**' in section:
            summary_start = section.find('**핵심 요약:**') + len('**핵심 요약:**')
            summary_end = section.find('**인사이트:**', summary_start)
            if summary_end == -1:
                summary_end = section.find('**연관 기술:**', summary_start)
            summary = section[summary_start:summary_end].strip()
            news_item['summary'] = summary
        
        # 인사이트 추출
        if '**인사이트:**' in section:
            insights_start = section.find('**인사이트:**') + len('**인사이트:**')
            insights_end = section.find('**연관 기술:**', insights_start)
            if insights_end == -1:
                insights_end = len(section)
            insights = section[insights_start:insights_end].strip()
            news_item['insights'] = insights
        
        # 연관 기술 추출
        if '**연관 기술:**' in section:
            tech_start = section.find('**연관 기술:**') + len('**연관 기술:**')
            tech_text = section[tech_start:].strip()
            # 해시태그 추출
            import re
            tech_tags = re.findall(r'#(\w+)', tech_text)
            news_item['related_tech'] = tech_tags if tech_tags else []
        else:
            news_item['related_tech'] = []
        
        # 원본 뉴스에서 링크 찾기 (제목 매칭)
        if news_item.get('title'):
            for news in news_list:
                if news_item['title'] in news.get('title', '') or news.get('title', '') in news_item['title']:
                    news_item['link'] = news.get('link', '')
                    break
        
        if news_item.get('title'):
            top3_news.append(news_item)
    
    return top3_news


def generate_daily_briefing(news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    참신성 높은 Top 3 뉴스 선별 및 분석
    
    Args:
        news_list: 분석된 뉴스 리스트
        
    Returns:
        Top 3 뉴스 정보가 포함된 딕셔너리
        {
            "top3_news": [
                {
                    "title": "제목",
                    "summary": "핵심 요약",
                    "insights": "인사이트",
                    "related_tech": ["기술1", "기술2"],
                    "link": "링크"
                }
            ],
            "markdown": "마크다운 형식 텍스트"
        }
    """
    if not news_list:
        return {
            "top3_news": [],
            "markdown": "오늘 수집된 뉴스가 없습니다."
        }
    
    _configure_api()
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 뉴스 목록 구성 (최대 30개)
    news_items = []
    for i, news in enumerate(news_list[:30], 1):
        title = news.get('title', '제목 없음')
        description = news.get('description', '')[:200] or news.get('summary', '')[:200]
        link = news.get('link', '')
        news_items.append(f"{i}. 제목: {title}\n   내용: {description}\n   링크: {link}")
    
    news_text = "\n\n".join(news_items)
    
    prompt = f"""제공된 IT 뉴스 목록을 분석해. 그 중 가장 참신하고 혁신적인 뉴스 3건을 엄선해.

**선별 기준:**
- 참신성(Novelty)이 높고 혁신적인 뉴스만 선별
- 단순한 사건 사고나 일반적인 소식은 제외
- 기술적 혁신, 시장 변화, 새로운 트렌드와 관련된 뉴스 우선

**뉴스 목록:**
{news_text}

**출력 형식 (마크다운):**
각 선별된 뉴스에 대해 아래 형식으로 정확히 출력해줘:

## Top 1: [뉴스 제목]

**핵심 요약:**
[기사 내용을 1~2문장으로 요약]

**인사이트:**
[이 뉴스가 시장이나 업계에 미치는 영향 분석 (2-3문장)]

**연관 기술:**
#기술키워드1 #기술키워드2 #기술키워드3

---

## Top 2: [뉴스 제목]

**핵심 요약:**
[기사 내용을 1~2문장으로 요약]

**인사이트:**
[이 뉴스가 시장이나 업계에 미치는 영향 분석 (2-3문장)]

**연관 기술:**
#기술키워드1 #기술키워드2 #기술키워드3

---

## Top 3: [뉴스 제목]

**핵심 요약:**
[기사 내용을 1~2문장으로 요약]

**인사이트:**
[이 뉴스가 시장이나 업계에 미치는 영향 분석 (2-3문장)]

**연관 기술:**
#기술키워드1 #기술키워드2 #기술키워드3

위 형식을 정확히 따라 마크다운으로 출력해줘.
"""
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 2000,
            }
        )
        
        result_text = response.text
        
        # 마크다운에서 Top 3 뉴스 파싱
        top3_news = parse_top3_news(result_text, news_list)
        
        return {
            "top3_news": top3_news,
            "markdown": result_text
        }
        
    except Exception as e:
        logger.error(f"브리핑 생성 실패: {e}")
        import traceback
        logger.error(traceback.format_exc())
        news_titles = "\n".join([f"- {news.get('title', '제목 없음')}" for news in news_list[:10]])
        return {
            "top3_news": [],
            "markdown": f"# 오늘의 IT 주요 뉴스 브리핑\n\n오늘 {len(news_list)}개의 뉴스가 수집되었습니다.\n\n## 주요 뉴스\n{news_titles}"
        }


def parse_top3_news(markdown_text: str, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    마크다운 텍스트에서 Top 3 뉴스 정보 파싱
    
    Args:
        markdown_text: Gemini가 생성한 마크다운 텍스트
        news_list: 원본 뉴스 리스트 (링크 매칭용)
        
    Returns:
        Top 3 뉴스 리스트
    """
    top3_news = []
    
    # Top 1, 2, 3 섹션 분리
    sections = []
    for i in range(1, 4):
        pattern = f"## Top {i}:"
        if pattern in markdown_text:
            start_idx = markdown_text.find(pattern)
            if i < 3:
                next_pattern = f"## Top {i+1}:"
                end_idx = markdown_text.find(next_pattern)
                if end_idx == -1:
                    end_idx = len(markdown_text)
            else:
                end_idx = len(markdown_text)
            
            sections.append(markdown_text[start_idx:end_idx])
    
    for section in sections:
        news_item = {}
        
        # 제목 추출
        title_match = section.split('\n')[0].replace('## Top', '').replace(':', '').strip()
        if title_match:
            news_item['title'] = title_match
        
        # 핵심 요약 추출
        if '**핵심 요약:**' in section:
            summary_start = section.find('**핵심 요약:**') + len('**핵심 요약:**')
            summary_end = section.find('**인사이트:**', summary_start)
            if summary_end == -1:
                summary_end = section.find('**연관 기술:**', summary_start)
            summary = section[summary_start:summary_end].strip()
            news_item['summary'] = summary
        
        # 인사이트 추출
        if '**인사이트:**' in section:
            insights_start = section.find('**인사이트:**') + len('**인사이트:**')
            insights_end = section.find('**연관 기술:**', insights_start)
            if insights_end == -1:
                insights_end = len(section)
            insights = section[insights_start:insights_end].strip()
            news_item['insights'] = insights
        
        # 연관 기술 추출
        if '**연관 기술:**' in section:
            tech_start = section.find('**연관 기술:**') + len('**연관 기술:**')
            tech_text = section[tech_start:].strip()
            # 해시태그 추출
            import re
            tech_tags = re.findall(r'#(\w+)', tech_text)
            news_item['related_tech'] = tech_tags if tech_tags else []
        else:
            news_item['related_tech'] = []
        
        # 원본 뉴스에서 링크 찾기 (제목 매칭)
        if news_item.get('title'):
            for news in news_list:
                if news_item['title'] in news.get('title', '') or news.get('title', '') in news_item['title']:
                    news_item['link'] = news.get('link', '')
                    break
        
        if news_item.get('title'):
            top3_news.append(news_item)
    
    return top3_news

