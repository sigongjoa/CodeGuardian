#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 간소화된 저장소 관리
SQLite 대신 메모리 기반 저장소 사용
"""

import os
import time
import logging
from pathlib import Path

# 메모리 저장소
_storage = {
    "function_calls": [],
    "errors": [],
    "changes": [],
    "protected_functions": [],
    "protected_blocks": []
}

def setup_storage():
    """저장소 초기화"""
    logging.info("간소화된 메모리 저장소 초기화 시작")
    # 백업 디렉토리 생성
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backup_dir = os.path.join(base_dir, "backups/")
    os.makedirs(backup_dir, exist_ok=True)
    logging.info("간소화된 메모리 저장소 초기화 완료")
    return True

def store_call_info(caller_file, caller_function, callee_file, callee_function, call_time, args, module):
    """함수 호출 정보 저장"""
    try:
        call_info = {
            "id": len(_storage["function_calls"]) + 1,
            "caller_file": caller_file,
            "caller_function": caller_function,
            "callee_file": callee_file,
            "callee_function": callee_function,
            "call_time": call_time,
            "args": args,
            "module": module
        }
        _storage["function_calls"].append(call_info)
        return True
    except Exception as e:
        logging.error(f"호출 정보 저장 오류: {str(e)}")
        return False

def store_error_info(function_name, error_type, error_message, stack_trace, context):
    """에러 정보 저장"""
    try:
        error_info = {
            "id": len(_storage["errors"]) + 1,
            "function_name": function_name,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "timestamp": time.time(),
            "context": context
        }
        _storage["errors"].append(error_info)
        return True
    except Exception as e:
        logging.error(f"에러 정보 저장 오류: {str(e)}")
        return False

def store_change_info(file_path, function_name, change_type, original_hash, new_hash, diff, automatic_restore=False):
    """변경 정보 저장"""
    try:
        change_info = {
            "id": len(_storage["changes"]) + 1,
            "file_path": file_path,
            "function_name": function_name,
            "change_type": change_type,
            "original_hash": original_hash,
            "new_hash": new_hash,
            "diff": diff,
            "timestamp": time.time(),
            "automatic_restore": automatic_restore
        }
        _storage["changes"].append(change_info)
        return True
    except Exception as e:
        logging.error(f"변경 정보 저장 오류: {str(e)}")
        return False

def add_protected_function(file_path, function_name, hash_value, protection_type="decorator"):
    """보호된 함수 추가"""
    try:
        # 이미 존재하는지 확인
        for i, func in enumerate(_storage["protected_functions"]):
            if func["file_path"] == file_path and func["function_name"] == function_name:
                # 업데이트
                _storage["protected_functions"][i]["hash"] = hash_value
                _storage["protected_functions"][i]["protection_type"] = protection_type
                _storage["protected_functions"][i]["last_verified"] = time.time()
                return True
        
        # 새로 추가
        func_info = {
            "id": len(_storage["protected_functions"]) + 1,
            "file_path": file_path,
            "function_name": function_name,
            "hash": hash_value,
            "protection_type": protection_type,
            "last_verified": time.time()
        }
        _storage["protected_functions"].append(func_info)
        return True
    except Exception as e:
        logging.error(f"보호 함수 추가 오류: {str(e)}")
        return False

def add_protected_block(file_path, start_line, end_line, hash_value, protection_type="comment"):
    """보호된 코드 블록 추가"""
    try:
        # 이미 존재하는지 확인
        for i, block in enumerate(_storage["protected_blocks"]):
            if (block["file_path"] == file_path and 
                block["start_line"] == start_line and 
                block["end_line"] == end_line):
                # 업데이트
                _storage["protected_blocks"][i]["hash"] = hash_value
                _storage["protected_blocks"][i]["protection_type"] = protection_type
                _storage["protected_blocks"][i]["last_verified"] = time.time()
                return True
        
        # 새로 추가
        block_info = {
            "id": len(_storage["protected_blocks"]) + 1,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "hash": hash_value,
            "protection_type": protection_type,
            "last_verified": time.time()
        }
        _storage["protected_blocks"].append(block_info)
        return True
    except Exception as e:
        logging.error(f"보호 블록 추가 오류: {str(e)}")
        return False

def get_recent_calls(limit=100):
    """최근 함수 호출 정보 조회"""
    try:
        # 시간순 정렬 (내림차순)
        sorted_calls = sorted(
            _storage["function_calls"], 
            key=lambda x: x["call_time"], 
            reverse=True
        )
        return sorted_calls[:limit]
    except Exception as e:
        logging.error(f"최근 호출 조회 오류: {str(e)}")
        return []

def get_recent_changes(limit=100):
    """최근 코드 변경 정보 조회"""
    try:
        # 시간순 정렬 (내림차순)
        sorted_changes = sorted(
            _storage["changes"], 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        return sorted_changes[:limit]
    except Exception as e:
        logging.error(f"최근 변경 조회 오류: {str(e)}")
        return []

def get_recent_errors(limit=100):
    """최근 에러 정보 조회"""
    try:
        # 시간순 정렬 (내림차순)
        sorted_errors = sorted(
            _storage["errors"], 
            key=lambda x: x["timestamp"], 
            reverse=True
        )
        return sorted_errors[:limit]
    except Exception as e:
        logging.error(f"최근 에러 조회 오류: {str(e)}")
        return []

def get_protected_functions():
    """보호된 함수 목록 조회"""
    try:
        return _storage["protected_functions"]
    except Exception as e:
        logging.error(f"보호 함수 조회 오류: {str(e)}")
        return []

def get_protected_blocks():
    """보호된 코드 블록 목록 조회"""
    try:
        return _storage["protected_blocks"]
    except Exception as e:
        logging.error(f"보호 블록 조회 오류: {str(e)}")
        return []

def close_connection():
    """연결 종료 (메모리 저장소에서는 아무 작업 안 함)"""
    pass

def close_all_connections():
    """모든 연결 종료 (메모리 저장소에서는 아무 작업 안 함)"""
    pass
