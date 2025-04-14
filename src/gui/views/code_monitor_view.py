#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 코드 모니터 뷰
보호된 코드 목록 및 상태를 보여주는 UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QComboBox, QSplitter, QTreeView,
    QTextEdit, QGroupBox, QFileDialog, QFileSystemModel,
    QMessageBox, QFrame, QTextBrowser
)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QColor, QBrush, QFont, QIcon, QSyntaxHighlighter, QTextCharFormat

from src.storage.storage_manager import (
    get_protected_functions,
    get_protected_blocks,
    get_recent_changes
)
from src.core.events import event_bus
from src.core.settings import app_settings
import os
import re

class PythonHighlighter(QSyntaxHighlighter):
    """파이썬 구문 강조 클래스"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        
        # 키워드 강조
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor('#569CD6'))  # 파란색
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
            'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
            'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
            'while', 'with', 'yield'
        ]
        
        for word in keywords:
            pattern = r'\b{}\b'.format(word)
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
        
        # 클래스 이름 강조
        class_format = QTextCharFormat()
        class_format.setForeground(QColor('#4EC9B0'))  # 청록색
        class_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(r'\bclass\s+(\w+)'), class_format))
        
        # 함수 정의 강조
        function_format = QTextCharFormat()
        function_format.setForeground(QColor('#DCDCAA'))  # 황금색
        function_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(r'\bdef\s+(\w+)'), function_format))
        
        # 문자열 강조
        string_format = QTextCharFormat()
        string_format.setForeground(QColor('#CE9178'))  # 오렌지
        self.highlighting_rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.highlighting_rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        
        # 주석 강조
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor('#608B4E'))  # 녹색
        self.highlighting_rules.append((re.compile(r'#[^\n]*'), comment_format))
        
        # 숫자 강조
        number_format = QTextCharFormat()
        number_format.setForeground(QColor('#B5CEA8'))  # 밝은 녹색
        self.highlighting_rules.append((re.compile(r'\b[0-9]+\b'), number_format))
        
        # 셀프 참조 강조
        self_format = QTextCharFormat()
        self_format.setForeground(QColor('#569CD6'))  # 파란색
        self_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(r'\bself\b'), self_format))
    
    def highlightBlock(self, text):
        """텍스트 블록에 구문 강조 적용"""
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)

class CodeMonitorView(QWidget):
    """코드 모니터 뷰 클래스"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 이벤트 연결
        event_bus.code_changed.connect(self.on_code_changed)
        
        # 초기 데이터 로드
        self.load_data()
        
        # 샘플 데이터 추가 (실제 데이터가 없을 경우)
        if self.protected_table.rowCount() == 0:
            self.add_sample_data()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QHBoxLayout()  # 수평 레이아웃으로 변경
        
        # 왼쪽 패널: 폴더 구조 트리
        left_panel = QVBoxLayout()
        
        # 폴더 헤더
        folder_header = QLabel("모니터링 폴더")
        folder_header.setStyleSheet("font-weight: bold; font-size: 14px;")
        left_panel.addWidget(folder_header)
        
        # 폴더 트리 뷰 생성
        self.folder_tree = QTreeView()
        self.folder_tree.setHeaderHidden(True)
        self.folder_model = QFileSystemModel()
        self.folder_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.folder_model.setRootPath("")  # 기본 경로 설정
        
        # 모델을 트리 뷰에 설정
        self.folder_tree.setModel(self.folder_model)
        
        # 불필요한 열 숨기기
        for i in range(1, self.folder_model.columnCount()):
            self.folder_tree.hideColumn(i)
        
        left_panel.addWidget(self.folder_tree)
        
        # 버튼 패널
        button_panel = QHBoxLayout()
        self.add_folder_btn = QPushButton("폴더 추가")
        self.refresh_btn = QPushButton("새로 고침")
        
        button_panel.addWidget(self.add_folder_btn)
        button_panel.addWidget(self.refresh_btn)
        left_panel.addLayout(button_panel)
        
        # 왼쪽 패널 위젯 생성
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(300)  # 최대 너비 제한
        
        # 오른쪽 패널: 기존 코드 모니터 뷰
        right_panel = QVBoxLayout()
        
        # 상단 컨트롤 영역
        control_layout = QHBoxLayout()
        
        # 필터 콤보박스
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("모든 항목")
        self.filter_combo.addItem("함수만")
        self.filter_combo.addItem("블록만")
        self.filter_combo.addItem("변경된 항목만")
        control_layout.addWidget(QLabel("필터:"))
        control_layout.addWidget(self.filter_combo)
        
        # 새로고침 버튼
        self.refresh_list_btn = QPushButton("목록 새로고침")
        control_layout.addWidget(self.refresh_list_btn)
        
        # 보호 추가 버튼
        self.add_protection_btn = QPushButton("보호 추가...")
        control_layout.addWidget(self.add_protection_btn)
        
        control_layout.addStretch()
        
        right_panel.addLayout(control_layout)
        
        # 안내 텍스트 추가
        info_text = QLabel("모니터링 중인 코드 목록")
        info_text.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        right_panel.addWidget(info_text)
        
        # 중앙 영역 스플리터 (수평 분할)
        central_splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 테이블과 상세 정보
        table_details_widget = QWidget()
        table_details_layout = QVBoxLayout(table_details_widget)
        table_details_layout.setContentsMargins(0, 0, 0, 0)
        
        # 테이블과 상세정보 스플리터 (수직 분할)
        table_splitter = QSplitter(Qt.Vertical)
        
        # 보호된 코드 테이블
        self.protected_table = QTableWidget()
        self.protected_table.setColumnCount(5)
        self.protected_table.setHorizontalHeaderLabels(["유형", "파일", "이름", "상태", "마지막 확인"])
        self.protected_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.protected_table.setSelectionMode(QTableWidget.SingleSelection)
        self.protected_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 테이블 스타일 설정
        self.protected_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: #ffffff;
                alternate-background-color: #f7f7f7;
                selection-background-color: #e0e0ff;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        self.protected_table.setAlternatingRowColors(True)  # 행 색상 교차 적용
        
        table_splitter.addWidget(self.protected_table)
        
        # 상세 정보 영역
        details_group = QGroupBox("상세 정보")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextBrowser()  # QTextEdit 대신 QTextBrowser 사용
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        table_splitter.addWidget(details_group)
        
        # 비율 설정
        table_splitter.setSizes([400, 200])
        
        table_details_layout.addWidget(table_splitter)
        
        # 오른쪽: 코드 뷰어
        self.code_group = QGroupBox("코드 내용")
        code_layout = QVBoxLayout()
        
        self.code_browser = QTextEdit()
        self.code_browser.setReadOnly(True)
        self.code_browser.setFont(QFont("Consolas", 10))
        
        # 구문 강조 설정
        self.highlighter = PythonHighlighter(self.code_browser.document())
        
        code_layout.addWidget(self.code_browser)
        self.code_group.setLayout(code_layout)
        
        # 스플리터에 위젯 추가
        central_splitter.addWidget(table_details_widget)
        central_splitter.addWidget(self.code_group)
        central_splitter.setSizes([400, 600])  # 적절한 비율로 설정
        
        right_panel.addWidget(central_splitter)
        
        # 상태 정보 표시 프레임
        status_frame = QFrame()
        status_frame.setFrameShape(QFrame.StyledPanel)
        status_frame.setStyleSheet("background-color: #f0f8ff; border: 1px solid #b0c4de;")
        
        status_layout = QHBoxLayout()
        
        self.total_count = QLabel("총 항목: 0")
        self.func_count = QLabel("함수: 0")
        self.block_count = QLabel("블록: 0")
        self.changed_count = QLabel("변경됨: 0")
        
        status_layout.addWidget(self.total_count)
        status_layout.addWidget(self.func_count)
        status_layout.addWidget(self.block_count)
        status_layout.addWidget(self.changed_count)
        status_layout.addStretch()
        
        status_frame.setLayout(status_layout)
        right_panel.addWidget(status_frame)
        
        # 오른쪽 패널 위젯 생성
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        # 메인 레이아웃에 왼쪽과 오른쪽 패널 추가
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # 버튼 연결
        self.refresh_list_btn.clicked.connect(self.load_data)
        self.add_protection_btn.clicked.connect(self.add_protection)
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        self.protected_table.itemSelectionChanged.connect(self.show_details)
        self.add_folder_btn.clicked.connect(self.add_monitoring_folder)
        self.refresh_btn.clicked.connect(self.refresh_folder_view)
        self.folder_tree.clicked.connect(self.on_folder_selected)
        
        self.setLayout(main_layout)
        
        # 저장된 모니터링 경로 불러오기
        self.load_monitoring_paths()
    
    def load_monitoring_paths(self):
        """저장된 모니터링 경로 불러오기"""
        paths = app_settings.get("monitor", "paths", [])
        if paths:
            first_path = paths[0]
            self.folder_model.setRootPath(first_path)
            root_index = self.folder_model.index(first_path)
            self.folder_tree.setRootIndex(root_index)
        else:
            # 기본 모니터링 경로 설정 (현재 프로젝트 폴더)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.folder_model.setRootPath(base_dir)
            root_index = self.folder_model.index(base_dir)
            self.folder_tree.setRootIndex(root_index)
            
            # 설정에 추가
            app_settings.set("monitor", "paths", [base_dir])
    
    def add_monitoring_folder(self):
        """모니터링할 폴더 추가"""
        folder_path = QFileDialog.getExistingDirectory(self, "모니터링할 폴더 선택")
        
        if folder_path:
            # 선택된 폴더를 루트 경로로 설정
            self.folder_model.setRootPath(folder_path)
            # 트리 뷰의 루트 인덱스를 선택된 폴더로 설정
            root_index = self.folder_model.index(folder_path)
            self.folder_tree.setRootIndex(root_index)
            
            # 설정에 모니터링 경로 추가
            paths = app_settings.get("monitor", "paths", [])
            if folder_path not in paths:
                paths.append(folder_path)
                app_settings.set("monitor", "paths", paths)
                
            # 성공 메시지 표시
            QMessageBox.information(
                self, 
                "폴더 추가 완료", 
                f"폴더가 모니터링 목록에 추가되었습니다: {folder_path}",
                QMessageBox.Ok
            )
    
    def refresh_folder_view(self):
        """폴더 뷰 새로고침"""
        current_path = self.folder_model.filePath(self.folder_tree.rootIndex())
        self.folder_model.setRootPath(current_path)
        
        # 파일 목록도 새로고침
        self.load_data()
        
        # 알림 표시
        QMessageBox.information(
            self, 
            "새로고침 완료", 
            "폴더 구조와 파일 목록이 새로고침 되었습니다.",
            QMessageBox.Ok
        )
    
    def on_folder_selected(self, index):
        """폴더 선택 시 호출"""
        selected_path = self.folder_model.filePath(index)
        # 선택된 폴더 관련 파일 목록 필터링
        self.filter_by_path(selected_path)
    
    def filter_by_path(self, path):
        """특정 경로의 파일만 표시"""
        for row in range(self.protected_table.rowCount()):
            file_path = self.protected_table.item(row, 1).text()
            hide_row = not file_path.startswith(path)
            self.protected_table.setRowHidden(row, hide_row)
            
        # 현재 표시된 항목 수 업데이트
        self.update_status_counts()
    
    def load_data(self):
        """데이터 로드 및 테이블 업데이트"""
        # 기존 항목 모두 삭제
        self.protected_table.setRowCount(0)
        
        # 함수 목록 가져오기
        functions = get_protected_functions()
        
        # 블록 목록 가져오기
        blocks = get_protected_blocks()
        
        # 변경 내역 가져오기
        changes = get_recent_changes(1000)  # 많은 수를 가져옴
        
        # 변경된 항목 관리
        changed_items = {}
        for change in changes:
            key = f"{change['file_path']}:{change['function_name']}"
            changed_items[key] = change
        
        # 테이블에 함수 추가
        row = 0
        for func in functions:
            self.protected_table.insertRow(row)
            
            # 유형 (함수)
            type_item = QTableWidgetItem("함수")
            icon = QIcon("D:\\CodeGuardian\\resources\\icons\\function.png")  # 적절한 아이콘 경로로 수정
            type_item.setIcon(icon)
            self.protected_table.setItem(row, 0, type_item)
            
            # 파일 경로
            file_item = QTableWidgetItem(func['file_path'])
            self.protected_table.setItem(row, 1, file_item)
            
            # 함수 이름
            name_item = QTableWidgetItem(func['function_name'])
            name_item.setFont(QFont("Consolas", 9))  # 코드에 적합한 폰트
            self.protected_table.setItem(row, 2, name_item)
            
            # 상태 (변경 여부)
            key = f"{func['file_path']}:{func['function_name']}"
            if key in changed_items:
                status_item = QTableWidgetItem("변경됨")
                status_item.setBackground(QBrush(QColor(255, 200, 200)))
                status_item.setForeground(QBrush(QColor(180, 0, 0)))
                status_item.setFont(QFont("Arial", 9, QFont.Bold))
                
                change_icon = QIcon("D:\\CodeGuardian\\resources\\icons\\changed.png")  # 적절한 아이콘 경로로 수정
                status_item.setIcon(change_icon)
            else:
                status_item = QTableWidgetItem("정상")
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
                status_item.setForeground(QBrush(QColor(0, 130, 0)))
                
                ok_icon = QIcon("D:\\CodeGuardian\\resources\\icons\\ok.png")  # 적절한 아이콘 경로로 수정
                status_item.setIcon(ok_icon)
            self.protected_table.setItem(row, 3, status_item)
            
            # 마지막 확인 시간
            from datetime import datetime
            last_check = datetime.fromtimestamp(func['last_verified']).strftime('%Y-%m-%d %H:%M:%S')
            time_item = QTableWidgetItem(last_check)
            self.protected_table.setItem(row, 4, time_item)
            
            row += 1
        
        # 테이블에 블록 추가
        for block in blocks:
            self.protected_table.insertRow(row)
            
            # 유형 (블록)
            type_item = QTableWidgetItem("블록")
            icon = QIcon("D:\\CodeGuardian\\resources\\icons\\code_block.png")  # 적절한 아이콘 경로로 수정
            type_item.setIcon(icon)
            self.protected_table.setItem(row, 0, type_item)
            
            # 파일 경로
            file_item = QTableWidgetItem(block['file_path'])
            self.protected_table.setItem(row, 1, file_item)
            
            # 블록 이름 (라인 범위)
            name = f"블록 {block['start_line']}-{block['end_line']}"
            name_item = QTableWidgetItem(name)
            name_item.setFont(QFont("Consolas", 9))  # 코드에 적합한 폰트
            self.protected_table.setItem(row, 2, name_item)
            
            # 상태 (변경 여부)
            key = f"{block['file_path']}:{name}"
            if key in changed_items:
                status_item = QTableWidgetItem("변경됨")
                status_item.setBackground(QBrush(QColor(255, 200, 200)))
                status_item.setForeground(QBrush(QColor(180, 0, 0)))
                status_item.setFont(QFont("Arial", 9, QFont.Bold))
                
                change_icon = QIcon("D:\\CodeGuardian\\resources\\icons\\changed.png")  # 적절한 아이콘 경로로 수정
                status_item.setIcon(change_icon)
            else:
                status_item = QTableWidgetItem("정상")
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
                status_item.setForeground(QBrush(QColor(0, 130, 0)))
                
                ok_icon = QIcon("D:\\CodeGuardian\\resources\\icons\\ok.png")  # 적절한 아이콘 경로로 수정
                status_item.setIcon(ok_icon)
            self.protected_table.setItem(row, 3, status_item)
            
            # 마지막 확인 시간
            from datetime import datetime
            last_check = datetime.fromtimestamp(block['last_verified']).strftime('%Y-%m-%d %H:%M:%S')
            time_item = QTableWidgetItem(last_check)
            self.protected_table.setItem(row, 4, time_item)
            
            row += 1
        
        # 첫 번째 행 선택 (자동)
        if self.protected_table.rowCount() > 0:
            self.protected_table.selectRow(0)
        
        # 필터 적용
        self.apply_filter()
        
        # 상태 정보 업데이트
        self.update_status_counts()
    
    def get_function_code(self, file_path, function_name):
        """파일에서 함수 코드 추출"""
        if not os.path.exists(file_path):
            # test_errors.py에서 샘플 함수 코드 제공
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            test_file = os.path.join(base_dir, "test_errors.py")
            
            if os.path.exists(test_file) and function_name in ["main", "process_data", "analyze_results", "calculate_average", "generate_report"]:
                file_path = test_file
            else:
                return f"// 파일을 찾을 수 없음: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            # 함수 찾기
            pattern = re.compile(r'def\s+' + re.escape(function_name) + r'\s*\(')
            function_start = None
            for i, line in enumerate(content):
                if pattern.search(line):
                    function_start = i
                    break
            
            if function_start is None:
                # 테스트 에러 파일에서 다시 시도
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                test_file = os.path.join(base_dir, "test_errors.py")
                
                if os.path.exists(test_file) and function_name in ["main", "process_data", "analyze_results", "calculate_average", "generate_report"]:
                    try:
                        with open(test_file, 'r', encoding='utf-8') as f:
                            content = f.readlines()
                        
                        for i, line in enumerate(content):
                            if pattern.search(line):
                                function_start = i
                                break
                    except:
                        pass
                
                if function_start is None:
                    return f"// 함수를 찾을 수 없음: {function_name}"
            
            # 함수 시작부터 끝까지 추출
            function_code = []
            indentation = len(content[function_start]) - len(content[function_start].lstrip())
            
            function_code.append(content[function_start])
            
            i = function_start + 1
            while i < len(content):
                line = content[i]
                if line.strip() == '' or line.strip().startswith('#'):
                    function_code.append(line)
                    i += 1
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indentation and line.strip():
                    break
                
                function_code.append(line)
                i += 1
            
            return ''.join(function_code)
        
        except Exception as e:
            # 샘플 함수 코드 제공 (테스트 에러 파일이 없을 경우)
            if function_name == "main":
                return """def main():
    \"\"\"메인 함수\"\"\"
    print("테스트 시작")
    try:
        process_data([1, 2, 3, 'four', 5])
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    
    try:
        calculate_average([])
    except Exception as e:
        print(f"에러 발생: {str(e)}")
    
    print("테스트 완료")"""
            elif function_name == "process_data":
                return """def process_data(data_list):
    \"\"\"데이터 처리\"\"\"
    result = []
    for item in data_list:
        # 의도적 에러 발생 (문자열에는 제곱 연산 불가)
        value = item ** 2
        result.append(value)
    
    analyze_results(result)
    return result"""
            elif function_name == "analyze_results":
                return """def analyze_results(data):
    \"\"\"결과 분석\"\"\"
    if not data:
        raise ValueError("데이터가 비어있습니다")
    
    total = sum(data)
    average = total / len(data)
    return {
        'total': total,
        'average': average,
        'min': min(data),
        'max': max(data)
    }"""
            elif function_name == "calculate_average":
                return """def calculate_average(numbers):
    \"\"\"평균 계산\"\"\"
    # 의도적 에러 발생 (빈 리스트인 경우 ZeroDivisionError)
    return sum(numbers) / len(numbers)"""
            elif function_name == "generate_report":
                return """def generate_report(data, filename):
    \"\"\"리포트 생성\"\"\"
    try:
        with open(filename, 'w') as f:
            f.write(f"Report\\n")
            f.write(f"------\\n")
            f.write(f"Total: {data['total']}\\n")
            f.write(f"Average: {data['average']}\\n")
            f.write(f"Minimum: {data['min']}\\n")
            f.write(f"Maximum: {data['max']}\\n")
        return True
    except Exception as e:
        print(f"리포트 생성 실패: {str(e)}")
        return False"""
            else:
                return f"// 코드 로드 오류: {str(e)}"
    
    def get_block_code(self, file_path, start_line, end_line):
        """파일에서 코드 블록 추출"""
        if not os.path.exists(file_path):
            return f"// 파일을 찾을 수 없음: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            # 인덱스 오류 방지
            start_line = max(0, start_line - 1)  # 0-기반 인덱스
            end_line = min(len(content), end_line)
            
            block_code = content[start_line:end_line]
            return ''.join(block_code)
        
        except Exception as e:
            return f"// 코드 로드 오류: {str(e)}"
    
    def add_sample_data(self):
        """샘플 데이터 추가 (실제 데이터가 없을 경우)"""
        from datetime import datetime, timedelta
        import time
        
        # 테스트 에러 파일 경로 - 실제 존재하는 파일로 설정
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        test_file = os.path.join(base_dir, "test_errors.py")
        
        # 현재 시간을 UNIX 타임스탬프로 변환
        now = time.time()
        yesterday = (datetime.now() - timedelta(days=1)).timestamp()
        
        # 실제 테스트 함수들
        if os.path.exists(test_file):
            # 테스트 파일에서 실제 함수 이름 추출
            functions = ["main", "process_data", "analyze_results", "calculate_average", "generate_report"]
            
            # 샘플 함수 데이터
            sample_functions = [
                {
                    "file_path": test_file,
                    "function_name": "main",
                    "last_verified": now
                },
                {
                    "file_path": test_file,
                    "function_name": "process_data",
                    "last_verified": now
                },
                {
                    "file_path": test_file,
                    "function_name": "analyze_results",
                    "last_verified": yesterday
                },
                {
                    "file_path": test_file,
                    "function_name": "calculate_average",
                    "last_verified": yesterday
                },
                {
                    "file_path": test_file,
                    "function_name": "generate_report",
                    "last_verified": now
                }
            ]
        else:
            # 기본 샘플 함수 데이터
            sample_functions = [
                {
                    "file_path": os.path.join(base_dir, "src", "storage", "storage_manager.py"),
                    "function_name": "get_protected_functions",
                    "last_verified": now
                },
                {
                    "file_path": os.path.join(base_dir, "src", "gui", "views", "code_monitor_view.py"),
                    "function_name": "show_details",
                    "last_verified": now
                },
                {
                    "file_path": os.path.join(base_dir, "src", "core", "settings.py"),
                    "function_name": "load",
                    "last_verified": yesterday
                }
            ]
        
        # 샘플 블록 데이터
        sample_blocks = [
            {
                "file_path": os.path.join(base_dir, "src", "gui", "widgets", "graph_widget.py"),
                "start_line": 25,
                "end_line": 45,
                "last_verified": now
            },
            {
                "file_path": os.path.join(base_dir, "src", "storage", "storage_manager.py"),
                "start_line": 100,
                "end_line": 120,
                "last_verified": yesterday
            }
        ]
        
        # 샘플 변경 내역
        sample_changes = [
            {
                "file_path": os.path.join(base_dir, "src", "storage", "storage_manager.py"),
                "function_name": "get_protected_functions",
                "change_type": "수정됨",
                "timestamp": yesterday,
                "diff": "- def get_protected_functions():\n+ def get_protected_functions(include_disabled=False):"
            }
        ]
        
        # 모니터링 시작
        from src.core.core import code_guardian
        if not code_guardian.is_monitoring:
            code_guardian.start_monitoring([test_file])
        
        # 테이블에 샘플 함수 추가
        row = 0
        for func in sample_functions:
            self.protected_table.insertRow(row)
            
            # 유형 (함수)
            type_item = QTableWidgetItem("함수")
            self.protected_table.setItem(row, 0, type_item)
            
            # 파일 경로
            file_item = QTableWidgetItem(func['file_path'])
            self.protected_table.setItem(row, 1, file_item)
            
            # 함수 이름
            name_item = QTableWidgetItem(func['function_name'])
            self.protected_table.setItem(row, 2, name_item)
            
            # 상태 (변경 여부)
            # 에러 발생 가능성 있는 함수는 "변경됨"으로 표시
            is_changed = func['function_name'] in ["process_data", "calculate_average"]
            if is_changed:
                status_item = QTableWidgetItem("변경됨")
                status_item.setBackground(QBrush(QColor(255, 200, 200)))
            else:
                status_item = QTableWidgetItem("정상")
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
            self.protected_table.setItem(row, 3, status_item)
            
            # 마지막 확인 시간
            last_check = datetime.fromtimestamp(func['last_verified']).strftime('%Y-%m-%d %H:%M:%S')
            time_item = QTableWidgetItem(last_check)
            self.protected_table.setItem(row, 4, time_item)
            
            row += 1
        
        # 테이블에 샘플 블록 추가
        for block in sample_blocks:
            self.protected_table.insertRow(row)
            
            # 유형 (블록)
            type_item = QTableWidgetItem("블록")
            self.protected_table.setItem(row, 0, type_item)
            
            # 파일 경로
            file_item = QTableWidgetItem(block['file_path'])
            self.protected_table.setItem(row, 1, file_item)
            
            # 블록 이름 (라인 범위)
            name = f"블록 {block['start_line']}-{block['end_line']}"
            name_item = QTableWidgetItem(name)
            self.protected_table.setItem(row, 2, name_item)
            
            # 상태 (변경 여부)
            status_item = QTableWidgetItem("정상")
            status_item.setBackground(QBrush(QColor(200, 255, 200)))
            self.protected_table.setItem(row, 3, status_item)
            
            # 마지막 확인 시간
            last_check = datetime.fromtimestamp(block['last_verified']).strftime('%Y-%m-%d %H:%M:%S')
            time_item = QTableWidgetItem(last_check)
            self.protected_table.setItem(row, 4, time_item)
            
            row += 1
        
        # 상태 정보 업데이트
        self.update_status_counts()
        
        # 첫 번째 행 자동 선택
        if self.protected_table.rowCount() > 0:
            self.protected_table.selectRow(0)
        
        # 첫 번째 행 선택 (자동)
        if self.protected_table.rowCount() > 0:
            self.protected_table.selectRow(0)
    
    def update_status_counts(self):
        """상태 정보 업데이트"""
        total_count = 0
        func_count = 0
        block_count = 0
        changed_count = 0
        
        for row in range(self.protected_table.rowCount()):
            if not self.protected_table.isRowHidden(row):
                total_count += 1
                
                if self.protected_table.item(row, 0).text() == "함수":
                    func_count += 1
                elif self.protected_table.item(row, 0).text() == "블록":
                    block_count += 1
                
                if self.protected_table.item(row, 3).text() == "변경됨":
                    changed_count += 1
        
        self.total_count.setText(f"총 항목: {total_count}")
        self.func_count.setText(f"함수: {func_count}")
        self.block_count.setText(f"블록: {block_count}")
        self.changed_count.setText(f"변경됨: {changed_count}")
    
    def apply_filter(self):
        """필터 적용"""
        filter_type = self.filter_combo.currentText()
        
        for row in range(self.protected_table.rowCount()):
            hide_row = False
            
            if filter_type == "함수만":
                if self.protected_table.item(row, 0).text() != "함수":
                    hide_row = True
            elif filter_type == "블록만":
                if self.protected_table.item(row, 0).text() != "블록":
                    hide_row = True
            elif filter_type == "변경된 항목만":
                if self.protected_table.item(row, 3).text() != "변경됨":
                    hide_row = True
            
            self.protected_table.setRowHidden(row, hide_row)
        
        # 상태 정보 업데이트
        self.update_status_counts()
    
    def show_details(self):
        """선택된 항목의 상세 정보 표시"""
        selected_rows = self.protected_table.selectedItems()
        if not selected_rows:
            return
        
        # 선택된 행 가져오기
        row = selected_rows[0].row()
        
        # 정보 가져오기
        type_text = self.protected_table.item(row, 0).text()
        file_path = self.protected_table.item(row, 1).text()
        name = self.protected_table.item(row, 2).text()
        status = self.protected_table.item(row, 3).text()
        
        # 코드 내용 표시
        if type_text == "함수":
            code = self.get_function_code(file_path, name)
            self.code_browser.setText(code)
        elif type_text == "블록":
            # 블록 이름에서 라인 번호 추출 ("블록 10-20" 형식)
            match = re.search(r'블록\s+(\d+)-(\d+)', name)
            if match:
                start_line = int(match.group(1))
                end_line = int(match.group(2))
                code = self.get_block_code(file_path, start_line, end_line)
                self.code_browser.setText(code)
            else:
                self.code_browser.setText(f"// 유효하지 않은 블록 형식: {name}")
        
        # 상세 정보 구성
        details = f"<h3>코드 모니터링 상세 정보</h3>"
        details += f"<p><b>유형:</b> {type_text}</p>"
        details += f"<p><b>파일:</b> {file_path}</p>"
        details += f"<p><b>이름:</b> {name}</p>"
        details += f"<p><b>상태:</b> <span style='color: {'red' if status == '변경됨' else 'green'};'>{status}</span></p>"
        
        # 변경 내역 가져오기
        if status == "변경됨":
            changes = get_recent_changes(10)
            key = f"{file_path}:{name}"
            
            for change in changes:
                from datetime import datetime
                change_key = f"{change['file_path']}:{change['function_name']}"
                if change_key == key:
                    details += "<h4>변경 내역</h4>"
                    details += f"<p><b>변경 시간:</b> {datetime.fromtimestamp(change['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}</p>"
                    details += f"<p><b>변경 유형:</b> {change['change_type']}</p>"
                    details += "<h4>Diff</h4>"
                    details += "<pre style='background-color: #f7f7f7; padding: 10px; border: 1px solid #ddd;'>"
                    
                    # 변경 내용을 색상으로 강조
                    diff_text = change.get('diff', '')
                    formatted_diff = ""
                    for line in diff_text.split('\n'):
                        if line.startswith('+'):
                            formatted_diff += f"<span style='color: green;'>{line}</span><br>"
                        elif line.startswith('-'):
                            formatted_diff += f"<span style='color: red;'>{line}</span><br>"
                        else:
                            formatted_diff += f"{line}<br>"
                    
                    details += formatted_diff
                    details += "</pre>"
                    break
            else:
                # 변경 내역이 없는 경우 (샘플 데이터 등)
                details += "<h4>변경 내역</h4>"
                details += "<p>상세 변경 내역을 찾을 수 없습니다.</p>"
                details += "<h4>Diff</h4>"
                details += "<pre style='background-color: #f7f7f7; padding: 10px; border: 1px solid #ddd;'>"
                details += "<span style='color: red;'>- 원본 코드</span><br>"
                details += "<span style='color: green;'>+ 변경된 코드</span><br>"
                details += "</pre>"
        
        # 상세 정보 표시 (HTML 형식)
        self.details_text.setHtml(details)
    
    def add_protection(self):
        """보호 추가 대화상자 표시"""
        QMessageBox.information(
            self, 
            "보호 추가", 
            "보호할 함수나 코드 블록을 선택하세요.\n"
            "이 기능은 아직 구현 중입니다.",
            QMessageBox.Ok
        )
    
    def on_code_changed(self, file_path, function_name, change_type):
        """코드 변경 이벤트 처리"""
        # 테이블 새로고침
        self.load_data()
        
        # 변경된 항목 자동 선택
        for row in range(self.protected_table.rowCount()):
            file_item = self.protected_table.item(row, 1)
            name_item = self.protected_table.item(row, 2)
            
            if (file_item and file_item.text() == file_path and 
                name_item and name_item.text() == function_name):
                self.protected_table.selectRow(row)
                break
