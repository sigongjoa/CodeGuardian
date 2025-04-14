import os
import re
import sqlite3
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from src.core.settings import app_settings

# 디버그 메시지
print("함수 관리자 모듈 로드됨")

def get_available_functions():
    """
    사용 가능한 모든 함수 목록을 반환합니다.
    
    Returns:
        list: 함수 이름 리스트
    """
    try:
        # 데이터베이스 연결
        db_path = app_settings.get("storage", "db_path", "data/codeguardian.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 함수 목록 쿼리
        cursor.execute("SELECT function_name FROM functions ORDER BY function_name")
        functions = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # 함수가 없을 경우 예시 함수 반환 (개발용)
        if not functions:
            functions = [
                "main", "process_data", "calculate_average", "generate_report", 
                "validate_input", "load_config", "save_results", "handle_error",
                "calculate_division", "recursive_error", "helper_function"
            ]
            print(f"데이터베이스에 함수가 없어 예시 함수 {len(functions)}개를 사용합니다.")
        else:
            print(f"데이터베이스에서 {len(functions)}개 함수를 로드했습니다.")
            
        return functions
    except Exception as e:
        print(f"함수 목록 로드 중 오류 발생: {str(e)}")
        # 에러 발생 시 기본 함수 목록 반환
        return ["main", "process_data", "calculate_average", "generate_report"]

def get_function_code(function_name):
    """
    지정된 함수의 코드를 HTML 형식으로 반환합니다.
    
    Args:
        function_name (str): 함수 이름
        
    Returns:
        str: HTML로 포맷팅된 함수 코드
    """
    try:
        # 데이터베이스에서 함수 코드 검색
        db_path = app_settings.get("storage", "db_path", "data/codeguardian.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT file_path, source_code FROM functions WHERE function_name = ?", 
            (function_name,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            file_path, source_code = result
            print(f"함수 코드 로드됨: {function_name}")
            
            # Pygments로 코드 구문 강조
            formatter = HtmlFormatter(style='colorful', linenos=True)
            highlighted_code = highlight(source_code, PythonLexer(), formatter)
            
            # CSS 스타일 추가
            css = formatter.get_style_defs('.highlight')
            html_code = f"<style>{css}</style>{highlighted_code}"
            
            return html_code
        else:
            # 데이터베이스에 없을 경우 예시 코드 생성 (개발용)
            example_code = generate_example_code(function_name)
            print(f"데이터베이스에 {function_name} 함수가 없어 예시 코드를 생성합니다.")
            
            # 코드 구문 강조
            formatter = HtmlFormatter(style='colorful', linenos=True)
            highlighted_code = highlight(example_code, PythonLexer(), formatter)
            
            # CSS 스타일 추가
            css = formatter.get_style_defs('.highlight')
            html_code = f"<style>{css}</style>{highlighted_code}"
            
            return html_code
    except Exception as e:
        print(f"함수 코드 로드 중 오류 발생: {str(e)}")
        return f"<pre>함수 코드를 로드할 수 없습니다: {str(e)}</pre>"

def get_function_info(function_name):
    """
    함수의 메타 정보를 반환합니다.
    
    Args:
        function_name (str): 함수 이름
        
    Returns:
        dict: 함수 메타 정보
    """
    try:
        # 데이터베이스에서 함수 정보 검색
        db_path = app_settings.get("storage", "db_path", "data/codeguardian.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 함수 기본 정보
        cursor.execute(
            "SELECT file_path, is_protected, module_name, type FROM functions WHERE function_name = ?", 
            (function_name,)
        )
        result = cursor.fetchone()
        
        if result:
            file_path, is_protected, module_name, func_type = result
            
            # 호출하는 함수 목록 (이 함수가 호출하는 다른 함수들)
            cursor.execute(
                "SELECT callee FROM function_calls WHERE caller = ? GROUP BY callee", 
                (function_name,)
            )
            callees = [row[0] for row in cursor.fetchall()]
            
            # 호출되는 함수 목록 (이 함수를 호출하는 다른 함수들)
            cursor.execute(
                "SELECT caller FROM function_calls WHERE callee = ? GROUP BY caller", 
                (function_name,)
            )
            callers = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            info = {
                "module": module_name or os.path.basename(file_path),
                "file_path": file_path,
                "type": func_type or "일반 함수",
                "is_protected": bool(is_protected),
                "callees": callees or ["없음"],
                "callers": callers or ["없음"]
            }
            
            print(f"함수 정보 로드됨: {function_name}")
            return info
        else:
            # 데이터베이스에 없을 경우 예시 정보 생성 (개발용)
            conn.close()
            
            info = generate_example_info(function_name)
            print(f"데이터베이스에 {function_name} 함수가 없어 예시 정보를 생성합니다.")
            return info
    except Exception as e:
        print(f"함수 정보 로드 중 오류 발생: {str(e)}")
        return {
            "module": "알 수 없음",
            "file_path": "알 수 없음",
            "type": "일반 함수",
            "is_protected": False,
            "callees": ["없음"],
            "callers": ["없음"]
        }

def generate_example_code(function_name):
    """
    함수명에 따라 예시 코드를 생성합니다. (개발 및 테스트용)
    
    Args:
        function_name (str): 함수 이름
        
    Returns:
        str: 예시 코드
    """
    if function_name == "main":
        return '''def main():
    """메인 함수"""
    print("테스트 시작")
    try:
        process_data(1, 2, 'four', 5])
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        
    try:
        calculate_average([])
    except Exception as e:
        print(f"에러 발생: {str(e)}")
'''
    elif function_name == "process_data":
        return '''def process_data(a, b, c, d):
    """데이터 처리 함수"""
    print("데이터 처리 중...")
    result = a + b + c + d
    return result
'''
    elif function_name == "calculate_average":
        return '''def calculate_average(numbers):
    """평균 계산 함수"""
    if not numbers:
        raise ValueError("빈 리스트로 평균을 계산할 수 없습니다")
    
    total = sum(numbers)
    return total / len(numbers)
'''
    elif function_name == "generate_report":
        return '''def generate_report(data, format="json"):
    """보고서 생성 함수"""
    if format == "json":
        return json.dumps(data)
    elif format == "csv":
        return ",".join(str(item) for item in data)
    else:
        raise ValueError(f"지원하지 않는 형식: {format}")
'''
    else:
        return f'''def {function_name}(arg1, arg2=None):
    """
    {function_name} 함수
    
    Args:
        arg1: 첫 번째 인자
        arg2: 두 번째 인자 (기본값: None)
        
    Returns:
        결과값
    """
    # 함수 본문
    result = process_data(arg1, arg2)
    return result
'''

def generate_example_info(function_name):
    """
    함수명에 따라 예시 메타 정보를 생성합니다. (개발 및 테스트용)
    
    Args:
        function_name (str): 함수 이름
        
    Returns:
        dict: 예시 메타 정보
    """
    function_info = {
        "main": {
            "module": "test_errors.py",
            "file_path": "src/examples/test_errors.py",
            "type": "일반 함수",
            "is_protected": True,
            "callees": ["process_data", "calculate_average"],
            "callers": ["없음"]
        },
        "process_data": {
            "module": "test_errors.py",
            "file_path": "src/examples/test_errors.py",
            "type": "일반 함수",
            "is_protected": False,
            "callees": ["없음"],
            "callers": ["main", "generate_report"]
        },
        "calculate_average": {
            "module": "test_errors.py",
            "file_path": "src/examples/test_errors.py",
            "type": "일반 함수",
            "is_protected": False,
            "callees": ["없음"],
            "callers": ["main"]
        },
        "generate_report": {
            "module": "test_errors.py",
            "file_path": "src/examples/test_errors.py",
            "type": "일반 함수",
            "is_protected": False,
            "callees": ["process_data"],
            "callers": ["없음"]
        }
    }
    
    # 기본 함수 정보가 있으면 해당 정보 반환, 없으면 기본 정보 생성
    if function_name in function_info:
        return function_info[function_name]
    else:
        return {
            "module": "test_module.py",
            "file_path": f"src/examples/test_module.py",
            "type": "일반 함수",
            "is_protected": False,
            "callees": ["process_data"],
            "callers": ["없음"]
        }
