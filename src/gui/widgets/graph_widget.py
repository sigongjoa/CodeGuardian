#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CodeGuardian 그래프 위젯
호출 그래프 시각화를 위한 커스텀 위젯
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
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
        self.zoom_level = 1.0
        
    def init_ui(self):
        """UI 초기화"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 웹 엔진 뷰 생성
        self.web_view = QWebEngineView()
        
        # 기본 HTML 템플릿 로드
        self.load_template()
        
        # 줌 컨트롤 패널
        zoom_panel = QHBoxLayout()
        
        # 줌 슬라이더
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 200)  # 10% ~ 200%
        self.zoom_slider.setValue(100)      # 초기값 100%
        self.zoom_slider.setTracking(True)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        
        # 줌 레이블
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; padding: 2px;")
        
        # 줌 버튼
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(30, 30)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(30, 30)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        
        self.zoom_reset_btn = QPushButton("100%")
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        
        # 패널에 컨트롤 추가
        zoom_panel.addWidget(self.zoom_out_btn)
        zoom_panel.addWidget(self.zoom_slider)
        zoom_panel.addWidget(self.zoom_in_btn)
        zoom_panel.addWidget(self.zoom_label)
        zoom_panel.addWidget(self.zoom_reset_btn)
        
        # 레이아웃에 위젯 추가
        main_layout.addWidget(self.web_view)
        main_layout.addLayout(zoom_panel)
        
        self.setLayout(main_layout)
    
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
    
    def zoom_in(self):
        """줌 인"""
        new_zoom = min(self.zoom_level * 1.2, 2.0)
        self.set_zoom_level(new_zoom)
    
    def zoom_out(self):
        """줌 아웃"""
        new_zoom = max(self.zoom_level * 0.8, 0.1)
        self.set_zoom_level(new_zoom)
    
    def zoom_reset(self):
        """줌 리셋"""
        self.set_zoom_level(1.0)
    
    def on_zoom_slider_changed(self, value):
        """줌 슬라이더 변경 이벤트 처리"""
        zoom_level = value / 100.0
        self.set_zoom_level(zoom_level, update_slider=False)
    
    def set_zoom_level(self, level, update_slider=True):
        """줌 레벨 설정"""
        self.zoom_level = level
        
        # 레이블 업데이트
        zoom_percentage = int(level * 100)
        self.zoom_label.setText(f"{zoom_percentage}%")
        
        # 슬라이더 업데이트 (슬라이더가 변경되지 않았을 때만)
        if update_slider:
            self.zoom_slider.setValue(zoom_percentage)
        
        # JavaScript로 줌 레벨 전달
        js_code = f"if (typeof setZoom === 'function') {{ setZoom({level}); }}"
        self.web_view.page().runJavaScript(js_code)
    
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
            background-color: #fafafa;
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
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
        }
        .zoom-controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 5px;
            background: rgba(255, 255, 255, 0.8);
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #ddd;
            box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
        }
        .zoom-btn {
            width: 30px;
            height: 30px;
            font-size: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: white;
            border: 1px solid #ccc;
            border-radius: 3px;
            cursor: pointer;
        }
        .zoom-btn:hover {
            background: #f0f0f0;
        }
        .module-legend {
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            font-size: 12px;
            max-width: 200px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }
        .legend-color {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-right: 8px;
        }
        /* 그래프가 없을 때 표시할 가이드 메시지 */
        .empty-message {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
            color: #666;
            max-width: 80%;
        }
        .empty-message h3 {
            margin-bottom: 10px;
            color: #333;
        }
        .empty-message p {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <svg width="100%" height="100%"></svg>
    <div class="tooltip"></div>
    <div class="module-legend" style="display: none;">
        <h4 style="margin-top: 0; margin-bottom: 10px;">모듈 범례</h4>
        <div id="legend-items"></div>
    </div>
    
    <div class="empty-message">
        <h3>CodeGuardian 호출 그래프</h3>
        <p>함수 호출 관계를 시각적으로 확인할 수 있습니다.<br>
           왼쪽 패널에서 함수를 선택하고 '그래프 생성' 버튼을 클릭하세요.</p>
    </div>

    <script>
    let svg = d3.select("svg");
    let width = window.innerWidth;
    let height = window.innerHeight;
    let tooltip = d3.select(".tooltip");
    let legendDiv = d3.select(".module-legend");
    let emptyMessage = d3.select(".empty-message");
    
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
    
    // 마커 정의 (화살표)
    svg.append("defs").append("marker")
        .attr("id", "arrowhead")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 20)
        .attr("refY", 0)
        .attr("orient", "auto")
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .append("path")
        .attr("d", "M0,-5L10,0L0,5")
        .attr("fill", "#999");
    
    // 확대/축소 레벨 설정 함수
    function setZoom(level) {
        // 현재 transform 가져오기
        let transform = d3.zoomTransform(svg.node());
        
        // 현재 translate 유지하고 scale만 변경
        let newTransform = d3.zoomIdentity
            .translate(transform.x, transform.y)
            .scale(level);
        
        // 애니메이션으로 확대/축소 적용
        svg.transition()
            .duration(300)
            .call(zoom.transform, newTransform);
    }
    
    // 그래프 업데이트 함수
    function updateGraph(graph) {
        // 그래프 데이터가 없으면 빈 메시지 표시
        if (!graph || !graph.nodes || !graph.links || graph.nodes.length === 0) {
            emptyMessage.style("display", "block");
            legendDiv.style("display", "none");
            return;
        }
        
        // 빈 메시지 숨기기
        emptyMessage.style("display", "none");
        
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
                tooltip.html(`<strong>${d.label || d.id}</strong><br>${d.group ? '모듈: ' + d.group : '모듈: 알 수 없음'}`);
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
        
        // 모듈 그룹 색상 매핑
        const moduleGroups = [...new Set(graph.nodes.map(d => d.group))];
        const color = d3.scaleOrdinal(d3.schemeCategory10).domain(moduleGroups);
        
        // 모듈 범례 생성
        const legendItems = d3.select("#legend-items");
        legendItems.html("");  // 기존 내용 삭제
        
        moduleGroups.forEach(group => {
            if (!group) return;  // 그룹이 없는 경우 무시
            
            const item = legendItems.append("div")
                .attr("class", "legend-item");
            
            item.append("div")
                .attr("class", "legend-color")
                .style("background-color", color(group));
            
            item.append("span")
                .text(group);
        });
        
        // 범례 표시 (모듈이 2개 이상일 때만)
        if (moduleGroups.length > 1) {
            legendDiv.style("display", "block");
        } else {
            legendDiv.style("display", "none");
        }
        
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
        
        // 그래프가 로드되면 전체 그래프가 보이도록 자동 조정
        autoFitGraph();
        
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
    
    // 그래프를 화면에 맞게 자동 조정
    function autoFitGraph() {
        // 노드가 없으면 무시
        if (!simulation.nodes().length) return;
        
        // 시뮬레이션이 안정화될 때까지 대기
        setTimeout(() => {
            // 모든 노드의 경계 계산
            const nodeElements = container.selectAll(".node").nodes();
            if (!nodeElements.length) return;
            
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            
            simulation.nodes().forEach(d => {
                minX = Math.min(minX, d.x);
                minY = Math.min(minY, d.y);
                maxX = Math.max(maxX, d.x);
                maxY = Math.max(maxY, d.y);
            });
            
            // 패딩 추가
            const padding = 50;
            minX -= padding;
            minY -= padding;
            maxX += padding;
            maxY += padding;
            
            // 그래프 너비, 높이 계산
            const graphWidth = maxX - minX;
            const graphHeight = maxY - minY;
            
            // 화면 비율에 맞는 스케일 계산
            const scaleX = width / graphWidth;
            const scaleY = height / graphHeight;
            const scale = Math.min(scaleX, scaleY, 1.5); // 너무 크게 확대되지 않도록 제한
            
            // 가운데 정렬을 위한 이동 계산
            const centerX = (minX + maxX) / 2;
            const centerY = (minY + maxY) / 2;
            
            // transform 적용
            const transform = d3.zoomIdentity
                .translate(width / 2, height / 2)
                .scale(scale)
                .translate(-centerX, -centerY);
            
            svg.transition()
                .duration(500)
                .call(zoom.transform, transform);
        }, 1000); // 시뮬레이션이 어느정도 안정화될 시간
    }
    
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
