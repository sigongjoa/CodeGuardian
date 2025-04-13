#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
보안 유틸리티 테스트 모듈
주석 기반 보호 예시
"""

import hashlib
import hmac
import time
import base64
import random

# 보호할 코드 블록 정의 (주석 기반)

def generate_secure_token(user_id, secret_key, expiry_seconds=3600):
    """보안 토큰 생성"""
    # @LOCK: START
    # 이 블록은 보안상 중요하므로 변경되지 않도록 보호됩니다
    timestamp = int(time.time())
    expiry = timestamp + expiry_seconds
    
    # 서명 데이터 생성
    message = f"{user_id}:{expiry}".encode('utf-8')
    digest = hmac.new(
        secret_key.encode('utf-8'),
        message,
        hashlib.sha256
    ).digest()
    
    signature = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
    
    # 토큰 조립
    token = f"{user_id}:{expiry}:{signature}"
    return base64.urlsafe_b64encode(token.encode('utf-8')).decode('utf-8')
    # @LOCK: END

def verify_secure_token(token, secret_key):
    """보안 토큰 검증"""
    try:
        # @LOCK: START
        # 이 블록은 보안상 중요하므로 변경되지 않도록 보호됩니다
        decoded = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
        user_id, expiry, signature = decoded.split(':', 2)
        
        # 만료 시간 검사
        current_time = int(time.time())
        if current_time > int(expiry):
            return False, "토큰이 만료되었습니다."
        
        # 서명 검증
        message = f"{user_id}:{expiry}".encode('utf-8')
        expected_digest = hmac.new(
            secret_key.encode('utf-8'),
            message,
            hashlib.sha256
        ).digest()
        
        expected_signature = base64.urlsafe_b64encode(expected_digest).decode('utf-8').rstrip('=')
        
        if signature != expected_signature:
            return False, "서명이 유효하지 않습니다."
        
        return True, user_id
        # @LOCK: END
    except Exception as e:
        return False, f"토큰 검증 오류: {str(e)}"

# 보호할 필요가 없는 일반 유틸리티 함수
def generate_random_string(length=12):
    """랜덤 문자열 생성"""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(random.choice(chars) for _ in range(length))

def format_timestamp(timestamp=None):
    """타임스탬프 포매팅"""
    if timestamp is None:
        timestamp = time.time()
    
    from datetime import datetime
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 테스트 함수
def test_secure_utils():
    """모듈 테스트"""
    print("=== 보안 유틸리티 테스트 ===")
    
    # 토큰 생성 및 검증 테스트
    secret_key = "tEsT_s3crEt_k3y"
    user_id = "test_user_123"
    
    token = generate_secure_token(user_id, secret_key, 60)
    print(f"생성된 토큰: {token}")
    
    valid, result = verify_secure_token(token, secret_key)
    print(f"토큰 검증 결과: {'성공' if valid else '실패'}, {result}")
    
    # 기타 유틸리티 테스트
    print(f"랜덤 문자열: {generate_random_string()}")
    print(f"현재 시간: {format_timestamp()}")

if __name__ == "__main__":
    test_secure_utils()
