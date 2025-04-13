#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 그래프 위젯
호출 그래프 시각화를 위한 커스텀 위젯
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import json
import os
import tempfile

class GraphWidget(QWidget):
    """그래프 위젯 클래스"""
    
    # 노드 선택 시그널
    node_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 웹 엔진 뷰 생성
        self.web_view = QWebEngineView()
        
        # 기본 HTML 템플릿 로드
        self.load_template()
        
        layout.addWidget(self.web_view)
        self.setLayout(layout)
    
    def load_template(self):
        """그래프 템플릿 로드"""
        # 템플릿 디렉토리 생성
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        template_dir = os.path.join(base_dir, "resources", "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        # 내장 D3.js 기반 그래프 HTML 템플릿 생성
        template_path = os.path.join(template_dir, "force_directed_graph.html")
        
        # 파일이 없으면 생성
        if not os.path.exists(template_path):
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(self.get_graph_template())
        
        # 템플릿 로드
        self.web_view.load(QUrl.fromLocalFile(template_path))
        
        # 노드 선택 이벤트 연결
        self.web_view.page().runJavaScript(
            """
            window.addEventListener('message', function(event) {
                if (event.data.type === 'nodeSelected') {
                    new QWebChannel(qt.webChannelTransport, function(channel) {
                        channel.objects.handler.handleNodeSelected(event.data.nodeId);
                    });
                }
            });
            """
        )
    
    def set_graph_data(self, graph_data):
        """그래프 데이터 설정"""
        # 그래프 데이터가 없으면 무시
        if not graph_data:
            return
        
        # JSON으로 직렬화
        graph_json = json.dumps(graph_data)
        
        # JavaScript로 데이터 전달
        js_code = f"if (typeof updateGraph === 'function') {{ updateGraph({graph_json}); }}"
        self.web_view.page().runJavaScript(js_code)
    
    def on_node_selected(self, node_id):
        """노드 선택 이벤트 처리"""
        # 시그널 발생
        self.node_selected.emit(node_id)
    
    def export_as_image(self, file_path):
        """그래프를 이미지로 내보내기"""
        # TODO: 그래프 이미지 내보내기 구현
        pass
    
    def get_graph_template(self):
        """D3.js 기반 그래프 HTML 템플릿 반환"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>CodeGuardian Call Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            overflow: hidden;
        }
        .node {
            cursor: pointer;
        }
        .node circle {
            stroke: #fff;
            stroke-width: 1.5px;
        }
        .node text {
            font-size: 10px;
            pointer-events: none;
        }
        .link {
            fill: none;
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 1.5px;
        }
        .changed {
            fill: #ff7f7f;
        }
        .tooltip {
            position: absolute;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #ddd;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
        }
    </style>
</head>
<body>
    <svg width="100%" height="100%"></svg>
    <div class="tooltip"></div>

    <script>
    let svg = d3.select("svg");
    let width = window.innerWidth;
    let height = window.innerHeight;
    let tooltip = d3.select(".tooltip");
    
    // 그래프 시뮬레이션 설정
    let simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(60));
    
    // 확대/축소 설정
    let zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on("zoom", (event) => {
            container.attr("transform", event.transform);
        });
    
    svg.call(zoom);
    
    // 그래프 요소 컨테이너
    let container = svg.append("g");
    
    // 그래프 업데이트 함수
    function updateGraph(graph) {
        // 기존 요소 제거
        container.selectAll(".link").remove();
        container.selectAll(".node").remove();
        
        // 링크 생성
        let link = container.selectAll(".link")
            .data(graph.links)
            .enter().append("line")
            .attr("class", "link")
            .attr("marker-end", "url(#arrowhead)")
            .style("stroke-width", d => Math.sqrt(d.value || 1) * 1.5);
        
        // 노드 생성
        let node = container.selectAll(".node")
            .data(graph.nodes)
            .enter().append("g")
            .attr("class", "node")
            .on("click", (event, d) => {
                // 노드 선택 이벤트 발생
                window.postMessage({ 
                    type: 'nodeSelected', 
                    nodeId: d.id 
                }, '*');
                
                // 노드 하이라이트
                node.select("circle")
                    .style("stroke", n => n.id === d.id ? "#f00" : "#fff")
                    .style("stroke-width", n => n.id === d.id ? 3 : 1.5);
            })
            .on("mouseover", (event, d) => {
                // 툴팁 표시
                tooltip.html(`<strong>${d.id}</strong><br/>${d.group || 'Module: Unknown'}`);
                tooltip.style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px")
                    .style("opacity", 1);
            })
            .on("mouseout", () => {
                // 툴팁 숨기기
                tooltip.style("opacity", 0);
            })
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // 노드 원 추가
        node.append("circle")
            .attr("r", d => (d.size || 5) * 2)
            .attr("class", d => d.changed ? "changed" : "")
            .style("fill", d => color(d.group));
        
        // 노드 텍스트 추가
        node.append("text")
            .attr("dy", ".3em")
            .attr("x", d => (d.size || 5) * 2 + 5)
            .text(d => d.label || d.id);
        
        // 시뮬레이션 업데이트
        simulation.nodes(graph.nodes)
            .on("tick", ticked);
        
        simulation.force("link")
            .links(graph.links);
        
        // 시뮬레이션 재시작
        simulation.alpha(1).restart();
        
        // tick 함수 (매 프레임마다 요소 위치 업데이트)
        function ticked() {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("transform", d => `translate(${d.x},${d.y})`);
        }
        
        // 드래그 이벤트 핸들러
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }
        
        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }
        
        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }
    }
    
    // 색상 스케일
    const color = d3.scaleOrdinal(d3.schemeCategory10);
    
    // 창 크기 변경 시 그래프 크기 조정
    window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
        simulation.force("center", d3.forceCenter(width / 2, height / 2));
        simulation.alpha(1).restart();
    });
    </script>
</body>
</html>
"""
