"""
GitHub 연동 모듈
PyGithub를 사용하여 리포지토리의 JSON 파일을 읽고 쓰기
"""
import json
import base64
from typing import Dict, Any, Optional
from github import Github
from github.GithubException import GithubException
import time
from config import get_github_token, get_repo_name


class GithubManager:
    """GitHub 리포지토리와 상호작용하는 클래스"""
    
    def __init__(self):
        """GitHub Manager 초기화"""
        self.token = get_github_token()
        self.repo_name = get_repo_name()
        self.github = Github(self.token)
        self.repo = self.github.get_repo(self.repo_name)
        self._rate_limit_delay = 0.5  # Rate Limit 방지를 위한 지연 시간
    
    def _check_rate_limit(self):
        """Rate Limit 확인 및 대기"""
        try:
            rate_limit = self.github.get_rate_limit()
            # PyGithub 버전에 따라 다른 속성 구조 지원
            if hasattr(rate_limit, 'core'):
                remaining = rate_limit.core.remaining
                reset_time = rate_limit.core.reset
            elif hasattr(rate_limit, 'remaining'):
                remaining = rate_limit.remaining
                reset_time = getattr(rate_limit, 'reset', None)
            else:
                # Rate Limit 정보를 가져올 수 없으면 스킵
                return
            
            if remaining and remaining < 10:
                if reset_time:
                    wait_time = (reset_time - time.time()) + 1
                    if wait_time > 0:
                        time.sleep(wait_time)
        except Exception:
            # Rate Limit 체크 실패해도 계속 진행
            pass
    
    def read_json(self, file_path: str) -> Dict[str, Any]:
        """
        GitHub에서 JSON 파일 읽기
        
        Args:
            file_path: 리포지토리 내 파일 경로 (예: 'data/feeds.json')
            
        Returns:
            파싱된 JSON 데이터 (딕셔너리)
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
            json.JSONDecodeError: JSON 파싱 실패 시
        """
        try:
            self._check_rate_limit()
            
            # 최신 파일 내용 가져오기
            file_content = self.repo.get_contents(file_path)
            
            # Base64 디코딩
            decoded_content = base64.b64decode(file_content.content).decode('utf-8')
            
            # JSON 파싱
            data = json.loads(decoded_content)
            return data
            
        except GithubException as e:
            if e.status == 404:
                # 파일이 없으면 기본값 반환
                return {}
            raise Exception(f"GitHub API 오류: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 파싱 오류 ({file_path}): {e}")
        except Exception as e:
            raise Exception(f"파일 읽기 오류 ({file_path}): {e}")
    
    def write_json(self, file_path: str, data: Dict[str, Any], commit_message: str = "Update JSON file") -> bool:
        """
        JSON 데이터를 GitHub에 커밋 및 푸시
        
        Args:
            file_path: 리포지토리 내 파일 경로
            data: 저장할 데이터 (딕셔너리)
            commit_message: 커밋 메시지
            
        Returns:
            성공 여부 (bool)
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self._check_rate_limit()
                
                # JSON 문자열로 변환
                json_content = json.dumps(data, ensure_ascii=False, indent=2)
                json_bytes = json_content.encode('utf-8')
                
                # 파일 존재 여부 확인
                try:
                    existing_file = self.repo.get_contents(file_path)
                    # 파일이 존재하면 업데이트
                    self.repo.update_file(
                        path=file_path,
                        message=commit_message,
                        content=json_bytes,
                        sha=existing_file.sha
                    )
                except GithubException as e:
                    if e.status == 404:
                        # 파일이 없으면 생성
                        self.repo.create_file(
                            path=file_path,
                            message=commit_message,
                            content=json_bytes
                        )
                    else:
                        raise
                
                # 성공 시 약간의 지연 (동시성 문제 방지)
                time.sleep(self._rate_limit_delay)
                return True
                
            except GithubException as e:
                if e.status == 409:  # Conflict - 동시성 문제
                    retry_count += 1
                    if retry_count < max_retries:
                        # 최신 파일을 다시 읽고 재시도
                        time.sleep(1)
                        continue
                    else:
                        raise Exception(f"파일 업데이트 충돌 ({file_path}): 최대 재시도 횟수 초과")
                elif e.status == 403:  # Rate Limit
                    try:
                        rate_limit = self.github.get_rate_limit()
                        if hasattr(rate_limit, 'core'):
                            reset_time = rate_limit.core.reset
                        elif hasattr(rate_limit, 'reset'):
                            reset_time = rate_limit.reset
                        else:
                            reset_time = None
                        
                        if reset_time:
                            wait_time = (reset_time - time.time()) + 1
                            if wait_time > 0:
                                time.sleep(wait_time)
                                retry_count -= 1  # 재시도 카운트 유지
                                continue
                    except Exception:
                        pass
                    raise Exception(f"GitHub API Rate Limit 초과")
                else:
                    raise Exception(f"GitHub API 오류 ({file_path}): {e}")
            except Exception as e:
                raise Exception(f"파일 쓰기 오류 ({file_path}): {e}")
        
        return False
    
    def file_exists(self, file_path: str) -> bool:
        """파일 존재 여부 확인"""
        try:
            self._check_rate_limit()
            self.repo.get_contents(file_path)
            return True
        except GithubException as e:
            if e.status == 404:
                return False
            raise

