#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 설정 관리
애플리케이션 설정 로드, 저장 및 관리
"""

import json
import os
from PyQt5.QtCore import QObject, pyqtSignal

class Settings(QObject):
    """설정 관리 클래스"""
    settings_changed = pyqtSignal(str, object)  # section, value
    
    def __init__(self, config_file="config/settings.json"):
        super().__init__()
        # 절대 경로 계산
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_file = os.path.join(base_dir, config_file)
        self.settings = {}
        self.auto_save = True
        
        # 초기 설정 로드
        self.load()
        
    def load(self):
        """설정 파일 로드"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        else:
            # 기본 설정 생성
            self.settings = {
                "monitor": {
                    "paths": [],
                    "interval": 5  # 초 단위
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
            # 설정 디렉토리 생성
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            self.save()
    
    def save(self):
        """설정 파일 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
    
    def get(self, section, key, default=None):
        """설정 값 가져오기"""
        if section in self.settings and key in self.settings[section]:
            return self.settings[section][key]
        return default
    
    def set(self, section, key, value):
        """설정 값 설정"""
        if section not in self.settings:
            self.settings[section] = {}
        
        # 변경 사항이 있을 때만 처리
        if self.settings[section].get(key) != value:
            self.settings[section][key] = value
            
            # 시그널 발생
            self.settings_changed.emit(f"{section}.{key}", value)
            
            # 자동 저장 모드면 바로 저장
            if self.auto_save:
                self.save()
                
    def set_auto_save(self, enabled):
        """자동 저장 모드 설정"""
        self.auto_save = enabled

# 전역 설정 인스턴스
app_settings = Settings()
