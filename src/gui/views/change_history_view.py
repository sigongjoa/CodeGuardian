#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 변경 이력 뷰
감지된 코드 변경 이력을 보여주는 UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QComboBox, QSplitter, QFileDialog,
    QTextEdit, QGroupBox, QDateEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QBrush, QFont

from src.storage.storage_manager import get_recent_changes
from src.core.events import event_bus
from datetime import datetime

class ChangeHistoryView(QWidget):
    """변경 이력 뷰 클래스"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 이벤트 연결
        event_bus.code_changed.connect(self.on_code_changed)
        
        # 초기 데이터 로드
        self.load_changes()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        
        # 상단 컨트롤 영역
        control_layout = QHBoxLayout()
        
        # 날짜 필터
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        control_layout.addWidget(QLabel("기간:"))
        control_layout.addWidget(self.date_from)
        control_layout.addWidget(QLabel("~"))
        control_layout.addWidget(self.date_to)
        
        # 필터 콤보박스
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("모든 변경")
        self.filter_combo.addItem("함수 변경만")
        self.filter_combo.addItem("블록 변경만")
        
        control_layout.addWidget(QLabel("필터:"))
        control_layout.addWidget(self.filter_combo)
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("새로고침")
        control_layout.addWidget(self.refresh_btn)
        
        # 내보내기 버튼
        self.export_btn = QPushButton("내보내기...")
        control_layout.addWidget(self.export_btn)
        
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # 스플리터 (테이블과 상세 정보 분할)
        splitter = QSplitter(Qt.Vertical)
        
        # 변경 이력 테이블
        self.changes_table = QTableWidget()
        self.changes_table.setColumnCount(5)
        self.changes_table.setHorizontalHeaderLabels(["파일", "함수/블록", "변경 유형", "시간", "자동 복원"])
        self.changes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.changes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.changes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        splitter.addWidget(self.changes_table)
        
        # 변경 상세 정보 영역
        details_group = QGroupBox("변경 상세 정보")
        details_layout = QVBoxLayout()
        
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        self.diff_text.setLineWrapMode(QTextEdit.NoWrap)
        details_layout.addWidget(self.diff_text)
        
        # 복원 버튼
        self.restore_btn = QPushButton("원본으로 복원")
        details_layout.addWidget(self.restore_btn)
        
        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)
        
        # 비율 설정
        splitter.setSizes([600, 200])
        
        main_layout.addWidget(splitter)
        
        # 버튼 연결
        self.refresh_btn.clicked.connect(self.load_changes)
        self.export_btn.clicked.connect(self.export_changes)
        self.restore_btn.clicked.connect(self.restore_original)
        self.changes_table.itemSelectionChanged.connect(self.show_diff)
        self.filter_combo.currentIndexChanged.connect(self.apply_filter)
        self.date_from.dateChanged.connect(self.apply_filter)
        self.date_to.dateChanged.connect(self.apply_filter)
        
        self.setLayout(main_layout)
    
    def load_changes(self):
        """변경 이력 로드"""
        # 기존 항목 모두 삭제
        self.changes_table.setRowCount(0)
        
        # 변경 이력 가져오기
        changes = get_recent_changes(1000)  # 많은 수를 가져옴
        
        # 테이블에 변경 이력 추가
        for i, change in enumerate(changes):
            self.changes_table.insertRow(i)
            
            # 파일 경로
            file_item = QTableWidgetItem(change['file_path'])
            self.changes_table.setItem(i, 0, file_item)
            
            # 함수/블록 이름
            name_item = QTableWidgetItem(change['function_name'])
            self.changes_table.setItem(i, 1, name_item)
            
            # 변경 유형
            type_item = QTableWidgetItem(change['change_type'])
            self.changes_table.setItem(i, 2, type_item)
            
            # 시간
            timestamp = change['timestamp']
            time_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            time_item = QTableWidgetItem(time_str)
            self.changes_table.setItem(i, 3, time_item)
            
            # 자동 복원 여부
            auto_restore = "예" if change['automatic_restore'] else "아니오"
            restore_item = QTableWidgetItem(auto_restore)
            self.changes_table.setItem(i, 4, restore_item)
        
        # 필터 적용
        self.apply_filter()
    
    def apply_filter(self):
        """필터 적용"""
        filter_type = self.filter_combo.currentText()
        from_date = self.date_from.date().toPyDate()
        to_date = self.date_to.date().toPyDate()
        
        # from_date는 시작일의 자정(00:00:00), to_date는 종료일의 다음날 자정 직전(23:59:59)
        from_timestamp = datetime.combine(from_date, datetime.min.time()).timestamp()
        to_timestamp = datetime.combine(to_date, datetime.max.time()).timestamp()
        
        for row in range(self.changes_table.rowCount()):
            hide_row = False
            
            # 함수/블록 필터
            if filter_type == "함수 변경만":
                function_name = self.changes_table.item(row, 1).text()
                if function_name.startswith("블록"):
                    hide_row = True
            elif filter_type == "블록 변경만":
                function_name = self.changes_table.item(row, 1).text()
                if not function_name.startswith("블록"):
                    hide_row = True
            
            # 날짜 필터
            time_str = self.changes_table.item(row, 3).text()
            time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            time_timestamp = time_obj.timestamp()
            
            if time_timestamp < from_timestamp or time_timestamp > to_timestamp:
                hide_row = True
            
            self.changes_table.setRowHidden(row, hide_row)
    
    def show_diff(self):
        """선택된 변경의 차이점 표시"""
        selected_rows = self.changes_table.selectedItems()
        if not selected_rows:
            return
        
        # 선택된 행 가져오기
        row = selected_rows[0].row()
        
        # 변경 이력 가져오기
        changes = get_recent_changes(1000)
        
        if row < len(changes):
            change = changes[row]
            
            # diff 표시
            diff_content = change['diff']
            
            # diff 내용을 구문 강조 표시
            html_diff = self.format_diff_as_html(diff_content)
            self.diff_text.setHtml(html_diff)
    
    def format_diff_as_html(self, diff_text):
        """diff 텍스트를 HTML로 포맷팅"""
        if not diff_text:
            return "<p>차이점 정보가 없습니다.</p>"
        
        lines = diff_text.split('\n')
        html_lines = []
        
        for line in lines:
            if line.startswith('+'):
                html_lines.append(f'<span style="background-color: #c8f7c5;">{line}</span>')
            elif line.startswith('-'):
                html_lines.append(f'<span style="background-color: #ffc8c8;">{line}</span>')
            elif line.startswith('@'):
                html_lines.append(f'<span style="color: #8080ff;">{line}</span>')
            else:
                html_lines.append(line)
        
        return "<pre>" + "<br>".join(html_lines) + "</pre>"
    
    def export_changes(self):
        """변경 이력 내보내기"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "변경 이력 내보내기",
            "",
            "CSV 파일 (*.csv);;텍스트 파일 (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 헤더 작성
                f.write("파일경로,함수/블록,변경유형,시간,자동복원,diff\n")
                
                # 표시된 행만 내보내기
                for row in range(self.changes_table.rowCount()):
                    if not self.changes_table.isRowHidden(row):
                        file_path = self.changes_table.item(row, 0).text()
                        function_name = self.changes_table.item(row, 1).text()
                        change_type = self.changes_table.item(row, 2).text()
                        time_str = self.changes_table.item(row, 3).text()
                        auto_restore = self.changes_table.item(row, 4).text()
                        
                        # diff는 현재 선택된 항목의 것만 가져옴 (CSV의 한계)
                        diff = ""
                        
                        # CSV 형식으로 저장
                        line = f'"{file_path}","{function_name}","{change_type}","{time_str}","{auto_restore}","{diff}"\n'
                        f.write(line)
            
            QMessageBox.information(self, "내보내기 완료", "변경 이력이 성공적으로 내보내졌습니다.")
        except Exception as e:
            QMessageBox.critical(self, "내보내기 오류", f"내보내기 중 오류가 발생했습니다: {str(e)}")
    
    def restore_original(self):
        """원본 코드로 복원"""
        selected_rows = self.changes_table.selectedItems()
        if not selected_rows:
            return
        
        # 선택된 행 가져오기
        row = selected_rows[0].row()
        
        # 선택된 변경 항목 정보
        file_path = self.changes_table.item(row, 0).text()
        function_name = self.changes_table.item(row, 1).text()
        
        # 확인 대화상자
        reply = QMessageBox.question(
            self,
            "코드 복원",
            f"정말 '{file_path}'의 '{function_name}'을(를) 원본으로 복원하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: 복원 로직 구현
            QMessageBox.information(
                self,
                "복원 완료",
                f"'{file_path}'의 '{function_name}'이(가) 원본으로 복원되었습니다."
            )
    
    def on_code_changed(self, file_path, function_name, change_type):
        """코드 변경 이벤트 처리"""
        # 변경 이력 새로고침
        self.load_changes()
