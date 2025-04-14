"""
테스트용 에러 함수 모듈
CodeGuardian 에러 분석 기능 테스트를 위한 코드
"""

def calculate_division(a, b):
    """두 수를 나누는 함수
    
    테스트용 함수로, 의도적으로 0으로 나누기 에러를 발생시킨다.
    Args:
        a: 분자
        b: 분모
    Returns:
        a / b의 결과
    """
    try:
        return a / b
    except ZeroDivisionError:
        # 여기서 의도적으로 에러를 기록하게 함
        import traceback
        error_info = {
            "function_name": "calculate_division",
            "error_type": "ZeroDivisionError",
            "error_message": "Division by zero",
            "stack_trace": traceback.format_exc()
        }
        # 에러 정보를 저장 (실제로는 이 부분이 코드가드의 에러 추적 시스템과 연결됨)
        print(f"에러 정보 저장: {error_info}")
        raise

def recursive_error(depth=0):
    """재귀적으로 호출되어 스택 오버플로우를 발생시키는 함수
    
    Args:
        depth: 현재 재귀 깊이
    """
    if depth > 100:  # 스택 오버플로우를 방지하기 위한 안전장치
        return
    
    # 다른 함수 호출하여 호출 그래프 생성에 도움
    helper_function(depth)
    
    # 재귀 호출
    recursive_error(depth + 1)

def helper_function(value):
    """recursive_error 함수의 도우미 함수
    
    Args:
        value: 작업할 값
    """
    # 의도적으로 10으로 나눌 때 에러 발생
    if value == 10:
        calculate_division(1, 0)
    
    # 다른 에러 타입도 발생시키기
    try:
        if value == 5:
            # 인덱스 에러
            test_list = [1, 2, 3]
            print(test_list[10])
        elif value == 7:
            # 타입 에러
            print("text" + 123)
    except Exception as e:
        import traceback
        error_info = {
            "function_name": "helper_function",
            "error_type": str(type(e).__name__),
            "error_message": str(e),
            "stack_trace": traceback.format_exc()
        }
        print(f"에러 정보 저장: {error_info}")
        raise

def test_function():
    """테스트용 함수"""
    print("test_function 호출")
    calculate_division(1, 0)

def syntax_error_simulation():
    """구문 오류를 시뮬레이션하는 함수"""
    try:
        # eval을 사용하여 런타임에 구문 오류 발생시키기
        eval("print('Incomplete string)")
    except SyntaxError as e:
        import traceback
        error_info = {
            "function_name": "syntax_error_simulation",
            "error_type": "SyntaxError",
            "error_message": str(e),
            "stack_trace": traceback.format_exc()
        }
        print(f"에러 정보 저장: {error_info}")
        raise

# 테스트용 메인 함수
if __name__ == "__main__":
    try:
        # 0으로 나누기 에러 테스트
        calculate_division(10, 0)
    except:
        pass
    
    try:
        # 재귀 호출 테스트
        recursive_error()
    except:
        pass
    
    try:
        # 구문 오류 테스트
        syntax_error_simulation()
    except:
        pass
