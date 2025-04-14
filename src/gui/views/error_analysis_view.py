"""
에러 분석 뷰
에러 정보를 분석하고 표시하는 뷰
"""

import sys
import os
import re
import traceback
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                            QSplitter, QTextEdit, QCheckBox, QComboBox, QMessageBox,
                            QGroupBox, QTreeWidget, QTreeWidgetItem, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from core.core import code_guardian

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

class ErrorAnalysisView(QWidget):
    """에러 분석 뷰 클래스"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.current_error_data = []
        
        # 테스트 파일 경로 설정
        self.error_test_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                           "tests", "error_test.py")
        
        # 테스트 파일 목록
        self.test_files = [
            self.error_test_file,
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "test_errors.py")
        ]
        
        # 지연 로딩 - 구성요소가 모두 초기화된 후 데이터 로딩
        QTimer.singleShot(500, self.delayed_loading)
    
    def delayed_loading(self):
        """지연 로딩 함수 - 컴포넌트 초기화 후 호출"""
        try:
            # 테스트 파일 목록 로드
            self.load_test_file_list()
            
            # 처음에는 첫 번째 파일 선택
            if self.file_combo.count() > 0:
                self.file_combo.setCurrentIndex(0)
            
            self.refresh_error_data()
            self.load_test_functions()
        except Exception as e:
            print(f"초기 데이터 로딩 중 오류: {str(e)}")
            traceback.print_exc()
    
    def init_ui(self):
        """UI 구성"""
        main_layout = QHBoxLayout()  # 전체 레이아웃을 수평으로 변경
        
        # 왼쪽 패널: 함수 목록과 코드 뷰어
        left_panel = QVBoxLayout()
        
        # 함수 트리 그룹
        func_group = QGroupBox("테스트 함수 목록")
        func_layout = QVBoxLayout()
        
        # 테스트 파일 선택 컬트롤 추가
        file_control = QHBoxLayout()
        file_label = QLabel("테스트 파일:")
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(180)
        
        # 파일 선택버튼 추가
        self.select_file_btn = QPushButton("파일 선택...")
        self.select_file_btn.clicked.connect(self.on_select_file_clicked)
        
        file_control.addWidget(file_label)
        file_control.addWidget(self.file_combo, 1)
        file_control.addWidget(self.select_file_btn)
        
        # 함수 트리 위젯
        self.function_tree = QTreeWidget()
        self.function_tree.setHeaderLabels(["함수 이름"])
        self.function_tree.setMinimumWidth(250)
        self.function_tree.itemClicked.connect(self.on_function_selected)
        
        # 레이아웃에 추가
        func_layout.addLayout(file_control)
        func_layout.addWidget(self.function_tree)
        func_group.setLayout(func_layout)
        
        # 파일 선택 변경 이벤트 연결
        self.file_combo.currentIndexChanged.connect(self.on_test_file_changed)
        
        # 코드 뷰어 그룹
        code_group = QGroupBox("함수 코드")
        code_layout = QVBoxLayout()
        
        # 코드 에디터
        self.code_editor = QTextEdit()
        self.code_editor.setReadOnly(True)
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setMinimumHeight(300)
        
        # 구문 강조 설정
        self.highlighter = PythonHighlighter(self.code_editor.document())
        
        code_layout.addWidget(self.code_editor)
        code_group.setLayout(code_layout)
        
        # 왼쪽 패널에 추가
        left_panel.addWidget(func_group)
        left_panel.addWidget(code_group)
        
        # 왼쪽 패널 위젯 생성
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMinimumWidth(350)
        
        # 오른쪽 패널: 에러 분석
        right_panel = QVBoxLayout()
        
        # 상단 컨트롤 패널
        control_panel = QHBoxLayout()
        
        # 함수명 필터
        function_label = QLabel("함수:")
        self.function_filter = QLineEdit()
        self.function_filter.setPlaceholderText("함수명으로 검색...")
        
        # 에러 유형 필터
        error_type_label = QLabel("에러 유형:")
        self.error_type_combo = QComboBox()
        self.error_type_combo.addItem("모든 에러", "")
        self.error_type_combo.addItem("ZeroDivisionError", "ZeroDivisionError")
        self.error_type_combo.addItem("IndexError", "IndexError")
        self.error_type_combo.addItem("TypeError", "TypeError")
        self.error_type_combo.addItem("SyntaxError", "SyntaxError")
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.on_refresh_btn_clicked)
        
        # 컨트롤 패널에 위젯 추가
        control_panel.addWidget(function_label)
        control_panel.addWidget(self.function_filter)
        control_panel.addWidget(error_type_label)
        control_panel.addWidget(self.error_type_combo)
        control_panel.addStretch(1)
        control_panel.addWidget(self.refresh_btn)
        
        # 에러 목록 테이블
        self.error_table = QTableWidget()
        self.error_table.setColumnCount(5)
        self.error_table.setHorizontalHeaderLabels(["함수", "에러 타입", "에러 메시지", "시간", "ID"])
        
        # 테이블 설정
        self.error_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.error_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.error_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.error_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.error_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # 선택 이벤트 연결
        self.error_table.itemSelectionChanged.connect(self.on_error_selected)
        
        # 에러 상세 정보 패널
        self.error_details = QTextEdit()
        self.error_details.setReadOnly(True)
        self.error_details.setMinimumHeight(200)
        
        # 옵션 패널
        option_panel = QHBoxLayout()
        
        # 스택 트레이스 표시 옵션
        self.show_stack_trace = QCheckBox("스택 트레이스 표시")
        self.show_stack_trace.setChecked(True)
        self.show_stack_trace.stateChanged.connect(self.update_error_details)
        
        # 컨텍스트 정보 표시 옵션
        self.show_context = QCheckBox("컨텍스트 정보 표시")
        self.show_context.setChecked(True)
        self.show_context.stateChanged.connect(self.update_error_details)
        
        # 자동 새로고침 옵션
        self.auto_refresh = QCheckBox("자동 새로고침")
        
        option_panel.addWidget(self.show_stack_trace)
        option_panel.addWidget(self.show_context)
        option_panel.addWidget(self.auto_refresh)
        option_panel.addStretch(1)
        
        # 스플리터로 테이블과 상세 정보 패널 분할
        splitter = QSplitter(Qt.Vertical)
        
        # 테이블 위젯을 담을 컨테이너
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.addWidget(self.error_table)
        table_container.setLayout(table_layout)
        
        # 상세 정보 위젯을 담을 컨테이너
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.addWidget(QLabel("에러 상세 정보:"))
        details_layout.addWidget(self.error_details)
        details_layout.addLayout(option_panel)
        details_container.setLayout(details_layout)
        
        # 스플리터에 위젯 추가
        splitter.addWidget(table_container)
        splitter.addWidget(details_container)
        splitter.setSizes([500, 200])
        
        # 오른쪽 패널에 추가
        right_panel.addLayout(control_panel)
        right_panel.addWidget(splitter)
        
        # 오른쪽 패널 위젯 생성
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        # 전체 레이아웃에 왼쪽과 오른쪽 패널 추가
        main_layout.addWidget(left_widget, 1)  # 1:2 비율로 설정
        main_layout.addWidget(right_widget, 2)
        
        self.setLayout(main_layout)
    
    def on_refresh_btn_clicked(self):
        """새로고침 버튼 클릭 이벤트 처리"""
        # 버튼 비활성화로 더블 클릭 방지
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("로딩 중...")
        
        # 실제 갱신 작업 수행
        try:
            self.refresh_error_data()
        except Exception as e:
            print(f"새로고침 중 오류: {str(e)}")
            self.error_details.setText(f"새로고침 중 오류 발생: {str(e)}")
            
            # 오류 알림
            QMessageBox.warning(self, "새로고침 오류", 
                               f"에러 데이터를 새로고침하는 중 문제가 발생했습니다:\n{str(e)}")
        
        # 버튼 복원
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("새로고침")
    
    def refresh_error_data(self):
        """에러 데이터 새로고침"""
        # 현재 필터 가져오기
        function_filter = self.function_filter.text()
        error_type_filter = self.error_type_combo.currentData()
        
        try:
            # 에러 데이터 가져오기
            error_data = []
            try:
                error_data = code_guardian.get_error_data(function_filter if function_filter else None)
            except Exception as e:
                print(f"에러 데이터 조회 실패: {str(e)}")
                traceback.print_exc()
                error_data = []  # 빈 리스트로 초기화
            
            # 에러 유형 필터링
            if error_type_filter and error_data:
                error_data = [err for err in error_data if err.get('error_type') == error_type_filter]
            
            self.update_error_table(error_data)
            
            # 현재 데이터 저장
            self.current_error_data = error_data
            
        except Exception as e:
            traceback.print_exc()
            self.error_table.setRowCount(0)
            self.error_details.setText(f"에러 데이터 로드 중 오류 발생: {str(e)}")
            self.current_error_data = []  # 빈 리스트로 초기화
    
    def update_error_table(self, error_data):
        """에러 테이블 업데이트
        
        Args:
            error_data: 에러 데이터 리스트
        """
        # 테이블 초기화
        self.error_table.setRowCount(0)
        
        if not error_data:
            # 데이터가 없으면 메시지 표시
            self.error_details.setText("에러 데이터가 없습니다. 먼저 테스트를 실행하거나 모니터링을 시작하세요.")
            return
        
        # 데이터 추가
        for row, error in enumerate(error_data):
            self.error_table.insertRow(row)
            
            # 함수명
            function_name = error.get('function_name', 'Unknown')
            self.error_table.setItem(row, 0, QTableWidgetItem(function_name))
            
            # 에러 유형
            error_type = error.get('error_type', 'Unknown')
            type_item = QTableWidgetItem(error_type)
            if error_type == 'ZeroDivisionError':
                type_item.setBackground(Qt.red)
                type_item.setForeground(Qt.white)
            elif error_type == 'IndexError':
                type_item.setBackground(Qt.yellow)
            elif error_type == 'TypeError':
                type_item.setBackground(Qt.blue)
                type_item.setForeground(Qt.white)
            self.error_table.setItem(row, 1, type_item)
            
            # 에러 메시지
            error_message = error.get('error_message', 'No message')
            self.error_table.setItem(row, 2, QTableWidgetItem(error_message))
            
            # 시간
            timestamp = error.get('timestamp', '')
            self.error_table.setItem(row, 3, QTableWidgetItem(timestamp))
            
            # ID
            error_id = str(error.get('id', ''))
            id_item = QTableWidgetItem(error_id)
            id_item.setTextAlignment(Qt.AlignCenter)
            self.error_table.setItem(row, 4, id_item)
            
            # 데이터 저장 (사용자 데이터)
            for col in range(5):
                item = self.error_table.item(row, col)
                if item:  # None 체크 추가
                    item.setData(Qt.UserRole, row)
        
        # 자동으로 첫 번째 행 선택
        if self.error_table.rowCount() > 0:
            self.error_table.selectRow(0)
    
    def on_error_selected(self):
        """에러 항목 선택 시 호출"""
        selected_items = self.error_table.selectedItems()
        if not selected_items:
            self.error_details.setText("선택된 에러가 없습니다")
            return
        
        # 선택된 에러의 인덱스 가져오기
        row_index = selected_items[0].data(Qt.UserRole)
        if row_index is None:
            return
            
        if row_index < len(self.current_error_data):
            error = self.current_error_data[row_index]
            self.update_error_details(error)
            
            # 해당 함수의 코드도 표시
            function_name = error.get('function_name', '')
            if function_name:
                self.show_function_code(function_name)
    
    def load_test_file_list(self):
        """테스트 파일 로드"""
        try:
            # 파일 목록 저장
            self.file_combo.clear()
            
            for file_path in self.test_files:
                if os.path.exists(file_path):
                    self.file_combo.addItem(os.path.basename(file_path), file_path)
            
            # 파일이 없을 경우 "(No files)" 항목 추가
            if self.file_combo.count() == 0:
                self.file_combo.addItem("(파일 없음)", None)
                print("Debug: No test files found")
            else:
                print(f"Debug: Loaded {self.file_combo.count()} test files")
                # 첫 번째 파일을 기본값으로 설정
                self.error_test_file = self.file_combo.itemData(0)
                print(f"Debug: Set default test file to: {self.error_test_file}")
                
        except Exception as e:
            print(f"Debug: Error loading test files: {str(e)}")
            traceback.print_exc()
            
    def on_select_file_clicked(self):
        """파일 선택 버튼 클릭 처리"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "테스트 파일 선택", "", "Python 파일 (*.py)"
        )
        
        if file_path:
            print(f"Debug: Selected file: {file_path}")
            
            # 이미 목록에 있는지 확인
            for i in range(self.file_combo.count()):
                if self.file_combo.itemData(i) == file_path:
                    self.file_combo.setCurrentIndex(i)
                    return
            
            # 새 파일 추가
            self.file_combo.addItem(os.path.basename(file_path), file_path)
            self.file_combo.setCurrentIndex(self.file_combo.count() - 1)
            
            # 파일 목록에 추가
            if file_path not in self.test_files:
                self.test_files.append(file_path)
    
    def on_test_file_changed(self, index):
        """테스트 파일 변경 처리"""
        if index < 0:
            return
            
        # 현재 선택된 파일 데이터 가져오기
        current_data = self.file_combo.itemData(index)
        
        # None 값 처리
        if current_data is None:
            print(f"Debug: No file data for index {index}")
            return
            
        self.error_test_file = current_data
        print(f"Debug: Changed test file to: {self.error_test_file}")
        
        # 함수 목록 다시 로드
        self.load_test_functions()
        
        # 오류 데이터 새로고침
        self.refresh_error_data()
    
    def load_test_functions(self):
        """테스트 함수 목록 로드"""
        try:
            # 트리 초기화
            self.function_tree.clear()
            
            if self.error_test_file is None:
                # 파일이 선택되지 않은 경우
                item = QTreeWidgetItem(["파일을 선택하세요"])
                self.function_tree.addTopLevelItem(item)
                return
            
            if not os.path.exists(self.error_test_file):
                # 파일이 없을 경우 메시지 표시
                item = QTreeWidgetItem(["테스트 파일을 찾을 수 없습니다"])
                self.function_tree.addTopLevelItem(item)
                return
            
            # 파일에서 함수 정의 추출
            with open(self.error_test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 함수 정의 찾기 (정규식)
            function_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]*)\):', re.MULTILINE)
            matches = function_pattern.finditer(content)
            
            # 루트 노드 추가
            file_name = os.path.basename(self.error_test_file)
            root_item = QTreeWidgetItem([file_name])
            self.function_tree.addTopLevelItem(root_item)
            
            # 각 함수를 트리에 추가
            for match in matches:
                func_name = match.group(1)
                func_item = QTreeWidgetItem([func_name])
                # 함수 코드 시작 위치 저장
                func_item.setData(0, Qt.UserRole, match.start())
                root_item.addChild(func_item)
            
            # 트리 확장
            root_item.setExpanded(True)
            
            # 함수를 찾지 못했을 경우
            if root_item.childCount() == 0:
                func_item = QTreeWidgetItem(["함수를 찾을 수 없습니다"])
                root_item.addChild(func_item)
            
        except Exception as e:
            # 에러 발생 시 처리
            print(f"함수 목록 로드 중 오류: {str(e)}")
            traceback.print_exc()
            
            item = QTreeWidgetItem([f"오류: {str(e)}"])
            self.function_tree.addTopLevelItem(item)
    
    def on_function_selected(self, item, column):
        """함수 선택 시 코드 표시"""
        # 선택한 항목이 함수인지 확인
        if not item.parent():  # 루트 노드(파일)인 경우
            return
        
        # 함수 위치 가져오기 (저장된 데이터)
        func_pos = item.data(0, Qt.UserRole)
        if func_pos is None:
            self.code_editor.setText("함수 정보를 찾을 수 없습니다")
            return
        
        # 함수 코드 추출
        func_name = item.text(0)
        self.show_function_code(func_name, func_pos)
        
        # 에러 데이터에서 해당 함수 관련 에러만 필터링
        self.function_filter.setText(func_name)
        self.refresh_error_data()
    
    def show_function_code(self, func_name, func_pos=None):
        """함수 코드 표시
        
        Args:
            func_name: 함수 이름
            func_pos: 함수 시작 위치 (없으면 이름으로 검색)
        """
        try:
            if self.error_test_file is None:
                self.code_editor.setText("파일이 선택되지 않았습니다. 파일을 먼저 선택하세요.")
                return
                
            if not os.path.exists(self.error_test_file):
                self.code_editor.setText(f"테스트 파일을 찾을 수 없습니다: {self.error_test_file}")
                return
            
            with open(self.error_test_file, 'r', encoding='utf-8') as f:
                content = f.readlines()
                
            # 함수 찾기
            if func_pos is None:
                # 위치가 주어지지 않은 경우 함수 이름으로 검색
                pattern = re.compile(r'def\s+' + re.escape(func_name) + r'\s*\(')
                func_start = None
                for i, line in enumerate(content):
                    if pattern.search(line):
                        func_start = i
                        break
                
                if func_start is None:
                    self.code_editor.setText(f"함수를 찾을 수 없음: {func_name}")
                    return
            else:
                # 위치가 주어진 경우 해당 위치의 행 찾기
                func_start = 0
                pos = 0
                for i, line in enumerate(content):
                    if pos + len(line) > func_pos:
                        func_start = i
                        break
                    pos += len(line)
            
            # 함수 코드 추출
            func_code = []
            indentation = len(content[func_start]) - len(content[func_start].lstrip())
            func_code.append(content[func_start])
            
            i = func_start + 1
            while i < len(content):
                line = content[i]
                if line.strip() == '' or line.strip().startswith('#'):
                    func_code.append(line)
                    i += 1
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= indentation and line.strip():
                    break
                
                func_code.append(line)
                i += 1
            
            # 코드 에디터에 표시
            self.code_editor.setText(''.join(func_code))
            
        except Exception as e:
            print(f"함수 코드 표시 중 오류: {str(e)}")
            traceback.print_exc()
            self.code_editor.setText(f"코드 로딩 오류: {str(e)}")
    
    def update_error_details(self, error=None):
        """에러 상세 정보 업데이트
        
        Args:
            error: 에러 데이터 (None이면 현재 선택된 에러 사용)
        """
        if error is None:
            # 체크박스 상태 변경 시 현재 선택된 에러 정보 업데이트
            selected_items = self.error_table.selectedItems()
            if not selected_items:
                return
            
            row_index = selected_items[0].data(Qt.UserRole)
            if row_index is None or row_index >= len(self.current_error_data):
                return
                
            error = self.current_error_data[row_index]
        
        # 상세 정보 구성
        details = f"<h3>에러 정보</h3>"
        details += f"<p><b>함수:</b> {error.get('function_name', 'Unknown')}</p>"
        details += f"<p><b>에러 유형:</b> {error.get('error_type', 'Unknown')}</p>"
        details += f"<p><b>에러 메시지:</b> {error.get('error_message', 'No message')}</p>"
        details += f"<p><b>시간:</b> {error.get('timestamp', '')}</p>"
        
        # 함수 코드 링크 추가
        function_name = error.get('function_name', '')
        if function_name:
            details += f"<p><button onclick='showCode(\"{function_name}\")'>함수 코드 보기</button></p>"
        
        # 스택 트레이스 추가 (옵션에 따라)
        if self.show_stack_trace.isChecked() and 'stack_trace' in error:
            details += f"<h3>스택 트레이스</h3>"
            details += f"<pre>{error['stack_trace']}</pre>"
        
        # 컨텍스트 정보 추가 (옵션에 따라)
        if self.show_context.isChecked() and 'context' in error:
            details += f"<h3>컨텍스트 정보</h3>"
            details += f"<pre>{error['context']}</pre>"
        
        # HTML로 설정
        self.error_details.setHtml(details)
        
        # 에러와 관련된 함수가 있으면 트리에서 자동 선택
        if function_name:
            self.select_function_in_tree(function_name)
    
    def select_function_in_tree(self, function_name):
        """트리에서 함수 선택"""
        # 루트 노드 가져오기
        if self.function_tree.topLevelItemCount() == 0:
            return
            
        root_item = self.function_tree.topLevelItem(0)
        
        # 모든 함수 아이템 확인
        for i in range(root_item.childCount()):
            func_item = root_item.child(i)
            if func_item.text(0) == function_name:
                # 함수 선택
                self.function_tree.setCurrentItem(func_item)
                
                # 함수 코드 표시
                func_pos = func_item.data(0, Qt.UserRole)
                self.show_function_code(function_name, func_pos)
                return