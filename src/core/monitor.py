#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 파일 모니터링 시스템
보호 대상 파일의 변경을 감지하고 처리하는 모듈
"""

import os
import time
import hashlib
import difflib
from pathlib import Path
from threading import Thread, Event, Lock
import logging

from src.core.events import event_bus
from src.storage.storage_manager import (
    get_protected_functions, 
    get_protected_blocks,
    store_change_info
)
from src.core.settings import app_settings

# 모니터링 스레드 객체
_monitor_thread = None
_stop_event = Event()
_monitor_lock = Lock()
_monitoring_active = False

def calculate_file_hash(file_path):
    """파일 전체 해시 계산"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logging.error(f"파일 해시 계산 오류: {str(e)}")
        return None

def calculate_function_hash(file_path, function_name):
    """파일에서 특정 함수의 해시 계산"""
    try:
        # 함수 코드 추출 (간단한 구현)
        # 실제로는 AST(Abstract Syntax Tree) 파싱이 필요할 수 있음
        import ast
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # 함수 코드 범위 가져오기
                func_lines = content.splitlines()[node.lineno-1:node.end_lineno]
                func_code = '\n'.join(func_lines)
                return hashlib.sha256(func_code.encode('utf-8')).hexdigest()
        
        return None
    except Exception as e:
        logging.error(f"함수 해시 계산 오류: {str(e)}")
        return None

def calculate_block_hash(file_path, start_line, end_line):
    """파일에서 특정 코드 블록의 해시 계산"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 0-인덱스를 1-인덱스로 조정
        block_lines = lines[start_line-1:end_line]
        block_code = ''.join(block_lines)
        return hashlib.sha256(block_code.encode('utf-8')).hexdigest()
    except Exception as e:
        logging.error(f"블록 해시 계산 오류: {str(e)}")
        return None

def generate_diff(file_path, original_content, current_content):
    """두 코드 사이의 차이점 계산"""
    try:
        original_lines = original_content.splitlines()
        current_lines = current_content.splitlines()
        
        diff = difflib.unified_diff(
            original_lines,
            current_lines,
            fromfile=f"{file_path} (원본)",
            tofile=f"{file_path} (변경됨)",
            lineterm=''
        )
        
        return '\n'.join(diff)
    except Exception as e:
        logging.error(f"Diff 생성 오류: {str(e)}")
        return f"Diff 생성 중 오류 발생: {str(e)}"

def check_file_integrity(file_path):
    """파일 무결성 검사"""
    logging.info(f"파일 무결성 검사: {file_path}")
    
    changes_detected = False
    
    # 보호된 함수 확인
    protected_functions = get_protected_functions()
    
    for func in protected_functions:
        if func['file_path'] == file_path:
            function_name = func['function_name']
            original_hash = func['hash']
            
            logging.info(f"보호된 함수 검사: {function_name}")
            
            # 현재 해시 계산
            current_hash = calculate_function_hash(file_path, function_name)
            
            if current_hash and current_hash != original_hash:
                logging.warning(f"함수 변경 감지: {function_name}")
                
                # 변경 감지
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                
                # TODO: 원본 내용 가져오기 (백업에서)
                original_content = f"# 원본 함수: {function_name}\n# 해시: {original_hash}\n\n"
                
                # Diff 생성
                diff = generate_diff(file_path, original_content, current_content)
                
                # 변경 정보 저장
                store_change_info(
                    file_path, 
                    function_name, 
                    "modified", 
                    original_hash, 
                    current_hash, 
                    diff,
                    False
                )
                
                # 이벤트 발생
                event_bus.code_changed.emit(file_path, function_name, "modified")
                changes_detected = True
    
    # 보호된 블록 확인
    protected_blocks = get_protected_blocks()
    
    for block in protected_blocks:
        if block['file_path'] == file_path:
            start_line = block['start_line']
            end_line = block['end_line']
            original_hash = block['hash']
            
            logging.info(f"보호된 블록 검사: {start_line}-{end_line}")
            
            # 현재 해시 계산
            current_hash = calculate_block_hash(file_path, start_line, end_line)
            
            if current_hash and current_hash != original_hash:
                logging.warning(f"블록 변경 감지: {start_line}-{end_line}")
                
                # 변경 감지
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
                
                # TODO: 원본 내용 가져오기 (백업에서)
                original_content = f"# 원본 블록: {start_line}-{end_line}\n# 해시: {original_hash}\n\n"
                
                # Diff 생성
                diff = generate_diff(file_path, original_content, current_content)
                
                # 변경 정보 저장
                block_name = f"Block {start_line}-{end_line}"
                store_change_info(
                    file_path, 
                    block_name, 
                    "modified", 
                    original_hash, 
                    current_hash, 
                    diff,
                    False
                )
                
                # 이벤트 발생
                event_bus.code_changed.emit(file_path, block_name, "modified")
                changes_detected = True
    
    return changes_detected

def monitor_directories():
    """모니터링 디렉토리 목록 가져오기"""
    # 설정에서 모니터링 경로 가져오기
    paths = app_settings.get("monitor", "paths", [])
    
    # 디렉토리 리스트 반환
    return [p for p in paths if os.path.isdir(p)]

def monitor_files():
    """파일 모니터링 스레드 함수"""
    global _monitoring_active
    
    # 모니터링 상태 설정
    with _monitor_lock:
        _monitoring_active = True
    
    logging.info("파일 모니터링 시작됨")
    
    while not _stop_event.is_set():
        try:
            # 모니터링 간격 가져오기
            interval = app_settings.get("monitor", "interval", 5)
            
            # 모니터링할 디렉토리 가져오기
            directories = monitor_directories()
            
            if not directories:
                logging.warning("모니터링할 디렉토리가 없음")
                _stop_event.wait(interval)
                continue
            
            logging.info(f"모니터링 중인 디렉토리: {directories}")
            
            # 보호된 함수와 블록에 해당하는 파일들 모니터링
            functions = get_protected_functions()
            blocks = get_protected_blocks()
            
            # 모든 파일 경로를 중복 없이 수집
            file_paths = set()
            for func in functions:
                file_paths.add(func['file_path'])
            
            for block in blocks:
                file_paths.add(block['file_path'])
            
            logging.info(f"모니터링 중인 파일 수: {len(file_paths)}")
            
            # 각 파일 확인
            changes_detected = False
            for file_path in file_paths:
                if os.path.exists(file_path):
                    file_changes = check_file_integrity(file_path)
                    changes_detected = changes_detected or file_changes
                else:
                    logging.warning(f"파일이 존재하지 않음: {file_path}")
            
            if changes_detected:
                logging.info("변경 사항이 감지됨")
            else:
                logging.info("변경 사항 없음")
                    
        except Exception as e:
            logging.error(f"모니터링 오류: {str(e)}")
        
        # 지정된 간격만큼 대기
        logging.info(f"{interval}초 후 다음 검사 실행")
        _stop_event.wait(interval)
    
    # 모니터링 상태 해제
    with _monitor_lock:
        _monitoring_active = False
    
    logging.info("파일 모니터링 중지됨")

def start_file_monitoring():
    """파일 모니터링 시작"""
    global _monitor_thread, _stop_event, _monitoring_active
    
    # 이미 실행 중인 경우
    with _monitor_lock:
        if _monitoring_active:
            logging.info("모니터링이 이미 실행 중")
            return True
    
    # 이미 실행 중인 스레드 종료
    if _monitor_thread and _monitor_thread.is_alive():
        stop_file_monitoring()
    
    # 새 스레드 시작
    _stop_event.clear()
    _monitor_thread = Thread(target=monitor_files, daemon=True)
    _monitor_thread.start()
    
    logging.info("파일 모니터링 스레드 시작됨")
    return True

def stop_file_monitoring():
    """파일 모니터링 중지"""
    global _monitor_thread, _stop_event, _monitoring_active
    
    # 이미 중지된 경우
    with _monitor_lock:
        if not _monitoring_active:
            logging.info("모니터링이 이미 중지됨")
            return True
    
    if _monitor_thread and _monitor_thread.is_alive():
        _stop_event.set()
        _monitor_thread.join(timeout=1.0)
        _monitor_thread = None
        logging.info("파일 모니터링 스레드 중지됨")
    
    return True

def scan_for_comment_protected_blocks(file_path):
    """주석으로 보호된 코드 블록 스캔"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        # 블록 찾기
        start_line = None
        blocks = []
        
        for i, line in enumerate(content, 1):
            if "@LOCK: START" in line and start_line is None:
                start_line = i
            elif "@LOCK: END" in line and start_line is not None:
                end_line = i
                blocks.append((start_line, end_line))
                start_line = None
        
        return blocks
    except Exception as e:
        logging.error(f"보호 블록 스캔 오류: {str(e)}")
        return []

def is_monitoring_active():
    """모니터링 활성화 상태 확인"""
    with _monitor_lock:
        return _monitoring_active
