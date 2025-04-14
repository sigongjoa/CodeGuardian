#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
테스트 예제 파일
에러 분석 탭에서 사용할 간단한 테스트 케이스입니다.
"""

import unittest
import sys
import time

# 디버그용 print 문 추가
print("테스트 시작")

def calculate_average(numbers):
    """리스트의 평균을 계산하는 함수"""
    if not numbers:
        # 빈 리스트인 경우 에러 발생
        raise ValueError("빈 리스트의 평균을 계산할 수 없습니다.")
    return sum(numbers) / len(numbers)

def process_data(a, b, c, d):
    """데이터 처리 함수"""
    # 디버그용 print 문 추가
    print(f"process_data 호출: {a}, {b}, {c}, {d}")
    
    result = a + b * c - d
    return result

class TestSampleFunctions(unittest.TestCase):
    """샘플 함수 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 디버그용 print 문 추가
        print("\n테스트 케이스 설정")
    
    def test_process_data(self):
        """process_data 함수 테스트"""
        # 디버그용 print 문 추가
        print("process_data 테스트 시작")
        
        result = process_data(1, 2, 3, 4)
        self.assertEqual(result, 3)  # 1 + 2*3 - 4 = 3
        
        # 디버그용 print 문 추가
        print("process_data 테스트 완료")
    
    def test_calculate_average(self):
        """calculate_average 함수 테스트"""
        # 디버그용 print 문 추가
        print("calculate_average 테스트 시작")
        
        # 정상 케이스
        result = calculate_average([1, 2, 3, 4, 5])
        self.assertEqual(result, 3.0)
        
        # 에러 케이스 (일부러 에러 발생)
        with self.assertRaises(ValueError):
            calculate_average([])
        
        # 디버그용 print 문 추가
        print("calculate_average 테스트 완료")
    
    def test_that_fails(self):
        """일부러 실패하는 테스트"""
        # 디버그용 print 문 추가
        print("실패하는 테스트 시작")
        
        # 잠시 대기 (테스트 실행 시간 시뮬레이션)
        time.sleep(1)
        
        # 실패하는 assertion
        self.assertEqual(1, 2, "이 테스트는 일부러 실패합니다")
        
        # 디버그용 print 문 추가 (실행되지 않음)
        print("실패하는 테스트 완료")

if __name__ == "__main__":
    # 디버그용 print 문 추가
    print("테스트 시작 - __main__")
    unittest.main()
