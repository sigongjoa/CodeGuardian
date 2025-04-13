#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
중요 함수를 포함하는 테스트 모듈
데코레이터 기반 보호 예시
"""

import hashlib
import time
from functools import wraps

# 보호 데코레이터 정의
def protect(func):
    """중요 함수를 보호하는 데코레이터"""
    
    # 함수 코드의 해시값 계산
    func_code = func.__code__
    code_str = func_code.co_code
    original_hash = hashlib.sha256(code_str).hexdigest()
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 실행 시 함수 코드 무결성 검사
        current_code = func.__code__.co_code
        current_hash = hashlib.sha256(current_code).hexdigest()
        
        if current_hash != original_hash:
            raise SecurityError(f"함수 '{func.__name__}'가 변경되었습니다!")
        
        # 원본 함수 실행
        return func(*args, **kwargs)
    
    # 원본 해시 저장
    wrapper._original_hash = original_hash
    return wrapper

class SecurityError(Exception):
    """보안 관련 예외"""
    pass

# 보호할 중요 함수들

@protect
def validate_user_credentials(username, password):
    """사용자 인증 정보 검증 (보호 대상)"""
    # 실제로는 더 복잡한 검증 로직이 있을 것
    if len(username) < 3 or len(password) < 8:
        return False
    
    # 간단한 검증 로직 (실제 환경에서는 안전하지 않음)
    valid_users = {
        "admin": "securepwd123",
        "user1": "userpassword1",
        "testuser": "test12345"
    }
    
    return username in valid_users and valid_users[username] == password

@protect
def calculate_sensitive_data(input_value, secret_key):
    """민감한 계산 수행 (보호 대상)"""
    # 보호해야 할 중요한 알고리즘
    result = 0
    for i in range(len(input_value)):
        char_val = ord(input_value[i]) if isinstance(input_value, str) else input_value[i]
        result += char_val * (i + 1) * ord(secret_key[i % len(secret_key)])
    
    return result % 10000

# 보호되지 않는 일반 함수
def format_output(data):
    """결과 포맷팅 (보호 필요 없음)"""
    return f"처리 결과: {data}"

# 테스트 함수
def test_functions():
    """모듈 테스트"""
    print("=== 보호된 함수 테스트 ===")
    
    # 인증 테스트
    print("인증 테스트:", validate_user_credentials("admin", "securepwd123"))
    
    # 계산 테스트
    print("계산 테스트:", calculate_sensitive_data("test_input", "secret"))
    
    # 출력 포맷팅
    print(format_output(12345))

if __name__ == "__main__":
    test_functions()
