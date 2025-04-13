#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터 처리 모듈
호출 추적 테스트용
"""

class DataProcessor:
    """데이터 처리 클래스"""
    
    def __init__(self):
        """초기화"""
        self.processing_count = 0
    
    def process(self, data):
        """데이터 처리"""
        self.processing_count += 1
        print(f"데이터 처리 중... (처리 횟수: {self.processing_count})")
        
        # 데이터 처리 로직 (간단한 예시)
        processed = []
        for item in data:
            # 값 변환 등의 처리
            processed_item = dict(item)  # 복사
            processed_item["value"] = item["value"] * 2  # 값 두 배로
            processed_item["processed"] = True
            processed.append(processed_item)
        
        # 추가 처리를 위한 내부 메서드 호출
        self._post_process(processed)
        
        return processed
    
    def _post_process(self, data):
        """추가 데이터 처리 (내부 메서드)"""
        # 내부적인 추가 처리 로직
        for item in data:
            item["processed_at"] = self._get_timestamp()
    
    def _get_timestamp(self):
        """타임스탬프 생성 (내부 메서드)"""
        import time
        return time.time()
    
    def filter_by_category(self, data, category):
        """카테고리별 필터링"""
        print(f"카테고리 '{category}'로 필터링 중...")
        
        # 필터링 로직
        filtered = [item for item in data if item["category"] == category]
        
        return filtered
    
    def analyze(self, data):
        """데이터 분석"""
        print(f"데이터 분석 중... (항목 수: {len(data)})")
        
        # 분석 로직 (간단한 예시: 평균값 계산)
        if not data:
            return {"average": 0, "count": 0}
        
        total = sum(item["value"] for item in data)
        average = total / len(data)
        
        # 추가 분석 수행
        stats = self._calculate_statistics(data)
        
        result = {
            "average": average,
            "count": len(data),
            "stats": stats
        }
        
        return result
    
    def _calculate_statistics(self, data):
        """통계 계산 (내부 메서드)"""
        if not data:
            return {"min": 0, "max": 0}
        
        values = [item["value"] for item in data]
        
        return {
            "min": min(values),
            "max": max(values),
            "sum": sum(values)
        }
