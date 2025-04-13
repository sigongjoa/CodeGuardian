#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 보호 대상 스캐너
파일을 스캔하여 보호할 함수와 코드 블록을 자동으로 찾고 등록
"""

import os
import ast
import hashlib
import re
import logging
from pathlib import Path

from src.storage.storage_manager import (
    add_protected_function,
    add_protected_block,
    get_protected_functions,
    get_protected_blocks
)

def scan_directory(directory_path):
    """디렉토리 스캔하여 보호 대상 찾기"""
    results = {
        "functions": [],
        "blocks": []
    }
    
    logging.info(f"디렉토리 스캔 시작: {directory_path}")
    
    try:
        # 디렉토리 내 모든 Python 파일 스캔
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    logging.info(f"파일 스캔 중: {file_path}")
                    
                    # 데코레이터 기반 보호 함수 검색
                    decorator_functions = scan_for_decorator_protected(file_path)
                    results["functions"].extend(decorator_functions)
                    
                    # 주석 기반 보호 블록 검색
                    comment_blocks = scan_for_comment_protected(file_path)
                    results["blocks"].extend(comment_blocks)
        
        logging.info(f"스캔 완료: {len(results['functions'])} 함수, {len(results['blocks'])} 블록 발견")
    except Exception as e:
        logging.error(f"디렉토리 스캔 오류: {str(e)}")
    
    return results

def scan_for_decorator_protected(file_path):
    """데코레이터로 보호된 함수 찾기"""
    protected_functions = []
    
    try:
        # 파일 내용 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST 파싱
        tree = ast.parse(content)
        
        # 함수 정의 검색
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 데코레이터 확인
                for decorator in node.decorator_list:
                    # 'protect' 데코레이터 찾기
                    if (isinstance(decorator, ast.Name) and decorator.id == 'protect') or \
                       (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == 'protect'):
                        
                        # 함수 코드 추출
                        func_lines = content.splitlines()[node.lineno-1:node.end_lineno]
                        func_code = '\n'.join(func_lines)
                        
                        # 해시 계산
                        func_hash = hashlib.sha256(func_code.encode('utf-8')).hexdigest()
                        
                        # 보호 함수 정보 추가
                        protected_functions.append({
                            "file_path": file_path,
                            "function_name": node.name,
                            "hash": func_hash,
                            "protection_type": "decorator"
                        })
                        
                        logging.info(f"데코레이터 보호 함수 발견: {node.name} in {file_path}")
                        
                        # 보호 함수 등록
                        add_protected_function(file_path, node.name, func_hash, "decorator")
        
    except Exception as e:
        logging.error(f"데코레이터 보호 함수 스캔 오류 ({file_path}): {str(e)}")
    
    return protected_functions

def scan_for_comment_protected(file_path):
    """주석으로 보호된 코드 블록 찾기"""
    protected_blocks = []
    
    try:
        # 파일 내용 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        # 주석 찾기
        start_line = None
        
        for i, line in enumerate(content, 1):
            # 시작 주석 찾기
            if "@LOCK: START" in line and start_line is None:
                start_line = i
            
            # 종료 주석 찾기
            elif "@LOCK: END" in line and start_line is not None:
                end_line = i
                
                # 블록 코드 추출
                block_lines = content[start_line-1:end_line]
                block_code = ''.join(block_lines)
                
                # 해시 계산
                block_hash = hashlib.sha256(block_code.encode('utf-8')).hexdigest()
                
                # 보호 블록 정보 추가
                protected_blocks.append({
                    "file_path": file_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "hash": block_hash,
                    "protection_type": "comment"
                })
                
                logging.info(f"주석 보호 블록 발견: 라인 {start_line}-{end_line} in {file_path}")
                
                # 보호 블록 등록
                add_protected_block(file_path, start_line, end_line, block_hash, "comment")
                
                # 초기화
                start_line = None
        
    except Exception as e:
        logging.error(f"주석 보호 블록 스캔 오류 ({file_path}): {str(e)}")
    
    return protected_blocks

def register_project(project_path):
    """프로젝트 등록 및 보호 대상 스캔"""
    logging.info(f"프로젝트 등록 및 스캔 시작: {project_path}")
    
    # 경로 확인
    if not os.path.exists(project_path):
        logging.error(f"프로젝트 경로가 존재하지 않습니다: {project_path}")
        return False
    
    # 보호 대상 스캔
    results = scan_directory(project_path)
    
    # 결과 확인
    if results["functions"] or results["blocks"]:
        logging.info(f"프로젝트 등록 성공: {len(results['functions'])} 함수, {len(results['blocks'])} 블록")
        return True
    else:
        logging.warning(f"프로젝트에서 보호 대상을 찾지 못했습니다: {project_path}")
        return False

def get_project_status(project_path=None):
    """프로젝트의 보호 상태 가져오기"""
    functions = get_protected_functions()
    blocks = get_protected_blocks()
    
    # 특정 프로젝트만 필터링
    if project_path:
        functions = [f for f in functions if f["file_path"].startswith(project_path)]
        blocks = [b for b in blocks if b["file_path"].startswith(project_path)]
    
    return {
        "functions": functions,
        "blocks": blocks,
        "total_functions": len(functions),
        "total_blocks": len(blocks)
    }
