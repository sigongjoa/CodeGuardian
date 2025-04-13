"""
CodeGuardian 코어 모듈
애플리케이션의 핵심 기능 제공
"""

import os
import sys
import hashlib
import inspect
import re
import traceback
from functools import wraps

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from storage.db_manager import DBManager
from tracer.call_tracer import call_tracer

class CodeGuardian:
    """코드 보호 및 모니터링 핵심 클래스"""
    
    def __init__(self):
        """초기화"""
        self.db_manager = DBManager()
        self.monitored_files = []
        self.monitored_functions = []
        self.is_monitoring = False
    
    def start_monitoring(self, files_to_monitor=None, modules_to_monitor=None):
        """코드 모니터링 시작
        
        Args:
            files_to_monitor: 모니터링할 파일 경로 리스트
            modules_to_monitor: 모니터링할 모듈 리스트
        """
        if files_to_monitor:
            self.monitored_files = files_to_monitor
        
        # 호출 추적 시작
        call_tracer.start_tracing(modules_to_monitor)
        
        self.is_monitoring = True
        print(f"코드 모니터링 시작됨. 파일: {self.monitored_files}")
    
    def stop_monitoring(self):
        """코드 모니터링 중지"""
        call_tracer.stop_tracing()
        self.is_monitoring = False
        print("코드 모니터링 중지됨")
    
    def lock(self, func):
        """함수를 보호하는 데코레이터
        
        Args:
            func: 보호할 함수
            
        Returns:
            래핑된 함수
        """
        # 함수 코드 추출 및 해시 계산
        source_code = inspect.getsource(func)
        code_hash = hashlib.md5(source_code.encode()).hexdigest()
        
        # 함수 정보 저장
        self.db_manager.store_protected_code(
            file_path=inspect.getfile(func),
            function_name=func.__name__,
            code_hash=code_hash,
            protection_type='decorator'
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 함수 호출 시 무결성 검증
            self.verify_function_integrity(func)
            return func(*args, **kwargs)
        
        return wrapper
    
    def verify_function_integrity(self, func):
        """함수 코드 무결성 검증
        
        Args:
            func: 검증할 함수
            
        Raises:
            ValueError: 함수 코드가 변경된 경우
        """
        # 현재 함수 코드 해시 계산
        current_source = inspect.getsource(func)
        current_hash = hashlib.md5(current_source.encode()).hexdigest()
        
        # DB에서 원본 해시 조회
        cursor = self.db_manager._get_connection().cursor()
        cursor.execute('''
        SELECT code_hash FROM protected_code
        WHERE function_name = ? AND file_path = ?
        ORDER BY last_verified DESC
        LIMIT 1
        ''', (func.__name__, inspect.getfile(func)))
        
        result = cursor.fetchone()
        if not result:
            print(f"WARNING: {func.__name__} 함수가 보호 대상이 아님")
            return
        
        original_hash = result[0]
        
        # 해시 비교
        if current_hash != original_hash:
            # 변경 감지됨
            self.db_manager.store_code_change(
                file_path=inspect.getfile(func),
                function_name=func.__name__,
                change_type='modified',
                original_hash=original_hash,
                new_hash=current_hash,
                diff=f"Original hash: {original_hash}\nCurrent hash: {current_hash}"
            )
            
            print(f"WARNING: {func.__name__} 함수가 변경됨")
            # 실제 애플리케이션에서는 자동 복구 또는 경고 메시지 표시
    
    def scan_for_protected_blocks(self, file_path):
        """주석으로 보호된 코드 블록 스캔
        
        Args:
            file_path: 스캔할 파일 경로
        """
        try:
            # 다양한 인코딩 시도
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break  # 성공하면 루프 종료
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise UnicodeDecodeError("all encodings failed", b"", 0, 1, "Cannot decode file")
            
            # @LOCK: START와 @LOCK: END 사이 블록 찾기
            pattern = r'#\s*@LOCK:\s*START\s*\n(.*?)#\s*@LOCK:\s*END'
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                # 블록 내용 추출
                block_content = match.group(1)
                block_hash = hashlib.md5(block_content.encode()).hexdigest()
                
                # 블록 위치 찾기
                start_pos = match.start()
                end_pos = match.end()
                
                # 라인 번호 계산
                start_line = content[:start_pos].count('\n') + 1
                end_line = content[:end_pos].count('\n') + 1
                
                # 함수명 추출 시도
                function_name = "unknown"
                lines_before = content[:start_pos].split('\n')
                for i in range(len(lines_before) - 1, -1, -1):
                    if 'def ' in lines_before[i]:
                        # 'def function_name(' 패턴에서 함수명 추출
                        func_match = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', lines_before[i])
                        if func_match:
                            function_name = func_match.group(1)
                            break
                
                # 보호 정보 저장
                self.db_manager.store_protected_code(
                    file_path=file_path,
                    function_name=function_name,
                    start_line=start_line,
                    end_line=end_line,
                    code_hash=block_hash,
                    protection_type='comment'
                )
                
                print(f"보호된 블록 발견: {file_path}, 함수: {function_name}, 라인: {start_line}-{end_line}")
                
        except Exception as e:
            print(f"WARNING: {file_path} 스캔 중 오류: {str(e)}")
    
    def check_file_integrity(self, file_path):
        """파일 무결성 검사
        
        Args:
            file_path: 검사할 파일 경로
            
        Returns:
            변경된 보호 블록 리스트
        """
        if not os.path.exists(file_path):
            print(f"ERROR: 파일이 존재하지 않음 - {file_path}")
            return []
        
        # 모든 보호 블록 조회
        cursor = self.db_manager._get_connection().cursor()
        cursor.execute('''
        SELECT id, function_name, start_line, end_line, code_hash, protection_type
        FROM protected_code
        WHERE file_path = ?
        ''', (file_path,))
        
        changed_blocks = []
        
        try:
            # 다양한 인코딩 시도
            encodings = ['utf-8', 'cp949', 'euc-kr', 'latin1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break  # 성공하면 루프 종료
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise UnicodeDecodeError("all encodings failed", b"", 0, 1, "Cannot decode file")
                
            lines = content.split('\n')
        
            for row in cursor.fetchall():
                id, function_name, start_line, end_line, original_hash, protection_type = row
                
                if protection_type == 'comment':
                    # 주석 보호 블록 검사
                    if start_line and end_line and start_line <= len(lines) and end_line <= len(lines):
                        # 현재 블록 내용 추출
                        block_lines = lines[start_line-1:end_line]
                        block_content = '\n'.join(block_lines)
                        
                        # 주석 마커 제거
                        pattern = r'#\s*@LOCK:\s*(?:START|END)'
                        block_content = re.sub(pattern, '', block_content)
                        
                        # 해시 계산 및 비교
                        current_hash = hashlib.md5(block_content.encode()).hexdigest()
                        
                        if current_hash != original_hash:
                            changed_blocks.append({
                                'id': id,
                                'file_path': file_path,
                                'function_name': function_name,
                                'start_line': start_line,
                                'end_line': end_line,
                                'original_hash': original_hash,
                                'current_hash': current_hash
                            })
                
                elif protection_type == 'decorator':
                    # 데코레이터 보호 함수 검사
                    try:
                        # 함수 찾기
                        function_pattern = r'def\s+' + re.escape(function_name) + r'\s*\('
                        matches = list(re.finditer(function_pattern, content))
                        
                        if matches:
                            # 함수 시작 위치
                            func_start = matches[0].start()
                            
                            # 함수 끝 위치 찾기 (다음 함수 시작 전까지)
                            next_func_match = re.search(r'def\s+[a-zA-Z0-9_]+\s*\(', content[func_start + 1:])
                            
                            if next_func_match:
                                func_end = func_start + 1 + next_func_match.start()
                            else:
                                func_end = len(content)
                            
                            # 함수 코드 추출
                            func_code = content[func_start:func_end]
                            
                            # 해시 계산 및 비교
                            current_hash = hashlib.md5(func_code.encode()).hexdigest()
                            
                            if current_hash != original_hash:
                                changed_blocks.append({
                                    'id': id,
                                    'file_path': file_path,
                                    'function_name': function_name,
                                    'original_hash': original_hash,
                                    'current_hash': current_hash
                                })
                    except Exception as e:
                        print(f"ERROR: 함수 코드 검사 중 오류 - {function_name}: {str(e)}")
        
        except Exception as e:
            print(f"ERROR: 파일 검사 중 오류 - {file_path}: {str(e)}")
            return []
            
        # 변경 사항 기록
        for block in changed_blocks:
            self.db_manager.store_code_change(
                file_path=file_path,
                function_name=block['function_name'],
                change_type='modified',
                original_hash=block['original_hash'],
                new_hash=block['current_hash'],
                diff=f"Block ID: {block['id']}\nOriginal hash: {block['original_hash']}\nCurrent hash: {block['current_hash']}"
            )
            
            print(f"WARNING: 보호된 코드가 변경됨 - {file_path}, 함수: {block['function_name']}")
        
        return changed_blocks
    
    def get_call_graph(self, function_name=None, depth=2):
        """호출 그래프 데이터 가져오기
        
        Args:
            function_name: 시작 함수명. None이면 전체 그래프
            depth: 호출 깊이
            
        Returns:
            노드와 엣지 데이터 포함하는 그래프 데이터
        """
        return call_tracer.get_call_graph(function_name, depth)
    
    def get_error_data(self, function_name=None, limit=50):
        """에러 데이터 가져오기
        
        Args:
            function_name: 특정 함수의 에러만 가져오기. None이면 모든 에러
            limit: 최대 에러 수
            
        Returns:
            에러 정보 리스트
        """
        return call_tracer.get_error_data(function_name, limit)

# 전역 인스턴스
code_guardian = CodeGuardian()

# 편의를 위한 데코레이터 함수
def lock(func):
    """함수를 보호하는 데코레이터"""
    return code_guardian.lock(func)
