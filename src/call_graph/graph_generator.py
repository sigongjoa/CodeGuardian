#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 호출 그래프 생성기
함수 호출 관계를 그래프 데이터로 변환
"""

import os
import re
from collections import defaultdict

from src.storage.storage_manager import get_recent_calls, get_recent_changes

class CallGraphOptimizer:
    """호출 그래프 최적화 클래스"""
    
    def __init__(self, max_cache_size=10):
        self.cache = {}  # 그래프 캐시
        self.max_cache_size = max_cache_size
    
    def get_call_graph(self, function_name, depth, direction="both", show_modules=True, group_calls=False, highlight_changes=False):
        """캐시된 호출 그래프 가져오기"""
        cache_key = f"{function_name}_{depth}_{direction}_{show_modules}_{group_calls}_{highlight_changes}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 캐시에 없으면 계산
        graph_data = generate_call_graph(function_name, depth, direction, show_modules, group_calls, highlight_changes)
        
        # 캐시 크기 관리
        if len(self.cache) >= self.max_cache_size:
            # 가장 오래된 항목 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        # 캐시에 저장
        self.cache[cache_key] = graph_data
        return graph_data
    
    def invalidate_cache(self, function_name=None):
        """캐시 무효화"""
        if function_name:
            # 특정 함수 관련 캐시만 무효화
            keys_to_remove = [k for k in self.cache if k.startswith(f"{function_name}_")]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            # 전체 캐시 초기화
            self.cache.clear()

# 전역 최적화 인스턴스
graph_optimizer = CallGraphOptimizer()

def simplify_graph(nodes, edges, importance_threshold=0.3):
    """중요도가 낮은 노드/엣지를 제거하여 그래프 단순화"""
    # 노드 중요도 계산 (연결 수 기반)
    node_importance = {}
    for node in nodes:
        # 연결 수 계산
        connections = len([e for e in edges if e['source'] == node['id'] or e['target'] == node['id']])
        # 정규화된 중요도 (0~1)
        max_connections = max(1, max(len([e for e in edges if e['source'] == n['id'] or e['target'] == n['id']]) for n in nodes))
        node_importance[node['id']] = connections / max_connections
    
    # 중요도가 높은 노드만 필터링
    important_nodes = [node for node in nodes if node_importance[node['id']] >= importance_threshold]
    important_node_ids = [node['id'] for node in important_nodes]
    
    # 중요 노드 간의 엣지만 유지
    important_edges = [edge for edge in edges 
                       if edge['source'] in important_node_ids 
                       and edge['target'] in important_node_ids]
    
    return important_nodes, important_edges

def get_call_graph(function_name, depth=2, direction="both", show_modules=True, group_calls=False, highlight_changes=False):
    """호출 그래프 데이터 가져오기 (캐시 사용)"""
    return graph_optimizer.get_call_graph(function_name, depth, direction, show_modules, group_calls, highlight_changes)

def generate_call_graph(function_name, depth=2, direction="both", show_modules=True, group_calls=False, highlight_changes=False):
    """호출 그래프 생성"""
    # 호출 데이터 가져오기
    calls = get_recent_calls(1000)  # 충분히 많은 수 가져오기
    
    # 변경 데이터 가져오기 (변경된 함수 강조 표시용)
    changes = get_recent_changes(1000) if highlight_changes else []
    changed_functions = set()
    for change in changes:
        changed_functions.add(change['function_name'])
    
    # 호출 관계 맵 구성
    callers = defaultdict(set)  # 호출자 맵 (키: 피호출자, 값: 호출자 집합)
    callees = defaultdict(set)  # 피호출자 맵 (키: 호출자, 값: 피호출자 집합)
    module_map = {}  # 함수 -> 모듈 맵
    
    for call in calls:
        caller = call['caller_function']
        callee = call['callee_function']
        
        callees[caller].add(callee)
        callers[callee].add(caller)
        
        # 모듈 정보 저장
        module_map[caller] = os.path.basename(call['caller_file'])
        module_map[callee] = os.path.basename(call['callee_file'])
    
    # 그래프 노드 & 엣지 구성
    nodes = []
    edges = []
    
    # 노드 집합 (중복 방지)
    node_set = set()
    
    # 시작 노드
    node_set.add(function_name)
    
    # 관련 노드 찾기 (BFS)
    queue = [(function_name, 0)]  # (노드, 깊이)
    visited = {function_name}
    
    while queue:
        current, current_depth = queue.pop(0)
        
        # 깊이 제한 확인
        if current_depth >= depth:
            continue
        
        # 방향에 따라 연결된 노드 추가
        if direction in ["both", "caller"]:
            for caller in callers[current]:
                edges.append({
                    "source": caller,
                    "target": current,
                    "value": 1
                })
                node_set.add(caller)
                
                if caller not in visited:
                    visited.add(caller)
                    queue.append((caller, current_depth + 1))
        
        if direction in ["both", "callee"]:
            for callee in callees[current]:
                edges.append({
                    "source": current,
                    "target": callee,
                    "value": 1
                })
                node_set.add(callee)
                
                if callee not in visited:
                    visited.add(callee)
                    queue.append((callee, current_depth + 1))
    
    # 노드 리스트 생성
    for node_id in node_set:
        node_data = {
            "id": node_id,
            "label": node_id
        }
        
        # 모듈 정보 추가
        if show_modules and node_id in module_map:
            node_data["group"] = module_map[node_id]
        
        # 변경된 함수 표시
        if highlight_changes and node_id in changed_functions:
            node_data["changed"] = True
        
        # 중심 노드 강조
        if node_id == function_name:
            node_data["size"] = 10
        else:
            node_data["size"] = 5
        
        nodes.append(node_data)
    
    # 그래프 단순화 (옵션)
    if group_calls and len(nodes) > 20:
        nodes, edges = simplify_graph(nodes, edges, 0.2)
    
    return {
        "nodes": nodes,
        "links": edges
    }
