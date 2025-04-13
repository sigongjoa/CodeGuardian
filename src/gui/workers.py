"""
스레드 작업자 클래스
백그라운드 작업을 처리하는 스레드 클래스들
"""

import sys
import os
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 코어 모듈 임포트
from core.core import code_guardian


class RefreshWorker(QThread):
    """백그라운드 새로고침 작업을 위한 스레드 클래스"""
    
    finished = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.task_type = "all"  # "all", "graph", "errors", "changes"
        self.params = {}
    
    def set_task(self, task_type, **params):
        """실행할 작업 설정
        
        Args:
            task_type: 작업 유형
            params: 추가 매개변수
        """
        self.task_type = task_type
        self.params = params
    
    def run(self):
        """스레드 실행"""
        result = {"type": self.task_type}
        
        try:
            if self.task_type == "graph":
                # 그래프 데이터 가져오기
                function_name = self.params.get("function_name")
                depth = self.params.get("depth", 2)
                
                graph_data = code_guardian.get_call_graph(function_name, depth)
                result["data"] = graph_data
                result["success"] = True
                
            elif self.task_type == "errors":
                # 에러 데이터 가져오기
                function_name = self.params.get("function_name")
                limit = self.params.get("limit", 50)
                
                error_data = code_guardian.get_error_data(function_name, limit)
                result["data"] = error_data
                result["success"] = True
                
            elif self.task_type == "changes":
                # 변경 이력 가져오기
                file_path = self.params.get("file_path")
                function_name = self.params.get("function_name")
                limit = self.params.get("limit", 50)
                
                changes = []
                if hasattr(code_guardian.db_manager, "get_changes"):
                    changes = code_guardian.db_manager.get_changes(file_path, function_name, limit)
                    result["success"] = True
                else:
                    result["success"] = False
                    result["error"] = "Method not available"
                
                result["data"] = changes
                
            else:  # "all"
                # 모든 데이터 가져오기
                try:
                    graph_data = code_guardian.get_call_graph()
                    result["graph"] = graph_data
                    result["graph_success"] = True
                except Exception as e:
                    result["graph"] = {}
                    result["graph_success"] = False
                    result["graph_error"] = str(e)
                
                try:
                    error_data = code_guardian.get_error_data()
                    result["errors"] = error_data
                    result["errors_success"] = True
                except Exception as e:
                    result["errors"] = []
                    result["errors_success"] = False
                    result["errors_error"] = str(e)
                
                try:
                    if hasattr(code_guardian.db_manager, "get_changes"):
                        changes = code_guardian.db_manager.get_changes()
                        result["changes"] = changes
                        result["changes_success"] = True
                    else:
                        result["changes"] = []
                        result["changes_success"] = False
                        result["changes_error"] = "Method not available" 
                except Exception as e:
                    result["changes"] = []
                    result["changes_success"] = False
                    result["changes_error"] = str(e)
                
                result["success"] = (
                    result.get("graph_success", False) or 
                    result.get("errors_success", False) or 
                    result.get("changes_success", False)
                )
        
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            print(f"ERROR in RefreshWorker: {error_msg}")
            print(error_trace)
            
            result["success"] = False
            result["error"] = error_msg
            result["trace"] = error_trace
        
        self.finished.emit(result)


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
        result = {}
        
        try:
            # 그래프 데이터 가져오기
            graph_data = code_guardian.get_call_graph(self.function_name, self.depth)
            
            # 그래프 생성 성공
            result["success"] = True
            result["data"] = graph_data
            
        except Exception as e:
            error_msg = str(e)
            error_trace = traceback.format_exc()
            
            print(f"ERROR in GraphGeneratorThread: {error_msg}")
            print(error_trace)
            
            result["success"] = False
            result["error"] = error_msg
            result["trace"] = error_trace
        
        self.finished.emit(result)


class FileMonitorThread(QThread):
    """파일 모니터링 작업을 위한 스레드 클래스"""
    
    status_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_monitoring = False
        self.files_to_monitor = []
    
    def set_files(self, files_to_monitor):
        """모니터링할 파일 설정
        
        Args:
            files_to_monitor: 모니터링할 파일 경로 리스트
        """
        self.files_to_monitor = files_to_monitor
    
    def start_monitoring(self):
        """모니터링 시작"""
        self.is_monitoring = True
        if not self.isRunning():
            self.start()
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
    
    def run(self):
        """스레드 실행"""
        while self.is_monitoring:
            try:
                # 각 파일 상태 확인
                for file_path in self.files_to_monitor:
                    if not os.path.exists(file_path):
                        self.status_changed.emit({
                            "file_path": file_path,
                            "status": "missing",
                            "message": "파일이 존재하지 않음"
                        })
                        continue
                    
                    try:
                        # 파일 변경 감지
                        changes = code_guardian.check_file_integrity(file_path)
                        
                        if changes:
                            self.status_changed.emit({
                                "file_path": file_path,
                                "status": "changed",
                                "changes": changes,
                                "message": f"파일 변경 감지됨 ({len(changes)}개 변경사항)"
                            })
                        else:
                            self.status_changed.emit({
                                "file_path": file_path,
                                "status": "ok",
                                "message": "파일 정상"
                            })
                            
                    except Exception as e:
                        self.status_changed.emit({
                            "file_path": file_path,
                            "status": "error",
                            "error": str(e),
                            "message": f"파일 확인 중 오류: {str(e)}"
                        })
            
            except Exception as e:
                print(f"ERROR in FileMonitorThread: {str(e)}")
                print(traceback.format_exc())
            
            # 대기
            self.sleep(5)  # 5초마다 확인
