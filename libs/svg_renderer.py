from __future__ import annotations

from typing import List, Optional


def svg_sparkline(
    values: List[float],
    width: int = 120,
    height: int = 36,
    min_override: Optional[float] = None,
    max_override: Optional[float] = None,
    span_override: Optional[float] = None,
) -> str:
    if not values:
        values = [0.0]
    
    n = len(values)
    use_minmax = (
        min_override is not None
        and max_override is not None
        and float(max_override) > float(min_override)
    )
    if use_minmax:
        min_v = float(min_override)  # type: ignore
        max_v = float(max_override)  # type: ignore
        denom = max_v - min_v
    else:
        if span_override is not None and span_override > 0:
            span = float(span_override)
        else:
            min_auto = min(values + [0.0])
            max_auto = max(values + [0.0])
            span = max(abs(min_auto), abs(max_auto)) or 1.0
        min_v, max_v = -span, span
        denom = max_v - min_v
    pad_x, pad_y = 6, 2
    plot_w, plot_h = width - pad_x * 2, height - pad_y * 2
    pts = []
    for i, v in enumerate(values):
        x = pad_x + (plot_w * (i / max(1, n - 1)))
        y_norm = 0.5 if denom == 0 else (v - min_v) / denom
        y = pad_y + (plot_h * (1 - y_norm))
        pts.append((x, y))
    path_d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    y0 = None
    if min_v <= 0.0 <= max_v and denom != 0:
        y0_norm = (0.0 - min_v) / denom
        y0 = pad_y + (plot_h * (1 - y0_norm))
    circles = "\n".join(
        (
            f"<circle cx='{x:.1f}' cy='{y:.1f}' r='2.7' fill='{('#dc2626' if values[i] >= 0 else '#1d4ed8')}' />"
        )
        for i, (x, y) in enumerate(pts)
    )
    label_x = width - pad_x - 3
    return (
        f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg' aria-label='sparkline'>"
        + f"<rect x='0' y='0' width='{width}' height='{height}' fill='white'/>"
        + (f"<line x1='{pad_x}' y1='{y0:.1f}' x2='{width-pad_x}' y2='{y0:.1f}' stroke='#000000' stroke-width='1'/>" if y0 is not None else "")
        + (f"<text x='{label_x}' y='{y0:.1f}' fill='#6b7280' font-size='10' text-anchor='end' dominant-baseline='middle'>0%</text>" if y0 is not None else "")
        + f"<polyline fill='none' stroke='#d1d5db' stroke-width='1.2' points='{path_d}'/>"
        + circles
        + "</svg>"
    )

