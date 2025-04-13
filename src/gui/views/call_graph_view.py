"""
호출 그래프 뷰
함수 호출 관계를 그래프로 시각화하는 뷰
"""

import sys
import os
import tempfile
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QSlider, QComboBox, QCheckBox, QFileDialog,
                            QSplitter, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from core.core import code_guardian
from visualizer.graph_visualizer import graph_visualizer

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
            
            # 3. 그래프 시각화 이미지 생성
            image_path = graph_visualizer.visualize_graph(layout=self.layout)
            
            self.finished.emit({
                "success": True, 
                "image_path": image_path, 
                "graph_data": graph_data
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
        
        # 그래프 생성 스레드
        self.graph_thread = GraphGeneratorThread()
        self.graph_thread.finished.connect(self.on_graph_generated)
    
    def init_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        
        # 상단 컨트롤 패널
        control_panel = QHBoxLayout()
        
        # 함수명 입력
        function_label = QLabel("함수:")
        self.function_input = QLineEdit()
        self.function_input.setPlaceholderText("함수명 입력...")
        
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
        control_panel.addWidget(self.function_input)
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
        
        # 그래프 이미지 표시 영역
        self.graph_scroll = QScrollArea()
        self.graph_scroll.setWidgetResizable(True)
        self.graph_scroll.setMinimumSize(800, 500)
        
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
        main_layout.addWidget(self.graph_scroll)
        main_layout.addLayout(option_panel)
        
        self.setLayout(main_layout)
    
    def generate_graph(self):
        """그래프 생성"""
        function_name = self.function_input.text()
        depth = self.depth_slider.value()
        layout = self.layout_combo.currentText()
        
        # 로딩 메시지 표시
        self.graph_label.setText(f"그래프 생성 중... 함수: {function_name}, 깊이: {depth}")
        
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
            self.graph_label.setText(f"그래프 생성 실패: {error_msg}")
            return
        
        # 이미지 파일 경로
        image_path = result.get("image_path")
        
        if not image_path or not os.path.exists(image_path):
            self.graph_label.setText("그래프 이미지 파일을 찾을 수 없습니다")
            return
        
        # 이미지 표시
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.graph_label.setText("이미지 로드 실패")
            return
        
        self.graph_label.setPixmap(pixmap)
        self.graph_label.setAlignment(Qt.AlignCenter)
        
        # 그래프 정보 업데이트
        graph_data = result.get("graph_data", {})
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        self.node_count.setText(f"노드: {len(nodes)}")
        self.edge_count.setText(f"엣지: {len(edges)}")
        
        # 에러 노드 수 계산 (실제로는 에러 노드를 파악하는 더 정교한 방법이 필요)
        error_count = 0
        if graph_visualizer.graph:
            error_nodes = graph_visualizer._get_error_nodes()
            error_count = sum(1 for node in graph_visualizer.graph.nodes() if node in error_nodes)
            
        self.error_count.setText(f"에러 함수: {error_count}")
    
    def save_graph_image(self):
        """그래프 이미지 저장"""
        if not graph_visualizer.graph:
            # 그래프가 없으면 저장 불가
            self.graph_label.setText("저장할 그래프가 없습니다. 먼저 그래프를 생성하세요.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "그래프 이미지 저장", "", "PNG 이미지 (*.png);;JPEG 이미지 (*.jpg)"
        )
        
        if file_path:
            try:
                layout = self.layout_combo.currentText()
                graph_visualizer.visualize_graph(file_path, layout)
                
                # 성공 메시지
                self.graph_label.setText(f"이미지가 저장되었습니다: {file_path}")
                
                # 2초 후 원래 그래프 복원
                pixmap = self.graph_label.pixmap()
                if not pixmap.isNull():
                    import threading
                    threading.Timer(2, lambda: self.graph_label.setPixmap(pixmap)).start()
                
            except Exception as e:
                self.graph_label.setText(f"이미지 저장 실패: {str(e)}")
    
    def export_graph_json(self):
        """그래프 JSON 내보내기"""
        if not graph_visualizer.graph:
            # 그래프가 없으면 내보내기 불가
            self.graph_label.setText("내보낼 그래프가 없습니다. 먼저 그래프를 생성하세요.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "그래프 JSON 내보내기", "", "JSON 파일 (*.json)"
        )
        
        if file_path:
            try:
                graph_visualizer.export_json(file_path)
                
                # 성공 메시지
                self.graph_label.setText(f"JSON이 저장되었습니다: {file_path}")
                
                # 2초 후 원래 그래프 복원
                pixmap = self.graph_label.pixmap()
                if not pixmap.isNull():
                    import threading
                    threading.Timer(2, lambda: self.graph_label.setPixmap(pixmap)).start()
                
            except Exception as e:
                self.graph_label.setText(f"JSON 내보내기 실패: {str(e)}")
