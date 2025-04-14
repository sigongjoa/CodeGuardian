"""
호출 그래프 뷰
함수 호출 관계를 그래프로 시각화하는 뷰
"""

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QSlider, QComboBox, QCheckBox, QFileDialog,
                            QSplitter, QScrollArea, QFrame, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont, QColor, QTextCharFormat, QSyntaxHighlighter
import re

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from core.core import code_guardian
from visualizer.graph_visualizer import graph_visualizer
from src.gui.widgets.graph_widget import GraphWidget

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

class GraphGeneratorThread(QThread):
    """그래프 생성 작업을 위한 스레드 클래스"""
    
    finished = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.function_name = None
        self.depth = 2
        self.layout = 'spring'
    
    def set_params(self, function_name, depth, layout):
        """파라미터 설정
        
        Args:
            function_name: 시작 함수명
            depth: 호출 깊이
            layout: 레이아웃 유형
        """
        self.function_name = function_name
        self.depth = depth
        self.layout = layout
    
    def run(self):
        """스레드 실행"""
        try:
            # 1. 먼저 그래프 데이터 가져오기
            graph_data = code_guardian.get_call_graph(self.function_name, self.depth)
            
            # 2. 그래프 시각화 객체에 그래프 설정
            graph_visualizer.create_call_graph(self.function_name, self.depth)
            
            # 3. D3.js용 그래프 데이터 변환
            nodes = []
            links = []
            
            if graph_data and "nodes" in graph_data and "edges" in graph_data:
                # 노드 변환
                for node in graph_data["nodes"]:
                    nodes.append({
                        "id": node.get("id", "unknown"),
                        "group": node.get("group", "default"),
                        "size": node.get("size", 5),
                        "changed": node.get("changed", False),
                        "label": node.get("label", node.get("id", "unknown"))
                    })
                
                # 링크 변환
                for edge in graph_data["edges"]:
                    links.append({
                        "source": edge.get("source", ""),
                        "target": edge.get("target", ""),
                        "value": edge.get("value", 1)
                    })
            
            # 4. 구조화된 데이터 반환
            d3_graph_data = {
                "nodes": nodes,
                "links": links
            }
            
            # 5. 이미지 파일 경로 생성 (기존 코드와의 호환성 유지)
            image_path = graph_visualizer.visualize_graph(layout=self.layout)
            
            self.finished.emit({
                "success": True, 
                "image_path": image_path, 
                "graph_data": graph_data,
                "d3_graph_data": d3_graph_data
            })
        
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            print(f"그래프 생성 중 오류: {error_msg}")
            print(error_trace)
            
            self.finished.emit({
                "success": False, 
                "error": error_msg,
                "trace": error_trace
            })


class CallGraphView(QWidget):
    """호출 그래프 뷰 클래스"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.selected_node = None
        
        # 그래프 생성 스레드
        self.graph_thread = GraphGeneratorThread()
        self.graph_thread.finished.connect(self.on_graph_generated)
        
        # 이벤트 연결
        self.function_combo.currentIndexChanged.connect(self.on_function_selected)
        
        # 샘플 그래프 표시
        self.show_sample_graph()
    
    def init_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        
        # 상단 컨트롤 패널
        control_panel = QHBoxLayout()
        
        # 함수 선택 드롭박스 추가
        function_label = QLabel("함수:")
        self.function_combo = QComboBox()
        self.function_combo.setEditable(True)
        self.function_combo.setMinimumWidth(200)
        
        # 기존 입력 필드 유지 (호환성)
        self.function_input = self.function_combo.lineEdit()
        self.function_input.setPlaceholderText("함수명 입력 또는 선택...")
        
        # 호출 깊이 선택
        depth_label = QLabel("호출 깊이:")
        self.depth_value = QLabel("2")
        self.depth_slider = QSlider(Qt.Horizontal)
        self.depth_slider.setRange(1, 5)
        self.depth_slider.setValue(2)
        self.depth_slider.valueChanged.connect(lambda v: self.depth_value.setText(str(v)))
        
        # 레이아웃 선택
        layout_label = QLabel("레이아웃:")
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["spring", "circular", "shell", "random"])
        
        # 그래프 생성 버튼
        self.generate_btn = QPushButton("그래프 생성")
        self.generate_btn.clicked.connect(self.generate_graph)
        
        # 컨트롤 패널에 위젯 추가
        control_panel.addWidget(function_label)
        control_panel.addWidget(self.function_combo)
        control_panel.addWidget(depth_label)
        control_panel.addWidget(self.depth_slider)
        control_panel.addWidget(self.depth_value)
        control_panel.addWidget(layout_label)
        control_panel.addWidget(self.layout_combo)
        control_panel.addWidget(self.generate_btn)
        
        # 그래프 상세 정보 패널
        info_panel = QHBoxLayout()
        
        self.node_count = QLabel("노드: 0")
        self.edge_count = QLabel("엣지: 0")
        self.error_count = QLabel("에러 함수: 0")
        
        info_panel.addWidget(self.node_count)
        info_panel.addWidget(self.edge_count)
        info_panel.addWidget(self.error_count)
        info_panel.addStretch(1)
        
        # 중앙 영역 스플리터 (수평 분할)
        central_splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 그래프 위젯
        self.graph_widget = GraphWidget()
        self.graph_widget.node_selected.connect(self.on_node_selected)
        
        # 그래프가 없을 때 표시할 메시지 프레임
        self.empty_frame = QFrame()
        self.empty_frame.setFrameShape(QFrame.StyledPanel)
        self.empty_frame.setFrameShadow(QFrame.Sunken)
        empty_layout = QVBoxLayout()
        
        self.empty_message = QLabel("함수명을 입력하고 '그래프 생성' 버튼을 클릭하세요")
        self.empty_message.setAlignment(Qt.AlignCenter)
        self.empty_message.setStyleSheet("font-size: 14px; color: #666;")
        
        # 안내 메시지 추가
        guide_message = QLabel(
            "함수 호출 그래프는 코드의 함수 간 호출 관계를 시각적으로 보여줍니다.\n"
            "그래프를 통해 코드 구조를 파악하고 에러가 발생하는 경로를 추적할 수 있습니다.\n\n"
            "1. 분석할 함수명을 입력하세요\n"
            "2. 호출 깊이를 선택하세요 (깊이가 클수록 더 많은 함수를 표시)\n"
            "3. 원하는 레이아웃을 선택하세요\n"
            "4. '그래프 생성' 버튼을 클릭하세요"
        )
        guide_message.setAlignment(Qt.AlignCenter)
        guide_message.setWordWrap(True)
        guide_message.setStyleSheet("font-size: 12px; color: #666; padding: 20px;")
        
        # 추천 함수 목록
        recommended_label = QLabel("추천 함수 목록:")
        recommended_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        
        recommended_functions = QHBoxLayout()
        for func in ["main", "process_data", "analyze_results", "calculate_average", "generate_report"]:
            func_btn = QPushButton(func)
            func_btn.setStyleSheet("padding: 5px 10px;")
            func_btn.clicked.connect(lambda checked, f=func: self.function_input.setText(f))
            recommended_functions.addWidget(func_btn)
        
        # 빈 그래프 프레임에 위젯 추가
        empty_layout.addStretch(1)
        empty_layout.addWidget(self.empty_message)
        empty_layout.addWidget(guide_message)
        empty_layout.addSpacing(20)
        empty_layout.addWidget(recommended_label, 0, Qt.AlignCenter)
        empty_layout.addLayout(recommended_functions)
        empty_layout.addStretch(1)
        
        self.empty_frame.setLayout(empty_layout)
        
        # 그래프 스택 레이아웃 (빈 프레임과 그래프 위젯을 전환)
        graph_stack = QVBoxLayout()
        graph_stack.addWidget(self.empty_frame)
        graph_stack.addWidget(self.graph_widget)
        
        # 기본적으로는 빈 프레임만 표시
        self.graph_widget.setVisible(False)
        
        # 왼쪽 패널 위젯 생성
        left_widget = QWidget()
        left_widget.setLayout(graph_stack)
        
        # 오른쪽: 함수 코드 뷰어
        right_panel = QVBoxLayout()
        
        # 선택된 함수 정보
        self.selected_func_label = QLabel("선택된 함수: 없음")
        self.selected_func_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_panel.addWidget(self.selected_func_label)
        
        # 코드 뷰어
        self.code_editor = QTextEdit()
        self.code_editor.setReadOnly(True)
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setMinimumWidth(400)
        
        # 구문 강조 설정
        self.highlighter = PythonHighlighter(self.code_editor.document())
        
        right_panel.addWidget(self.code_editor)
        
        # 함수 정보 표시 영역
        info_group = QFrame()
        info_group.setFrameShape(QFrame.StyledPanel)
        info_group.setStyleSheet("background-color: #f7f7f7; border: 1px solid #ddd; border-radius: 5px;")
        
        info_layout = QVBoxLayout()
        
        self.func_info_label = QLabel("함수 정보")
        self.func_info_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        info_layout.addWidget(self.func_info_label)
        
        # 함수 세부 정보
        self.func_details = QLabel("")
        self.func_details.setWordWrap(True)
        info_layout.addWidget(self.func_details)
        
        info_group.setLayout(info_layout)
        right_panel.addWidget(info_group)
        
        # 오른쪽 패널 위젯 생성
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        # 스플리터에 위젯 추가
        central_splitter.addWidget(left_widget)
        central_splitter.addWidget(right_widget)
        central_splitter.setSizes([600, 400])  # 좌우 크기 비율 설정
        
        # 기존 그래프 이미지 표시 영역 (호환성 유지)
        self.graph_scroll = QScrollArea()
        self.graph_scroll.setWidgetResizable(True)
        self.graph_scroll.setVisible(False)  # 숨김 처리
        
        self.graph_label = QLabel("함수명을 입력하고 '그래프 생성' 버튼을 클릭하세요")
        self.graph_label.setAlignment(Qt.AlignCenter)
        self.graph_label.setStyleSheet("background-color: white;")
        
        self.graph_scroll.setWidget(self.graph_label)
        
        # 옵션 패널
        option_panel = QHBoxLayout()
        
        # 에러 함수 강조 옵션
        self.highlight_errors = QCheckBox("에러 함수 강조")
        self.highlight_errors.setChecked(True)
        
        # 모듈 정보 표시 옵션
        self.show_modules = QCheckBox("모듈 정보 표시")
        
        # 이미지 저장 버튼
        self.save_image_btn = QPushButton("이미지 저장")
        self.save_image_btn.clicked.connect(self.save_graph_image)
        
        # JSON 내보내기 버튼
        self.export_json_btn = QPushButton("JSON 내보내기")
        self.export_json_btn.clicked.connect(self.export_graph_json)
        
        option_panel.addWidget(self.highlight_errors)
        option_panel.addWidget(self.show_modules)
        option_panel.addStretch(1)
        option_panel.addWidget(self.save_image_btn)
        option_panel.addWidget(self.export_json_btn)
        
        # 메인 레이아웃에 추가
        main_layout.addLayout(control_panel)
        main_layout.addLayout(info_panel)
        main_layout.addWidget(central_splitter)
        main_layout.addWidget(self.graph_scroll)  # 숨겨졌지만 호환성을 위해 유지
        main_layout.addLayout(option_panel)
        
        self.setLayout(main_layout)
        
        # 샘플 데이터로 UI 초기화
        self.function_input.setText("main")
        
        # 함수 목록 로드
        self.load_function_list()
    
    def load_function_list(self):
        """available functions list"""
        try:
            # test_errors.py 파일의 함수들 추출
            # 테스트 코드 파일 경로
            file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))), "test_errors.py")
            
            print(f"Debug: Loading functions from {file_path}")
            
            if not os.path.exists(file_path):
                self.function_combo.addItem("main")
                self.function_combo.addItem("process_data")
                self.function_combo.addItem("calculate_average")
                print(f"Debug: File not found, adding sample functions")
                return
            
            # 파일에서 함수 정의 추출
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 함수 정의 찾기 (정규식)
            function_pattern = re.compile(r'def\s+(\w+)\s*\(([^)]*)\):', re.MULTILINE)
            matches = function_pattern.finditer(content)
            
            # 결과 추가
            function_list = []
            for match in matches:
                func_name = match.group(1)
                function_list.append(func_name)
            
            # 드롭박스에 함수 목록 추가
            if function_list:
                self.function_combo.clear()
                for func in function_list:
                    self.function_combo.addItem(func)
                print(f"Debug: Added {len(function_list)} functions to dropdown")
            else:
                # 함수를 찾지 못한 경우 샘플 함수 추가
                self.function_combo.addItem("main")
                self.function_combo.addItem("process_data")
                self.function_combo.addItem("calculate_average")
                print(f"Debug: No functions found, adding sample functions")
                
        except Exception as e:
            print(f"Debug: Error loading functions: {str(e)}")
            # 샘플 함수 추가
            self.function_combo.addItem("main")
            self.function_combo.addItem("process_data")
            self.function_combo.addItem("calculate_average")
    
    def get_function_code(self, func_name):
        """함수의 소스 코드 가져오기"""
        # 테스트 코드 파일 경로
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))), "test_errors.py")
        
        if not os.path.exists(file_path):
            return "// 함수 코드를 찾을 수 없습니다."
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            
            # 함수 찾기
            pattern = re.compile(r'def\s+' + re.escape(func_name) + r'\s*\(')
            function_start = None
            for i, line in enumerate(content):
                if pattern.search(line):
                    function_start = i
                    break
            
            if function_start is None:
                return f"// 함수를 찾을 수 없음: {func_name}"
            
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
            return f"// 코드 로드 오류: {str(e)}"
    
    def show_sample_graph(self):
        """샘플 그래프 표시"""
        # 샘플 그래프 데이터 생성
        sample_data = {
            "nodes": [
                {"id": "main", "group": "main", "size": 8, "label": "main()"},
                {"id": "process_data", "group": "core", "size": 6, "label": "process_data()"},
                {"id": "analyze_results", "group": "analysis", "size": 5, "label": "analyze_results()"},
                {"id": "calculate_average", "group": "error", "size": 4, "label": "calculate_average()"},
                {"id": "generate_report", "group": "io", "size": 5, "label": "generate_report()"}
            ],
            "links": [
                {"source": "main", "target": "process_data", "value": 2},
                {"source": "process_data", "target": "analyze_results", "value": 1},
                {"source": "main", "target": "calculate_average", "value": 1},
                {"source": "analyze_results", "target": "generate_report", "value": 1}
            ]
        }
        
        # 노드 수와 엣지 수 업데이트
        self.node_count.setText(f"노드: {len(sample_data['nodes'])}")
        self.edge_count.setText(f"엣지: {len(sample_data['links'])}")
        self.error_count.setText(f"에러 함수: 1")
        
        # 빈 프레임 숨기고 그래프 표시
        self.empty_frame.setVisible(False)
        self.graph_widget.setVisible(True)
        
        # 그래프 위젯에 샘플 데이터 설정
        self.graph_widget.set_graph_data(sample_data)
        
        # main 함수 코드 표시
        self.selected_node = "main"
        code = self.get_function_code("main")
        self.selected_func_label.setText("선택된 함수: main()")
        self.code_editor.setText(code)
        
        # 함수 정보 표시
        self.func_details.setText(
            "<b>모듈:</b> test_errors.py<br>"
            "<b>유형:</b> 일반 함수<br>"
            "<b>에러:</b> 없음<br>"
            "<b>호출하는 함수:</b> process_data(), calculate_average()<br>"
            "<b>호출 받는 함수:</b> 없음"
        )
    
    def generate_graph(self):
        """그래프 생성"""
        function_name = self.function_input.text()
        depth = self.depth_slider.value()
        layout = self.layout_combo.currentText()
        
        if not function_name:
            self.graph_label.setText("함수명을 입력해주세요")
            return
        
        # 로딩 메시지 표시
        self.empty_message.setText(f"그래프 생성 중... 함수: {function_name}, 깊이: {depth}")
        self.empty_frame.setVisible(True)
        self.graph_widget.setVisible(False)
        
        # 버튼 비활성화
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("생성 중...")
        
        # 스레드에서 그래프 생성
        self.graph_thread.set_params(function_name, depth, layout)
        self.graph_thread.start()
    
    def on_graph_generated(self, result):
        """그래프 생성 완료 시 호출
        
        Args:
            result: 생성 결과 데이터
        """
        # 버튼 활성화
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("그래프 생성")
        
        if not result.get("success", False):
            # 에러 발생 시
            error_msg = result.get("error", "Unknown error")
            self.empty_message.setText(f"그래프 생성 실패: {error_msg}")
            self.empty_frame.setVisible(True)
            self.graph_widget.setVisible(False)
            return
        
        # 그래프 정보 업데이트
        graph_data = result.get("graph_data", {})
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        self.node_count.setText(f"노드: {len(nodes)}")
        self.edge_count.setText(f"엣지: {len(edges)}")
        
        # 에러 노드 수 계산 (실제로는 에러 노드를 파악하는 더 정교한 방법이 필요)
        error_count = 0
        if graph_visualizer.graph:
            error_nodes = graph_visualizer._get_error_nodes() if hasattr(graph_visualizer, '_get_error_nodes') else []
            error_count = sum(1 for node in graph_visualizer.graph.nodes() if node in error_nodes)
            
        self.error_count.setText(f"에러 함수: {error_count}")
        
        # D3.js 그래프 위젯에 데이터 전달
        d3_graph_data = result.get("d3_graph_data", {"nodes": [], "links": []})
        
        # 그래프 표시
        self.empty_frame.setVisible(False)
        self.graph_widget.setVisible(True)
        self.graph_widget.set_graph_data(d3_graph_data)
        
        # 선택된 함수의 코드 표시
        function_name = self.function_input.text()
        self.select_function(function_name)
        
        # 이미지 파일 경로 (기존 코드와 호환성 유지)
        image_path = result.get("image_path")
        
        if image_path and os.path.exists(image_path):
            # 이미지 로드 (호환성 유지)
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.graph_label.setPixmap(pixmap)
                self.graph_label.setAlignment(Qt.AlignCenter)
    
    def select_function(self, func_name):
        """함수 선택하여 코드 표시"""
        self.selected_node = func_name
        
        # 선택된 함수 레이블 업데이트
        self.selected_func_label.setText(f"선택된 함수: {func_name}()")
        
        # 코드 표시
        code = self.get_function_code(func_name)
        self.code_editor.setText(code)
        
        # 함수 정보 표시
        # 샘플 데이터에서 노드와 에지 관계 찾기
        incoming_edges = []
        outgoing_edges = []
        
        # 그래프 데이터에서 관계 찾기
        graph_data = code_guardian.get_call_graph(func_name, 2)
        if graph_data and "edges" in graph_data:
            for edge in graph_data["edges"]:
                if edge["source"] == func_name:
                    outgoing_edges.append(edge["target"])
                if edge["target"] == func_name:
                    incoming_edges.append(edge["source"])
        
        # 에러 함수 여부
        error_nodes = code_guardian.get_error_data()
        is_error = False
        error_type = ""
        for error in error_nodes:
            if error["function_name"] == func_name:
                is_error = True
                error_type = error["error_type"]
                break
        
        # 정보 텍스트 구성
        info_text = (
            f"<b>모듈:</b> test_errors.py<br>"
            f"<b>유형:</b> {'에러 발생 함수' if is_error else '일반 함수'}<br>"
        )
        
        if is_error:
            info_text += f"<b>에러 유형:</b> <span style='color: red;'>{error_type}</span><br>"
        
        if outgoing_edges:
            info_text += f"<b>호출하는 함수:</b> {', '.join([f'{e}()' for e in outgoing_edges])}<br>"
        else:
            info_text += "<b>호출하는 함수:</b> 없음<br>"
        
        if incoming_edges:
            info_text += f"<b>호출 받는 함수:</b> {', '.join([f'{e}()' for e in incoming_edges])}<br>"
        else:
            info_text += "<b>호출 받는 함수:</b> 없음<br>"
        
        self.func_details.setText(info_text)
    
    def on_function_selected(self, index):
        """드롭박스에서 함수 선택 시 처리"""
        if index < 0:  # 유효하지 않은 인덱스
            return
            
        selected_function = self.function_combo.currentText()
        print(f"Debug: Selected function from dropdown: {selected_function}")
        
        # 선택된 함수 코드 표시
        code = self.get_function_code(selected_function)
        self.code_editor.setText(code)
        
        # 필요하다면 그래프 자동 생성
        # 여기서는 사용자가 그래프 생성 버튼을 명시적으로 누르도록 함
    
    def on_node_selected(self, node_id):
        """노드 선택 이벤트 처리"""
        # 선택된 노드 정보 표시
        self.select_function(node_id)
    
    def save_graph_image(self):
        """그래프 이미지 저장"""
        if not graph_visualizer.graph:
            # 그래프가 없으면 저장 불가
            self.empty_message.setText("저장할 그래프가 없습니다. 먼저 그래프를 생성하세요.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "그래프 이미지 저장", "", "PNG 이미지 (*.png);;JPEG 이미지 (*.jpg)"
        )
        
        if file_path:
            try:
                layout = self.layout_combo.currentText()
                graph_visualizer.visualize_graph(file_path, layout)
                
                # 성공 메시지
                self.empty_message.setText(f"이미지가 저장되었습니다: {file_path}")
                
                # 2초 후 원래 그래프 복원
                import threading
                pixmap = self.graph_label.pixmap()
                if pixmap and not pixmap.isNull():
                    threading.Timer(2, lambda: self.graph_label.setPixmap(pixmap)).start()
                
            except Exception as e:
                self.empty_message.setText(f"이미지 저장 실패: {str(e)}")
    
    def export_graph_json(self):
        """그래프 JSON 내보내기"""
        if not graph_visualizer.graph:
            # 그래프가 없으면 내보내기 불가
            self.empty_message.setText("내보낼 그래프가 없습니다. 먼저 그래프를 생성하세요.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "그래프 JSON 내보내기", "", "JSON 파일 (*.json)"
        )
        
        if file_path:
            try:
                graph_visualizer.export_json(file_path)
                
                # 성공 메시지
                self.empty_message.setText(f"JSON이 저장되었습니다: {file_path}")
                
                # 2초 후 원래 그래프 복원
                import threading
                pixmap = self.graph_label.pixmap()
                if pixmap and not pixmap.isNull():
                    threading.Timer(2, lambda: self.graph_label.setPixmap(pixmap)).start()
                
            except Exception as e:
                self.empty_message.setText(f"JSON 내보내기 실패: {str(e)}")
