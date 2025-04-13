"""
코드 가디언 에러 테스트 스크립트
여러 에러 유형을 발생시켜 에러 분석 기능 테스트
"""

import sys
import os
import traceback
import time

# 패키지 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 테스트 에러 함수 임포트
from tests.error_test import calculate_division, recursive_error, syntax_error_simulation, helper_function

# 코어 모듈 임포트 (데이터베이스 기록을 위해)
from src.core.core import code_guardian
from src.tracer.call_tracer import call_tracer

def test_zero_division():
    """0으로 나누기 에러 테스트"""
    print("0으로 나누기 에러 테스트 시작...")
    try:
        result = calculate_division(10, 0)
        print(f"결과: {result}")  # 실행되지 않음
    except Exception as e:
        print(f"0으로 나누기 에러 발생: {str(e)}")

def test_index_error():
    """인덱스 에러 테스트"""
    print("\n인덱스 에러 테스트 시작...")
    try:
        helper_function(5)  # 인덱스 에러 발생 코드 호출
    except Exception as e:
        print(f"인덱스 에러 발생: {str(e)}")

def test_type_error():
    """타입 에러 테스트"""
    print("\n타입 에러 테스트 시작...")
    try:
        helper_function(7)  # 타입 에러 발생 코드 호출
    except Exception as e:
        print(f"타입 에러 발생: {str(e)}")

def test_syntax_error():
    """구문 에러 테스트"""
    print("\n구문 에러 테스트 시작...")
    try:
        syntax_error_simulation()  # 구문 에러 발생 코드 호출
    except Exception as e:
        print(f"구문 에러 발생: {str(e)}")

def test_recursive_error():
    """재귀 호출 테스트"""
    print("\n재귀 호출 테스트 시작...")
    try:
        recursive_error(0)  # 재귀 호출 함수 시작 (10번째 호출에서 에러 발생)
    except Exception as e:
        print(f"재귀 호출 중 에러 발생: {str(e)}")

def manually_add_errors():
    """직접 에러 정보 데이터베이스에 추가"""
    print("\n에러 정보 직접 추가 중...")
    
    # DB 관리자에 직접 에러 정보 추가
    try:
        # 코드 가디언 DB 관리자 가져오기
        db_manager = code_guardian.db_manager
        
        # 에러 데이터 직접 삽입 테스트
        db_manager.store_error(
            function_name="test_function",
            error_type="TestError",
            error_message="This is a test error message",
            stack_trace="Traceback (most recent call last):\n  File 'test.py', line 10\n    raise TestError\nTestError: This is a test error message",
            context="args=(), kwargs={}"
        )
        
        db_manager.store_error(
            function_name="another_test",
            error_type="ValueError",
            error_message="Invalid value provided",
            stack_trace="Traceback (most recent call last):\n  File 'test.py', line 15\n    validate(x)\n  File 'test.py', line 5\n    raise ValueError\nValueError: Invalid value provided",
            context="args=(42,), kwargs={'test': True}"
        )
        
        print("에러 정보가 데이터베이스에 직접 추가되었습니다.")
    except Exception as e:
        print(f"에러 정보 직접 추가 중 오류 발생: {str(e)}")
        traceback.print_exc()

def main():
    """테스트 함수 실행"""
    print("=== CodeGuardian 에러 테스트 시작 ===")
    
    # 모니터링 시작
    test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tests/error_test.py'))
    print(f"테스트 파일 경로: {test_file}")
    
    try:
        # 먼저 DB에 직접 에러 추가 (모니터링 없이도 에러 데이터 확인 가능)
        manually_add_errors()
        
        # 모니터링 시작
        code_guardian.start_monitoring([test_file], ['tests'])
        
        # 각 에러 유형 테스트
        test_zero_division()
        test_index_error()
        test_type_error()
        test_syntax_error()
        test_recursive_error()
        
        # 잠시 대기 (에러 데이터 저장 시간 확보)
        print("\n데이터 저장 중... 잠시 대기")
        time.sleep(2)
        
        # 호출 추적 중지
        code_guardian.stop_monitoring()
        
        print("\n=== 테스트 완료 ===")
        
        # 기록된 에러 정보 확인
        try:
            errors = code_guardian.get_error_data()
            print(f"\n기록된 에러 수: {len(errors)}")
            
            # 호출 그래프 정보 확인
            graph = code_guardian.get_call_graph("recursive_error")
            if graph:
                nodes = graph.get("nodes", [])
                edges = graph.get("edges", [])
                print(f"recursive_error 함수 호출 그래프: 노드 {len(nodes)}개, 엣지 {len(edges)}개")
        except Exception as e:
            print(f"데이터 확인 중 오류: {str(e)}")
            traceback.print_exc()
    
    except Exception as e:
        print(f"테스트 실행 중 오류: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
