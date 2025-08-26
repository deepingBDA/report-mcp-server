"""
복잡한 차트 생성기 모듈
비교 분석 워크플로우에서 사용하는 특수 차트들
"""

from typing import List, Dict, Any, Tuple, Optional
import math
from .chart_base import BaseChart
from .color_utils import get_chart_colors, hex_to_rgb, interpolate_color


class ComparisonBarLineChart(BaseChart):
    """막대-라인 복합 차트 (전주/금주 비교 + 변화율)"""
    
    def __init__(self,
                 dates: List[str],
                 weekdays: List[str],
                 prev_visitors: List[int],
                 curr_visitors: List[int],
                 growth_rates: List[float],
                 site_name: str,
                 width: int = 1100,
                 height: int = 640,
                 padding: int = 100):
        """
        Args:
            dates: 날짜 리스트
            weekdays: 요일 리스트  
            prev_visitors: 전주 방문자 수
            curr_visitors: 금주 방문자 수
            growth_rates: 증감률
            site_name: 매장명
        """
        super().__init__(width, height, padding)
        self.dates = dates
        self.weekdays = weekdays
        self.prev_visitors = prev_visitors
        self.curr_visitors = curr_visitors
        self.growth_rates = growth_rates
        self.site_name = site_name
        
    def render(self) -> str:
        """차트를 렌더링합니다."""
        # 차트 영역 계산
        chart_width = self.width - 2 * self.padding
        chart_height = self.height - 2 * self.padding
        
        # UI 스케일 (기본 500 높이 기준) - 1.4배 확대
        ui_scale = max(0.8, chart_height / 500) * 1.4
        
        # 동적 Y축 스케일 계산 (방문자 수)
        visitor_min = min(min(self.prev_visitors), min(self.curr_visitors))
        visitor_max = max(max(self.prev_visitors), max(self.curr_visitors))
        visitor_range = max(1, visitor_max - visitor_min)
        visitor_padding = visitor_range * 0.1  # 10% 여백
        padded_min = visitor_min - visitor_padding
        padded_max = visitor_max + visitor_padding
        
        # Nice step 계산
        approx_step = max(1, (padded_max - padded_min) / 5)
        magnitude = 10 ** int(math.floor(math.log10(approx_step)))
        
        for m in (1, 2, 5, 10):
            nice_step = m * magnitude
            if nice_step >= approx_step:
                break
        
        ticks_min = int(math.floor(padded_min / nice_step) * nice_step)
        ticks_max = int(math.ceil(padded_max / nice_step) * nice_step) + int(nice_step)
        ticks_range = max(1, ticks_max - ticks_min)
        visitor_scale = chart_height / ticks_range
        
        # 증감률 Y축 스케일
        growth_min, growth_max = min(self.growth_rates), max(self.growth_rates)
        growth_range = max(0.1, growth_max - growth_min)
        growth_padding = growth_range * 0.1
        growth_scale_min = growth_min - growth_padding
        growth_scale_max = growth_max + growth_padding
        growth_scale_range = growth_scale_max - growth_scale_min
        growth_scale = chart_height / growth_scale_range
        
        # X축 스케일
        bar_offset = int(30 * ui_scale)
        x_origin = self.padding + bar_offset
        x_scale = (chart_width - 2 * bar_offset) / (len(self.dates) - 1) if len(self.dates) > 1 else (chart_width - 2 * bar_offset)
        
        # 막대 폭/간격
        bar_width = max(14, min(int(x_scale * 0.22), int(40 * ui_scale)))
        bar_gap = max(4, int(x_scale * 0.06))
        
        svg_elements = []
        
        # 매장명 제목
        svg_elements.append(
            f'<text x="{self.width//2}" y="{self.padding//2}" '
            f'font-size="{int(24*ui_scale)}" font-weight="bold" '
            f'text-anchor="middle" fill="#1f2937">{self.site_name}</text>'
        )
        
        # 그리드 라인 (방문자 수 기준)
        visitor_step = int(nice_step)
        for i in range(ticks_min, ticks_max + 1, visitor_step):
            y = self.padding + (1 - (i - ticks_min) / ticks_range) * chart_height
            
            # 그리드 라인
            svg_elements.append(
                f'<line x1="{self.padding}" y1="{y}" '
                f'x2="{self.width-self.padding}" y2="{y}" '
                f'stroke="#f3f4f6" stroke-width="{max(1,int(1*ui_scale))}" />'
            )
            
            # 좌측 Y축 눈금
            svg_elements.append(
                f'<line x1="{self.padding}" y1="{y}" '
                f'x2="{self.padding-10}" y2="{y}" '
                f'stroke="#6b7280" stroke-width="{max(1,int(1*ui_scale))}" />'
            )
            
            # 좌측 Y축 라벨
            svg_elements.append(
                f'<text x="{self.padding-14}" y="{y+4}" '
                f'font-size="{int(16*ui_scale)}" text-anchor="end" fill="#6b7280">{i}</text>'
            )
        
        # 0% 기준선 (변화율)
        if growth_min < 0 and growth_max > 0:
            zero_y = self.padding + (1 - (0 - (growth_min - growth_padding)) / (growth_range + 2 * growth_padding)) * chart_height
            svg_elements.append(
                f'<line x1="{self.padding}" y1="{zero_y}" '
                f'x2="{self.width-self.padding}" y2="{zero_y}" '
                f'stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="5,5" />'
            )
        
        # 변화율 Y축 눈금
        if growth_range > 0:
            growth_step = max(1, int(growth_range // 4))
            for i in range(int(growth_scale_min), int(growth_scale_max + 1), growth_step):
                y = self.padding + chart_height - (i - growth_scale_min) * growth_scale
                
                if self.padding <= y <= self.padding + chart_height:
                    tick_line_length = int(10 * ui_scale)
                    svg_elements.append(
                        f'<line x1="{self.width-self.padding}" y1="{y}" '
                        f'x2="{self.width-self.padding+tick_line_length}" y2="{y}" '
                        f'stroke="#6b7280" stroke-width="{max(1,int(1*ui_scale))}" />'
                    )
                    
                    label_offset = int(14 * ui_scale)
                    svg_elements.append(
                        f'<text x="{self.width-self.padding+label_offset}" y="{y+4}" '
                        f'font-size="{int(15*ui_scale)}" text-anchor="start" fill="#6b7280">{i}%</text>'
                    )
        
        # 막대그래프 그리기
        for i, (date_str, weekday) in enumerate(zip(self.dates, self.weekdays)):
            x_center = x_origin + i * x_scale
            
            # 전주 막대 (파란색)
            prev_height = (self.prev_visitors[i] - ticks_min) * visitor_scale
            prev_y = self.padding + chart_height - prev_height
            prev_x = x_center - (bar_gap//2) - bar_width
            
            svg_elements.append(
                f'<rect x="{prev_x}" y="{prev_y}" width="{bar_width}" height="{prev_height}" '
                f'fill="#93c5fd" stroke="#3b82f6" stroke-width="{max(1,int(2*ui_scale))}" />'
            )
            svg_elements.append(
                f'<text x="{prev_x + bar_width/2}" y="{prev_y-8}" '
                f'font-size="{int(16*ui_scale)}" text-anchor="middle" '
                f'fill="#1f2937" font-weight="bold">{self.prev_visitors[i]}</text>'
            )
            
            # 금주 막대 (빨간색)
            curr_height = (self.curr_visitors[i] - ticks_min) * visitor_scale
            curr_y = self.padding + chart_height - curr_height
            curr_x = x_center + (bar_gap//2)
            
            svg_elements.append(
                f'<rect x="{curr_x}" y="{curr_y}" width="{bar_width}" height="{curr_height}" '
                f'fill="#fca5a5" stroke="#ef4444" stroke-width="{max(1,int(2*ui_scale))}" />'
            )
            svg_elements.append(
                f'<text x="{curr_x + bar_width/2}" y="{curr_y-8}" '
                f'font-size="{int(16*ui_scale)}" text-anchor="middle" '
                f'fill="#1f2937" font-weight="bold">{self.curr_visitors[i]}</text>'
            )
            
            # X축 라벨 (날짜 + 요일)
            svg_elements.append(
                f'<text x="{x_center}" y="{self.height-self.padding+25}" '
                f'font-size="{int(18*ui_scale)}" text-anchor="middle" fill="#6b7280">'
                f'{date_str}<tspan x="{x_center}" dy="{int(25*ui_scale)}">{weekday}</tspan></text>'
            )
        
        # 변화율 선 그래프 (초록색)
        points = []
        for i, rate in enumerate(self.growth_rates):
            x = x_origin + i * x_scale
            y = self.padding + chart_height - (rate - growth_scale_min) * growth_scale
            points.append(f"{x},{y}")
            
            # 변화율 라벨
            rate_text = f"+{rate:.1f}%" if rate > 0 else f"{rate:.1f}%"
            svg_elements.append(
                f'<text x="{x}" y="{y-15}" '
                f'font-size="{int(14*ui_scale)}" text-anchor="middle" '
                f'fill="#dc2626" font-weight="bold">{rate_text}</text>'
            )
        
        if len(points) > 1:
            # 선 그래프
            path_d = " ".join(points)
            svg_elements.append(
                f'<polyline fill="none" stroke="#10b981" '
                f'stroke-width="{max(2,int(3*ui_scale))}" points="{path_d}" />'
            )
            
            # 원형 마커
            for point in points:
                x, y = map(float, point.split(','))
                svg_elements.append(
                    f'<circle cx="{x}" cy="{y}" r="{int(4*ui_scale)}" '
                    f'fill="#10b981" stroke="#065f46" stroke-width="{max(1,int(1*ui_scale))}" />'
                )
        
        # Y축 라벨
        svg_elements.append(
            f'<text x="30" y="{self.height//2}" '
            f'font-size="{int(18*ui_scale)}" text-anchor="middle" fill="#6b7280" '
            f'transform="rotate(-90, 30, {self.height//2})">방문자 수(명)</text>'
        )
        svg_elements.append(
            f'<text x="{self.width-30}" y="{self.height//2}" '
            f'font-size="{int(18*ui_scale)}" text-anchor="middle" fill="#6b7280" '
            f'transform="rotate(90, {self.width-30}, {self.height//2})">변화율(%)</text>'
        )
        
        # 차트 테두리
        svg_elements.append(
            f'<rect x="{self.padding}" y="{self.padding}" '
            f'width="{chart_width}" height="{chart_height}" '
            f'fill="none" stroke="#e5e7eb" stroke-width="{max(1,int(2*ui_scale))}" rx="{int(4*ui_scale)}" />'
        )
        
        # 범례 추가
        self._add_legends(svg_elements, ui_scale)
        
        return self._create_svg_wrapper('\n'.join(svg_elements))
    
    def _add_legends(self, svg_elements: List[str], ui_scale: float):
        """범례를 추가합니다."""
        # 변화율 범례 - 차트 안 우상단
        category_y = self.padding + int(6*ui_scale)
        cat_w = int(70*ui_scale)
        cat_h = int(24*ui_scale)
        category_x = self.padding + self.chart_width - cat_w - int(6*ui_scale)
        
        svg_elements.extend([
            f'<rect x="{category_x}" y="{category_y}" width="{cat_w}" height="{cat_h}" '
            f'fill="#f9fafb" stroke="#e5e7eb" rx="4" />',
            f'<line x1="{category_x+int(8*ui_scale)}" y1="{category_y+cat_h//2}" '
            f'x2="{category_x+int(22*ui_scale)}" y2="{category_y+cat_h//2}" '
            f'stroke="#10b981" stroke-width="{max(2,int(3*ui_scale))}" />',
            f'<text x="{category_x+int(30*ui_scale)}" y="{category_y+int(0.67*cat_h)}" '
            f'font-size="{int(14*ui_scale)}" fill="#374151">변화율</text>'
        ])
        
        # 전주/금주 범례 - 차트 안 좌상단
        legend_y = self.padding + int(6*ui_scale)
        legend_x = self.padding + int(6*ui_scale)
        leg_w = int(96*ui_scale)
        leg_h = int(24*ui_scale)
        
        svg_elements.extend([
            f'<rect x="{legend_x}" y="{legend_y}" width="{leg_w}" height="{leg_h}" '
            f'fill="#f9fafb" stroke="#e5e7eb" rx="4" />',
            f'<rect x="{legend_x+int(6*ui_scale)}" y="{legend_y+int(6*ui_scale)}" '
            f'width="{int(10*ui_scale)}" height="{int(10*ui_scale)}" '
            f'fill="#93c5fd" stroke="#3b82f6" stroke-width="0.5" />',
            f'<text x="{legend_x+int(20*ui_scale)}" y="{legend_y+int(0.65*leg_h)}" '
            f'font-size="{int(13*ui_scale)}" fill="#374151">전주</text>',
            f'<rect x="{legend_x+int(52*ui_scale)}" y="{legend_y+int(6*ui_scale)}" '
            f'width="{int(10*ui_scale)}" height="{int(10*ui_scale)}" '
            f'fill="#fca5a5" stroke="#ef4444" stroke-width="0.5" />',
            f'<text x="{legend_x+int(66*ui_scale)}" y="{legend_y+int(0.65*leg_h)}" '
            f'font-size="{int(13*ui_scale)}" fill="#374151">금주</text>'
        ])


class HeatmapChart(BaseChart):
    """히트맵 차트"""
    
    def __init__(self,
                 data_a: List[List[int]],
                 data_b: List[List[int]],
                 x_labels: List[str],
                 y_labels: List[str],
                 title_a: str = "A",
                 title_b: str = "B",
                 width: int = 1100,
                 height: int = 520,
                 padding: int = 60):
        """
        Args:
            data_a: 첫 번째 히트맵 데이터
            data_b: 두 번째 히트맵 데이터
            x_labels: X축 라벨 (시간대 등)
            y_labels: Y축 라벨 (연령대 등)
            title_a: 첫 번째 히트맵 제목
            title_b: 두 번째 히트맵 제목
        """
        super().__init__(width, height, padding)
        self.data_a = data_a
        self.data_b = data_b
        self.x_labels = x_labels
        self.y_labels = y_labels
        self.title_a = title_a
        self.title_b = title_b
    
    def render(self) -> str:
        """히트맵을 렌더링합니다."""
        # 히트맵 영역 계산
        heatmap_width = self.width - 2 * self.padding
        heatmap_height = self.height - 2 * self.padding
        
        # 셀 크기 계산
        cell_width = heatmap_width / len(self.x_labels)
        cell_height = heatmap_height / len(self.y_labels)
        rect_w = cell_width / 2
        
        # UI 스케일
        ui_scale = max(0.8, min(cell_width, cell_height) / 50) * 1.2
        
        svg_elements = []
        
        # 첫 번째 히트맵 그리기
        self._draw_heatmap(svg_elements, self.data_a, 0, rect_w, cell_height)
        
        # 두 번째 히트맵 그리기
        self._draw_heatmap(svg_elements, self.data_b, self.width//2, rect_w, cell_height)
        
        # X축 라벨 (시간대)
        for i, label in enumerate(self.x_labels):
            if i % 3 == 0:  # 3시간 간격 라벨만 표시
                x = self.padding + (i * rect_w) + rect_w/2
                y = self.height - self.padding + 18
                
                svg_elements.append(
                    f'<text x="{x}" y="{y}" font-size="{int(12*ui_scale)}" '
                    f'text-anchor="middle" fill="#6b7280">{label}</text>'
                )
                
                x_b = self.padding + self.width//2 + (i * rect_w) + rect_w/2
                svg_elements.append(
                    f'<text x="{x_b}" y="{y}" font-size="{int(12*ui_scale)}" '
                    f'text-anchor="middle" fill="#6b7280">{label}</text>'
                )
        
        # Y축 라벨 (연령대)
        for j, label in enumerate(self.y_labels):
            x = self.padding - 10
            y = self.padding + (j * cell_height) + cell_height//2 + 4
            svg_elements.append(
                f'<text x="{x}" y="{y}" font-size="{int(14*ui_scale)}" '
                f'text-anchor="end" fill="#6b7280">{label}</text>'
            )
        
        # 제목
        svg_elements.append(
            f'<text x="{self.width//4}" y="{self.padding//2}" '
            f'font-size="{int(16*ui_scale)}" font-weight="bold" '
            f'text-anchor="middle" fill="#1f2937">{self.title_a}</text>'
        )
        svg_elements.append(
            f'<text x="{self.width*3//4}" y="{self.padding//2}" '
            f'font-size="{int(16*ui_scale)}" font-weight="bold" '
            f'text-anchor="middle" fill="#1f2937">{self.title_b}</text>'
        )
        
        # 차트 테두리
        svg_elements.append(
            f'<rect x="{self.padding}" y="{self.padding}" '
            f'width="{heatmap_width//2}" height="{heatmap_height}" '
            f'fill="none" stroke="#e5e7eb" stroke-width="{max(1,int(2*ui_scale))}" rx="4" />'
        )
        svg_elements.append(
            f'<rect x="{self.padding + self.width//2}" y="{self.padding}" '
            f'width="{heatmap_width//2}" height="{heatmap_height}" '
            f'fill="none" stroke="#e5e7eb" stroke-width="{max(1,int(2*ui_scale))}" rx="4" />'
        )
        
        return self._create_svg_wrapper('\n'.join(svg_elements))
    
    def _draw_heatmap(self, svg_elements: List[str], data: List[List[int]], 
                     x_offset: int, rect_w: float, cell_height: float):
        """하나의 히트맵을 그립니다."""
        # 최대값 계산
        max_value = max(max(row) for row in data) if data else 1
        
        for i in range(len(self.x_labels)):
            for j in range(len(self.y_labels)):
                x = self.padding + x_offset + (i * rect_w)
                y = self.padding + (j * cell_height)
                
                # 값에 따른 색상 계산
                value = data[i][j] if i < len(data) and j < len(data[i]) else 0
                intensity = value / max_value if max_value else 0
                
                # 색상 보간: hot(#741443) ↔ mid(#E48356) ↔ cool(#FFFFFF)
                color = self._get_heatmap_color(intensity)
                
                svg_elements.append(
                    f'<rect x="{x}" y="{y}" width="{rect_w}" height="{cell_height}" '
                    f'fill="{color}" />'
                )
    
    def _get_heatmap_color(self, intensity: float) -> str:
        """히트맵 색상을 계산합니다."""
        def hex_to_rgb(h):
            h = h.lstrip('#')
            return tuple(int(h[k:k+2], 16) for k in (0, 2, 4))
        
        def lerp(a, b, t):
            return int(a + (b - a) * t)
        
        hot = hex_to_rgb('#741443')
        mid = hex_to_rgb('#E48356')
        cool = hex_to_rgb('#FFFFFF')
        
        if intensity <= 0.5:
            t = intensity * 2
            r = lerp(hot[0], mid[0], t)
            g = lerp(hot[1], mid[1], t)
            b = lerp(hot[2], mid[2], t)
        else:
            t = (intensity - 0.5) * 2
            r = lerp(mid[0], cool[0], t)
            g = lerp(mid[1], cool[1], t)
            b = lerp(mid[2], cool[2], t)
        
        return f"rgb({r},{g},{b})"