#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
호출 추적 테스트를 위한 메인 애플리케이션
"""

from user_module import UserManager
from data_module import DataProcessor
import time

class Application:
    """테스트 애플리케이션"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.data_processor = DataProcessor()
    
    def start(self):
        """애플리케이션 시작"""
        print("애플리케이션을 시작합니다...")
        
        # 사용자 처리
        self.process_users()
        
        # 데이터 처리
        self.process_data()
        
        print("애플리케이션 실행 완료")
    
    def process_users(self):
        """사용자 처리 로직"""
        print("사용자 처리 중...")
        
        # 사용자 추가
        self.user_manager.add_user("user1", "email1@test.com")
        self.user_manager.add_user("user2", "email2@test.com")
        self.user_manager.add_user("admin", "admin@test.com", is_admin=True)
        
        # 사용자 인증
        self.user_manager.authenticate("user1", "password123")
        self.user_manager.authenticate("admin", "admin_password")
        
        # 권한 확인
        self.user_manager.check_permission("admin", "delete_data")
    
    def process_data(self):
        """데이터 처리 로직"""
        print("데이터 처리 중...")
        
        # 테스트 데이터 생성
        test_data = [
            {"id": 1, "value": 10, "category": "A"},
            {"id": 2, "value": 20, "category": "B"},
            {"id": 3, "value": 30, "category": "A"},
            {"id": 4, "value": 40, "category": "C"},
            {"id": 5, "value": 50, "category": "B"}
        ]
        
        # 데이터 처리
        processed_data = self.data_processor.process(test_data)
        
        # 데이터 필터링
        filtered_data = self.data_processor.filter_by_category(processed_data, "A")
        
        # 데이터 분석
        result = self.data_processor.analyze(filtered_data)
        
        print(f"데이터 분석 결과: {result}")

def main():
    """메인 함수"""
    app = Application()
    app.start()

if __name__ == "__main__":
    main()
