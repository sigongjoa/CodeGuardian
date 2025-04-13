#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 이벤트 시스템
모듈 간 통신을 위한 이벤트 버스 구현
"""

from PyQt5.QtCore import QObject, pyqtSignal

class CoreEvents(QObject):
    """코어 이벤트 클래스"""
    
    # 코드 변경 감지 시 발생하는 시그널
    code_changed = pyqtSignal(str, str, str)  # file_path, function_name, change_type
    
    # 함수 호출 감지 시그널
    function_called = pyqtSignal(str, str, float)  # caller, callee, timestamp
    
    # 보호 상태 변경 시그널
    protection_status_changed = pyqtSignal(str, bool)  # function_name, is_protected
    
    # 에러 감지 시그널
    error_detected = pyqtSignal(str, str, str)  # function_name, error_type, stack_trace

# 전역 이벤트 버스 인스턴스
event_bus = CoreEvents()
