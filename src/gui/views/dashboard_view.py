#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 대시보드 뷰
시스템 상태와 요약 정보를 보여주는 대시보드 UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QGridLayout, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from src.storage.storage_manager import (
    get_recent_calls, 
    get_recent_changes, 
    get_recent_errors,
    get_protected_functions,
    get_protected_blocks
)
from src.core.events import event_bus
from src.core.protection_scanner import get_project_status

class StatsCard(QFrame):
    """통계 카드 위젯"""
    
    def __init__(self, title, value, description=""):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumHeight(120)
        self.setMinimumWidth(200)
        
        # 레이아웃
        layout = QVBoxLayout()
        
        # 타이틀
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # 값
        value_label = QLabel(str(value))
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        
        # 설명
        desc_label = QLabel(description)
        desc_label.setAlignment(Qt.AlignCenter)
        
        # 레이아웃에 추가
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(desc_label)
        
        self.setLayout(layout)
        
        # 값 라벨 저장 (업데이트용)
        self.value_label = value_label
    
    def update_value(self, value):
        """값 업데이트"""
        self.value_label.setText(str(value))

class DashboardView(QWidget):
    """대시보드 뷰 클래스"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 타이머로 주기적 업데이트
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_stats)
        self.update_timer.start(5000)  # 5초마다 업데이트
        
        # 이벤트 연결
        event_bus.code_changed.connect(self.on_code_changed)
        event_bus.function_called.connect(self.on_function_called)
        event_bus.error_detected.connect(self.on_error_detected)
        
        # 초기 업데이트
        self.update_stats()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        
        # 제목
        title_label = QLabel("CodeGuardian 대시보드")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 프로젝트 정보
        self.project_label = QLabel("프로젝트: 선택되지 않음")
        main_layout.addWidget(self.project_label)
        
        # 통계 카드 섹션
        stats_layout = QHBoxLayout()
        
        # 보호된 함수 카드
        self.protected_funcs_card = StatsCard("보호된 함수", "0", "현재 보호 중인 함수 수")
        stats_layout.addWidget(self.protected_funcs_card)
        
        # 보호된 블록 카드
        self.protected_blocks_card = StatsCard("보호된 블록", "0", "현재 보호 중인 코드 블록 수")
        stats_layout.addWidget(self.protected_blocks_card)
        
        # 감지된 변경 카드
        self.changes_card = StatsCard("감지된 변경", "0", "감지된 코드 변경 수")
        stats_layout.addWidget(self.changes_card)
        
        # 에러 카드
        self.errors_card = StatsCard("감지된 에러", "0", "감지된 에러 수")
        stats_layout.addWidget(self.errors_card)
        
        main_layout.addLayout(stats_layout)
        
        # 최근 활동 섹션
        activity_group = QGroupBox("최근 활동")
        activity_layout = QVBoxLayout()
        
        self.activity_label = QLabel("활동 내역이 없습니다.")
        activity_layout.addWidget(self.activity_label)
        
        activity_group.setLayout(activity_layout)
        main_layout.addWidget(activity_group)
        
        # 빠른 액션 섹션
        actions_group = QGroupBox("빠른 액션")
        actions_layout = QGridLayout()
        
        # 액션 버튼들
        self.add_protection_btn = QPushButton("함수 보호 추가")
        self.start_monitoring_btn = QPushButton("모니터링 시작")
        self.view_call_graph_btn = QPushButton("호출 그래프 보기")
        self.check_integrity_btn = QPushButton("무결성 검사")
        
        actions_layout.addWidget(self.add_protection_btn, 0, 0)
        actions_layout.addWidget(self.start_monitoring_btn, 0, 1)
        actions_layout.addWidget(self.view_call_graph_btn, 1, 0)
        actions_layout.addWidget(self.check_integrity_btn, 1, 1)
        
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)
        
        # 버튼 연결
        self.add_protection_btn.clicked.connect(self.on_add_protection)
        self.start_monitoring_btn.clicked.connect(self.on_start_monitoring)
        self.view_call_graph_btn.clicked.connect(self.on_view_call_graph)
        self.check_integrity_btn.clicked.connect(self.on_check_integrity)
        
        self.setLayout(main_layout)
    
    def update_stats(self):
        """통계 정보 업데이트"""
        try:
            # 프로젝트 상태 가져오기
            project_status = get_project_status()
            
            # 보호된 함수 수
            self.protected_funcs_card.update_value(project_status["total_functions"])
            
            # 보호된 블록 수
            self.protected_blocks_card.update_value(project_status["total_blocks"])
            
            # 변경 수
            recent_changes = get_recent_changes()
            self.changes_card.update_value(len(recent_changes))
            
            # 에러 수
            recent_errors = get_recent_errors()
            self.errors_card.update_value(len(recent_errors))
            
            # 최근 활동 업데이트
            self.update_activity()
        except Exception as e:
            import logging
            logging.error(f"대시보드 통계 업데이트 오류: {str(e)}")
    
    def update_activity(self):
        """최근 활동 목록 업데이트"""
        # 모든 최근 활동 가져오기
        changes = get_recent_changes(5)
        errors = get_recent_errors(5)
        calls = get_recent_calls(5)
        
        # 활동 내역 조합
        activity_text = ""
        
        if changes:
            activity_text += "최근 변경:\n"
            for change in changes:
                activity_text += f"- {change['file_path']} ({change['function_name']}): {change['change_type']}\n"
            activity_text += "\n"
        
        if errors:
            activity_text += "최근 에러:\n"
            for error in errors:
                activity_text += f"- {error['function_name']}: {error['error_type']}\n"
            activity_text += "\n"
        
        if calls:
            activity_text += "최근 호출:\n"
            for call in calls:
                activity_text += f"- {call['caller_function']} → {call['callee_function']}\n"
        
        if not activity_text:
            activity_text = "활동 내역이 없습니다."
        
        self.activity_label.setText(activity_text)
    
    def update_project_info(self, project_path):
        """프로젝트 정보 업데이트"""
        self.project_label.setText(f"프로젝트: {project_path}")
        
        # 프로젝트 정보 업데이트 후 통계 갱신
        self.update_stats()
    
    def on_code_changed(self, file_path, function_name, change_type):
        """코드 변경 이벤트 처리"""
        # 통계 업데이트
        self.update_stats()
    
    def on_function_called(self, caller, callee, timestamp):
        """함수 호출 이벤트 처리"""
        # 통계 업데이트
        self.update_stats()
    
    def on_error_detected(self, function_name, error_type, stack_trace):
        """에러 감지 이벤트 처리"""
        # 통계 업데이트
        self.update_stats()
    
    def on_add_protection(self):
        """보호 추가 버튼 클릭 처리"""
        # 부모 윈도우의 메서드 호출
        parent = self.window()
        if hasattr(parent, 'add_function_protection'):
            parent.add_function_protection()
    
    def on_start_monitoring(self):
        """모니터링 시작 버튼 클릭 처리"""
        from src.core.monitor import start_file_monitoring, is_monitoring_active
        
        if is_monitoring_active():
            # 이미 활성화된 경우 중지
            from src.core.monitor import stop_file_monitoring
            stop_file_monitoring()
            self.start_monitoring_btn.setText("모니터링 시작")
        else:
            # 비활성화된 경우 시작
            start_file_monitoring()
            self.start_monitoring_btn.setText("모니터링 중지")
    
    def on_view_call_graph(self):
        """호출 그래프 보기 버튼 클릭 처리"""
        # 호출 그래프 탭으로 전환
        parent = self.window()
        if hasattr(parent, 'tabs'):
            # 호출 그래프 탭 인덱스 찾기
            for i in range(parent.tabs.count()):
                if parent.tabs.tabText(i) == "호출 그래프":
                    parent.tabs.setCurrentIndex(i)
                    break
    
    def on_check_integrity(self):
        """무결성 검사 버튼 클릭 처리"""
        # 현재 프로젝트 경로 가져오기
        from src.core.settings import app_settings
        paths = app_settings.get("monitor", "paths", [])
        
        if not paths:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "프로젝트 없음",
                "프로젝트가 로드되지 않았습니다. 먼저 프로젝트를 열어주세요."
            )
            return
        
        # 프로젝트 스캔
        parent = self.window()
        if hasattr(parent, 'scan_project'):
            parent.scan_project(paths[0])
