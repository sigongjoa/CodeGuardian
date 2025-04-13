"""
에러 분석 뷰
에러 정보를 분석하고 표시하는 뷰
"""

import sys
import os
import traceback
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                            QSplitter, QTextEdit, QCheckBox, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from core.core import code_guardian

class ErrorAnalysisView(QWidget):
    """에러 분석 뷰 클래스"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.current_error_data = []
        
        # 지연 로딩 - 구성요소가 모두 초기화된 후 데이터 로딩
        QTimer.singleShot(500, self.delayed_loading)
    
    def delayed_loading(self):
        """지연 로딩 함수 - 컴포넌트 초기화 후 호출"""
        try:
            self.refresh_error_data()
        except Exception as e:
            print(f"초기 데이터 로딩 중 오류: {str(e)}")
    
    def init_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        
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
        
        # 메인 레이아웃에 추가
        main_layout.addLayout(control_panel)
        main_layout.addWidget(splitter)
        
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
            self.update_error_details(self.current_error_data[row_index])
    
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
