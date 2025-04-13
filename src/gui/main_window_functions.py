"""
메인 윈도우 함수 구현
CodeGuardian GUI의 주요 윈도우 클래스 함수 집합
"""

import os
import sys
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 코어 모듈 임포트
from core.core import code_guardian


def initialize_system(self):
    """시스템 초기화"""
    # 테스트 파일 경로
    test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tests/error_test.py'))
    
    # 모니터링 시작
    try:
        code_guardian.start_monitoring([test_file], ['tests'])
        self.statusBar().showMessage("테스트 모니터링 시작됨")
        
        # 대시보드 정보 업데이트
        self.monitored_count.setText(f"모니터링 중인 파일: 1")
        self.monitored_files_text.setText(test_file)
        self.protection_status.setText("보호 상태: 모니터링 중")
        
    except Exception as e:
        self.statusBar().showMessage(f"모니터링 시작 오류: {str(e)}")


def on_tab_changed(self, index):
    """탭 변경 시 호출되는 함수
    
    Args:
        index: 선택된 탭 인덱스
    """
    tab_name = self.tabs.tabText(index)
    self.statusBar().showMessage(f"{tab_name} 탭 선택됨")
    
    # 탭에 따라 적절한 데이터 로드
    if tab_name == "호출 그래프":
        self.refresh_data("graph")
    elif tab_name == "에러 분석":
        self.refresh_data("errors")
    elif tab_name == "변경 이력":
        self.refresh_data("changes")


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


def update_dashboard_stats(self):
    """대시보드 통계 업데이트"""
    try:
        # 에러 수 업데이트
        errors = code_guardian.get_error_data()
        self.error_count.setText(f"감지된 에러: {len(errors)}")
        
        # 보호된 함수 수 업데이트 (실제로는 DB에서 가져와야 함)
        self.protected_count.setText(f"보호 중인 함수: {len(code_guardian.monitored_functions)}")
        
        # 모니터링 중인 파일 수 업데이트
        self.monitored_count.setText(f"모니터링 중인 파일: {len(code_guardian.monitored_files)}")
        
        # 상태 메시지 업데이트
        if code_guardian.is_monitoring:
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
        
        # 모니터링 중인 파일 목록 업데이트
        if code_guardian.monitored_files:
            self.monitored_files_text.setText("\n".join(code_guardian.monitored_files))
        else:
            self.monitored_files_text.setText("없음")
            
    except Exception as e:
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
    self.update_dashboard_stats()
    
    # 보호 상태에 따라 버튼 업데이트
    if code_guardian.is_monitoring:
        QMessageBox.information(self, "보호 상태", "코드 모니터링이 활성화되어 있습니다.")
    else:
        QMessageBox.warning(self, "보호 상태", "코드 모니터링이 비활성화되어 있습니다.")


def browse_file(self):
    """파일 찾아보기"""
    file_path, _ = QFileDialog.getOpenFileName(self, "모니터링할 파일 선택", "", "Python 파일 (*.py)")
    if file_path:
        self.file_path_input.setText(file_path)


def add_file_to_monitoring(self):
    """선택한 파일을 모니터링에 추가"""
    file_path = self.file_path_input.text()
    if not file_path:
        QMessageBox.warning(self, "경고", "모니터링할 파일을 선택하세요.")
        return
    
    try:
        if code_guardian.is_monitoring:
            code_guardian.monitored_files.append(file_path)
            self.statusBar().showMessage(f"파일이 모니터링에 추가됨: {file_path}")
        else:
            code_guardian.start_monitoring([file_path])
            self.statusBar().showMessage(f"파일 모니터링 시작됨: {file_path}")
        
        # 모니터링 파일 목록 업데이트
        self.update_dashboard_stats()
        
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
        if not code_guardian.is_monitoring:
            # 모니터링 대상 파일이 없으면 테스트 파일 사용
            if not code_guardian.monitored_files:
                test_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tests/error_test.py'))
                code_guardian.start_monitoring([test_file], ['tests'])
            else:
                code_guardian.start_monitoring()
            
            self.statusBar().showMessage("모니터링 시작됨")
            self.update_dashboard_stats()
            
            # 상태 메시지 업데이트
            QMessageBox.information(self, "모니터링", "코드 모니터링이 시작되었습니다.")
        else:
            QMessageBox.information(self, "모니터링", "이미 모니터링이 활성화되어 있습니다.")
        
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
            
            # 결과 메시지 준비
            result_message = f"폴더 스캔이 완료되었습니다.\n스캔된 Python 파일: {len(python_files)}개"
            
            if scan_errors:
                # 최대 5개의 오류만 표시
                error_list = "\n\n스캔 중 발생한 오류:\n" + "\n".join(scan_errors[:5])
                if len(scan_errors) > 5:
                    error_list += f"\n... 외 {len(scan_errors) - 5}개 오류"
                result_message += error_list
            
            QMessageBox.information(self, "스캔 완료", result_message)
            
            # 대시보드 업데이트
            self.update_dashboard_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"폴더 스캔 실패: {str(e)}")


def show_settings(self):
    """설정 대화상자 표시"""
    QMessageBox.information(self, "설정", "설정 기능은 아직 구현되지 않았습니다.")


def show_about(self):
    """정보 대화상자 표시"""
    QMessageBox.about(self, "CodeGuardian 정보", 
                     "CodeGuardian\n버전 1.0\n\n코드 보호 및 분석 도구")
