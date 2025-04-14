#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CodeGuardian 테스트 스크립트
개발 중인 기능들의 동작을 확인하기 위한 스크립트입니다.
"""

import sys
import os
import time

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 디버그 모드 설정
DEBUG = True

def debug_print(message):
    """디버그 메시지 출력"""
    if DEBUG:
        print(f"[DEBUG] {message}")

debug_print("테스트 스크립트 시작")

try:
    from PyQt5.QtWidgets import QApplication
    debug_print("PyQt5 import 성공")
except ImportError:
    print("PyQt5가 설치되어 있지 않습니다. 'pip install PyQt5' 명령으로 설치하세요.")
    sys.exit(1)

def test_call_graph_view():
    """호출 그래프 뷰 테스트"""
    debug_print("호출 그래프 뷰 테스트 시작")
    
    from src.gui.views.call_graph_view import CallGraphView
    
    app = QApplication(sys.argv)
    window = CallGraphView()
    window.show()
    
    debug_print("호출 그래프 뷰 표시됨")
    return app.exec_()

def test_error_analysis_view():
    """에러 분석 뷰 테스트"""
    debug_print("에러 분석 뷰 테스트 시작")
    
    from src.gui.views.error_analysis_view import ErrorAnalysisView
    
    app = QApplication(sys.argv)
    window = ErrorAnalysisView()
    window.show()
    
    debug_print("에러 분석 뷰 표시됨")
    return app.exec_()

def test_main_window():
    """메인 윈도우 테스트"""
    debug_print("메인 윈도우 테스트 시작")
    
    from src.gui.main_window import MainWindow
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    debug_print("메인 윈도우 표시됨")
    return app.exec_()

def run_sample_test():
    """샘플 테스트 실행"""
    debug_print("샘플 테스트 실행")
    
    import unittest
    from tests.test_sample import TestSampleFunctions
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSampleFunctions)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    debug_print(f"테스트 결과: 성공={result.wasSuccessful()}")
    return result.wasSuccessful()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "call_graph":
            sys.exit(test_call_graph_view())
        elif test_name == "error_analysis":
            sys.exit(test_error_analysis_view())
        elif test_name == "main_window":
            sys.exit(test_main_window())
        elif test_name == "sample_test":
            success = run_sample_test()
            sys.exit(0 if success else 1)
        else:
            print(f"알 수 없는 테스트 이름: {test_name}")
            print("사용 가능한 테스트: call_graph, error_analysis, main_window, sample_test")
            sys.exit(1)
    else:
        print("테스트 이름을 지정하세요:")
        print("python run_test.py [call_graph|error_analysis|main_window|sample_test]")
        sys.exit(1)
