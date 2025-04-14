import sqlite3
import os
from src.core.settings import app_settings

def generate_call_graph(function_name, depth=2):
    """
    함수 호출 그래프 데이터 생성
    
    Args:
        function_name (str): 함수 이름
        depth (int): 호출 깊이 (기본값: 2)
        
    Returns:
        dict: 그래프 데이터 (nodes, links)
    """
    try:
        # 데이터베이스 연결
        db_path = app_settings.get("storage", "db_path", "data/codeguardian.db")
        
        # 데이터베이스 파일이 존재하는지 확인
        if not os.path.exists(db_path):
            print(f"데이터베이스 파일이 없습니다: {db_path}, 예시 데이터 사용")
            return generate_example_graph(function_name, depth)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 함수 정보 가져오기
        cursor.execute(
            "SELECT function_name, module_name, is_protected FROM functions WHERE function_name = ?",
            (function_name,)
        )
        function_info = cursor.fetchone()
        
        if not function_info:
            print(f"함수 정보를 찾을 수 없습니다: {function_name}, 예시 데이터 사용")
            conn.close()
            return generate_example_graph(function_name, depth)
        
        # 노드와 링크를 저장할 딕셔너리 및 집합
        nodes = {}  # id -> node
        links = set()  # (source, target) -> 중복 방지
        
        # 시작 함수를 노드로 추가
        nodes[function_name] = {
            "id": function_name,
            "label": function_name,
            "is_center": True,
            "is_protected": bool(function_info[2]),
            "depth": 0
        }
        
        # BFS로 호출 그래프 구성
        process_queue = [(function_name, 0)]  # (함수명, 깊이)
        visited = {function_name}
        
        while process_queue:
            current_func, current_depth = process_queue.pop(0)
            
            # 최대 깊이 체크
            if current_depth >= depth:
                continue
            
            # 호출하는 함수 (outgoing)
            cursor.execute(
                "SELECT callee FROM function_calls WHERE caller = ?",
                (current_func,)
            )
            callees = cursor.fetchall()
            
            for callee_row in callees:
                callee = callee_row[0]
                
                # 함수 정보 가져오기
                cursor.execute(
                    "SELECT is_protected FROM functions WHERE function_name = ?",
                    (callee,)
                )
                callee_info = cursor.fetchone()
                is_protected = bool(callee_info[0]) if callee_info else False
                
                # 에러 여부 확인
                cursor.execute(
                    "SELECT COUNT(*) FROM errors WHERE function_name = ?",
                    (callee,)
                )
                error_count = cursor.fetchone()[0]
                is_error = error_count > 0
                
                # 노드 추가
                if callee not in nodes:
                    nodes[callee] = {
                        "id": callee,
                        "label": callee,
                        "is_protected": is_protected,
                        "is_error": is_error,
                        "depth": current_depth + 1
                    }
                
                # 링크 추가
                link_tuple = (current_func, callee)
                if link_tuple not in links:
                    links.add(link_tuple)
                
                # 방문하지 않은 함수면 큐에 추가
                if callee not in visited:
                    visited.add(callee)
                    process_queue.append((callee, current_depth + 1))
            
            # 함수를 호출하는 함수 (incoming) - 깊이 1까지만
            if current_depth < 1:
                cursor.execute(
                    "SELECT caller FROM function_calls WHERE callee = ?",
                    (current_func,)
                )
                callers = cursor.fetchall()
                
                for caller_row in callers:
                    caller = caller_row[0]
                    
                    # 자기 자신은 건너뛰기
                    if caller == current_func:
                        continue
                    
                    # 함수 정보 가져오기
                    cursor.execute(
                        "SELECT is_protected FROM functions WHERE function_name = ?",
                        (caller,)
                    )
                    caller_info = cursor.fetchone()
                    is_protected = bool(caller_info[0]) if caller_info else False
                    
                    # 에러 여부 확인
                    cursor.execute(
                        "SELECT COUNT(*) FROM errors WHERE function_name = ?",
                        (caller,)
                    )
                    error_count = cursor.fetchone()[0]
                    is_error = error_count > 0
                    
                    # 노드 추가
                    if caller not in nodes:
                        nodes[caller] = {
                            "id": caller,
                            "label": caller,
                            "is_protected": is_protected,
                            "is_error": is_error,
                            "depth": current_depth + 1
                        }
                    
                    # 링크 추가
                    link_tuple = (caller, current_func)
                    if link_tuple not in links:
                        links.add(link_tuple)
                    
                    # 방문하지 않은 함수면 큐에 추가 (깊이 1까지만)
                    if caller not in visited and current_depth < 1:
                        visited.add(caller)
                        process_queue.append((caller, current_depth + 1))
        
        conn.close()
        
        # 결과 구성
        nodes_list = list(nodes.values())
        links_list = [{"source": source, "target": target} for source, target in links]
        
        # 디버그 메시지
        print(f"함수 호출 그래프 생성: {function_name}, 노드 {len(nodes_list)}개, 링크 {len(links_list)}개")
        
        return {
            "nodes": nodes_list,
            "links": links_list
        }
    
    except Exception as e:
        print(f"호출 그래프 생성 오류: {str(e)}")
        return generate_example_graph(function_name, depth)

def generate_example_graph(function_name, depth=2):
    """
    예시 호출 그래프 데이터 생성 (개발 및 테스트용)
    
    Args:
        function_name (str): 함수 이름
        depth (int): 호출 깊이
        
    Returns:
        dict: 그래프 데이터 (nodes, links)
    """
    print(f"예시 호출 그래프 생성: {function_name}, 깊이 {depth}")
    
    # 예시 함수 관계 정의
    function_relations = {
        "main": ["process_data", "calculate_average", "validate_input"],
        "process_data": ["helper_function", "validate_input"],
        "calculate_average": ["validate_input"],
        "generate_report": ["process_data", "format_output"],
        "validate_input": ["check_type", "check_range"],
        "helper_function": ["calculate_division"],
        "calculate_division": ["recursive_error"],
        "recursive_error": ["recursive_error", "helper_function"],
        "format_output": []
    }
    
    # 함수가 예시 관계에 없으면 기본 패턴 생성
    if function_name not in function_relations:
        callees = [f"{function_name}_helper", f"{function_name}_util", f"validate_{function_name}"]
        function_relations[function_name] = callees
        
        for callee in callees:
            function_relations[callee] = []
    
    # 노드 및 링크 구성
    nodes = {}
    links = set()
    
    # 시작 함수를 노드로 추가
    nodes[function_name] = {
        "id": function_name,
        "label": function_name,
        "is_center": True,
        "is_protected": function_name in ["main", "validate_input"],
        "is_error": function_name in ["recursive_error", "calculate_division"],
        "depth": 0
    }
    
    # BFS로 그래프 구성
    process_queue = [(function_name, 0)]  # (함수명, 깊이)
    visited = {function_name}
    
    while process_queue:
        current_func, current_depth = process_queue.pop(0)
        
        # 최대 깊이 체크
        if current_depth >= depth:
            continue
        
        # 호출하는 함수들 처리
        callees = function_relations.get(current_func, [])
        
        for callee in callees:
            # 노드 추가
            if callee not in nodes:
                nodes[callee] = {
                    "id": callee,
                    "label": callee,
                    "is_protected": callee in ["main", "validate_input"],
                    "is_error": callee in ["recursive_error", "calculate_division"],
                    "depth": current_depth + 1
                }
            
            # 링크 추가
            link_tuple = (current_func, callee)
            if link_tuple not in links:
                links.add(link_tuple)
            
            # 방문하지 않은 함수면 큐에 추가
            if callee not in visited:
                visited.add(callee)
                process_queue.append((callee, current_depth + 1))
        
        # 호출되는 함수들 처리 (깊이 1까지만)
        if current_depth < 1:
            for potential_caller, callees in function_relations.items():
                if current_func in callees:
                    caller = potential_caller
                    
                    # 자기 자신은 건너뛰기
                    if caller == current_func:
                        continue
                    
                    # 노드 추가
                    if caller not in nodes:
                        nodes[caller] = {
                            "id": caller,
                            "label": caller,
                            "is_protected": caller in ["main", "validate_input"],
                            "is_error": caller in ["recursive_error", "calculate_division"],
                            "depth": current_depth + 1
                        }
                    
                    # 링크 추가
                    link_tuple = (caller, current_func)
                    if link_tuple not in links:
                        links.add(link_tuple)
                    
                    # 방문하지 않은 함수면 큐에 추가 (깊이 1까지만)
                    if caller not in visited and current_depth < 1:
                        visited.add(caller)
                        process_queue.append((caller, current_depth + 1))
    
    # 결과 구성
    nodes_list = list(nodes.values())
    links_list = [{"source": source, "target": target} for source, target in links]
    
    # 디버그 메시지
    print(f"예시 호출 그래프 생성 완료: 노드 {len(nodes_list)}개, 링크 {len(links_list)}개")
    
    return {
        "nodes": nodes_list,
        "links": links_list
    }
