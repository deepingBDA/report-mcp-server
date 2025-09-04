"""Scatter 카드 생성기 (기존 _build_scatter_card_html 로직 이관)."""

from __future__ import annotations

import math
from typing import List

from ..models import StoreRowDict, escape_html
from ..templates import SCATTER_CARD_TEMPLATE, SCATTER_NO_DATA_TEMPLATE


class ScatterCardGenerator:
    """Scatter 카드 생성기 (기존 _build_scatter_card_html 로직 완전 이관)."""
    
    def generate(self, rows: List[StoreRowDict]) -> str:
        """Scatter 카드 HTML 생성."""
        # 산점도: x=금주 방문객(curr_total), y=총 증감률(total_delta_pct)
        # 민맥스 스케일, 축 눈금값, 사분면 구분선(세로: 방문객 중위값, 가로: 0%), 굵은 라벨
        width, height = 1000, 600
        padding_left, padding_right = 120, 60
        padding_top, padding_bottom = 60, 120
        plot_w = width - padding_left - padding_right
        plot_h = height - padding_top - padding_bottom

        xs: List[float] = []
        ys: List[float] = []
        for r in rows:
            cx = r.get("curr_total")
            ty = r.get("total_delta_pct")
            if cx is not None and ty is not None:
                try:
                    xs.append(float(cx))
                    ys.append(float(ty))
                except Exception:
                    pass
        
        if not xs or not ys:
            return SCATTER_CARD_TEMPLATE.format(scatter_content=SCATTER_NO_DATA_TEMPLATE)

        # 1) 데이터 기반 최소/최대 및 10% 여백
        x_min_data, x_max_data = min(xs), max(xs)
        y_min_data, y_max_data = min(ys), max(ys)
        x_range = x_max_data - x_min_data or 1.0
        y_range = y_max_data - y_min_data or 1.0
        y_min_pad = y_min_data - y_range * 0.10
        y_max_pad = y_max_data + y_range * 0.10

        # 2) 알잘딱 Nice Scale로 깔끔한 축 경계/간격 계산
        def _nice_num(x: float, round_to: bool) -> float:
            if x <= 0:
                return 1.0
            exp = math.floor(math.log10(x))
            f = x / (10 ** exp)
            if round_to:
                if f < 1.5:
                    nf = 1
                elif f < 3:
                    nf = 2
                elif f < 7:
                    nf = 5
                else:
                    nf = 10
            else:
                if f <= 1:
                    nf = 1
                elif f <= 2:
                    nf = 2
                elif f <= 5:
                    nf = 5
                else:
                    nf = 10
            return nf * (10 ** exp)

        def _nice_scale(vmin: float, vmax: float, max_ticks: int = 5) -> tuple[float, float, float]:
            rng = _nice_num(max(vmax - vmin, 1e-6), False)
            tick = _nice_num(rng / max(1, (max_ticks - 1)), True)
            nice_min = math.floor(vmin / tick) * tick
            nice_max = math.ceil(vmax / tick) * tick
            return nice_min, nice_max, tick

        # X축 방문객 수: 중간값을 중심으로 대칭하게 스케일링
        x_mid = (x_min_data + x_max_data) / 2.0
        x_range_sym = max(x_max_data - x_mid, x_mid - x_min_data) * 1.15  # 15% 여백
        x_min_sym = x_mid - x_range_sym
        x_max_sym = x_mid + x_range_sym
        x_min, x_max, x_step = _nice_scale(x_min_sym, x_max_sym, 5)
        
        # Y축 증감률도 Nice scale로 적응적 설정 (큰 범위도 자동 대응)
        y_min, y_max, y_step = _nice_scale(y_min_pad, y_max_pad, 5)

        def sx(x: float) -> float:
            x_range = x_max - x_min or 1.0
            return padding_left + (x - x_min) / x_range * plot_w

        def sy(y: float) -> float:
            y_range = y_max - y_min or 1.0
            return padding_top + (1 - (y - y_min) / y_range) * plot_h

        # 가로 0% 기준선
        zero_y = sy(0) if (y_min <= 0 <= y_max) else None

        # 세로선: 방문객 수 최대값과 최소값의 평균 (이미 위에서 계산됨)
        mid_x_svg = sx(x_mid)

        # 3) 눈금 배열 생성
        x_ticks: List[float] = []
        v = x_min
        while v <= x_max + 1e-6:
            x_ticks.append(v)
            v += x_step
        y_ticks: List[float] = []
        v = y_min
        while v <= y_max + 1e-6:
            y_ticks.append(v)
            v += y_step

        def fmt_x(v: float) -> str:
            return f"{int(round(v)):,}"

        def fmt_y(v: float) -> str:
            return f"{v:.1f}%"

        grid_parts: List[str] = []
        for yv in y_ticks:
            gy = sy(yv)
            grid_parts.append(f"<line x1={padding_left} y1={gy:.1f} x2={width - padding_right} y2={gy:.1f} stroke=\"#eee\" />")
            is_zero = abs(yv) < 1e-6
            label_color = "#cbd5e1" if is_zero else "#6b7280"
            label_text = "0%" if is_zero else fmt_y(yv)
            grid_parts.append(f"<text x={padding_left-10} y={gy+4:.1f} font-size=\"12\" fill=\"{label_color}\" text-anchor=\"end\">{label_text}</text>")

        for xv in x_ticks:
            gx = sx(xv)
            grid_parts.append(f"<line x1={gx:.1f} y1={padding_top} x2={gx:.1f} y2={height - padding_bottom} stroke=\"#eee\" />")
            grid_parts.append(f"<text x={gx:.1f} y={height - padding_bottom + 24} font-size=\"12\" fill=\"#6b7280\" text-anchor=\"middle\">{fmt_x(xv)}</text>")

        # 축선 + 틱 마크
        axis_parts: List[str] = []
        x_axis_y = height - padding_bottom
        axis_parts.append(f"<line x1={padding_left} y1={x_axis_y:.1f} x2={width - padding_right} y2={x_axis_y:.1f} stroke=\"#111\" stroke-width=\"1.6\" />")
        axis_parts.append(f"<line x1={padding_left:.1f} y1={padding_top} x2={padding_left:.1f} y2={height - padding_bottom} stroke=\"#111\" stroke-width=\"1.6\" />")
        for yv in y_ticks:
            gy = sy(yv)
            axis_parts.append(f"<line x1={padding_left-6} y1={gy:.1f} x2={padding_left} y2={gy:.1f} stroke=\"#111\" stroke-width=\"1\" />")
        for xv in x_ticks:
            gx = sx(xv)
            axis_parts.append(f"<line x1={gx:.1f} y1={x_axis_y:.1f} x2={gx:.1f} y2={x_axis_y+6:.1f} stroke=\"#111\" stroke-width=\"1\" />")

        # 사분면 구분선
        divider_parts: List[str] = []
        if zero_y is not None:
            divider_parts.append(f"<line x1={padding_left} y1={zero_y:.1f} x2={width - padding_right} y2={zero_y:.1f} stroke=\"#cbd5e1\" stroke-width=\"1.2\" />")
        divider_parts.append(f"<line x1={mid_x_svg:.1f} y1={padding_top} x2={mid_x_svg:.1f} y2={height - padding_bottom} stroke=\"#cbd5e1\" stroke-width=\"1.4\" />")
        
        # 중앙값 라벨 (기존 X축 눈금과 겹치지 않을 때만 표시)
        mid_label = ""
        min_distance = 80  # 최소 거리 (픽셀)
        should_show = True
        for xv in x_ticks:
            if abs(x_mid - xv) < min_distance:
                should_show = False
                break
        
        if should_show:
            mid_label = f"<text x=\"{mid_x_svg:.1f}\" y=\"{height - padding_bottom + 24}\" font-size=\"12\" fill=\"#cbd5e1\" text-anchor=\"middle\">{int(round(x_mid)):,}명</text>"

        # 점 + 2줄 라벨(굵은 매장명 / 괄호에 값)
        points: List[str] = []
        labels: List[str] = []
        for r in rows:
            site = str(r.get("site", ""))
            cx = r.get("curr_total")
            ty = r.get("total_delta_pct")
            if cx is None or ty is None:
                continue
            try:
                x = sx(float(cx))
                y = sy(float(ty))
            except Exception:
                continue
            pct = float(ty)
            color = "#dc2626" if pct >= 10 else ("#10b981" if pct >= 0 else "#1d4ed8")
            points.append(f"<circle cx={x:.1f} cy={y:.1f} r=11 fill=\"{color}\" fill-opacity=\"0.9\" />")
            val_text = f"({int(round(float(cx))):,}, {pct:.1f}%)"
            labels.append(
                f"<text x={x:.1f} y={y-22:.1f} font-size=\"14\" text-anchor=\"middle\" fill=\"{color}\">"
                f"<tspan x={x:.1f} dy=\"0\" font-weight=\"700\">{escape_html(site)}</tspan>"
                f"<tspan x={x:.1f} dy=\"14\">{escape_html(val_text)}</tspan>"
                f"</text>"
            )

        # 범례 추가 (SVG 컨테이너 내부 오른쪽 아래에 배치)
        legend_width = 120
        legend_height = 70
        legend_x_start = width - legend_width - 20  # 오른쪽에서 20px 간격
        legend_y = height - legend_height - 20  # 아래에서 20px 간격
        
        svg = f"""<svg width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\" xmlns=\"http://www.w3.org/2000/svg\">
  <rect x=\"1\" y=\"1\" width=\"{width-2}\" height=\"{height-2}\" fill=\"#fff\" stroke=\"#e5e7eb\" rx=\"10\" />
  {''.join(grid_parts)}
  {''.join(axis_parts)}
  {''.join(divider_parts)}
  {mid_label}
  {''.join(points)}
  {''.join(labels)}
  <text x=\"{padding_left/2}\" y=\"{padding_top+plot_h/2}\" transform=\"rotate(-90 {padding_left/2},{padding_top+plot_h/2})\" font-size=\"19\" font-weight=\"600\" fill=\"#374151\" text-anchor=\"middle\">증감률 (%)</text>
  <text x=\"{padding_left+plot_w/2}\" y=\"{height-30}\" font-size=\"19\" font-weight=\"600\" fill=\"#374151\" text-anchor=\"middle\">방문객 수 (명)</text>
  
  <!-- 범례 -->
  <rect x=\"{legend_x_start}\" y=\"{legend_y}\" width=\"120\" height=\"70\" fill=\"transparent\" stroke=\"#e5e7eb\" rx=\"5\" />
  <!-- 고성장 (10% 이상) -->
  <rect x=\"{legend_x_start + 10}\" y=\"{legend_y + 12}\" width=\"10\" height=\"10\" fill=\"#dc2626\" />
  <text x=\"{legend_x_start + 25}\" y=\"{legend_y + 20}\" font-size=\"11\" fill=\"#374151\">고성장 (10%+)</text>
  <!-- 안정성장 (0~10%) -->
  <rect x=\"{legend_x_start + 10}\" y=\"{legend_y + 32}\" width=\"10\" height=\"10\" fill=\"#10b981\" />
  <text x=\"{legend_x_start + 25}\" y=\"{legend_y + 40}\" font-size=\"11\" fill=\"#374151\">안정성장 (0~10%)</text>
  <!-- 하락 (0% 이하) -->
  <rect x=\"{legend_x_start + 10}\" y=\"{legend_y + 52}\" width=\"10\" height=\"10\" fill=\"#1d4ed8\" />
  <text x=\"{legend_x_start + 25}\" y=\"{legend_y + 60}\" font-size=\"11\" fill=\"#374151\">하락 (0% 이하)</text>
</svg>"""

        scatter_content = f"""
  <div class="card-header">
    <h3>매장 성과</h3>
    <p class="card-subtitle">방문객 수와 전 기간 대비 방문객 증감률을 기준으로 매장별 성과와 위치를 한눈에 확인할 수 있습니다.</p>
  </div>
  <div style="text-align: center; margin-top: 16px;">{svg}</div>"""

        return SCATTER_CARD_TEMPLATE.format(scatter_content=scatter_content)