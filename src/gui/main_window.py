"""
메인 윈도우 구현
CodeGuardian GUI의 주요 윈도우 클래스
"""

import sys
import os
import time
from PyQt5.QtWidgets import (QMainWindow, QApplication, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QStatusBar, QMenu, QAction, QToolBar,
                             QComboBox, QSlider, QCheckBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 코어 모듈 임포트
from core.core import code_guardian
from tracer.call_tracer import call_tracer
from visualizer.graph_visualizer import graph_visualizer

# 뷰 모듈 임포트 (직접 구현한 것들만 임포트)
try:
    from gui.views.call_graph_view import CallGraphView
    call_graph_view_available = True
except ImportError:
    call_graph_view_available = False

try:
    from gui.views.error_analysis_view import ErrorAnalysisView
    error_analysis_view_available = True
except ImportError:
    error_analysis_view_available = False

# 스레드 작업 클래스 임포트
from gui.workers import RefreshWorker


class MainWindow(QMainWindow):
    """CodeGuardian 메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        
        # 윈도우 설정
        self.setWindowTitle("CodeGuardian")
        self.resize(1200, 800)
        
        # 작업 스레드
        self.refresh_worker = RefreshWorker()
        self.refresh_worker.finished.connect(self.on_refresh_complete)
        
        # UI 초기화
        self.init_ui()
        
        # 시스템 초기화
        self.initialize_system()
    
    def init_ui(self):
        """UI 구성"""
        # 메뉴바 생성
        self.create_menu_bar()
        
        # 툴바 생성
        self.create_toolbar()
        
        # 중앙 위젯 (탭 방식)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 대시보드 뷰
        self.dashboard_view = QWidget()
        self.setup_dashboard_view()
        self.tabs.addTab(self.dashboard_view, "대시보드")
        
        # 코드 모니터 뷰
        self.code_monitor_view = QWidget()
        self.setup_code_monitor_view()
        self.tabs.addTab(self.code_monitor_view, "코드 모니터")
        
        # 호출 그래프 뷰
        if call_graph_view_available:
            self.call_graph_view = CallGraphView()
        else:
            self.call_graph_view = QWidget()
            self.setup_call_graph_view()
        self.tabs.addTab(self.call_graph_view, "호출 그래프")
        
        # 변경 이력 뷰
        self.change_history_view = QWidget()
        self.setup_change_history_view()
        self.tabs.addTab(self.change_history_view, "변경 이력")
        
        # 에러 분석 뷰
        if error_analysis_view_available:
            self.error_analysis_view = ErrorAnalysisView()
        else:
            self.error_analysis_view = QWidget()
            self.setup_error_analysis_view()
        self.tabs.addTab(self.error_analysis_view, "에러 분석")
        
        # 탭 변경 이벤트 연결
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # 상태바 설정
        self.statusBar().showMessage("준비")
    
    def setup_dashboard_view(self):
        """대시보드 뷰 설정"""
        layout = QVBoxLayout()
        
        # 상태 요약 라벨
        title = QLabel("CodeGuardian 대시보드")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        
        # 통계 패널
        stats_layout = QHBoxLayout()
        
        # 보호 중인 함수 카운트
        self.protected_count = QLabel("보호 중인 함수: 0")
        self.protected_count.setStyleSheet("font-size: 14px; padding: 10px;")
        
        # 모니터링 중인 파일 카운트
        self.monitored_count = QLabel("모니터링 중인 파일: 0")
        self.monitored_count.setStyleSheet("font-size: 14px; padding: 10px;")
        
        # 감지된 에러 카운트
        self.error_count = QLabel("감지된 에러: 0")
        self.error_count.setStyleSheet("font-size: 14px; padding: 10px;")
        
        stats_layout.addWidget(self.protected_count)
        stats_layout.addWidget(self.monitored_count)
        stats_layout.addWidget(self.error_count)
        
        # 상태 메시지
        self.status_message = QLabel("CodeGuardian이 코드를 보호하고 있습니다.")
        self.status_message.setAlignment(Qt.AlignCenter)
        self.status_message.setStyleSheet("font-size: 14px; padding: 20px;")
        
        # 주요 기능 버튼
        buttons_layout = QHBoxLayout()
        
        self.monitor_btn = QPushButton("모니터링 시작")
        self.monitor_btn.clicked.connect(self.start_monitoring)
        
        self.scan_btn = QPushButton("코드 스캔")
        self.scan_btn.clicked.connect(self.scan_files)
        
        self.refresh_btn = QPushButton("데이터 새로고침")
        self.refresh_btn.clicked.connect(self.refresh_all_data)
        
        buttons_layout.addWidget(self.monitor_btn)
        buttons_layout.addWidget(self.scan_btn)
        buttons_layout.addWidget(self.refresh_btn)
        
        # 레이아웃에 추가
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addLayout(stats_layout)
        layout.addWidget(self.status_message)
        layout.addLayout(buttons_layout)
        layout.addStretch(1)
        
        self.dashboard_view.setLayout(layout)
    
    def setup_code_monitor_view(self):
        """코드 모니터 뷰 설정"""
        layout = QVBoxLayout()
        
        # 파일 선택 패널
        file_panel = QHBoxLayout()
        
        file_label = QLabel("파일:")
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        
        browse_btn = QPushButton("찾아보기...")
        browse_btn.clicked.connect(self.browse_file)
        
        add_btn = QPushButton("모니터링 추가")
        add_btn.clicked.connect(self.add_file_to_monitoring)
        
        file_panel.addWidget(file_label)
        file_panel.addWidget(self.file_path_input)
        file_panel.addWidget(browse_btn)
        file_panel.addWidget(add_btn)
        
        # 모니터링 중인 파일 목록 패널
        self.monitored_files_label = QLabel("모니터링 중인 파일:")
        self.monitored_files_text = QLabel("없음")
        
        # 보호 상태 패널
        status_layout = QHBoxLayout()
        
        self.protection_status = QLabel("보호 상태: 모니터링 중지됨")
        self.protection_status.setStyleSheet("font-weight: bold;")
        
        refresh_status_btn = QPushButton("상태 새로고침")
        refresh_status_btn.clicked.connect(self.refresh_protection_status)
        
        status_layout.addWidget(self.protection_status)
        status_layout.addStretch(1)
        status_layout.addWidget(refresh_status_btn)
        
        # 레이아웃에 추가
        layout.addLayout(file_panel)
        layout.addWidget(self.monitored_files_label)
        layout.addWidget(self.monitored_files_text)
        layout.addLayout(status_layout)
        layout.addStretch(1)
        
        self.code_monitor_view.setLayout(layout)
    
    def setup_call_graph_view(self):
        """호출 그래프 뷰 설정 (내장 구현)"""
        layout = QVBoxLayout()
        
        # 컨트롤 패널
        control_panel = QHBoxLayout()
        
        # 함수명 입력
        search_label = QLabel("함수: ")
        self.function_search = QLineEdit()
        self.function_search.setPlaceholderText("함수명 검색...")
        
        # 호출 깊이 슬라이더
        depth_label = QLabel("호출 깊이: ")
        self.depth_value_label = QLabel("2")
        self.depth_slider = QSlider(Qt.Horizontal)
        self.depth_slider.setRange(1, 5)
        self.depth_slider.setValue(2)
        self.depth_slider.valueChanged.connect(lambda v: self.depth_value_label.setText(str(v)))
        
        # 방향 선택
        direction_label = QLabel("방향: ")
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["양방향", "호출만", "피호출만"])
        
        # 그래프 생성 버튼
        self.create_graph_btn = QPushButton("그래프 생성")
        self.create_graph_btn.clicked.connect(self.on_create_graph)
        
        # 컨트롤 패널에 위젯 추가
        control_panel.addWidget(search_label)
        control_panel.addWidget(self.function_search)
        control_panel.addWidget(depth_label)
        control_panel.addWidget(self.depth_slider)
        control_panel.addWidget(self.depth_value_label)
        control_panel.addWidget(direction_label)
        control_panel.addWidget(self.direction_combo)
        control_panel.addWidget(self.create_graph_btn)
        
        # 그래프 표시 영역
        self.graph_view = QLabel("그래프가 여기에 표시됩니다")
        self.graph_view.setAlignment(Qt.AlignCenter)
        self.graph_view.setMinimumSize(800, 600)
        self.graph_view.setStyleSheet("background-color: white; border: 1px solid #cccccc;")
        
        # 옵션 패널
        option_panel = QHBoxLayout()
        
        self.show_module_cb = QCheckBox("모듈 정보 표시")
        self.highlight_errors_cb = QCheckBox("에러 발생 함수 강조")
        self.highlight_errors_cb.setChecked(True)
        
        option_panel.addWidget(self.show_module_cb)
        option_panel.addWidget(self.highlight_errors_cb)
        option_panel.addStretch(1)
        
        # 레이아웃에 추가
        layout.addLayout(control_panel)
        layout.addWidget(self.graph_view)
        layout.addLayout(option_panel)
        
        self.call_graph_view.setLayout(layout)
    
    def setup_change_history_view(self):
        """변경 이력 뷰 설정"""
        layout = QVBoxLayout()
        
        # 변경 이력 라벨
        title = QLabel("코드 변경 이력")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # 필터 패널
        filter_panel = QHBoxLayout()
        
        filter_label = QLabel("함수 필터:")
        self.change_function_filter = QLineEdit()
        self.change_function_filter.setPlaceholderText("함수명 입력...")
        
        refresh_changes_btn = QPushButton("변경 이력 새로고침")
        refresh_changes_btn.clicked.connect(self.refresh_changes)
        
        filter_panel.addWidget(filter_label)
        filter_panel.addWidget(self.change_function_filter)
        filter_panel.addStretch(1)
        filter_panel.addWidget(refresh_changes_btn)
        
        # 변경 이력 정보
        self.changes_info = QLabel("변경 이력 정보가 여기에 표시됩니다")
        self.changes_info.setAlignment(Qt.AlignCenter)
        self.changes_info.setStyleSheet("background-color: white; border: 1px solid #cccccc; padding: 10px;")
        self.changes_info.setMinimumHeight(400)
        
        # 레이아웃에 추가
        layout.addWidget(title)
        layout.addLayout(filter_panel)
        layout.addWidget(self.changes_info)
        
        self.change_history_view.setLayout(layout)
    
    def setup_error_analysis_view(self):
        """에러 분석 뷰 설정 (내장 구현)"""
        layout = QVBoxLayout()
        
        # 컨트롤 패널
        control_panel = QHBoxLayout()
        
        # 함수명 입력
        search_label = QLabel("함수: ")
        self.error_function_search = QLineEdit()
        self.error_function_search.setPlaceholderText("함수명 검색...")
        
        # 새로고침 버튼
        self.refresh_errors_btn = QPushButton("새로고침")
        self.refresh_errors_btn.clicked.connect(self.on_refresh_errors)
        
        # 컨트롤 패널에 위젯 추가
        control_panel.addWidget(search_label)
        control_panel.addWidget(self.error_function_search)
        control_panel.addStretch(1)
        control_panel.addWidget(self.refresh_errors_btn)
        
        # 에러 목록 (실제로는 테이블 위젯 사용)
        self.error_list = QLabel("에러 정보가 여기에 표시됩니다")
        self.error_list.setAlignment(Qt.AlignCenter)
        self.error_list.setMinimumSize(800, 400)
        self.error_list.setStyleSheet("background-color: white; border: 1px solid #cccccc;")
        
        # 에러 상세 정보
        self.error_details = QLabel("선택한 에러의 상세 정보")
        self.error_details.setAlignment(Qt.AlignCenter)
        self.error_details.setMinimumSize(800, 200)
        self.error_details.setStyleSheet("background-color: #f9f9f9; border: 1px solid #cccccc;")
        
        # 레이아웃에 추가
        layout.addLayout(control_panel)
        layout.addWidget(self.error_list)
        layout.addWidget(self.error_details)
        
        self.error_analysis_view.setLayout(layout)
    
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일')
        
        open_action = QAction('프로젝트 열기', self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction('저장', self)
        save_action.triggered.connect(self.save_data)
        file_menu.addAction(save_action)
        
        exit_action = QAction('종료', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 보기 메뉴
        view_menu = menubar.addMenu('보기')
        
        refresh_action = QAction('새로고침', self)
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)
        
        # 도구 메뉴
        tools_menu = menubar.addMenu('도구')
        
        start_monitoring_action = QAction('모니터링 시작', self)
        start_monitoring_action.triggered.connect(self.start_monitoring)
        tools_menu.addAction(start_monitoring_action)
        
        stop_monitoring_action = QAction('모니터링 중지', self)
        stop_monitoring_action.triggered.connect(self.stop_monitoring)
        tools_menu.addAction(stop_monitoring_action)
        
        scan_files_action = QAction('파일 스캔', self)
        scan_files_action.triggered.connect(self.scan_files)
        tools_menu.addAction(scan_files_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말')
        
        about_action = QAction('CodeGuardian 정보', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """툴바 생성"""
        toolbar = QToolBar("메인 툴바")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # 새로고침 버튼
        refresh_action = QAction('새로고침', self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 모니터링 시작/중지 버튼
        start_action = QAction('모니터링 시작', self)
        start_action.triggered.connect(self.start_monitoring)
        toolbar.addAction(start_action)
        
        stop_action = QAction('모니터링 중지', self)
        stop_action.triggered.connect(self.stop_monitoring)
        toolbar.addAction(stop_action)
        
        toolbar.addSeparator()
        
        # 설정 버튼
        settings_action = QAction('설정', self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)

    # 나머지 메서드는 main_window_functions.py 파일에 구현
    from gui.main_window_functions import (
        initialize_system, on_tab_changed, refresh_data, refresh_all_data,
        update_dashboard_stats, on_refresh_complete, update_graph_view,
        update_error_view, update_changes_view, on_create_graph,
        on_refresh_errors, refresh_changes, refresh_protection_status,
        browse_file, add_file_to_monitoring, open_project, save_data,
        start_monitoring, stop_monitoring, scan_files, show_settings,
        show_about
    )


# 테스트용 메인 함수
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
