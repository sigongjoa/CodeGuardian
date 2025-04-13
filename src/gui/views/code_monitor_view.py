#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 코드 모니터 뷰
보호된 코드 목록 및 상태를 보여주는 UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QComboBox, QSplitter,
    QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QFont

from src.storage.storage_manager import (
    get_protected_functions,
    get_protected_blocks,
    get_recent_changes
)
from src.core.events import event_bus

class CodeMonitorView(QWidget):
    """코드 모니터 뷰 클래스"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 이벤트 연결
        event_bus.code_changed.connect(self.on_code_changed)
        
        # 초기 데이터 로드
        self.load_data()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        
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
        self.refresh_btn = QPushButton("새로고침")
        control_layout.addWidget(self.refresh_btn)
        
        # 보호 추가 버튼
        self.add_protection_btn = QPushButton("보호 추가...")
        control_layout.addWidget(self.add_protection_btn)
        
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 스플리터 (테이블과 상세 정보 분할)
        splitter = QSplitter(Qt.Vertical)
        
        # 보호된 코드 테이블
        self.protected_table = QTableWidget()
        self.protected_table.setColumnCount(5)
        self.protected_table.setHorizontalHeaderLabels(["유형", "파일", "이름", "상태", "마지막 확인"])
        self.protected_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.protected_table.setSelectionMode(QTableWidget.SingleSelection)
        self.protected_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        splitter.addWidget(self.protected_table)
        
        # 상세 정보 영역
        details_group = QGroupBox("상세 정보")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)
        
        # 비율 설정
        splitter.setSizes([600, 200])
        
        main_layout.addWidget(splitter)
        
        # 버튼 연결
        self.refresh_btn.clicked.connect(self.load_data)
        self.add_protection_btn.clicked.connect(self.add_protection)
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        self.protected_table.itemSelectionChanged.connect(self.show_details)
        
        self.setLayout(main_layout)
    
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
            self.protected_table.setItem(row, 0, type_item)
            
            # 파일 경로
            file_item = QTableWidgetItem(func['file_path'])
            self.protected_table.setItem(row, 1, file_item)
            
            # 함수 이름
            name_item = QTableWidgetItem(func['function_name'])
            self.protected_table.setItem(row, 2, name_item)
            
            # 상태 (변경 여부)
            key = f"{func['file_path']}:{func['function_name']}"
            if key in changed_items:
                status_item = QTableWidgetItem("변경됨")
                status_item.setBackground(QBrush(QColor(255, 200, 200)))
            else:
                status_item = QTableWidgetItem("정상")
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
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
            self.protected_table.setItem(row, 0, type_item)
            
            # 파일 경로
            file_item = QTableWidgetItem(block['file_path'])
            self.protected_table.setItem(row, 1, file_item)
            
            # 블록 이름 (라인 범위)
            name = f"블록 {block['start_line']}-{block['end_line']}"
            name_item = QTableWidgetItem(name)
            self.protected_table.setItem(row, 2, name_item)
            
            # 상태 (변경 여부)
            key = f"{block['file_path']}:{name}"
            if key in changed_items:
                status_item = QTableWidgetItem("변경됨")
                status_item.setBackground(QBrush(QColor(255, 200, 200)))
            else:
                status_item = QTableWidgetItem("정상")
                status_item.setBackground(QBrush(QColor(200, 255, 200)))
            self.protected_table.setItem(row, 3, status_item)
            
            # 마지막 확인 시간
            from datetime import datetime
            last_check = datetime.fromtimestamp(block['last_verified']).strftime('%Y-%m-%d %H:%M:%S')
            time_item = QTableWidgetItem(last_check)
            self.protected_table.setItem(row, 4, time_item)
            
            row += 1
        
        # 필터 적용
        self.apply_filter()
    
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
        
        # 상세 정보 구성
        details = f"유형: {type_text}\n"
        details += f"파일: {file_path}\n"
        details += f"이름: {name}\n"
        details += f"상태: {status}\n\n"
        
        # 변경 내역 가져오기
        if status == "변경됨":
            changes = get_recent_changes(10)
            key = f"{file_path}:{name}"
            
            for change in changes:
                change_key = f"{change['file_path']}:{change['function_name']}"
                if change_key == key:
                    details += "변경 내역:\n"
                    details += f"변경 시간: {datetime.fromtimestamp(change['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    details += f"변경 유형: {change['change_type']}\n\n"
                    details += "Diff:\n"
                    details += change['diff']
                    break
        
        # 상세 정보 표시
        self.details_text.setText(details)
    
    def add_protection(self):
        """보호 추가 대화상자 표시"""
        # TODO: 보호 추가 대화상자 구현
        pass
    
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
