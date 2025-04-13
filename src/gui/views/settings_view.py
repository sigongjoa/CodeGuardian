#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 설정 뷰
애플리케이션 설정을 관리하는 UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QFormLayout, QSpinBox, QCheckBox,
    QComboBox, QPushButton, QFileDialog, QListWidget,
    QListWidgetItem, QLineEdit, QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from src.core.settings import app_settings

class SettingsView(QWidget):
    """설정 뷰 클래스"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        
        # 탭 위젯
        self.tabs = QTabWidget()
        
        # 일반 설정 탭
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        # 자동 저장 설정
        auto_save_group = QGroupBox("저장 설정")
        auto_save_layout = QVBoxLayout()
        
        self.auto_save_cb = QCheckBox("설정 변경 시 자동 저장")
        auto_save_layout.addWidget(self.auto_save_cb)
        
        auto_save_group.setLayout(auto_save_layout)
        general_layout.addWidget(auto_save_group)
        
        # UI 설정
        ui_group = QGroupBox("UI 설정")
        ui_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("밝은 테마")
        self.theme_combo.addItem("어두운 테마")
        ui_layout.addRow("테마:", self.theme_combo)
        
        self.auto_refresh_cb = QCheckBox("자동 새로고침")
        ui_layout.addRow("", self.auto_refresh_cb)
        
        ui_group.setLayout(ui_layout)
        general_layout.addWidget(ui_group)
        
        general_layout.addStretch(1)
        general_tab.setLayout(general_layout)
        
        # 모니터링 설정 탭
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout()
        
        # 모니터링 경로 설정
        paths_group = QGroupBox("모니터링 경로")
        paths_layout = QVBoxLayout()
        
        self.paths_list = QListWidget()
        paths_layout.addWidget(self.paths_list)
        
        paths_btn_layout = QHBoxLayout()
        self.add_path_btn = QPushButton("경로 추가...")
        self.remove_path_btn = QPushButton("경로 제거")
        paths_btn_layout.addWidget(self.add_path_btn)
        paths_btn_layout.addWidget(self.remove_path_btn)
        paths_layout.addLayout(paths_btn_layout)
        
        paths_group.setLayout(paths_layout)
        monitor_layout.addWidget(paths_group)
        
        # 모니터링 간격 설정
        interval_group = QGroupBox("모니터링 설정")
        interval_layout = QFormLayout()
        
        self.interval_spinner = QSpinBox()
        self.interval_spinner.setRange(1, 60)
        interval_layout.addRow("변경 감지 주기(초):", self.interval_spinner)
        
        interval_group.setLayout(interval_layout)
        monitor_layout.addWidget(interval_group)
        
        monitor_layout.addStretch(1)
        monitor_tab.setLayout(monitor_layout)
        
        # 보호 설정 탭
        protection_tab = QWidget()
        protection_layout = QVBoxLayout()
        
        # 자동 복구 설정
        recovery_group = QGroupBox("자동 복구 설정")
        recovery_layout = QVBoxLayout()
        
        self.auto_restore_cb = QCheckBox("변경된 함수 자동 복구")
        recovery_layout.addWidget(self.auto_restore_cb)
        
        recovery_group.setLayout(recovery_layout)
        protection_layout.addWidget(recovery_group)
        
        # 백업 설정
        backup_group = QGroupBox("백업 설정")
        backup_layout = QFormLayout()
        
        self.backup_path_edit = QLineEdit()
        self.backup_path_btn = QPushButton("찾아보기...")
        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self.backup_path_edit)
        backup_path_layout.addWidget(self.backup_path_btn)
        
        backup_layout.addRow("백업 위치:", backup_path_layout)
        
        backup_group.setLayout(backup_layout)
        protection_layout.addWidget(backup_group)
        
        protection_layout.addStretch(1)
        protection_tab.setLayout(protection_layout)
        
        # 탭에 추가
        self.tabs.addTab(general_tab, "일반")
        self.tabs.addTab(monitor_tab, "모니터링")
        self.tabs.addTab(protection_tab, "보호")
        
        main_layout.addWidget(self.tabs)
        
        # 하단 버튼 영역
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("설정 저장")
        self.reset_btn = QPushButton("기본값으로 초기화")
        
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 이벤트 연결
        self.auto_save_cb.toggled.connect(self.on_auto_save_changed)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        self.auto_refresh_cb.toggled.connect(self.on_auto_refresh_changed)
        self.interval_spinner.valueChanged.connect(self.on_interval_changed)
        self.auto_restore_cb.toggled.connect(self.on_auto_restore_changed)
        
        self.add_path_btn.clicked.connect(self.add_path)
        self.remove_path_btn.clicked.connect(self.remove_path)
        self.backup_path_btn.clicked.connect(self.select_backup_path)
        
        self.save_btn.clicked.connect(self.save_settings)
        self.reset_btn.clicked.connect(self.reset_settings)
    
    def load_settings(self):
        """설정 로드"""
        # 자동 저장 설정
        self.auto_save_cb.setChecked(app_settings.auto_save)
        
        # UI 설정
        theme = app_settings.get("ui", "theme", "light")
        self.theme_combo.setCurrentIndex(0 if theme == "light" else 1)
        
        auto_refresh = app_settings.get("ui", "auto_refresh", True)
        self.auto_refresh_cb.setChecked(auto_refresh)
        
        # 모니터링 경로
        paths = app_settings.get("monitor", "paths", [])
        self.paths_list.clear()
        for path in paths:
            self.paths_list.addItem(path)
        
        # 모니터링 간격
        interval = app_settings.get("monitor", "interval", 5)
        self.interval_spinner.setValue(interval)
        
        # 자동 복구 설정
        auto_restore = app_settings.get("protection", "auto_restore", True)
        self.auto_restore_cb.setChecked(auto_restore)
        
        # 백업 위치
        backup_location = app_settings.get("protection", "backup_location", "backups/")
        self.backup_path_edit.setText(backup_location)
        
        # 저장 버튼 상태 설정
        self.save_btn.setEnabled(not app_settings.auto_save)
    
    def save_settings(self):
        """설정 저장"""
        app_settings.save()
        QMessageBox.information(self, "설정 저장", "설정이 저장되었습니다.")
    
    def reset_settings(self):
        """설정 초기화"""
        reply = QMessageBox.question(
            self, 
            "설정 초기화", 
            "모든 설정을 기본값으로 초기화하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 기본 설정으로 초기화
            app_settings.settings = {
                "monitor": {
                    "paths": [],
                    "interval": 5
                },
                "protection": {
                    "auto_restore": True,
                    "backup_location": "backups/"
                },
                "ui": {
                    "theme": "light",
                    "auto_refresh": True,
                    "call_depth": 2
                }
            }
            
            # 자동 저장 상태 유지
            auto_save = app_settings.auto_save
            
            # 설정 저장
            if not auto_save:
                app_settings.save()
            
            # UI 업데이트
            self.load_settings()
            QMessageBox.information(self, "설정 초기화", "설정이 초기화되었습니다.")
    
    def on_auto_save_changed(self, checked):
        """자동 저장 설정 변경"""
        app_settings.set_auto_save(checked)
        self.save_btn.setEnabled(not checked)
    
    def on_theme_changed(self, index):
        """테마 설정 변경"""
        theme = "light" if index == 0 else "dark"
        app_settings.set("ui", "theme", theme)
    
    def on_auto_refresh_changed(self, checked):
        """자동 새로고침 설정 변경"""
        app_settings.set("ui", "auto_refresh", checked)
    
    def on_interval_changed(self, value):
        """모니터링 간격 설정 변경"""
        app_settings.set("monitor", "interval", value)
    
    def on_auto_restore_changed(self, checked):
        """자동 복구 설정 변경"""
        app_settings.set("protection", "auto_restore", checked)
    
    def add_path(self):
        """모니터링 경로 추가"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "모니터링할 디렉토리 선택",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            # 중복 확인
            existing_paths = app_settings.get("monitor", "paths", [])
            if directory not in existing_paths:
                existing_paths.append(directory)
                app_settings.set("monitor", "paths", existing_paths)
                
                # 목록에 추가
                self.paths_list.addItem(directory)
    
    def remove_path(self):
        """모니터링 경로 제거"""
        selected_items = self.paths_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        path = item.text()
        
        # 경로 목록에서 제거
        existing_paths = app_settings.get("monitor", "paths", [])
        if path in existing_paths:
            existing_paths.remove(path)
            app_settings.set("monitor", "paths", existing_paths)
            
            # 목록에서 제거
            self.paths_list.takeItem(self.paths_list.row(item))
    
    def select_backup_path(self):
        """백업 위치 선택"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "백업 디렉토리 선택",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            # 상대 경로로 변환
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            try:
                rel_path = os.path.relpath(directory, base_dir)
                if not rel_path.endswith('/'):
                    rel_path += '/'
                
                self.backup_path_edit.setText(rel_path)
                app_settings.set("protection", "backup_location", rel_path)
            except ValueError:
                # 다른 드라이브인 경우 절대 경로 사용
                self.backup_path_edit.setText(directory)
                app_settings.set("protection", "backup_location", directory)
