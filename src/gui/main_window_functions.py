"""
메인 윈도우 함수 구현
CodeGuardian GUI의 주요 윈도우 클래스 함수 집합
"""

import os
import sys
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import Qt

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 코어 모듈 임포트
from core.core import code_guardian


def initialize_system(self):
    """시스템 초기화"""
    try:
        # 상태바 메시지 설정
        self.statusBar().showMessage("시스템 초기화 중...")
        
        # 기존 데이터베이스 강제 초기화
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "data", "codeguardian.db")
        
        # 함수와 파일 목록 완전 초기화
        if hasattr(code_guardian, 'monitored_functions'):
            code_guardian.monitored_functions = []  # 함수 목록 초기화
            print("함수 목록 초기화됨")
            
        if hasattr(code_guardian, 'monitored_files'):
            code_guardian.monitored_files = []  # 파일 목록 초기화
            print("파일 목록 초기화됨")
            
        # 모니터링 상태 초기화
        if hasattr(code_guardian, 'is_monitoring') and code_guardian.is_monitoring:
            code_guardian.stop_monitoring()
            print("기존 모니터링 중지됨")
            
        # 데이터베이스 파일 강제 초기화
        try:
            # 스토리지 매니저의 초기화 함수 사용
            from storage.storage_manager import reset_storage
            reset_success = reset_storage()
            
            if reset_success:
                print("데이터베이스 초기화 성공")
            else:
                print("데이터베이스 초기화 실패")
            
        except Exception as e:
            print(f"데이터베이스 초기화 오류: {str(e)}")
        
        # 모니터링할 테스트 파일 찾기
        test_files = []
        
        # tests 디렉토리에서 Python 파일 검색
        tests_dir = os.path.join(base_dir, "tests")
        
        if os.path.exists(tests_dir):
            print(f"테스트 디렉토리 발견: {tests_dir}")
            # tests 디렉토리의 모든 Python 파일 스캔
            for file in os.listdir(tests_dir):
                if file.endswith(".py"):
                    test_files.append(os.path.join(tests_dir, file))
                    print(f"테스트 파일 추가: {file}")
        
        # 루트 디렉토리에서도 test로 시작하는 파일 검색
        for file in os.listdir(base_dir):
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(base_dir, file))
                print(f"루트 테스트 파일 추가: {file}")
        
        # 파일이 없으면 기본 경로 시도
        if not test_files:
            default_test = os.path.join(base_dir, "tests", "error_test.py")
            if os.path.exists(default_test):
                test_files.append(default_test)
                print(f"기본 테스트 파일 추가: {default_test}")
                
        print(f"발견된 테스트 파일: {len(test_files)}개")
                
        # 각 파일에서 함수 목록 추출
        all_functions = []
        if test_files and hasattr(self, 'extract_functions_from_file'):
            for file_path in test_files:
                try:
                    file_functions = self.extract_functions_from_file(file_path)
                    print(f"파일 {os.path.basename(file_path)}에서 {len(file_functions)}개 함수 추출")
                    all_functions.extend(file_functions)
                except Exception as e:
                    print(f"파일 {file_path} 함수 추출 오류: {str(e)}")
            
            # 중복 제거
            all_functions = list(dict.fromkeys(all_functions))
            print(f"중복 제거 후 총 {len(all_functions)}개 함수")
            
            # 함수 목록 업데이트
            code_guardian.monitored_functions = all_functions
        else:
            print("함수 추출 실패 - 파일 없음 또는 추출 함수 없음")
        
        # 모니터링 시작
        if test_files:
            code_guardian.start_monitoring(test_files, ['tests'])
            print(f"{len(test_files)}개 테스트 파일 모니터링 시작")
            self.statusBar().showMessage(f"{len(test_files)}개 테스트 파일 모니터링 시작됨")
        else:
            code_guardian.start_monitoring()
            print("빈 모니터링 시작")
            self.statusBar().showMessage("모니터링 시작됨 (파일 없음)")
        
        # 대시보드 정보 업데이트
        file_count = len(test_files) if test_files else 0
        func_count = len(all_functions) if all_functions else 0
        
        self.monitored_count.setText(f"모니터링 중인 파일: {file_count}")
        self.protected_count.setText(f"보호 중인 함수: {func_count}")
        
        if test_files:
            self.monitored_files_text.setText("\n".join(test_files))
        else:
            self.monitored_files_text.setText("없음")
        
        self.protection_status.setText("보호 상태: 모니터링 중")
        
        # 모든 통계 및 함수 목록 업데이트
        self.update_dashboard_stats()
        
        # 함수 목록 강제 업데이트
        if hasattr(self, 'update_monitored_functions'):
            self.update_monitored_functions()
        
        # 코드 모니터 탭의 함수 목록도 업데이트
        if hasattr(self, 'update_monitored_functions_display'):
            print("코드 모니터 함수 목록 업데이트")
            self.update_monitored_functions_display()
        
        # 명시적으로 새로고침 요청
        self.refresh_all_data()
        
    except Exception as e:
        print(f"모니터링 시작 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        self.statusBar().showMessage(f"모니터링 시작 오류: {str(e)}")


def on_tab_changed(self, index):
    """탭 변경 시 호출되는 함수
    
    Args:
        index: 선택된 탭 인덱스
    """
    tab_name = self.tabs.tabText(index)
    print(f"탭 변경: {tab_name} (인덱스: {index})")
    self.statusBar().showMessage(f"{tab_name} 탭 선택됨")
    
    # 탭에 따라 적절한 데이터 로드
    if tab_name == "대시보드":
        print("대시보드 탭 데이터 로드 중...")
        # 대시보드 통계 업데이트
        self.update_dashboard_stats()
        # 함수 목록 업데이트
        self.update_monitored_functions()
    elif tab_name == "코드 모니터":
        print("코드 모니터 탭 데이터 로드 중...")
        # 모니터링 중인 파일 및 함수 목록 업데이트
        self.update_monitored_functions_display()
    elif tab_name == "호출 그래프":
        print("호출 그래프 탭 데이터 로드 중...")
        self.refresh_data("graph")
    elif tab_name == "에러 분석":
        print("에러 분석 탭 데이터 로드 중...")
        self.refresh_data("errors")
    elif tab_name == "변경 이력":
        print("변경 이력 탭 데이터 로드 중...")
        self.refresh_data("changes")
    
    # GUI 화면 업데이트 강제 실행
    QApplication.processEvents()


def refresh_data(self, data_type="all"):
    """데이터 새로고침
    
    Args:
        data_type: 새로고침할 데이터 유형
    """
    self.statusBar().showMessage(f"데이터 새로고침 중...")
    
    # 현재 선택된 함수명과 깊이 및 기타 매개변수
    params = {}
    
    # 호출 그래프 탭
    if self.tabs.currentIndex() == 2:  
        if hasattr(self, 'function_search'):
            params["function_name"] = self.function_search.text()
        if hasattr(self, 'depth_slider'):
            params["depth"] = self.depth_slider.value()
    
    # 에러 분석 탭
    elif self.tabs.currentIndex() == 4:
        if hasattr(self, 'error_function_search'):
            params["function_name"] = self.error_function_search.text()
    
    # 변경 이력 탭
    elif self.tabs.currentIndex() == 3:
        if hasattr(self, 'change_function_filter'):
            params["function_name"] = self.change_function_filter.text()
    
    # 스레드에서 데이터 로드
    self.refresh_worker.set_task(data_type, **params)
    self.refresh_worker.start()


def refresh_all_data(self):
    """모든 데이터 새로고침"""
    self.refresh_data("all")
    self.update_dashboard_stats()
    
    # 코드 모니터 뷰의 함수 목록도 업데이트
    if hasattr(self, 'update_monitored_functions_display'):
        self.update_monitored_functions_display()


def update_dashboard_stats(self):
    """대시보드 통계 업데이트"""
    print('대시보드 통계 업데이트 함수 실행됨')
    
    # 상태바 메시지 설정
    self.statusBar().showMessage("대시보드 통계 업데이트 중...")
    
    # 모든 UI 요소 초기화
    self.protected_count.clear()
    self.monitored_count.clear()
    self.error_count.clear()
    self.status_message.clear()
    self.monitored_files_text.clear()
    QApplication.processEvents()
    
    try:
        # 먼저 모니터링 파일 목록 확인 및 업데이트
        if not hasattr(code_guardian, 'monitored_files') or not code_guardian.monitored_files:
            # 테스트 파일 검색 (동적으로 파일 찾기)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 모니터링할 파일 목록
            monitored_files = []
            
            # tests 디렉토리 검색
            tests_dir = os.path.join(base_dir, "tests")
            if os.path.exists(tests_dir):
                for file in os.listdir(tests_dir):
                    if file.endswith(".py"):
                        test_file = os.path.join(tests_dir, file)
                        monitored_files.append(test_file)
            
            # 루트 디렉토리에서 test_ 로 시작하는 파일 검색
            for file in os.listdir(base_dir):
                if file.startswith("test_") and file.endswith(".py"):
                    test_file = os.path.join(base_dir, file)
                    monitored_files.append(test_file)
            
            # test 디렉토리 검색
            test_dir = os.path.join(base_dir, "test")
            if os.path.exists(test_dir):
                # 모든 .py 파일 재귀적으로 찾기
                for root, dirs, files in os.walk(test_dir):
                    for file in files:
                        if file.endswith(".py"):
                            file_path = os.path.join(root, file)
                            monitored_files.append(file_path)
            
            # 모니터링 파일 목록 설정
            code_guardian.monitored_files = monitored_files
            print(f"모니터링 파일 목록 업데이트: {len(monitored_files)}개 파일")
            
            # 파일이 있으면 모니터링 시작
            if monitored_files and (not hasattr(code_guardian, 'is_monitoring') or not code_guardian.is_monitoring):
                code_guardian.start_monitoring(monitored_files)
                print("모니터링 자동 시작됨")
                
        # 모니터링 파일 수 업데이트
        file_count = len(code_guardian.monitored_files) if hasattr(code_guardian, 'monitored_files') else 0
        self.monitored_count.setText(f"모니터링 중인 파일: {file_count}")
        QApplication.processEvents()
        
        # 모니터링 파일 목록 업데이트 - 전체 경로 표시
        if hasattr(code_guardian, 'monitored_files') and code_guardian.monitored_files:
            self.monitored_files_text.setText("\n".join(code_guardian.monitored_files))
        else:
            self.monitored_files_text.setText("없음")
        QApplication.processEvents()
        
        # 함수 목록 동적으로 가져오기 (하드코딩 제거)
        function_count = 0
        monitored_functions = []
        print('동적으로 함수 목록 가져오기 시작')
        
        # 모든 파일에서 함수 목록 새로 추출
        all_functions = []
        for file_path in code_guardian.monitored_files:
            try:
                if os.path.exists(file_path):
                    print(f"파일에서 함수 추출: {file_path}")
                    functions = self.extract_functions_from_file(file_path)
                    all_functions.extend(functions)
            except Exception as e:
                print(f"파일 {file_path} 함수 추출 오류: {str(e)}")
        
        # 중복 제거
        monitored_functions = list(dict.fromkeys(all_functions))
        print(f"총 {len(monitored_functions)}개 함수 발견")
        
        # 코어에 함수 목록 업데이트
        code_guardian.monitored_functions = monitored_functions
        function_count = len(monitored_functions)
            
        # 보호된 함수 수 업데이트
        self.protected_count.setText(f"보호 중인 함수: {function_count}")
        QApplication.processEvents()
        
        # 에러 수 업데이트
        try:
            errors = code_guardian.get_error_data()
            error_count = len(errors) if errors else 0
            self.error_count.setText(f"감지된 에러: {error_count}")
        except Exception as e:
            print(f"에러 데이터 업데이트 오류: {str(e)}")
            self.error_count.setText("감지된 에러: 0")
        QApplication.processEvents()
        
        # 상태 메시지 업데이트
        if hasattr(code_guardian, 'is_monitoring') and code_guardian.is_monitoring:
            self.status_message.setText("CodeGuardian이 활성화되어 코드를 보호하고 있습니다.")
            self.protection_status.setText("보호 상태: 모니터링 중")
            self.monitor_btn.setText("모니터링 중지")
            try:
                self.monitor_btn.clicked.disconnect()
            except:
                pass
            self.monitor_btn.clicked.connect(self.stop_monitoring)
        else:
            self.status_message.setText("CodeGuardian이 비활성화 상태입니다. 모니터링을 시작하세요.")
            self.protection_status.setText("보호 상태: 모니터링 중지됨")
            self.monitor_btn.setText("모니터링 시작")
            try:
                self.monitor_btn.clicked.disconnect()
            except:
                pass
            self.monitor_btn.clicked.connect(self.start_monitoring)
        QApplication.processEvents()
        
        # 모든 UI 요소 강제 업데이트
        self.repaint()
        QApplication.processEvents()
        
        # 함수 목록 업데이트는 별도 처리 (이미 UI가 있으므로 비우고 새로 채우는 방식으로)
        print("함수 목록 화면 업데이트 중...")
        if hasattr(self, 'update_monitored_functions'):
            self.update_monitored_functions()
            
        # 상태 업데이트 완료 메시지
        self.statusBar().showMessage("대시보드 통계 업데이트 완료")
        print("대시보드 통계 업데이트 완료")
            
    except Exception as e:
        print(f"대시보드 통계 업데이트 오류: {str(e)}")
        traceback_info = traceback.format_exc()
        print(f"상세 오류 정보: {traceback_info}")
        self.statusBar().showMessage(f"대시보드 통계 업데이트 오류: {str(e)}")


def on_refresh_complete(self, result):
    """데이터 새로고침 완료 시 호출되는 함수
    
    Args:
        result: 새로고침 결과 데이터
    """
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        self.statusBar().showMessage(f"새로고침 오류: {error_msg}")
        return
    
    data_type = result.get("type", "unknown")
    
    if data_type == "graph" or data_type == "all":
        # 그래프 데이터 업데이트
        if self.tabs.currentIndex() == 2:  # 호출 그래프 탭
            graph_data = result.get("data") if data_type == "graph" else result.get("graph")
            if hasattr(self, 'call_graph_view_available') and not self.call_graph_view_available:
                self.update_graph_view(graph_data)
    
    if data_type == "errors" or data_type == "all":
        # 에러 데이터 업데이트
        if self.tabs.currentIndex() == 4:  # 에러 분석 탭
            error_data = result.get("data") if data_type == "errors" else result.get("errors")
            if hasattr(self, 'error_analysis_view_available') and not self.error_analysis_view_available:
                self.update_error_view(error_data)
    
    if data_type == "changes" or data_type == "all":
        # 변경 이력 업데이트
        if self.tabs.currentIndex() == 3:  # 변경 이력 탭
            changes_data = result.get("data") if data_type == "changes" else result.get("changes")
            self.update_changes_view(changes_data)
    
    self.statusBar().showMessage("데이터 새로고침 완료")


def update_graph_view(self, graph_data):
    """그래프 뷰 업데이트
    
    Args:
        graph_data: 그래프 데이터
    """
    if not graph_data or not graph_data.get("nodes"):
        self.graph_view.setText("그래프 데이터가 없습니다")
        return
    
    # 노드 및 엣지 수 표시
    node_count = len(graph_data.get("nodes", []))
    edge_count = len(graph_data.get("edges", []))
    
    self.graph_view.setText(f"그래프 데이터 로드됨\n노드: {node_count}개, 엣지: {edge_count}개")


def update_error_view(self, error_data):
    """에러 뷰 업데이트
    
    Args:
        error_data: 에러 데이터
    """
    if not error_data:
        self.error_list.setText("에러 데이터가 없습니다")
        return
    
    # 간단한 텍스트 표시 (실제로는 테이블 위젯 사용)
    error_text = "에러 목록:\n\n"
    
    for i, error in enumerate(error_data):
        error_text += f"{i+1}. 함수: {error.get('function_name', 'Unknown')}\n"
        error_text += f"   유형: {error.get('error_type', 'Unknown')}\n"
        error_text += f"   메시지: {error.get('error_message', 'No message')}\n\n"
    
    self.error_list.setText(error_text)


def update_changes_view(self, changes_data):
    """변경 이력 뷰 업데이트
    
    Args:
        changes_data: 변경 이력 데이터
    """
    if not changes_data:
        self.changes_info.setText("변경 이력 데이터가 없습니다")
        return
    
    # 변경 이력 텍스트 구성
    changes_text = "변경 이력:\n\n"
    
    for i, change in enumerate(changes_data):
        changes_text += f"{i+1}. 파일: {change.get('file_path', 'Unknown')}\n"
        changes_text += f"   함수: {change.get('function_name', 'Unknown')}\n"
        changes_text += f"   변경 유형: {change.get('change_type', 'Unknown')}\n"
        changes_text += f"   시간: {change.get('timestamp', '')}\n\n"
        
        if i < 5:  # 처음 5개의 변경 사항만 차이점 표시
            changes_text += f"   변경 내용:\n{change.get('diff', '')}\n\n"
    
    self.changes_info.setText(changes_text)


def on_create_graph(self):
    """그래프 생성 버튼 클릭 시 호출"""
    function_name = self.function_search.text()
    depth = self.depth_slider.value()
    
    self.statusBar().showMessage(f"'{function_name}' 함수의 호출 그래프 생성 중 (깊이: {depth})...")
    self.refresh_data("graph")


def on_refresh_errors(self):
    """에러 새로고침 버튼 클릭 시 호출"""
    function_name = self.error_function_search.text()
    
    if function_name:
        self.statusBar().showMessage(f"'{function_name}' 함수의 에러 데이터 로드 중...")
    else:
        self.statusBar().showMessage("모든 에러 데이터 로드 중...")
    
    self.refresh_data("errors")


def refresh_changes(self):
    """변경 이력 새로고침"""
    function_name = self.change_function_filter.text()
    
    if function_name:
        self.statusBar().showMessage(f"'{function_name}' 함수의 변경 이력 로드 중...")
    else:
        self.statusBar().showMessage("모든 변경 이력 로드 중...")
    
    self.refresh_data("changes")


def refresh_protection_status(self):
    """보호 상태 새로고침"""
    # 모니터링 중인 파일 확인
    try:
        monitored_files = []
        if hasattr(code_guardian, 'monitored_files'):
            monitored_files = code_guardian.monitored_files.copy()
    
        # 모니터링 상태 업데이트
        self.update_dashboard_stats()
        
        # 코드 모니터 함수 목록 새로고침
        if hasattr(self, 'update_monitored_functions_display'):
            self.update_monitored_functions_display()
        
        # 보호 상태에 따라 버튼 업데이트
        if hasattr(code_guardian, 'is_monitoring') and code_guardian.is_monitoring:
            message = "코드 모니터링이 활성화되어 있습니다."
            if monitored_files:
                message += f"\n\n모니터링 중인 파일: {len(monitored_files)}개"
                # 파일 목록 추가 (최대 5개만 표시)
                if len(monitored_files) <= 5:
                    message += "\n" + "\n".join(monitored_files)
                else:
                    message += "\n" + "\n".join(monitored_files[:5])
                    message += f"\n... 외 {len(monitored_files) - 5}개 파일"
            QMessageBox.information(self, "보호 상태", message)
        else:
            QMessageBox.warning(self, "보호 상태", "코드 모니터링이 비활성화되어 있습니다.")
            
            # 필요한 경우 모니터링 자동 시작
            if hasattr(code_guardian, 'start_monitoring'):
                code_guardian.start_monitoring()
                self.update_dashboard_stats()
    except Exception as e:
        QMessageBox.critical(self, "오류", f"상태 확인 중 오류 발생: {str(e)}")


def browse_file(self):
    """파일 찾아보기"""
    file_path, _ = QFileDialog.getOpenFileName(self, "모니터링할 파일 선택", "", "Python 파일 (*.py)")
    if file_path:
        self.file_path_input.setText(file_path)
        
        # 파일 정보 표시 - 선택 파일에 포함된 함수 분석
        try:
            # 함수 정보 분석
            import re
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 함수 추출
            func_pattern = re.compile(r'def\s+(\w+)\s*\(', re.MULTILINE)
            functions = func_pattern.findall(content)
            
            # 파일 정보 메시지
            message = f"파일: {file_path}\n"
            if functions:
                message += f"\n{len(functions)}개 함수 발견:\n- " + "\n- ".join(functions)
            else:
                message += "\n함수를 찾을 수 없습니다."
            
            # 파일 정보 표시
            self.statusBar().showMessage(f"파일 선택됨: {file_path} ({len(functions)}개 함수)")
        except Exception as e:
            self.statusBar().showMessage(f"파일 분석 오류: {str(e)}")


def update_monitored_functions_display(self):
    """모니터링 중인 함수 목록을 드롭다운과 정보 화면에 표시"""
    print("코드 모니터 함수 목록 표시 시작")
    
    # UI 요소 초기화 - 드롭다운 및 내용 비우기
    self.function_combo.clear()
    self.functions_content.clear()
    self.functions_content.setText("")
    QApplication.processEvents()
    
    # 모니터링 중인 함수들의 정보 가져오기
    functions_data = self.get_monitored_functions_data()
    print(f"가져온 함수 데이터 수: {len(functions_data)}")
    
    # 드롭다운에 함수 추가
    if functions_data:
        # 함수 목록 준비 (중복 제거)
        function_names = []
        for func in functions_data:
            if func['name'] not in function_names:
                function_names.append(func['name'])
        
        # 알파벳순 정렬
        function_names.sort()
        
        # 드롭다운에 추가
        for func_name in function_names:
            self.function_combo.addItem(func_name)
        
        print(f"드롭다운에 {len(function_names)}개 함수 추가됨")
        
        # 첫 번째 함수 선택
        self.function_combo.setCurrentIndex(0)
        self.on_function_selected(0)
    else:
        # 함수가 없는 경우
        self.functions_content.setText("<p>모니터링 중인 함수가 없습니다.</p>")
        print("모니터링 중인 함수가 없음")
    
    QApplication.processEvents()
    print("코드 모니터 함수 목록 표시 완료")

def add_file_to_monitoring(self):
    """선택한 파일을 모니터링에 추가"""
    file_path = self.file_path_input.text()
    if not file_path:
        QMessageBox.warning(self, "경고", "모니터링할 파일을 선택하세요.")
        return
    
    try:
        if hasattr(code_guardian, 'is_monitoring') and code_guardian.is_monitoring:
            # 이미 모니터링 중인 파일이면 무시
            if file_path in code_guardian.monitored_files:
                QMessageBox.information(self, "알림", f"이미 모니터링 중인 파일입니다: {file_path}")
                return
                
            # 새 파일 추가
            code_guardian.monitored_files.append(file_path)
            self.statusBar().showMessage(f"파일이 모니터링에 추가됨: {file_path}")
        else:
            # 모니터링 시작
            if not hasattr(code_guardian, 'monitored_files'):
                code_guardian.monitored_files = []
            code_guardian.monitored_files.append(file_path)
            code_guardian.start_monitoring([file_path])
            self.statusBar().showMessage(f"파일 모니터링 시작됨: {file_path}")
        
        # 새 파일에서 함수 추출
        if os.path.exists(file_path):
            new_functions = self.extract_functions_from_file(file_path)
            if new_functions:
                # 기존 함수 목록 확인
                if not hasattr(code_guardian, 'monitored_functions'):
                    code_guardian.monitored_functions = []
                
                # 새 함수만 추가 (중복 제거)
                for func in new_functions:
                    if func not in code_guardian.monitored_functions:
                        code_guardian.monitored_functions.append(func)
                
                print(f"파일 {file_path}에서 {len(new_functions)}개 함수 추가됨")
        
        # 모니터링 파일 목록 업데이트
        self.update_dashboard_stats()
        
        # 코드 모니터 뷰 업데이트
        self.update_monitored_functions_display()
        
        # 전체 리스트 표시
        self.monitored_files_text.setText("\n".join(code_guardian.monitored_files))
        
        # 성공 메시지
        QMessageBox.information(self, "파일 추가 성공", f"파일이 모니터링 목록에 추가되었습니다:\n{file_path}")
        
    except Exception as e:
        QMessageBox.critical(self, "오류", f"파일 모니터링 추가 실패: {str(e)}")


def open_project(self):
    """프로젝트 열기"""
    folder = QFileDialog.getExistingDirectory(self, "프로젝트 폴더 선택")
    if folder:
        self.statusBar().showMessage(f"프로젝트 폴더: {folder}")
        
        # 모니터링 중지 후 선택한 프로젝트 폴더의 Python 파일 스캔
        try:
            code_guardian.stop_monitoring()
            
            # 프로젝트 폴더 내 모든 Python 파일 찾기
            python_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(".py"):
                        python_files.append(os.path.join(root, file))
            
            if python_files:
                # 모니터링 시작
                code_guardian.start_monitoring(python_files)
                self.statusBar().showMessage(f"프로젝트 파일 {len(python_files)}개 모니터링 시작됨")
                
                # 대시보드 업데이트
                self.update_dashboard_stats()
            else:
                QMessageBox.warning(self, "경고", "선택한 폴더에 Python 파일이 없습니다.")
                
        except Exception as e:
            QMessageBox.critical(self, "오류", f"프로젝트 로드 실패: {str(e)}")


def save_data(self):
    """데이터 저장"""
    self.statusBar().showMessage("데이터 저장 중...")
    
    try:
        # 실제 구현에서는 설정 및 현재 상태 저장
        QMessageBox.information(self, "알림", "데이터가 저장되었습니다.")
    except Exception as e:
        QMessageBox.critical(self, "오류", f"데이터 저장 실패: {str(e)}")


def start_monitoring(self):
    """모니터링 시작"""
    try:
        # 모니터링 중이면 먼저 중지
        if code_guardian.is_monitoring:
            code_guardian.stop_monitoring()
        
        # 함수 목록 초기화
        code_guardian.monitored_functions = []
        
        # 모니터링 대상 파일 검색 및 자동 추가
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        test_files = []
        
        # tests 디렉토리에서 .py 파일 찾기
        tests_dir = os.path.join(base_dir, "tests")
        if os.path.exists(tests_dir):
            for file in os.listdir(tests_dir):
                if file.endswith(".py"):
                    test_files.append(os.path.join(tests_dir, file))
        
        # 루트 디렉토리에서 test_로 시작하는 파일 찾기
        for file in os.listdir(base_dir):
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(base_dir, file))
        
        # 파일별로 함수 추출
        all_functions = []
        if test_files and hasattr(self, 'extract_functions_from_file'):
            for file_path in test_files:
                functions = self.extract_functions_from_file(file_path)
                all_functions.extend(functions)
            
            # 중복 제거
            all_functions = list(dict.fromkeys(all_functions))
            
            # 함수 목록 업데이트
            code_guardian.monitored_functions = all_functions
        
        # 모니터링 시작
        if test_files:
            code_guardian.monitored_files = test_files  # 명시적으로 설정
            code_guardian.start_monitoring(test_files, ['tests'])
            self.statusBar().showMessage(f"{len(test_files)}개 파일 모니터링 시작됨")
        else:
            code_guardian.start_monitoring()
            self.statusBar().showMessage("모니터링 시작됨 (파일 없음)")
        
        # UI 업데이트
        self.update_dashboard_stats()
        
        # 함수 목록 표시 강제 업데이트
        if hasattr(self, 'update_monitored_functions'):
            self.update_monitored_functions()
        
        if hasattr(self, 'update_monitored_functions_display'):
            self.update_monitored_functions_display()
        
        # 데이터 전체 새로고침
        self.refresh_all_data()
        
        # GUI 강제 새로고침
        # 1. 모든 함수 목록 표시 강제 업데이트
        if hasattr(self, 'update_monitored_functions'):
            self.update_monitored_functions()
        
        if hasattr(self, 'update_monitored_functions_display'):
            self.update_monitored_functions_display()
        
        # 2. 전체 데이터 새로고침
        self.refresh_all_data()
        
        # 3. 대시보드 통계 업데이트
        self.update_dashboard_stats()
        
        # 4. 현재 탭에 따라 특정 뷰 업데이트
        current_tab = self.tabs.currentIndex()
        if current_tab == 0:  # 대시보드
            pass  # 이미 대시보드 통계 업데이트함
        elif current_tab == 1:  # 코드 모니터
            self.update_monitored_functions_display()
        elif current_tab == 2:  # 호출 그래프
            self.refresh_data("graph")
        elif current_tab == 3:  # 변경 이력
            self.refresh_data("changes")
        elif current_tab == 4:  # 에러 분석
            self.refresh_data("errors")
        
        # 상태 메시지 업데이트
        QMessageBox.information(self, "모니터링", f"코드 모니터링이 시작되었습니다.\n모니터링 중인 파일: {len(test_files)}개\n함수: {len(all_functions)}개\n\n데이터베이스 및 GUI가 초기화되었습니다.")
        
    except Exception as e:
        QMessageBox.critical(self, "오류", f"모니터링 시작 실패: {str(e)}")


def stop_monitoring(self):
    """모니터링 중지"""
    try:
        if code_guardian.is_monitoring:
            code_guardian.stop_monitoring()
            self.statusBar().showMessage("모니터링 중지됨")
            self.update_dashboard_stats()
            
            # 상태 메시지 업데이트
            QMessageBox.information(self, "모니터링", "코드 모니터링이 중지되었습니다.")
        else:
            QMessageBox.information(self, "모니터링", "모니터링이 이미 비활성화되어 있습니다.")
        
    except Exception as e:
        QMessageBox.critical(self, "오류", f"모니터링 중지 실패: {str(e)}")


def scan_files(self):
    """파일 스캔"""
    folder = QFileDialog.getExistingDirectory(self, "스캔할 폴더 선택")
    if folder:
        try:
            self.statusBar().showMessage(f"폴더 스캔 중: {folder}")
            
            # 폴더 내 모든 Python 파일 스캔
            python_files = []
            scan_errors = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        python_files.append(file_path)
                        
                        # 보호된 블록 스캔 (오류 처리 포함)
                        try:
                            code_guardian.scan_for_protected_blocks(file_path)
                        except Exception as e:
                            scan_errors.append(f"{file_path}: {str(e)}")
                            print(f"WARNING: {file_path} 스캔 중 오류: {str(e)}")
            
            # 모니터링 대상에 추가
            if python_files:
                # 스캔된 파일이 있으면 모니터링에 추가
                if not hasattr(code_guardian, 'is_monitoring') or not code_guardian.is_monitoring:
                    code_guardian.start_monitoring(python_files)
                else:
                    # 이미 모니터링 중이면 기존 목록에 추가 (중복 제거)
                    for file_path in python_files:
                        if file_path not in code_guardian.monitored_files:
                            code_guardian.monitored_files.append(file_path)
            
            # 결과 메시지 준비
            result_message = f"폴더 스캔이 완료되었습니다.\n스캔된 Python 파일: {len(python_files)}개"
            if python_files:
                result_message += f"\n\n모니터링에 {len(python_files)}개 파일이 추가되었습니다."
            
            if scan_errors:
                # 최대 5개의 오류만 표시
                error_list = "\n\n스캔 중 발생한 오류:\n" + "\n".join(scan_errors[:5])
                if len(scan_errors) > 5:
                    error_list += f"\n... 외 {len(scan_errors) - 5}개 오류"
                result_message += error_list
            
            QMessageBox.information(self, "스캔 완료", result_message)
            
            # 모니터링 파일 목록 및 GUI 업데이트
            if python_files:
                # 전체 목록 표시 (모니터링 중인 모든 파일)
                self.monitored_files_text.setText("\n".join(code_guardian.monitored_files))
                
                # 대시보드 정보 업데이트
                self.update_dashboard_stats()
                
                # 코드 모니터 뷰 업데이트
                if hasattr(self, 'update_monitored_functions_display'):
                    self.update_monitored_functions_display()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"폴더 스캔 실패: {str(e)}")


def show_settings(self):
    """설정 대화상자 표시"""
    QMessageBox.information(self, "설정", "설정 기능은 아직 구현되지 않았습니다.")


def refresh_gui(self):
    """GUI 명시적 새로고침 함수 - 강제로 UI 재생성"""
    print("GUI 명시적 새로고침 시작 - 강제 UI 재생성 방식")
    self.statusBar().showMessage("GUI 완전 새로고침 중...")
    
    try:
        # 1. 메인 윈도우의 현재 상태 저장
        current_tab_index = self.tabs.currentIndex()
        
        # 2. 파일 및 함수 목록 재검색
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        monitored_files = []
        
        # 모든 가능한 테스트 파일 검색
        print("모든 테스트 파일 검색 중...")
        
        # tests 디렉토리 검색
        tests_dir = os.path.join(base_dir, "tests")
        if os.path.exists(tests_dir):
            for file in os.listdir(tests_dir):
                if file.endswith(".py"):
                    monitored_files.append(os.path.join(tests_dir, file))
                    print(f"테스트 파일 추가: {file}")
        
        # 루트의 테스트 파일 검색
        for file in os.listdir(base_dir):
            if file.startswith("test_") and file.endswith(".py"):
                monitored_files.append(os.path.join(base_dir, file))
                print(f"루트 테스트 파일 추가: {file}")
        
        # test 디렉토리 검색
        test_dir = os.path.join(base_dir, "test")
        if os.path.exists(test_dir):
            for root, dirs, files in os.walk(test_dir):
                for file in files:
                    if file.endswith(".py"):
                        monitored_files.append(os.path.join(root, file))
                        print(f"테스트 디렉토리 파일 추가: {os.path.join(root, file)}")
        
        # 3. 모든 파일에서 함수 추출
        all_functions = []
        for file_path in monitored_files:
            try:
                if os.path.exists(file_path):
                    functions = self.extract_functions_from_file(file_path)
                    all_functions.extend(functions)
                    print(f"파일 {os.path.basename(file_path)}에서 {len(functions)}개 함수 추출")
            except Exception as e:
                print(f"파일 {file_path} 함수 추출 오류: {str(e)}")
        
        # 중복 제거
        all_functions = list(dict.fromkeys(all_functions))
        print(f"총 {len(all_functions)}개 함수 발견")
        
        # 4. 코어 시스템 재설정
        if hasattr(code_guardian, 'is_monitoring') and code_guardian.is_monitoring:
            code_guardian.stop_monitoring()
            print("기존 모니터링 중지")
        
        # 코어 데이터 설정
        code_guardian.monitored_files = monitored_files
        code_guardian.monitored_functions = all_functions
        
        # 모니터링 재시작
        code_guardian.start_monitoring(monitored_files)
        print(f"모니터링 재시작: {len(monitored_files)}개 파일")
        
        # 5. UI 강제 업데이트 - 대시보드 통계 업데이트
        self.protected_count.setText(f"보호 중인 함수: {len(all_functions)}")
        self.monitored_count.setText(f"모니터링 중인 파일: {len(monitored_files)}")
        QApplication.processEvents()
        
        # 6. 대시보드의 파일 및 함수 목록 업데이트
        file_list_text = "\n".join(monitored_files)
        self.monitored_files_text.clear()
        self.monitored_files_text.setText(file_list_text)
        QApplication.processEvents()
        
        # 7. 함수 목록 강제 재생성
        # HTML 구성을 처음부터 다시 만들어서 직접 설정
        html_content = "<b>모니터링 중인 파일:</b> "
        if len(monitored_files) == 1:
            html_content += monitored_files[0]
        else:
            html_content += f"{len(monitored_files)}개 파일"
        
        html_content += "<br><b>모니터링 중인 함수:</b><br>"
        
        # 함수 목록 생성
        for i, func_name in enumerate(all_functions):
            html_content += f"<div style='margin-bottom: 10px;'>"
            html_content += f"<span style='color: #5cb85c; font-weight: bold;'>{i+1}. {func_name}()</span>"
            
            # 함수 종류에 따른 상태 및 설명 
            if "error" in func_name.lower():
                html_content += f" - <span>주의</span>"
                html_content += f"<br><span style='margin-left: 20px; color: #666;'>에러 관련 함수</span>"
            elif "calc" in func_name.lower() or "comput" in func_name.lower():
                html_content += f" - <span>정상</span>"
                html_content += f"<br><span style='margin-left: 20px; color: #666;'>계산 함수</span>"
            elif "process" in func_name.lower():
                html_content += f" - <span>정상</span>"
                html_content += f"<br><span style='margin-left: 20px; color: #666;'>데이터 처리 함수</span>"
            else:
                html_content += f" - <span>정상</span>"
                html_content += f"<br><span style='margin-left: 20px; color: #666;'>일반 함수</span>"
            
            html_content += "</div>"
        
        # 함수 목록 표시
        self.functions_display.clear()
        self.functions_display.setText(html_content)
        QApplication.processEvents()
        
        # 8. 코드 모니터 함수 목록 강제 업데이트
        self.update_monitored_functions_display()
        QApplication.processEvents()
        
        # 9. 현재 선택된 탭에 따른 추가 업데이트
        if current_tab_index == 2:  # 호출 그래프
            self.refresh_data("graph")
        elif current_tab_index == 3:  # 변경 이력
            self.refresh_data("changes")
        elif current_tab_index == 4:  # 에러 분석
            self.refresh_data("errors")
        
        # 10. 전체 UI 새로고침 완료
        self.repaint()
        self.tabs.setCurrentIndex(current_tab_index)  # 현재 탭 유지
        QApplication.processEvents()
        
        # 업데이트 완료 메시지
        self.statusBar().showMessage("GUI 완전 새로고침 완료")
        print("GUI 완전 새로고침 완료")
        
    except Exception as e:
        print(f"GUI 새로고침 중 심각한 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        self.statusBar().showMessage(f"GUI 새로고침 오류: {str(e)}")

def on_function_selected(self, index):
    """함수 드롭다운에서 함수를 선택했을 때 처리"""
    if index < 0:
        return
        
    print(f"함수 선택: 인덱스 {index}")
    function_name = self.function_combo.currentText()
    print(f"선택된 함수: {function_name}")
    
    # 함수 정보 표시
    self.display_function_details(function_name)

def remove_function_from_monitoring(self):
    """현재 선택된 함수를 모니터링에서 제거"""
    function_name = self.function_combo.currentText()
    if not function_name:
        return
        
    print(f"함수 모니터링 중지: {function_name}")
    
    # 함수 목록에서 제거
    if hasattr(code_guardian, 'monitored_functions') and function_name in code_guardian.monitored_functions:
        code_guardian.monitored_functions.remove(function_name)
        print(f"함수 '{function_name}' 모니터링에서 제거됨")
        
        # 드롭다운에서 제거
        current_index = self.function_combo.currentIndex()
        self.function_combo.removeItem(current_index)
        
        # 남은 함수가 있으면 첫 번째 함수 선택
        if self.function_combo.count() > 0:
            self.function_combo.setCurrentIndex(0)
            self.on_function_selected(0)
        else:
            # 함수가 없으면 빈 화면 표시
            self.functions_content.setText("<p>모니터링 중인 함수가 없습니다.</p>")
            
        # 통계 업데이트
        self.update_dashboard_stats()
        
        # 성공 메시지
        self.statusBar().showMessage(f"함수 '{function_name}' 모니터링이 중지되었습니다.")
    else:
        self.statusBar().showMessage(f"함수 '{function_name}'을 찾을 수 없습니다.")

def display_function_details(self, function_name):
    """선택한 함수의 상세 정보 표시"""
    print(f"함수 상세 정보 표시: {function_name}")
    
    # 함수 데이터 가져오기
    functions_data = self.get_monitored_functions_data()
    
    # 선택한 함수 찾기
    selected_function = None
    for func in functions_data:
        if func['name'] == function_name:
            selected_function = func
            break
    
    if not selected_function:
        self.functions_content.setText(f"<p>함수 '{function_name}'에 대한 정보를 찾을 수 없습니다.</p>")
        return
    
    # CSS 스타일 정의
    css_style = """<style>
.function { margin-bottom: 20px; border-left: 3px solid #3498db; padding-left: 10px; }
.error-function { border-left-color: #e74c3c; }
.function-name { font-weight: bold; font-size: 14px; }
.error-name { color: #e74c3c; }
.function-code { background-color: #f9f9f9; padding: 5px; margin: 5px 0; border-radius: 3px; font-family: Consolas, monospace; }
.function-desc { color: #555; margin-top: 3px; }
.status-badge { padding: 2px 6px; border-radius: 3px; color: white; font-size: 12px; margin-left: 5px; }
.status-normal { background-color: #2ecc71; }
.status-warning { background-color: #f39c12; }
.status-error { background-color: #e74c3c; }
.file-info { font-size: 12px; color: #777; margin-bottom: 5px; font-style: italic; }
.section-header { background-color: #f4f4f4; padding: 5px 10px; margin: 10px 0; font-weight: bold; border-left: 5px solid #3498db; }
</style>"""
    
    # 함수 정보 HTML 구성
    html_content = css_style
    
    # 함수 상태에 따른 CSS 클래스 결정
    func_class = "function"
    name_class = "function-name"
    if selected_function['status'] == "위험":
        func_class += " error-function"
        name_class += " error-name"
    
    # 상태 배지 CSS 클래스 결정
    badge_class = "status-badge"
    if selected_function['status'] == "위험":
        badge_class += " status-error"
    elif selected_function['status'] == "주의":
        badge_class += " status-warning"
    else:
        badge_class += " status-normal"
    
    # 함수 HTML 구성
    html_content += f"""
<div class="{func_class}">
<span class="{name_class}">{selected_function['name']}({selected_function['params']})</span>
<span class="{badge_class}">{selected_function['status']}</span>
<div class="file-info">파일: {selected_function['file_name']}</div>
<div class="function-code">{selected_function['code_html']}</div>
<div class="function-desc">{selected_function['description']}</div>
</div>
"""
    
    # 내용 설정
    self.functions_content.setText(html_content)
    self.functions_content.repaint()
    QApplication.processEvents()
    print(f"함수 '{function_name}' 정보 표시 완료")

def show_about(self):
    """정보 대화상자 표시"""
    QMessageBox.about(self, "CodeGuardian 정보", 
                     "CodeGuardian\n버전 1.0\n\n코드 보호 및 분석 도구")
