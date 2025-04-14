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
                             QComboBox, QSlider, QCheckBox, QFileDialog, QMessageBox,
                             QScrollArea)
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
        
        # GUI 자동 업데이트 타이머 설정
        from PyQt5.QtCore import QTimer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(5000)  # 5초마다 업데이트
        
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
        
        # GUI 명시적 새로고침 버튼 추가
        self.gui_refresh_btn = QPushButton("GUI 새로고침")
        self.gui_refresh_btn.clicked.connect(self.refresh_gui)
        self.gui_refresh_btn.setToolTip("GUI 화면을 명시적으로 새로고침합니다")
        
        buttons_layout.addWidget(self.monitor_btn)
        buttons_layout.addWidget(self.scan_btn)
        buttons_layout.addWidget(self.refresh_btn)
        buttons_layout.addWidget(self.gui_refresh_btn)
        
        # 모니터링 함수 목록
        functions_label = QLabel("모니터링 중인 함수 목록:")
        functions_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 20px;")
        
        # 함수 목록 표시 영역 (스크롤 영역 추가)
        self.functions_display = QLabel()
        self.functions_display.setStyleSheet("""
            background-color: white; 
            border: 1px solid #cccccc; 
            padding: 15px;
            font-family: 'Consolas', monospace;
            font-size: 13px;
        """)
        self.functions_display.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.functions_display.setTextFormat(Qt.RichText)
        self.functions_display.setWordWrap(True)
        
        # 스크롤 영역 설정
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.functions_display)
        scroll_area.setMinimumHeight(400)  # 더 큰 높이로 설정
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)
        
        # 함수 코드 표시 예시
        self.update_monitored_functions()
        
        # 레이아웃에 추가
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addLayout(stats_layout)
        layout.addWidget(self.status_message)
        layout.addLayout(buttons_layout)
        layout.addWidget(functions_label)
        layout.addWidget(scroll_area)  # QLabel 대신 스크롤 영역 추가
        
        self.dashboard_view.setLayout(layout)
    
    def update_monitored_functions(self):
        """모니터링 중인 함수 목록 업데이트"""
        print("함수 목록 업데이트 시작")
        
        # UI 요소 초기화 - 텍스트 비우기
        self.functions_display.clear()
        self.functions_display.setText("")
        QApplication.processEvents()
        
        # 동적으로 모니터링 중인 함수 목록 가져오기
        monitored_functions = []
        
        # code_guardian에서 함수 목록 가져오기
        if hasattr(code_guardian, 'monitored_functions') and code_guardian.monitored_functions:
            monitored_functions = code_guardian.monitored_functions
            print(f"코어에서 함수 목록 가져옴: {len(monitored_functions)}개")
        
        # 함수 목록이 없으면 모니터링 중인 모든 파일에서 함수 추출
        if not monitored_functions and hasattr(code_guardian, 'monitored_files') and code_guardian.monitored_files:
            for file_path in code_guardian.monitored_files:
                if os.path.exists(file_path):
                    file_functions = self.extract_functions_from_file(file_path)
                    print(f"파일에서 함수 추출: {file_path}, {len(file_functions)}개 함수")
                    monitored_functions.extend(file_functions)
            
            # 중복 제거
            monitored_functions = list(dict.fromkeys(monitored_functions))
            print(f"중복 제거 후 함수 수: {len(monitored_functions)}")
            
            # code_guardian에 함수 목록 업데이트
            if monitored_functions:
                code_guardian.monitored_functions = monitored_functions
        
        # 기본 테스트 파일 시도 (여전히 함수가 없는 경우)
        if not monitored_functions:
            test_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      "tests", "error_test.py")
            if os.path.exists(test_file_path):
                file_functions = self.extract_functions_from_file(test_file_path)
                monitored_functions.extend(file_functions)
                print(f"기본 테스트 파일에서 함수 추출: {len(file_functions)}개")
                
                # code_guardian에 기본 테스트 파일 추가
                if test_file_path not in code_guardian.monitored_files:
                    code_guardian.monitored_files.append(test_file_path)
                
                # code_guardian에 함수 목록 업데이트
                if monitored_functions:
                    code_guardian.monitored_functions = monitored_functions
        
        # 함수 목록 HTML 구성
        html_content = "<b>모니터링 중인 파일:</b> "
        if hasattr(code_guardian, 'monitored_files') and code_guardian.monitored_files:
            if len(code_guardian.monitored_files) == 1:
                html_content += code_guardian.monitored_files[0]
            else:
                html_content += f"{len(code_guardian.monitored_files)}개 파일"
        else:
            html_content += "없음"
        
        html_content += "<br><b>모니터링 중인 함수:</b><br>"
        
        # 함수 분석 정보
        function_info = self.analyze_functions(monitored_functions)
        
        # 각 함수에 대한 정보 추가
        for i, func_data in enumerate(function_info):
            func_name = func_data['name']
            status = func_data['status']
            description = func_data['description']
            
            # 함수 상태에 따른 색상
            color = "#5cb85c"  # 기본 초록색 (정상)
            if status == "에러 발생 가능":
                color = "#d9534f"  # 빨간색
            elif status == "주의":
                color = "#f0ad4e"  # 노란색
            
            html_content += f"<div style='margin-bottom: 10px;'>"
            html_content += f"<span style='color: {color}; font-weight: bold;'>{i+1}. {func_name}()</span>"
            html_content += f" - <span>{status}</span>"
            
            # 설명 추가
            if description:
                html_content += f"<br><span style='margin-left: 20px; color: #666;'>{description}</span>"
            
            html_content += "</div>"
        
        # 함수 목록 정보 업데이트
        print(f"함수 목록 표시: {len(monitored_functions)}개")
        
        # 표시 - 완전히 새로 설정 (QLabel은 setHtml이 아닌 setText 사용)
        self.functions_display.setText(html_content)
        self.functions_display.repaint()
        QApplication.processEvents()
    
    def extract_functions_from_file(self, file_path):
        """파일에서 함수 목록 추출
        
        Args:
            file_path: 파일 경로
            
        Returns:
            함수명 목록
        """
        functions = []
        try:
            # 파일이 존재하는지 확인
            if not os.path.exists(file_path):
                print(f"파일이 존재하지 않음: {file_path}")
                return functions
                
            # 파일에서 함수 추출
            import re
            print(f"파일에서 함수 추출 시도: {file_path}")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            print(f"파일 내용에서 함수 추출 시작...")
            # 함수 정의 패턴 검색
            func_pattern = re.compile(r'def\s+(\w+)\s*\(', re.MULTILINE)
            functions = func_pattern.findall(content)
            
            # 추출된 함수 목록 출력
            for func in functions:
                print(f"함수 발견: {func}")
                
        except Exception as e:
            print(f"파일 {file_path}에서 함수 추출 오류: {str(e)}")
        
        return functions
    
    def analyze_functions(self, function_names):
        """함수 목록에 대한 상태 및 설명 분석
        
        Args:
            function_names: 함수명 목록
            
        Returns:
            함수 정보 목록 [{name, status, description}, ...]
        """
        result = []
        
        # 파일 내용 가져오기
        file_content = ""
        if hasattr(code_guardian, 'monitored_files') and code_guardian.monitored_files:
            try:
                with open(code_guardian.monitored_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
            except Exception as e:
                print(f"파일 읽기 오류: {str(e)}")
        
        for func_name in function_names:
            # 기본 정보
            func_info = {
                'name': func_name,
                'status': '정상',
                'description': ''
            }
            
            # 함수 코드에서 패턴 분석을 통한 자동 판단
            if file_content:
                import re
                # 함수 코드 추출
                pattern = re.compile(r'def\s+' + re.escape(func_name) + r'\s*\([^)]*\):(.*?)(?=\ndef|\Z)', re.DOTALL)
                matches = pattern.findall(file_content)
                
                if matches:
                    func_code = matches[0]
                    
                    # 에러 패턴 검색
                    if "ZeroDivisionError" in func_code or "division by zero" in func_code:
                        func_info['status'] = "에러 발생 가능"
                        func_info['description'] = "0으로 나누기 에러 발생 가능"
                    elif "IndexError" in func_code or "list index" in func_code:
                        func_info['status'] = "에러 발생 가능"
                        func_info['description'] = "인덱스 에러 발생 가능"
                    elif "TypeError" in func_code:
                        func_info['status'] = "에러 발생 가능"
                        func_info['description'] = "타입 에러 발생 가능"
                    elif "Exception" in func_code or "raise" in func_code:
                        func_info['status'] = "주의"
                        func_info['description'] = "예외 발생 가능성 있음"
                    
                    # 재귀 함수 확인
                    if func_name in func_code[10:]:  # 자기 자신을 호출하는지
                        func_info['status'] = "주의"
                        func_info['description'] = "재귀 함수, 스택 오버플로우 가능성"
                    
                    # 독스트링에서 설명 추출
                    docstring_match = re.search(r'"""(.*?)"""', func_code, re.DOTALL)
                    if docstring_match and not func_info['description']:
                        func_info['description'] = docstring_match.group(1).strip()
            
            # 특정 함수에 대한 하드코딩된 지식이 없을 경우 기본 설명
            if not func_info['description']:
                if "calculate" in func_name or "compute" in func_name:
                    func_info['description'] = "계산 함수"
                elif "process" in func_name:
                    func_info['description'] = "데이터 처리 함수"
                elif "validate" in func_name or "check" in func_name:
                    func_info['description'] = "유효성 검사 함수"
                elif "test" in func_name:
                    func_info['description'] = "테스트 함수"
                elif "error" in func_name:
                    func_info['status'] = "주의"
                    func_info['description'] = "오류 관련 함수"
                else:
                    func_info['description'] = "일반 함수"
            
            result.append(func_info)
        
        return result
    
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
        
        # 함수 선택 드롭다운 패널
        function_select_panel = QHBoxLayout()
        
        function_select_label = QLabel("함수 선택:")
        self.function_combo = QComboBox()
        self.function_combo.setMinimumWidth(300)
        self.function_combo.currentIndexChanged.connect(self.on_function_selected)
        
        function_select_panel.addWidget(function_select_label)
        function_select_panel.addWidget(self.function_combo)
        function_select_panel.addStretch(1)
        
        # 함수 정보 패널
        functions_label = QLabel("함수 정보:")
        functions_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        
        # 함수 정보를 표시할 레이블
        self.functions_content = QLabel()
        self.functions_content.setWordWrap(True)
        self.functions_content.setTextFormat(Qt.RichText)
        self.functions_content.setStyleSheet("""
            background-color: white;
            padding: 15px;
            font-family: Consolas, monospace;
            font-size: 13px;
        """)
        
        # 스크롤 영역 설정
        content_scroll_area = QScrollArea()
        content_scroll_area.setWidgetResizable(True)
        content_scroll_area.setWidget(self.functions_content)
        content_scroll_area.setMinimumHeight(400)  # 충분한 높이 설정
        content_scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
        """)
        
        # 액션 버튼 패널
        buttons_panel = QHBoxLayout()
        
        update_functions_btn = QPushButton("함수 목록 새로고침")
        update_functions_btn.clicked.connect(self.update_monitored_functions_display)
        
        remove_function_btn = QPushButton("함수 모니터링 중지")
        remove_function_btn.clicked.connect(self.remove_function_from_monitoring)
        remove_function_btn.setStyleSheet("background-color: #d9534f; color: white;")
        
        buttons_panel.addWidget(update_functions_btn)
        buttons_panel.addWidget(remove_function_btn)
        
        # 레이아웃에 추가
        layout.addLayout(file_panel)
        layout.addWidget(self.monitored_files_label)
        layout.addWidget(self.monitored_files_text)
        layout.addLayout(status_layout)
        layout.addLayout(function_select_panel)
        layout.addWidget(functions_label)
        layout.addWidget(content_scroll_area)  # 스크롤 영역 추가
        layout.addLayout(buttons_panel)
        
        self.code_monitor_view.setLayout(layout)
        
        # 초기 함수 목록 표시
        self.update_monitored_functions_display()
    
    def update_monitored_functions_display(self):
        """모니터링 중인 함수 정보를 화면에 표시"""
        print("코드 모니터 함수 목록 표시 시작")
        
        # UI 요소 초기화 - 텍스트 비우기
        self.functions_content.clear()
        self.functions_content.setText("")
        QApplication.processEvents()
        
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

        # 모니터링 중인 함수들의 정보 가져오기
        functions_data = self.get_monitored_functions_data()
        print(f"가져온 함수 데이터 수: {len(functions_data)}")
        
        # HTML 내용 구성 시작
        html_content = css_style
        
        # 모니터링 중인 파일 목록 표시
        html_content += "<h3>모니터링 중인 파일</h3>"
        
        # 파일별로 함수 그룹화
        file_dict = {}
        for func in functions_data:
            file_path = func['file_path']
            if file_path not in file_dict:
                file_dict[file_path] = []
            file_dict[file_path].append(func)
        
        # 파일별로 함수 목록 추가
        if file_dict:
            print(f"파일 그룹 수: {len(file_dict)}")
            for file_path, file_functions in file_dict.items():
                file_name = os.path.basename(file_path)
                html_content += f'<div class="section-header">{file_name} - {len(file_functions)}개 함수</div>'
                
                # 파일의 각 함수 정보 추가
                for func_data in file_functions:
                    # 함수 상태에 따른 CSS 클래스 결정
                    func_class = "function"
                    name_class = "function-name"
                    if func_data['status'] == "위험":
                        func_class += " error-function"
                        name_class += " error-name"
                    
                    # 상태 배지 CSS 클래스 결정
                    badge_class = "status-badge"
                    if func_data['status'] == "위험":
                        badge_class += " status-error"
                    elif func_data['status'] == "주의":
                        badge_class += " status-warning"
                    else:
                        badge_class += " status-normal"
                    
                    # 함수 HTML 구성
                    html_content += f"""
<div class="{func_class}">
<span class="{name_class}">{func_data['name']}({func_data['params']})</span>
<span class="{badge_class}">{func_data['status']}</span>
<div class="file-info">파일: {func_data['file_name']}</div>
<div class="function-code">{func_data['code_html']}</div>
<div class="function-desc">{func_data['description']}</div>
</div>
"""
        else:
            # 함수가 없는 경우
            html_content += "<p>모니터링 중인 함수가 없습니다.</p>"
            print("모니터링 중인 함수가 없음")
        
        # 내용 설정 - 완전히 새로 설정 (QLabel은 setHtml이 아닌 setText 사용)
        self.functions_content.setText(html_content)
        self.functions_content.repaint()
        QApplication.processEvents()
        print("코드 모니터 함수 목록 표시 완료")
    
    def get_monitored_functions_data(self):
        """모니터링 중인 함수 데이터를 가져옴"""
        print('모니터링된 함수 데이터 가져오기 실행')
        # 전체 함수 데이터
        all_functions_data = []
        
        # 모니터링 중인 파일 경로 목록 가져오기
        monitored_files = []
        print('모니터링 중인 파일 목록 가져오기')
        if hasattr(code_guardian, 'monitored_files') and code_guardian.monitored_files:
            monitored_files = code_guardian.monitored_files.copy()
            print(f'code_guardian에서 얻은 모니터링 파일 목록: {monitored_files}')
        else:
            # 기본 테스트 파일 경로
            test_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      "tests", "error_test.py")
            if os.path.exists(test_file):
                monitored_files.append(test_file)
                # code_guardian에 파일 경로 추가
                if not hasattr(code_guardian, 'monitored_files'):
                    code_guardian.monitored_files = []
                if test_file not in code_guardian.monitored_files:
                    code_guardian.monitored_files.append(test_file)
        
        # 각 파일에서 함수 정보 추출
        for file_path in monitored_files:
            # 파일이 존재하지 않으면 건너뜀
            if not os.path.exists(file_path):
                continue
            
            try:
                # 파일 읽기
                print(f'파일에서 함수 추출 시도: {file_path}')
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
                
                # 파일에서 함수 추출 - 개선된 정규식 패턴
                import re
                # 함수 정의를 찾는 패턴 (다음 함수 정의까지 또는 파일 끝까지)
                func_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]*)\):(.*?)(?=\s*def\s+\w+\s*\(|\Z)', re.DOTALL)
                
                print(f'파일 내용에서 함수 추출 시작...')
                matches = func_pattern.finditer(file_content)
                
                # 파일 내 모든 함수 이름 목록 (코어에 추가하기 위함)
                file_functions = []
                
                for match in matches:
                    func_name = match.group(1)
                    func_params = match.group(2).strip()
                    func_body = match.group(3).strip()
                    print(f'함수 발견: {func_name}({func_params})')
                    
                    # 함수 이름 목록에 추가
                    file_functions.append(func_name)
                    
                    # 함수 상태 결정 (위험/주의/정상)
                    status = "정상"
                    if "ZeroDivisionError" in func_body or "IndexError" in func_body or "TypeError" in func_body:
                        status = "위험"
                    elif "recursive" in func_name or func_name in func_body[10:]:  # 자기 자신을 호출하는지 확인
                        status = "주의"
                    
                    # HTML 코드 생성 (줄바꿈과 들여쓰기 처리)
                    code_html = "def " + func_name + "(" + func_params + "):<br>"
                    
                    # 함수 본문 처리
                    for line in func_body.split('\n'):
                        if line.strip():
                            # 들여쓰기 수준 계산
                            indent_level = len(line) - len(line.lstrip())
                            indent_html = "&nbsp;" * 4  # 4칸 들여쓰기를 기본으로 설정
                            
                            # HTML에서 안전하게 표시하기 위해 특수 문자 처리
                            line_content = line.strip().replace("<", "&lt;").replace(">", "&gt;")
                            
                            # 최종 줄 구성
                            code_html += indent_html + line_content + "<br>"
                    
                    # 함수 설명 추출 (독스트링이 있는 경우)
                    description = ""
                    docstring_match = re.search(r'"""(.*?)"""', func_body, re.DOTALL)
                    if docstring_match:
                        description = docstring_match.group(1).strip()
                    else:
                        # 독스트링이 없는 경우 상태별 기본 설명 제공
                        if status == "위험":
                            if "ZeroDivisionError" in func_body:
                                description = "0으로 나누기 에러 발생 가능"
                            elif "IndexError" in func_body:
                                description = "인덱스 에러 발생 가능"
                            elif "TypeError" in func_body:
                                description = "타입 에러 발생 가능"
                            else:
                                description = "다양한 에러 타입 발생 가능"
                        elif status == "주의":
                            description = "재귀 함수 - 스택 오버플로우 가능성"
                        else:
                            description = "정상 동작 함수"
                    
                    # 파일 경로 표시 (여러 파일을 모니터링할 경우 유용)
                    file_name = os.path.basename(file_path)
                    
                    # 함수 데이터 추가
                    all_functions_data.append({
                        'name': func_name,
                        'params': func_params,
                        'code_html': code_html,
                        'status': status,
                        'description': description,
                        'file_path': file_path,
                        'file_name': file_name
                    })
                
                # 파일에서 발견된 함수 목록을 코어에 추가 (중복 제거)
                if file_functions:
                    if not hasattr(code_guardian, 'monitored_functions'):
                        code_guardian.monitored_functions = []
                    
                    # 새 함수 추가 (중복 제거)
                    for func in file_functions:
                        if func not in code_guardian.monitored_functions:
                            code_guardian.monitored_functions.append(func)
                
            except Exception as e:
                # 오류 발생 시 로그 기록
                print(f"파일 '{file_path}' 함수 정보 파싱 오류: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 함수를 찾지 못한 경우 비어있는 목록 반환
        if not all_functions_data:
            # 기본 테스트 파일이 있는지 확인하고 있으면 파싱 시도
            test_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                      "tests", "error_test.py")
            if os.path.exists(test_file_path):
                try:
                    with open(test_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 간단한 함수 명만 추출
                    import re
                    func_pattern = re.compile(r'def\s+(\w+)\s*\(', re.MULTILINE)
                    functions = func_pattern.findall(content)
                    
                    # 간단한 설명만 제공
                    for func in functions:
                        all_functions_data.append({
                            'name': func,
                            'params': '...',
                            'code_html': f'def {func}(...):<br>&nbsp;&nbsp;&nbsp;&nbsp;# 함수 내용',
                            'status': '정상',
                            'description': '함수 정보를 가져올 수 없습니다',
                            'file_path': test_file_path,
                            'file_name': os.path.basename(test_file_path)
                        })
                except Exception as e:
                    print(f"테스트 파일 파싱 오류: {str(e)}")
        
        return all_functions_data
    
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
    
    def periodic_update(self):
        """GUI 주기적 업데이트 함수 - 타이머에 의해 호출됨"""
        # 현재 탭 확인
        current_tab = self.tabs.currentIndex()
        current_tab_name = self.tabs.tabText(current_tab)
        
        try:
            # 가벼운 업데이트만 수행
            if hasattr(code_guardian, 'monitored_functions'):
                function_count = len(code_guardian.monitored_functions)
                self.protected_count.setText(f"보호 중인 함수: {function_count}")
            
            if hasattr(code_guardian, 'monitored_files'):
                file_count = len(code_guardian.monitored_files)
                self.monitored_count.setText(f"모니터링 중인 파일: {file_count}")
            
            # 탭에 따른 추가 업데이트
            if current_tab == 0:  # 대시보드
                pass  # 이미 업데이트됨
            elif current_tab == 1:  # 코드 모니터
                pass  # 코드 모니터는 무거우므로 필요시만 업데이트
            elif current_tab == 2:  # 호출 그래프
                pass  # 호출 그래프는 무거우므로 필요시만 업데이트
            elif current_tab == 3:  # 변경 이력
                pass  # 변경 이력은 무거우므로 필요시만 업데이트
            elif current_tab == 4:  # 에러 분석
                # 에러 수는 자주 확인
                try:
                    errors = code_guardian.get_error_data()
                    error_count = len(errors) if errors else 0
                    self.error_count.setText(f"감지된 에러: {error_count}")
                except:
                    pass
            
            # UI 업데이트
            QApplication.processEvents()
            
        except Exception as e:
            # 주기적 업데이트에서는 오류 무시
            print(f"주기적 업데이트 중 오류 발생 (무시됨): {str(e)}")

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
        show_about, refresh_gui, on_function_selected, remove_function_from_monitoring,
        display_function_details, update_monitored_functions_display
    )


# 테스트용 메인 함수
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
