"""
함수 호출 추적 시스템
함수 간의 호출 관계를 추적하고 기록하는 모듈
"""

import sys
import inspect
import traceback
import time
import os
import sqlite3
from datetime import datetime

# 상대 경로로 storage 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from storage.db_manager import DBManager

class CallTracer:
    """함수 호출을 추적하는 클래스"""
    
    def __init__(self):
        self.is_tracing = False
        self.monitored_modules = []
        self.db_manager = DBManager()
        self.call_stack = []
        
    def start_tracing(self, modules_to_monitor=None):
        """호출 추적 시작
        
        Args:
            modules_to_monitor: 모니터링할 모듈 목록. None이면 모든 모듈 추적
        """
        if modules_to_monitor:
            self.monitored_modules = modules_to_monitor
        
        self.is_tracing = True
        sys.settrace(self._trace_calls)
        print(f"호출 추적 시작됨. 모니터링 모듈: {self.monitored_modules}")
    
    def stop_tracing(self):
        """호출 추적 중지"""
        self.is_tracing = False
        sys.settrace(None)
        print("호출 추적 중지됨")
    
    def _trace_calls(self, frame, event, arg):
        """호출 추적 함수
        
        Args:
            frame: 현재 스택 프레임
            event: 이벤트 타입 ('call', 'line', 'return', 'exception' 등)
            arg: 이벤트별 추가 정보
        
        Returns:
            다음 호출을 위한 트레이스 함수
        """
        if not self.is_tracing:
            return None
        
        if event == 'call':
            # 호출된 함수 정보 수집
            func_name = frame.f_code.co_name
            module_name = frame.f_globals.get('__name__', '')
            file_path = frame.f_code.co_filename
            
            # 모니터링 대상 검사
            if self.monitored_modules and module_name is not None:
                # 모듈 이름이 None인 경우 처리
                is_monitored = any(m for m in self.monitored_modules if module_name.startswith(m))
                if not is_monitored:
                    return None
            
            # 내부 및 라이브러리 함수 제외
            if file_path is None or file_path.startswith('<') or (isinstance(file_path, str) and 'site-packages' in file_path):
                return None
            
            # 호출 정보 저장
            caller = None
            if self.call_stack:
                caller = self.call_stack[-1]
            
            call_info = {
                'caller': caller,
                'callee': func_name,
                'module': module_name,
                'file_path': file_path,
                'timestamp': datetime.now(),
                'args': str(inspect.getargvalues(frame))
            }
            
            # 콜 스택에 추가
            self.call_stack.append(func_name)
            
            # DB에 저장
            if caller:  # 호출자가 있을 때만 저장 (최상위 호출은 제외)
                try:
                    self.db_manager.store_function_call(
                        caller=caller,
                        callee=func_name,
                        module=module_name,
                        call_time=call_info['timestamp'],
                        args=call_info['args']
                    )
                except Exception as e:
                    print(f"함수 호출 저장 중 오류: {str(e)}")
            
            return self._trace_calls
        
        elif event == 'return':
            # 함수 반환 시 스택에서 제거
            if self.call_stack:
                self.call_stack.pop()
            
            return self._trace_calls
        
        elif event == 'exception':
            # 예외 발생 처리
            if not self.call_stack:
                return self._trace_calls
                
            exc_type, exc_value, exc_traceback = arg
            
            # 현재 함수 이름 (예외 발생 함수)
            func_name = self.call_stack[-1] if self.call_stack else frame.f_code.co_name
            
            # 에러 정보 저장
            try:
                self.db_manager.store_error(
                    function_name=func_name,
                    error_type=exc_type.__name__,
                    error_message=str(exc_value),
                    stack_trace=traceback.format_exception(exc_type, exc_value, exc_traceback),
                    context=str(inspect.getargvalues(frame))
                )
            except Exception as e:
                print(f"에러 정보 저장 중 오류: {str(e)}")
            
            return self._trace_calls
        
        return self._trace_calls
    
    def get_call_graph(self, function_name=None, depth=2):
        """함수의 호출 그래프 데이터 가져오기
        
        Args:
            function_name: 시작 함수 이름. None이면 모든 호출 그래프
            depth: 호출 깊이
            
        Returns:
            nodes와 edges 딕셔너리 포함하는 그래프 데이터
        """
        try:
            return self.db_manager.get_call_graph(function_name, depth)
        except Exception as e:
            print(f"호출 그래프 조회 중 오류: {str(e)}")
            # 빈 그래프 반환
            return {"nodes": [], "edges": []}
    
    def get_error_data(self, function_name=None, limit=50):
        """에러 데이터 가져오기
        
        Args:
            function_name: 특정 함수의 에러만 가져오기. None이면 모든 에러
            limit: 가져올 최대 에러 수
            
        Returns:
            에러 정보 목록
        """
        try:
            return self.db_manager.get_errors(function_name, limit)
        except Exception as e:
            print(f"에러 데이터 조회 중 오류: {str(e)}")
            # 빈 리스트 반환
            return []


# 전역 인스턴스 생성
call_tracer = CallTracer()
