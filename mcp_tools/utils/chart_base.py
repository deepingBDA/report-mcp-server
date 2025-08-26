"""
차트 생성을 위한 기본 클래스 및 유틸리티
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import math


class BaseChart(ABC):
    """모든 차트의 기본 클래스"""
    
    def __init__(self, width: int = 800, height: int = 400, padding: int = 50):
        """
        Args:
            width: 차트 전체 너비
            height: 차트 전체 높이
            padding: 차트 여백
        """
        self.width = width
        self.height = height
        self.padding = padding
        
        # 실제 차트 영역 계산
        self.chart_width = width - 2 * padding
        self.chart_height = height - 2 * padding
        
        # SVG 요소들을 저장할 리스트
        self.svg_elements = []
        
    @abstractmethod
    def render(self) -> str:
        """차트를 SVG 문자열로 렌더링합니다."""
        pass
    
    def _create_svg_wrapper(self, content: str) -> str:
        """SVG 컨테이너를 생성합니다."""
        return f"""
<svg width="{self.width}" height="{self.height}" 
     viewBox="0 0 {self.width} {self.height}" 
     xmlns="http://www.w3.org/2000/svg" 
     style="background: white;">
    {content}
</svg>
"""
    
    def _add_title(self, title: str, y: Optional[int] = None, font_size: int = 24):
        """차트 제목을 추가합니다."""
        if y is None:
            y = self.padding // 2
        
        self.svg_elements.append(
            f'<text x="{self.width//2}" y="{y}" '
            f'font-size="{font_size}" font-weight="bold" '
            f'text-anchor="middle" fill="#1f2937">{title}</text>'
        )
    
    def _add_grid_lines(self, 
                       x_ticks: Optional[List[float]] = None,
                       y_ticks: Optional[List[float]] = None,
                       show_x_grid: bool = True,
                       show_y_grid: bool = True):
        """그리드 라인을 추가합니다."""
        if show_y_grid and y_ticks:
            for y in y_ticks:
                self.svg_elements.append(
                    f'<line x1="{self.padding}" y1="{y}" '
                    f'x2="{self.width - self.padding}" y2="{y}" '
                    f'stroke="#f3f4f6" stroke-width="1" />'
                )
        
        if show_x_grid and x_ticks:
            for x in x_ticks:
                self.svg_elements.append(
                    f'<line x1="{x}" y1="{self.padding}" '
                    f'x2="{x}" y2="{self.height - self.padding}" '
                    f'stroke="#f3f4f6" stroke-width="1" />'
                )
    
    def _add_axis_labels(self, 
                        x_label: Optional[str] = None,
                        y_label: Optional[str] = None,
                        font_size: int = 14):
        """축 라벨을 추가합니다."""
        if x_label:
            self.svg_elements.append(
                f'<text x="{self.width//2}" '
                f'y="{self.height - 10}" '
                f'font-size="{font_size}" text-anchor="middle" '
                f'fill="#6b7280">{x_label}</text>'
            )
        
        if y_label:
            self.svg_elements.append(
                f'<text x="30" y="{self.height//2}" '
                f'font-size="{font_size}" text-anchor="middle" '
                f'fill="#6b7280" transform="rotate(-90, 30, {self.height//2})">'
                f'{y_label}</text>'
            )
    
    def _add_legend(self, 
                   items: List[Tuple[str, str]],  # [(color, label), ...]
                   x: Optional[int] = None,
                   y: Optional[int] = None):
        """범례를 추가합니다."""
        if x is None:
            x = self.padding + 10
        if y is None:
            y = self.padding + 10
        
        box_size = 12
        gap = 20
        
        for i, (color, label) in enumerate(items):
            item_y = y + i * gap
            self.svg_elements.append(
                f'<rect x="{x}" y="{item_y}" '
                f'width="{box_size}" height="{box_size}" '
                f'fill="{color}" />'
            )
            self.svg_elements.append(
                f'<text x="{x + box_size + 5}" y="{item_y + box_size - 2}" '
                f'font-size="12" fill="#374151">{label}</text>'
            )
    
    def _calculate_nice_scale(self, min_val: float, max_val: float, 
                            tick_count: int = 5) -> Tuple[float, float, float]:
        """보기 좋은 축 스케일을 계산합니다.
        
        Returns:
            (min, max, step) 튜플
        """
        if min_val == max_val:
            return min_val - 1, max_val + 1, 1
        
        range_val = max_val - min_val
        
        # 여백 추가
        padding = range_val * 0.1
        padded_min = min_val - padding
        padded_max = max_val + padding
        
        # Nice step 계산
        rough_step = (padded_max - padded_min) / tick_count
        magnitude = 10 ** math.floor(math.log10(rough_step))
        
        for multiplier in [1, 2, 5, 10]:
            nice_step = multiplier * magnitude
            if nice_step >= rough_step:
                break
        
        # Nice bounds 계산
        nice_min = math.floor(padded_min / nice_step) * nice_step
        nice_max = math.ceil(padded_max / nice_step) * nice_step
        
        return nice_min, nice_max, nice_step


class BarChart(BaseChart):
    """막대 차트 클래스"""
    
    def __init__(self, 
                 data: List[Dict[str, Any]],
                 x_field: str,
                 y_fields: List[str],
                 colors: Optional[List[str]] = None,
                 **kwargs):
        """
        Args:
            data: 차트 데이터
            x_field: X축 필드명
            y_fields: Y축 필드명 리스트
            colors: 막대 색상 리스트
        """
        super().__init__(**kwargs)
        self.data = data
        self.x_field = x_field
        self.y_fields = y_fields
        self.colors = colors or ['#3b82f6', '#ef4444', '#10b981']
        
    def render(self) -> str:
        """막대 차트를 렌더링합니다."""
        if not self.data:
            return self._create_svg_wrapper("")
        
        # Y축 범위 계산
        all_values = []
        for item in self.data:
            for field in self.y_fields:
                if field in item and item[field] is not None:
                    all_values.append(item[field])
        
        if not all_values:
            return self._create_svg_wrapper("")
        
        y_min, y_max, y_step = self._calculate_nice_scale(min(all_values), max(all_values))
        
        # X축 스케일 계산
        x_count = len(self.data)
        x_scale = self.chart_width / x_count
        
        # 막대 너비 계산
        bar_width = x_scale * 0.8 / len(self.y_fields)
        bar_gap = x_scale * 0.1
        
        # Y축 스케일
        y_scale = self.chart_height / (y_max - y_min)
        
        # 그리드 그리기
        y_ticks = []
        for i in range(int((y_max - y_min) / y_step) + 1):
            y_val = y_min + i * y_step
            y_pos = self.padding + self.chart_height - (y_val - y_min) * y_scale
            y_ticks.append(y_pos)
            
            # Y축 라벨
            self.svg_elements.append(
                f'<text x="{self.padding - 10}" y="{y_pos + 4}" '
                f'font-size="12" text-anchor="end" fill="#6b7280">'
                f'{y_val:.0f}</text>'
            )
        
        self._add_grid_lines(y_ticks=y_ticks, show_x_grid=False)
        
        # 막대 그리기
        for i, item in enumerate(self.data):
            x_center = self.padding + (i + 0.5) * x_scale
            
            for j, field in enumerate(self.y_fields):
                if field not in item or item[field] is None:
                    continue
                
                value = item[field]
                bar_height = (value - y_min) * y_scale
                
                x_pos = x_center - (len(self.y_fields) * bar_width) / 2 + j * bar_width
                y_pos = self.padding + self.chart_height - bar_height
                
                color = self.colors[j % len(self.colors)]
                
                self.svg_elements.append(
                    f'<rect x="{x_pos}" y="{y_pos}" '
                    f'width="{bar_width}" height="{bar_height}" '
                    f'fill="{color}" />'
                )
                
                # 값 라벨
                self.svg_elements.append(
                    f'<text x="{x_pos + bar_width/2}" y="{y_pos - 5}" '
                    f'font-size="10" text-anchor="middle" fill="#1f2937">'
                    f'{value:.0f}</text>'
                )
            
            # X축 라벨
            x_label = item.get(self.x_field, "")
            self.svg_elements.append(
                f'<text x="{x_center}" y="{self.height - self.padding + 20}" '
                f'font-size="12" text-anchor="middle" fill="#6b7280">'
                f'{x_label}</text>'
            )
        
        # 차트 테두리
        self.svg_elements.append(
            f'<rect x="{self.padding}" y="{self.padding}" '
            f'width="{self.chart_width}" height="{self.chart_height}" '
            f'fill="none" stroke="#e5e7eb" stroke-width="2" />'
        )
        
        return self._create_svg_wrapper('\n'.join(self.svg_elements))


class LineChart(BaseChart):
    """라인 차트 클래스"""
    
    def __init__(self,
                 x_values: List[Any],
                 y_series: Dict[str, List[float]],  # {series_name: values}
                 colors: Optional[Dict[str, str]] = None,
                 **kwargs):
        """
        Args:
            x_values: X축 값들
            y_series: Y축 시리즈 데이터
            colors: 시리즈별 색상
        """
        super().__init__(**kwargs)
        self.x_values = x_values
        self.y_series = y_series
        self.colors = colors or {}
        
        # 기본 색상 설정
        default_colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
        for i, series_name in enumerate(y_series.keys()):
            if series_name not in self.colors:
                self.colors[series_name] = default_colors[i % len(default_colors)]
    
    def render(self) -> str:
        """라인 차트를 렌더링합니다."""
        if not self.x_values or not self.y_series:
            return self._create_svg_wrapper("")
        
        # Y축 범위 계산
        all_values = []
        for values in self.y_series.values():
            all_values.extend([v for v in values if v is not None])
        
        if not all_values:
            return self._create_svg_wrapper("")
        
        y_min, y_max, y_step = self._calculate_nice_scale(min(all_values), max(all_values))
        
        # 스케일 계산
        x_scale = self.chart_width / (len(self.x_values) - 1) if len(self.x_values) > 1 else self.chart_width
        y_scale = self.chart_height / (y_max - y_min)
        
        # 그리드 및 축 그리기
        self._draw_grid_and_axes(y_min, y_max, y_step, y_scale)
        
        # 각 시리즈 그리기
        for series_name, values in self.y_series.items():
            self._draw_series(series_name, values, x_scale, y_scale, y_min)
        
        # X축 라벨
        self._draw_x_labels(x_scale)
        
        # 차트 테두리
        self.svg_elements.append(
            f'<rect x="{self.padding}" y="{self.padding}" '
            f'width="{self.chart_width}" height="{self.chart_height}" '
            f'fill="none" stroke="#e5e7eb" stroke-width="2" />'
        )
        
        return self._create_svg_wrapper('\n'.join(self.svg_elements))
    
    def _draw_grid_and_axes(self, y_min: float, y_max: float, y_step: float, y_scale: float):
        """그리드와 축을 그립니다."""
        y_ticks = []
        for i in range(int((y_max - y_min) / y_step) + 1):
            y_val = y_min + i * y_step
            y_pos = self.padding + self.chart_height - (y_val - y_min) * y_scale
            y_ticks.append(y_pos)
            
            # Y축 라벨
            self.svg_elements.append(
                f'<text x="{self.padding - 10}" y="{y_pos + 4}" '
                f'font-size="12" text-anchor="end" fill="#6b7280">'
                f'{y_val:.0f}</text>'
            )
        
        self._add_grid_lines(y_ticks=y_ticks, show_x_grid=False)
    
    def _draw_series(self, series_name: str, values: List[float], 
                    x_scale: float, y_scale: float, y_min: float):
        """하나의 시리즈를 그립니다."""
        color = self.colors[series_name]
        points = []
        
        for i, value in enumerate(values):
            if value is None:
                continue
            
            x = self.padding + i * x_scale
            y = self.padding + self.chart_height - (value - y_min) * y_scale
            points.append(f"{x},{y}")
            
            # 데이터 포인트 원
            self.svg_elements.append(
                f'<circle cx="{x}" cy="{y}" r="3" '
                f'fill="{color}" />'
            )
        
        # 라인 그리기
        if len(points) > 1:
            self.svg_elements.append(
                f'<polyline points="{" ".join(points)}" '
                f'fill="none" stroke="{color}" stroke-width="2" />'
            )
    
    def _draw_x_labels(self, x_scale: float):
        """X축 라벨을 그립니다."""
        for i, label in enumerate(self.x_values):
            x = self.padding + i * x_scale
            self.svg_elements.append(
                f'<text x="{x}" y="{self.height - self.padding + 20}" '
                f'font-size="12" text-anchor="middle" fill="#6b7280">'
                f'{label}</text>'
            )