#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
사용자 관리 모듈
호출 추적 테스트용
"""

import hashlib
import time

class UserManager:
    """사용자 관리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.users = {}
        self.sessions = {}
    
    def add_user(self, username, email, is_admin=False):
        """사용자 추가"""
        # 실제로는 더 복잡한 로직이 있을 것
        user_id = len(self.users) + 1
        
        self.users[username] = {
            "id": user_id,
            "email": email,
            "is_admin": is_admin,
            "created_at": time.time()
        }
        
        print(f"사용자 추가됨: {username} (관리자: {is_admin})")
        return user_id
    
    def authenticate(self, username, password):
        """사용자 인증"""
        # 실제로는 암호화된 비밀번호 비교 등이 필요함
        if username in self.users:
            # 인증 성공 가정
            session_id = self._create_session(username)
            print(f"인증 성공: {username}")
            return session_id
        
        print(f"인증 실패: {username}")
        return None
    
    def _create_session(self, username):
        """사용자 세션 생성 (내부 메서드)"""
        session_id = hashlib.md5(f"{username}:{time.time()}".encode()).hexdigest()
        self.sessions[session_id] = {
            "username": username,
            "created_at": time.time(),
            "expires_at": time.time() + 3600  # 1시간
        }
        return session_id
    
    def check_permission(self, username, permission):
        """사용자 권한 확인"""
        if username not in self.users:
            print(f"권한 확인 실패: 사용자 없음 - {username}")
            return False
        
        user = self.users[username]
        
        # 간단한 권한 확인 로직
        if permission == "delete_data" and not user["is_admin"]:
            print(f"권한 없음: {username} - {permission}")
            return False
        
        print(f"권한 확인 성공: {username} - {permission}")
        return True
    
    def get_user_info(self, username):
        """사용자 정보 조회"""
        if username in self.users:
            return self.users[username]
        return None
