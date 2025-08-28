"""
차트 렌더러 (SVG)

비교 워크플로우에서 사용하는 간단한 SVG 차트들을 생성합니다.

주의사항
- 외부 라이브러리에 의존하지 않습니다. (브라우저 없이 파일로 바로 열 수 있도록)
- 입력은 워크플로우/더미 스크립트에서 사용하는 구조를 그대로 받습니다.
- 성능/정밀도보다 가독성과 견고성을 우선합니다.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class ChartRenderer:
    """간단한 SVG 차트 렌더러.

    제공 기능
    - 일별 방문추이 (전주/금주 막대 + 증감률 스파크라인 느낌의 라인)
    - 고객 구성 변화 (연령대별 남/여 비중 막대, 선택적으로 비교 남/여 포함)
    - 시간대/연령대 히트맵

    반환값은 모두 `<svg ...>...</svg>` 문자열입니다.
    """

    def __init__(self) -> None:
        # 팔레트 (Tailwind 계열 톤)
        self.color_primary = "#2563eb"  # 남성
        self.color_secondary = "#06b6d4"  # 여성
        self.color_compare_primary = "#93c5fd"  # 비교_남성
        self.color_compare_secondary = "#a7f3d0"  # 비교_여성
        self.color_axis = "#9ca3af"
        self.color_grid = "#e5e7eb"
        self.color_text = "#374151"

    # ------------------------------ 유틸 ------------------------------
    @staticmethod
    def _safe_get_percentage(d: Dict[str, Any], key: str) -> float:
        try:
            v = d.get(key, {}).get("percentage", 0)  # type: ignore[assignment]
            return float(v or 0)
        except Exception:
            return 0.0

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    # ------------------------- 일별 방문 추이 -------------------------
    def render_daily_trends_chart(
        self,
        daily_rows: List[Dict[str, Any]],
        *,
        store_name: Optional[str] = None,
        width: int = 800,
        height: int = 360,
    ) -> str:
        """전주/금주 일별 방문자 막대 + 간단한 라인.

        daily_rows: [{date, visitors, period_type('previous'|'current'), day_of_week(int)}]
        """

        pad_left, pad_right, pad_top, pad_bottom = 56, 16, 24, 36
        plot_w = width - pad_left - pad_right
        plot_h = height - pad_top - pad_bottom

        # 날짜 순으로 정렬 후, 같은 요일 위치에 이전/현재 두 막대를 그립니다
        rows = [r for r in daily_rows]
        rows.sort(key=lambda r: r.get("date", ""))

        # x 축은 인덱스 0..n-1, 그룹당 2막대
        unique_dates = [r["date"] for r in rows if isinstance(r.get("date"), str)]
        dates = list(dict.fromkeys(unique_dates))
        n = len(dates)
        if n == 0:
            return f"<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'></svg>"

        # 값 범위
        max_visitors = max(int(r.get("visitors", 0) or 0) for r in rows) or 1

        bar_group_w = plot_w / n
        single_bar_w = bar_group_w * 0.35
        gap_in_group = bar_group_w * 0.1

        svg_parts: List[str] = []
        svg_parts.append(f"<rect x='0' y='0' width='{width}' height='{height}' fill='white' />")

        # 격자선
        grid_steps = 4
        for i in range(grid_steps + 1):
            y = pad_top + plot_h * (i / grid_steps)
            svg_parts.append(
                f"<line x1='{pad_left}' y1='{y:.1f}' x2='{pad_left + plot_w}' y2='{y:.1f}' stroke='{self.color_grid}' stroke-width='1' />"
            )

        # 막대들
        for idx, d in enumerate(dates):
            # 이전/현재 값 꺼내기
            prev = next((r for r in rows if r["date"] == d and r.get("period_type") == "previous"), None)
            curr = next((r for r in rows if r["date"] == d and r.get("period_type") == "current"), None)
            prev_v = int(prev.get("visitors", 0)) if prev else 0
            curr_v = int(curr.get("visitors", 0)) if curr else 0

            x0 = pad_left + idx * bar_group_w
            # previous
            h_prev = plot_h * self._clamp(prev_v / max_visitors, 0, 1)
            x_prev = x0 + (bar_group_w - (2 * single_bar_w + gap_in_group)) / 2
            y_prev = pad_top + plot_h - h_prev
            svg_parts.append(
                f"<rect x='{x_prev:.1f}' y='{y_prev:.1f}' width='{single_bar_w:.1f}' height='{h_prev:.1f}' fill='#9CA3AF' />"
            )

            # current
            h_curr = plot_h * self._clamp(curr_v / max_visitors, 0, 1)
            x_curr = x_prev + single_bar_w + gap_in_group
            y_curr = pad_top + plot_h - h_curr
            svg_parts.append(
                f"<rect x='{x_curr:.1f}' y='{y_curr:.1f}' width='{single_bar_w:.1f}' height='{h_curr:.1f}' fill='{self.color_primary}' />"
            )

            # x 라벨 (격주로 표시)
            if idx % 2 == 0:
                svg_parts.append(
                    f"<text x='{x0 + bar_group_w/2:.1f}' y='{height - 10}' text-anchor='middle' font-size='11' fill='{self.color_text}'>{d[5:]}</text>"
                )

        # 범례
        legend_y = pad_top - 6
        svg_parts.append(
            f"<circle cx='{pad_left}' cy='{legend_y}' r='5' fill='{self.color_primary}' />"
        )
        svg_parts.append(
            f"<text x='{pad_left + 10}' y='{legend_y + 4}' font-size='12' fill='{self.color_text}'>금주</text>"
        )
        svg_parts.append(
            f"<rect x='{pad_left + 50}' y='{legend_y - 5}' width='10' height='10' fill='#9CA3AF' />"
        )
        svg_parts.append(
            f"<text x='{pad_left + 65}' y='{legend_y + 4}' font-size='12' fill='{self.color_text}'>전주</text>"
        )

        return (
            f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg'>"
            + "".join(svg_parts)
            + "</svg>"
        )

    # ----------------------- 고객 구성 (연령/성별) ----------------------
    def render_customer_composition_chart(
        self,
        gender_distribution: Dict[str, Dict[str, Any]],
        age_distribution: Dict[str, Dict[str, Any]],
        *,
        compare_gender_distribution: Optional[Dict[str, Dict[str, Any]]] = None,
        compare_age_distribution: Optional[Dict[str, Dict[str, Any]]] = None,
        width: int = 800,
        height: int = 380,
    ) -> str:
        """연령대별 남/여 비중을 수평 막대로 표현합니다.

        비교 데이터가 주어지면 동일 축 상에 얇은 바(비교_남/여)를 추가해 이미지와 유사한 4범례 구성을 만듭니다.
        입력 구조 예시:
            gender_distribution = {"male": {"count": int, "percentage": float}, "female": {...}}
            age_distribution = {"10s": {...}, "20s": {...}, ..., "60s+": {...}}
        """

        # 연령대 순서 및 라벨
        age_keys = ["10s", "20s", "30s", "40s", "50s", "60s+"]
        age_labels = {
            "10s": "10~19세",
            "20s": "20~29세",
            "30s": "30~39세",
            "40s": "40~49세",
            "50s": "50~59세",
            "60s+": "60세~",
        }

        pad_left, pad_right, pad_top, pad_bottom = 110, 20, 28, 26
        plot_w = width - pad_left - pad_right
        bar_band_h = (height - pad_top - pad_bottom) / len(age_keys)
        bar_h = bar_band_h * 0.32  # 남/여 2줄 + 비교 2줄
        gap_y = bar_band_h * 0.06

        # 성별 전체 비중을 퍼센트로 사용 (막대 색은 성별 기준)
        male_pct = self._safe_get_percentage(gender_distribution, "male")
        female_pct = self._safe_get_percentage(gender_distribution, "female")

        # 비교 데이터가 없으면 현재 값을 기반으로 5%p 내외 변형해 시각적으로 비교 느낌 제공 (더미용)
        if compare_gender_distribution is None:
            compare_gender_distribution = {
                "male": {"percentage": max(0.0, min(100.0, male_pct - 4.0))},
                "female": {"percentage": max(0.0, min(100.0, female_pct + 4.0))},
            }
        if compare_age_distribution is None:
            compare_age_distribution = {}
            for k in age_keys:
                base = float(age_distribution.get(k, {}).get("percentage", 0) or 0)
                compare_age_distribution[k] = {"percentage": max(0.0, min(100.0, base * 0.9 + 2.0))}

        # 연령대별 현재 비중
        age_pct: Dict[str, float] = {
            k: float(age_distribution.get(k, {}).get("percentage", 0) or 0) for k in age_keys
        }
        # 연령대별 비교 비중
        cmp_age_pct: Dict[str, float] = {
            k: float(compare_age_distribution.get(k, {}).get("percentage", 0) or 0) for k in age_keys
        }

        # 한 축은 0~최대 30%로 클램프 (연령대 비중이 과도하게 크지 않다는 가정의 안정적 시각화)
        axis_max = max(10.0, min(50.0, max(list(age_pct.values() or [0]) + list(cmp_age_pct.values() or [0]))))

        def pct_to_w(p: float) -> float:
            return plot_w * self._clamp(p / axis_max, 0.0, 1.0)

        svg: List[str] = []
        svg.append(f"<rect x='0' y='0' width='{width}' height='{height}' fill='white' />")

        # y축 라벨 및 가이드 라인
        for i, k in enumerate(age_keys):
            y_band_top = pad_top + i * bar_band_h
            # 가이드 라인
            svg.append(
                f"<line x1='{pad_left}' y1='{y_band_top + bar_band_h:.1f}' x2='{pad_left + plot_w}' y2='{y_band_top + bar_band_h:.1f}' stroke='{self.color_grid}' stroke-width='1' />"
            )
            # 라벨
            svg.append(
                f"<text x='{pad_left - 8}' y='{y_band_top + bar_band_h/2 + 4:.1f}' font-size='12' fill='{self.color_text}' text-anchor='end'>{age_labels[k]}</text>"
            )

            # 현재 남/여 막대 (두 줄)
            y_male = y_band_top + (bar_band_h - 2 * bar_h - gap_y) / 2
            y_female = y_male + bar_h + gap_y
            w_male = pct_to_w(age_pct[k] * (male_pct / max(1.0, male_pct + female_pct)))
            w_female = pct_to_w(age_pct[k] * (female_pct / max(1.0, male_pct + female_pct)))
            svg.append(
                f"<rect x='{pad_left}' y='{y_male:.1f}' width='{w_male:.1f}' height='{bar_h:.1f}' fill='{self.color_primary}' rx='4' />"
            )
            svg.append(
                f"<rect x='{pad_left}' y='{y_female:.1f}' width='{w_female:.1f}' height='{bar_h:.1f}' fill='{self.color_secondary}' rx='4' />"
            )

            # 비교 남/여 얇은 바 (겹치지 않도록 y를 조금 아래)
            y_cmp_male = y_female + gap_y + 2
            y_cmp_female = y_cmp_male + bar_h * 0.7 + 2
            cmp_male_share = float(compare_gender_distribution.get("male", {}).get("percentage", 0) or 0)
            cmp_female_share = float(compare_gender_distribution.get("female", {}).get("percentage", 0) or 0)
            w_cmp_male = pct_to_w(cmp_age_pct[k] * (cmp_male_share / max(1.0, cmp_male_share + cmp_female_share)))
            w_cmp_female = pct_to_w(cmp_age_pct[k] * (cmp_female_share / max(1.0, cmp_male_share + cmp_female_share)))
            svg.append(
                f"<rect x='{pad_left}' y='{y_cmp_male:.1f}' width='{w_cmp_male:.1f}' height='{(bar_h*0.7):.1f}' fill='{self.color_compare_primary}' rx='3' />"
            )
            svg.append(
                f"<rect x='{pad_left}' y='{y_cmp_female:.1f}' width='{w_cmp_female:.1f}' height='{(bar_h*0.7):.1f}' fill='{self.color_compare_secondary}' rx='3' />"
            )

            # 각 밴드 오른쪽에 백분율 라벨(현재 합)
            total_pct = age_pct[k]
            svg.append(
                f"<text x='{pad_left + pct_to_w(total_pct) + 6:.1f}' y='{y_female + bar_h/2 + 4:.1f}' font-size='11' fill='{self.color_text}'>{total_pct:.1f}%</text>"
            )

        # x 축 눈금 (0, axis_max)
        for t in range(0, int(axis_max) + 1, max(5, int(axis_max // 3) or 5)):
            x = pad_left + pct_to_w(float(t))
            svg.append(
                f"<line x1='{x:.1f}' y1='{pad_top}' x2='{x:.1f}' y2='{height - pad_bottom}' stroke='{self.color_grid}' stroke-width='1' />"
            )
            svg.append(
                f"<text x='{x:.1f}' y='{height - 6}' font-size='11' fill='{self.color_text}' text-anchor='middle'>{t}%</text>"
            )

        # 범례
        lx = pad_left
        ly = 18
        legend_items: List[Tuple[str, str]] = [
            (self.color_primary, "남성"),
            (self.color_secondary, "여성"),
            (self.color_compare_primary, "비교_남성"),
            (self.color_compare_secondary, "비교_여성"),
        ]
        for i, (c, name) in enumerate(legend_items):
            svg.append(f"<rect x='{lx + i * 110}' y='{ly - 10}' width='14' height='14' rx='3' fill='{c}' />")
            svg.append(
                f"<text x='{lx + i * 110 + 20}' y='{ly + 2}' font-size='12' fill='{self.color_text}'>{name}</text>"
            )

        # 타이틀(선택)
        if False:
            svg.append(
                f"<text x='{width/2:.1f}' y='18' font-size='14' fill='{self.color_text}' text-anchor='middle'>연령 분포</text>"
            )

        return (
            f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg'>"
            + "".join(svg)
            + "</svg>"
        )

    # --------------------------- 히트맵 ---------------------------
    def render_heatmap_chart(
        self,
        heat_rows: List[Dict[str, Any]],
        *,
        width: int = 800,
        height: int = 420,
    ) -> str:
        """시간대 x 연령대 히트맵.

        heat_rows: [{hour: int, age_group: str, visitor_count: int}]
        """

        age_keys = ["10s", "20s", "30s", "40s", "50s", "60s+"]
        age_labels = {
            "10s": "10대",
            "20s": "20대",
            "30s": "30대",
            "40s": "40대",
            "50s": "50대",
            "60s+": "60+",
        }

        pad_left, pad_right, pad_top, pad_bottom = 56, 16, 26, 28
        plot_w = width - pad_left - pad_right
        plot_h = height - pad_top - pad_bottom

        # 데이터 매핑: (hour, age) -> count
        grid: Dict[Tuple[int, str], int] = {}
        for r in heat_rows:
            try:
                grid[(int(r.get("hour", 0)), str(r.get("age_group", "")))] = int(
                    r.get("visitor_count", 0) or 0
                )
            except Exception:
                continue

        hours = list(range(9, 21))  # 9~20시
        max_val = max([grid.get((h, a), 0) for h in hours for a in age_keys] or [1])

        cell_w = plot_w / len(hours)
        cell_h = plot_h / len(age_keys)

        def color_for(v: int) -> str:
            # 0 -> #eff6ff, max -> #1d4ed8
            ratio = self._clamp(v / max_val, 0.0, 1.0)
            # 간단한 보간 (밝은 파랑 -> 진한 파랑)
            start = (239, 246, 255)
            end = (29, 78, 216)
            r = int(start[0] + (end[0] - start[0]) * ratio)
            g = int(start[1] + (end[1] - start[1]) * ratio)
            b = int(start[2] + (end[2] - start[2]) * ratio)
            return f"rgb({r},{g},{b})"

        svg: List[str] = []
        svg.append(f"<rect x='0' y='0' width='{width}' height='{height}' fill='white' />")

        # Y 라벨
        for i, a in enumerate(age_keys):
            y = pad_top + i * cell_h + cell_h / 2
            svg.append(
                f"<text x='{pad_left - 8}' y='{y:.1f}' text-anchor='end' font-size='12' fill='{self.color_text}'>{age_labels[a]}</text>"
            )

        # 그리드 및 색상 칠하기
        for i, a in enumerate(age_keys):
            for j, h in enumerate(hours):
                x = pad_left + j * cell_w
                y = pad_top + i * cell_h
                val = grid.get((h, a), 0)
                svg.append(
                    f"<rect x='{x:.1f}' y='{y:.1f}' width='{cell_w:.1f}' height='{cell_h:.1f}' fill='{color_for(val)}' stroke='white' stroke-width='1' />"
                )

        # X 라벨 (시간)
        for j, h in enumerate(hours):
            x = pad_left + j * cell_w + cell_w / 2
            svg.append(
                f"<text x='{x:.1f}' y='{height - 6}' text-anchor='middle' font-size='11' fill='{self.color_text}'>{h}시</text>"
            )

        return (
            f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg'>"
            + "".join(svg)
            + "</svg>"
        )

