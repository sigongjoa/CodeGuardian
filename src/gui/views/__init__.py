"""
CodeGuardian 뷰 패키지 초기화
"""

try:
    from .call_graph_view import CallGraphView
except ImportError:
    pass

try:
    from .error_analysis_view import ErrorAnalysisView
except ImportError:
    pass
