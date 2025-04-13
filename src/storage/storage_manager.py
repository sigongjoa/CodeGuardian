#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 저장소 관리
함수 호출 정보, 보호 상태 및 변경 이력 저장
"""

import os
import sqlite3
import json
import time
import logging
from pathlib import Path
import threading

from src.core.settings import app_settings

# SQLite 연결 관리
_connections = {}
_lock = threading.RLock()
_db_path = None
_initialized = False

def get_db_path():
    """데이터베이스 파일 경로 반환"""
    global _db_path
    
    if _db_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_dir = os.path.join(base_dir, "data")
        os.makedirs(db_dir, exist_ok=True)
        _db_path = os.path.join(db_dir, "codeguardian.db")
        logging.info(f"데이터베이스 경로: {_db_path}")
    
    return _db_path

def get_connection():
    """현재 스레드에 대한 데이터베이스 연결 객체 반환"""
    thread_id = threading.get_ident()
    
    with _lock:
        # 현재 스레드에 연결이 없으면 새로 생성
        if thread_id not in _connections or _connections[thread_id] is None:
            logging.info(f"스레드 {thread_id}에 대한 새 연결 생성")
            db_path = get_db_path()
            conn = sqlite3.connect(db_path, timeout=20.0)
            conn.row_factory = sqlite3.Row
            _connections[thread_id] = conn
    
    return _connections[thread_id]

def setup_storage():
    """저장소 초기화"""
    global _initialized
    
    logging.info("저장소 초기화 시작")
    start_time = time.time()
    
    try:
        with _lock:
            # 이미 초기화되었는지 확인
            if _initialized:
                logging.info("저장소가 이미 초기화되어 있음")
                return True
            
            logging.info("데이터베이스 초기화 중...")
            
            # 데이터베이스 연결 가져오기
            conn = get_connection()
            cursor = conn.cursor()
            
            # 함수 호출 테이블
            logging.info("function_calls 테이블 생성 중...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS function_calls (
                id INTEGER PRIMARY KEY,
                caller_file TEXT,
                caller_function TEXT,
                callee_file TEXT,
                callee_function TEXT,
                call_time TIMESTAMP,
                args TEXT,
                module TEXT
            )
            ''')
            
            # 에러 테이블
            logging.info("errors 테이블 생성 중...")
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
            logging.info("changes 테이블 생성 중...")
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
            
            # 보호된 함수 테이블
            logging.info("protected_functions 테이블 생성 중...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS protected_functions (
                id INTEGER PRIMARY KEY,
                file_path TEXT,
                function_name TEXT,
                hash TEXT,
                protection_type TEXT,
                last_verified TIMESTAMP
            )
            ''')
            
            # 보호된 코드 블록 테이블
            logging.info("protected_blocks 테이블 생성 중...")
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS protected_blocks (
                id INTEGER PRIMARY KEY,
                file_path TEXT,
                start_line INTEGER,
                end_line INTEGER,
                hash TEXT,
                protection_type TEXT,
                last_verified TIMESTAMP
            )
            ''')
            
            conn.commit()
            logging.info("데이터베이스 테이블 생성 완료")
            
            # 백업 디렉토리 생성
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            backup_dir = os.path.join(base_dir, app_settings.get("protection", "backup_location", "backups/"))
            os.makedirs(backup_dir, exist_ok=True)
            logging.info(f"백업 디렉토리 생성: {backup_dir}")
            
            # 초기화 완료 표시
            _initialized = True
        
        end_time = time.time()
        logging.info(f"저장소 초기화 완료: {end_time - start_time:.3f}초")
        return True
    except sqlite3.Error as e:
        logging.error(f"SQLite 오류: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"저장소 초기화 오류: {str(e)}")
        return False

def store_call_info(caller_file, caller_function, callee_file, callee_function, call_time, args, module):
    """함수 호출 정보 저장"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO function_calls 
        (caller_file, caller_function, callee_file, callee_function, call_time, args, module)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (caller_file, caller_function, callee_file, callee_function, call_time, args, module))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"호출 정보 저장 오류: {str(e)}")
        return False

def store_error_info(function_name, error_type, error_message, stack_trace, context):
    """에러 정보 저장"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        timestamp = time.time()
        
        cursor.execute('''
        INSERT INTO errors 
        (function_name, error_type, error_message, stack_trace, timestamp, context)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (function_name, error_type, error_message, stack_trace, timestamp, context))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"에러 정보 저장 오류: {str(e)}")
        return False

def store_change_info(file_path, function_name, change_type, original_hash, new_hash, diff, automatic_restore=False):
    """변경 정보 저장"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        timestamp = time.time()
        
        cursor.execute('''
        INSERT INTO changes 
        (file_path, function_name, change_type, original_hash, new_hash, diff, timestamp, automatic_restore)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_path, function_name, change_type, original_hash, new_hash, diff, timestamp, automatic_restore))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"변경 정보 저장 오류: {str(e)}")
        return False

def add_protected_function(file_path, function_name, hash_value, protection_type="decorator"):
    """보호된 함수 추가"""
    try:
        # 저장소 초기화 확인
        if not _initialized:
            setup_storage()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        timestamp = time.time()
        
        # 이미 존재하는지 확인
        cursor.execute('''
        SELECT id FROM protected_functions 
        WHERE file_path = ? AND function_name = ?
        ''', (file_path, function_name))
        
        existing = cursor.fetchone()
        
        if existing:
            # 업데이트
            cursor.execute('''
            UPDATE protected_functions 
            SET hash = ?, protection_type = ?, last_verified = ?
            WHERE file_path = ? AND function_name = ?
            ''', (hash_value, protection_type, timestamp, file_path, function_name))
        else:
            # 새로 추가
            cursor.execute('''
            INSERT INTO protected_functions 
            (file_path, function_name, hash, protection_type, last_verified)
            VALUES (?, ?, ?, ?, ?)
            ''', (file_path, function_name, hash_value, protection_type, timestamp))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"보호 함수 추가 오류: {str(e)}")
        return False

def add_protected_block(file_path, start_line, end_line, hash_value, protection_type="comment"):
    """보호된 코드 블록 추가"""
    try:
        # 저장소 초기화 확인
        if not _initialized:
            setup_storage()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        timestamp = time.time()
        
        # 이미 존재하는지 확인
        cursor.execute('''
        SELECT id FROM protected_blocks 
        WHERE file_path = ? AND start_line = ? AND end_line = ?
        ''', (file_path, start_line, end_line))
        
        existing = cursor.fetchone()
        
        if existing:
            # 업데이트
            cursor.execute('''
            UPDATE protected_blocks 
            SET hash = ?, protection_type = ?, last_verified = ?
            WHERE file_path = ? AND start_line = ? AND end_line = ?
            ''', (hash_value, protection_type, timestamp, file_path, start_line, end_line))
        else:
            # 새로 추가
            cursor.execute('''
            INSERT INTO protected_blocks 
            (file_path, start_line, end_line, hash, protection_type, last_verified)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_path, start_line, end_line, hash_value, protection_type, timestamp))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"보호 블록 추가 오류: {str(e)}")
        return False

def get_recent_calls(limit=100):
    """최근 함수 호출 정보 조회"""
    try:
        # 저장소 초기화 확인
        if not _initialized:
            setup_storage()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM function_calls 
        ORDER BY call_time DESC 
        LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"최근 호출 조회 오류: {str(e)}")
        return []

def get_recent_changes(limit=100):
    """최근 코드 변경 정보 조회"""
    try:
        # 저장소 초기화 확인
        if not _initialized:
            setup_storage()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM changes 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"최근 변경 조회 오류: {str(e)}")
        return []

def get_recent_errors(limit=100):
    """최근 에러 정보 조회"""
    try:
        # 저장소 초기화 확인
        if not _initialized:
            setup_storage()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM errors 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"최근 에러 조회 오류: {str(e)}")
        return []

def get_protected_functions():
    """보호된 함수 목록 조회"""
    try:
        # 저장소 초기화 확인
        if not _initialized:
            setup_storage()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM protected_functions')
        
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"보호 함수 조회 오류: {str(e)}")
        return []

def get_protected_blocks():
    """보호된 코드 블록 목록 조회"""
    try:
        # 저장소 초기화 확인
        if not _initialized:
            setup_storage()
            
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM protected_blocks')
        
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"보호 블록 조회 오류: {str(e)}")
        return []

def close_connection():
    """현재 스레드의 데이터베이스 연결 종료"""
    thread_id = threading.get_ident()
    
    with _lock:
        if thread_id in _connections and _connections[thread_id] is not None:
            try:
                _connections[thread_id].close()
                _connections[thread_id] = None
                logging.info(f"스레드 {thread_id}의 연결을 닫음")
            except Exception as e:
                logging.error(f"연결 종료 오류: {str(e)}")

def close_all_connections():
    """모든 데이터베이스 연결 종료"""
    with _lock:
        for thread_id, conn in list(_connections.items()):
            if conn is not None:
                try:
                    conn.close()
                    _connections[thread_id] = None
                    logging.info(f"스레드 {thread_id}의 연결을 닫음")
                except Exception as e:
                    logging.error(f"연결 종료 오류: {str(e)}")
        
        # 모든 연결 정보 초기화
        _connections.clear()
        logging.info("모든 데이터베이스 연결 닫힘")
