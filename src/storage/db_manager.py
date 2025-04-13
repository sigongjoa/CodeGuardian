"""
데이터베이스 관리 모듈
함수 호출 및 에러 정보 저장 및 조회 - 스레드 안전 구현
"""

import os
import sqlite3
import json
import threading
from datetime import datetime
import time

class DBManager:
    """데이터베이스 관리 클래스 - 스레드 안전 버전"""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, db_path=None):
        """싱글톤 패턴 구현"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DBManager, cls).__new__(cls)
                cls._instance.is_initialized = False
            return cls._instance
    
    def __init__(self, db_path=None):
        """초기화
        
        Args:
            db_path: 데이터베이스 파일 경로. None이면 기본 경로 사용
        """
        # 이미 초기화되었으면 중복 초기화 방지
        if hasattr(self, 'is_initialized') and self.is_initialized:
            return
            
        if db_path is None:
            # 애플리케이션 경로 기준으로 DB 파일 경로 설정
            app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
            config_dir = os.path.join(app_dir, 'config')
            
            # 디렉토리가 없으면 생성
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            db_path = os.path.join(config_dir, 'codeguardian.db')
            
        self.db_path = db_path
        self.local = threading.local()  # 스레드 로컬 저장소
        self.is_initialized = True
        
        # 초기 연결 테스트 및 테이블 생성
        try:
            conn = self._get_connection()
            self._initialize_tables(conn)
        except Exception as e:
            print(f"DB 초기화 중 오류: {str(e)}")
    
    def _get_connection(self):
        """현재 스레드에 대한 데이터베이스 연결 가져오기
        
        Returns:
            현재 스레드의 SQLite 연결 객체
        """
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            try:
                self.local.conn = sqlite3.connect(self.db_path)
                # 외래 키 제약 활성화
                self.local.conn.execute("PRAGMA foreign_keys = ON")
            except Exception as e:
                print(f"DB 연결 오류: {str(e)}")
                raise
                
        return self.local.conn
    
    def _initialize_tables(self, conn):
        """데이터베이스 테이블 초기화
        
        Args:
            conn: 데이터베이스 연결 객체
        """
        cursor = conn.cursor()
        
        # 함수 호출 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS function_calls (
            id INTEGER PRIMARY KEY,
            caller TEXT,
            callee TEXT,
            call_time TIMESTAMP,
            call_context TEXT,
            args TEXT,
            module TEXT
        )
        ''')
        
        # 에러 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY,
            function_name TEXT,
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            timestamp TIMESTAMP,
            context TEXT
        )
        ''')
        
        # 변경 이력 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY,
            file_path TEXT,
            function_name TEXT,
            change_type TEXT,
            original_hash TEXT,
            new_hash TEXT,
            diff TEXT,
            timestamp TIMESTAMP,
            automatic_restore BOOLEAN
        )
        ''')
        
        # 보호된 코드 정보 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS protected_code (
            id INTEGER PRIMARY KEY,
            file_path TEXT,
            function_name TEXT,
            start_line INTEGER,
            end_line INTEGER,
            code_hash TEXT,
            protection_type TEXT,
            last_verified TIMESTAMP
        )
        ''')
        
        conn.commit()
    
    def close_connection(self):
        """현재 스레드의 데이터베이스 연결 종료"""
        if hasattr(self.local, 'conn') and self.local.conn:
            try:
                self.local.conn.close()
            except Exception as e:
                print(f"DB 연결 종료 오류: {str(e)}")
            finally:
                self.local.conn = None
    
    def store_function_call(self, caller, callee, module, call_time, args=None, call_context=None):
        """함수 호출 정보 저장
        
        Args:
            caller: 호출자 함수명
            callee: 피호출자 함수명
            module: 모듈명
            call_time: 호출 시간
            args: 함수 인자 정보 (문자열)
            call_context: 호출 컨텍스트 정보 (문자열)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 시간 형식 처리
            if isinstance(call_time, datetime):
                call_time = call_time.isoformat()
            
            cursor.execute('''
            INSERT INTO function_calls (caller, callee, call_time, call_context, args, module)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (caller, callee, call_time, call_context, args, module))
            
            conn.commit()
        except Exception as e:
            print(f"함수 호출 정보 저장 오류: {str(e)}")
    
    def store_error(self, function_name, error_type, error_message, stack_trace, context=None):
        """에러 정보 저장
        
        Args:
            function_name: 에러 발생 함수명
            error_type: 에러 유형
            error_message: 에러 메시지
            stack_trace: 스택 트레이스 정보 (문자열 또는 리스트)
            context: 에러 발생 컨텍스트 정보 (문자열)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 스택 트레이스가 리스트면 문자열로 변환
            if isinstance(stack_trace, list):
                stack_trace = ''.join(stack_trace)
            
            cursor.execute('''
            INSERT INTO errors (function_name, error_type, error_message, stack_trace, timestamp, context)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (function_name, error_type, error_message, stack_trace, datetime.now().isoformat(), context))
            
            conn.commit()
        except Exception as e:
            print(f"에러 정보 저장 오류: {str(e)}")
    
    def store_code_change(self, file_path, function_name, change_type, original_hash, new_hash, diff, automatic_restore=False):
        """코드 변경 정보 저장
        
        Args:
            file_path: 변경된 파일 경로
            function_name: 변경된 함수명
            change_type: 변경 유형 (수정, 삭제 등)
            original_hash: 원본 코드 해시
            new_hash: 변경된 코드 해시
            diff: 변경 내용 (문자열)
            automatic_restore: 자동 복구 여부
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO changes (file_path, function_name, change_type, original_hash, new_hash, diff, timestamp, automatic_restore)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, function_name, change_type, original_hash, new_hash, diff, datetime.now().isoformat(), automatic_restore))
            
            conn.commit()
        except Exception as e:
            print(f"코드 변경 정보 저장 오류: {str(e)}")
    
    def store_protected_code(self, file_path, function_name, code_hash, protection_type, start_line=None, end_line=None):
        """보호 코드 정보 저장
        
        Args:
            file_path: 파일 경로
            function_name: 함수명
            code_hash: 코드 해시
            protection_type: 보호 유형 (decorator, comment 등)
            start_line: 시작 라인 번호 (코멘트 보호 시)
            end_line: 종료 라인 번호 (코멘트 보호 시)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO protected_code (file_path, function_name, start_line, end_line, code_hash, protection_type, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, function_name, start_line, end_line, code_hash, protection_type, datetime.now().isoformat()))
            
            conn.commit()
        except Exception as e:
            print(f"보호 코드 정보 저장 오류: {str(e)}")
    
    def get_call_graph(self, function_name=None, depth=2):
        """함수 호출 그래프 데이터 조회
        
        Args:
            function_name: 시작 함수명. None이면 전체 그래프
            depth: 조회할 호출 깊이
            
        Returns:
            nodes와 edges 리스트를 포함하는 딕셔너리
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            nodes = set()
            edges = []
            
            # 함수 호출 데이터 조회 쿼리
            if function_name:
                # 특정 함수부터 시작하는 호출 그래프
                process_queue = [(function_name, 0)]  # (함수명, 현재 깊이)
                processed = set()
                
                while process_queue:
                    current_func, current_depth = process_queue.pop(0)
                    
                    if current_func in processed or current_depth > depth:
                        continue
                    
                    processed.add(current_func)
                    nodes.add(current_func)
                    
                    # 현재 함수가 호출하는 함수들 조회
                    cursor.execute('''
                    SELECT DISTINCT callee FROM function_calls 
                    WHERE caller = ?
                    ''', (current_func,))
                    
                    for row in cursor.fetchall():
                        callee = row[0]
                        if callee:
                            nodes.add(callee)
                            edges.append((current_func, callee))
                            
                            if current_depth < depth:
                                process_queue.append((callee, current_depth + 1))
                    
                    # 현재 함수를 호출하는 함수들 조회 (역방향)
                    if current_depth < depth:
                        cursor.execute('''
                        SELECT DISTINCT caller FROM function_calls 
                        WHERE callee = ?
                        ''', (current_func,))
                        
                        for row in cursor.fetchall():
                            caller = row[0]
                            if caller and caller != current_func:  # 자기 자신 호출 제외
                                nodes.add(caller)
                                edges.append((caller, current_func))
                                process_queue.append((caller, current_depth + 1))
            else:
                # 전체 호출 그래프
                cursor.execute('''
                SELECT DISTINCT caller, callee FROM function_calls
                ''')
                
                for row in cursor.fetchall():
                    caller, callee = row
                    if caller and callee:
                        nodes.add(caller)
                        nodes.add(callee)
                        edges.append((caller, callee))
            
            # 노드와 엣지 형식 변환
            nodes_list = [{"id": node, "label": node} for node in nodes]
            edges_list = [{"source": source, "target": target} for source, target in edges]
            
            return {
                "nodes": nodes_list,
                "edges": edges_list
            }
        except Exception as e:
            print(f"호출 그래프 조회 오류: {str(e)}")
            return {"nodes": [], "edges": []}
    
    def get_errors(self, function_name=None, limit=50):
        """에러 정보 조회
        
        Args:
            function_name: 특정 함수의 에러만 조회. None이면 모든 에러
            limit: 최대 조회 건수
            
        Returns:
            에러 정보 리스트
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if function_name:
                cursor.execute('''
                SELECT id, function_name, error_type, error_message, stack_trace, timestamp, context 
                FROM errors
                WHERE function_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (function_name, limit))
            else:
                cursor.execute('''
                SELECT id, function_name, error_type, error_message, stack_trace, timestamp, context 
                FROM errors
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (limit,))
            
            errors = []
            for row in cursor.fetchall():
                id, func_name, error_type, error_message, stack_trace, timestamp, context = row
                errors.append({
                    "id": id,
                    "function_name": func_name,
                    "error_type": error_type,
                    "error_message": error_message,
                    "stack_trace": stack_trace,
                    "timestamp": timestamp,
                    "context": context
                })
            
            return errors
        except Exception as e:
            print(f"에러 정보 조회 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            return []  # 오류 발생 시 빈 리스트 반환
    
    def get_changes(self, file_path=None, function_name=None, limit=50):
        """코드 변경 이력 조회
        
        Args:
            file_path: 특정 파일의 변경만 조회. None이면 모든 파일
            function_name: 특정 함수의 변경만 조회. None이면 모든 함수
            limit: 최대 조회 건수
            
        Returns:
            변경 이력 리스트
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT id, file_path, function_name, change_type, diff, timestamp FROM changes"
            params = []
            
            if file_path and function_name:
                query += " WHERE file_path = ? AND function_name = ?"
                params.extend([file_path, function_name])
            elif file_path:
                query += " WHERE file_path = ?"
                params.append(file_path)
            elif function_name:
                query += " WHERE function_name = ?"
                params.append(function_name)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            changes = []
            for row in cursor.fetchall():
                id, file_path, function_name, change_type, diff, timestamp = row
                changes.append({
                    "id": id,
                    "file_path": file_path,
                    "function_name": function_name,
                    "change_type": change_type,
                    "diff": diff,
                    "timestamp": timestamp
                })
            
            return changes
        except Exception as e:
            print(f"변경 이력 조회 오류: {str(e)}")
            return []
    
    def get_protected_code(self, file_path=None, function_name=None):
        """보호된 코드 정보 조회
        
        Args:
            file_path: 특정 파일의 보호 코드만 조회. None이면 모든 파일
            function_name: 특정 함수의 보호 코드만 조회. None이면 모든 함수
            
        Returns:
            보호된 코드 정보 리스트
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT id, file_path, function_name, start_line, end_line, code_hash, protection_type, last_verified FROM protected_code"
            params = []
            
            if file_path and function_name:
                query += " WHERE file_path = ? AND function_name = ?"
                params.extend([file_path, function_name])
            elif file_path:
                query += " WHERE file_path = ?"
                params.append(file_path)
            elif function_name:
                query += " WHERE function_name = ?"
                params.append(function_name)
                
            cursor.execute(query, params)
            
            protected_codes = []
            for row in cursor.fetchall():
                id, file_path, function_name, start_line, end_line, code_hash, protection_type, last_verified = row
                protected_codes.append({
                    "id": id,
                    "file_path": file_path,
                    "function_name": function_name,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code_hash": code_hash,
                    "protection_type": protection_type,
                    "last_verified": last_verified
                })
            
            return protected_codes
        except Exception as e:
            print(f"보호 코드 정보 조회 오류: {str(e)}")
            return []

    def clear_data(self, table_name=None):
        """데이터 삭제
        
        Args:
            table_name: 삭제할 테이블명. None이면 모든 테이블 데이터 삭제
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if table_name:
                # 특정 테이블만 삭제
                cursor.execute(f"DELETE FROM {table_name}")
            else:
                # 모든 테이블 데이터 삭제
                cursor.execute("DELETE FROM function_calls")
                cursor.execute("DELETE FROM errors")
                cursor.execute("DELETE FROM changes")
                cursor.execute("DELETE FROM protected_code")
            
            conn.commit()
        except Exception as e:
            print(f"데이터 삭제 오류: {str(e)}")
