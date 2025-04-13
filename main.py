"""
CodeGuardian 메인 엔트리 포인트
애플리케이션 시작점
"""

import sys
import os

# 패키지 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow

def main():
    """애플리케이션 시작 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("CodeGuardian")
    app.setStyle("Fusion")  # 일관된 UI 스타일 적용
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 애플리케이션 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
