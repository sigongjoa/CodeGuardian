"""
그래프 시각화 모듈
함수 호출 그래프를 시각화하는 기능 제공
"""

import os
import sys
import json
import tempfile
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# 상대 경로로 다른 모듈 접근
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.core import code_guardian

class GraphVisualizer:
    """호출 그래프 시각화 클래스"""
    
    def __init__(self):
        """초기화"""
        self.graph = None
        self.temp_files = []
    
    def create_call_graph(self, function_name=None, depth=2):
        """호출 그래프 생성
        
        Args:
            function_name: 시작 함수명. None이면 전체 그래프
            depth: 호출 깊이
            
        Returns:
            NetworkX 그래프 객체
        """
        # 호출 데이터 가져오기
        graph_data = code_guardian.get_call_graph(function_name, depth)
        
        # NetworkX 그래프 생성
        G = nx.DiGraph()
        
        # 노드 추가
        for node in graph_data.get("nodes", []):
            G.add_node(node["id"], label=node.get("label", node["id"]))
        
        # 엣지 추가
        for edge in graph_data.get("edges", []):
            G.add_edge(edge["source"], edge["target"])
        
        self.graph = G
        return G
    
    def visualize_graph(self, output_path=None, layout='spring'):
        """그래프 시각화하여 이미지 파일 생성
        
        Args:
            output_path: 출력 이미지 경로. None이면 임시 파일 생성
            layout: 레이아웃 알고리즘 ('spring', 'circular', 'random', 'shell')
            
        Returns:
            생성된 이미지 파일 경로
        """
        if not self.graph:
            raise ValueError("그래프가 먼저 생성되어야 합니다.")
        
        G = self.graph
        
        # 그래프가 비어있는 경우
        if len(G.nodes()) == 0:
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, "No function call data available", 
                     horizontalalignment='center', fontsize=14)
            plt.axis('off')
        else:
            plt.figure(figsize=(12, 10))
            
            # 레이아웃 선택
            if layout == 'spring':
                pos = nx.spring_layout(G, k=0.3, iterations=50)
            elif layout == 'circular':
                pos = nx.circular_layout(G)
            elif layout == 'shell':
                pos = nx.shell_layout(G)
            else:
                pos = nx.random_layout(G)
            
            # 노드 크기 계산 (호출 수에 비례)
            node_sizes = []
            for node in G.nodes():
                # 호출하는 함수 수 + 호출받는 함수 수
                size = (len(list(G.successors(node))) + len(list(G.predecessors(node)))) * 200 + 500
                node_sizes.append(size)
            
            # 노드 색상 - 에러 발생 여부에 따라 변경
            error_nodes = self._get_error_nodes()
            node_colors = ['#ff6b6b' if node in error_nodes else '#1e88e5' for node in G.nodes()]
            
            # 노드 그리기
            nx.draw_networkx_nodes(G, pos, 
                                  node_size=node_sizes,
                                  node_color=node_colors,
                                  alpha=0.8)
            
            # 엣지 그리기
            nx.draw_networkx_edges(G, pos, 
                                  edge_color='#aaaaaa',
                                  width=1.0,
                                  alpha=0.7,
                                  arrows=True,
                                  arrowstyle='-|>',
                                  arrowsize=15)
            
            # 레이블 그리기
            nx.draw_networkx_labels(G, pos, 
                                   font_size=10,
                                   font_family='sans-serif',
                                   font_weight='bold')
            
            plt.axis('off')
            plt.title("Function Call Graph", fontsize=16)
        
        # 범례 추가
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#1e88e5', markersize=15, label='Normal Function'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff6b6b', markersize=15, label='Error Function')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # 파일 저장
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=100)
        else:
            # 임시 파일 생성
            fd, temp_path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            plt.savefig(temp_path, bbox_inches='tight', dpi=100)
            self.temp_files.append(temp_path)
            output_path = temp_path
        
        plt.close()
        return output_path
    
    def _get_error_nodes(self):
        """에러가 발생한 함수 노드 목록 조회
        
        Returns:
            에러 발생 함수명 집합
        """
        # 에러 데이터 가져오기
        error_data = code_guardian.get_error_data(limit=100)
        
        # 에러 발생 함수 추출
        error_functions = set()
        for error in error_data:
            error_functions.add(error['function_name'])
        
        return error_functions
    
    def export_json(self, output_path=None):
        """그래프 데이터를 JSON 형식으로 내보내기
        
        Args:
            output_path: 출력 JSON 파일 경로. None이면 문자열 반환
            
        Returns:
            JSON 문자열 또는 파일 경로
        """
        if not self.graph:
            raise ValueError("그래프가 먼저 생성되어야 합니다.")
        
        G = self.graph
        
        # 노드 데이터 변환
        nodes = []
        for node_id in G.nodes():
            nodes.append({
                "id": node_id,
                "label": G.nodes[node_id].get('label', node_id)
            })
        
        # 엣지 데이터 변환
        edges = []
        for u, v in G.edges():
            edges.append({
                "source": u,
                "target": v
            })
        
        # JSON 데이터 구성
        json_data = {
            "nodes": nodes,
            "edges": edges
        }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(json_data, f, indent=2)
            return output_path
        else:
            return json.dumps(json_data, indent=2)
    
    def cleanup(self):
        """임시 파일 정리"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"WARNING: 임시 파일 삭제 실패 - {temp_file}: {str(e)}")
        
        self.temp_files = []

# 전역 인스턴스
graph_visualizer = GraphVisualizer()
