"""
색상 변환 및 처리 유틸리티
RGB, HSL, HEX 간 변환 및 색상 조작 함수들
"""

from typing import Tuple, List
import math


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """HEX 색상을 RGB로 변환합니다 (0.0-1.0 범위).
    
    Args:
        hex_color: HEX 색상 문자열 (예: "#FF0000" 또는 "FF0000")
    
    Returns:
        RGB 튜플 (각 값은 0.0-1.0 범위)
    """
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 3:
        # 3자리 HEX를 6자리로 확장
        hex_color = ''.join([c*2 for c in hex_color])
    
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    
    return r, g, b


def rgb_to_hex(r: float, g: float, b: float) -> str:
    """RGB를 HEX 색상으로 변환합니다.
    
    Args:
        r: 빨강 값 (0.0-1.0)
        g: 초록 값 (0.0-1.0)
        b: 파랑 값 (0.0-1.0)
    
    Returns:
        HEX 색상 문자열 (예: "#FF0000")
    """
    r_int = int(max(0, min(255, round(r * 255))))
    g_int = int(max(0, min(255, round(g * 255))))
    b_int = int(max(0, min(255, round(b * 255))))
    
    return f'#{r_int:02X}{g_int:02X}{b_int:02X}'


def rgb_to_hsl(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """RGB를 HSL로 변환합니다.
    
    Args:
        r: 빨강 값 (0.0-1.0)
        g: 초록 값 (0.0-1.0)
        b: 파랑 값 (0.0-1.0)
    
    Returns:
        HSL 튜플 (H: 0.0-1.0, S: 0.0-1.0, L: 0.0-1.0)
    """
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    l = (max_val + min_val) / 2
    
    if max_val == min_val:
        h = s = 0.0  # 무채색
    else:
        d = max_val - min_val
        s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
        
        if max_val == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_val == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6
    
    return h, s, l


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[float, float, float]:
    """HSL을 RGB로 변환합니다.
    
    Args:
        h: 색조 (0.0-1.0)
        s: 채도 (0.0-1.0)
        l: 명도 (0.0-1.0)
    
    Returns:
        RGB 튜플 (각 값은 0.0-1.0 범위)
    """
    def hue2rgb(p: float, q: float, t: float) -> float:
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
    
    if s == 0:
        r = g = b = l  # 무채색
    else:
        q = l * (1 + s) if l < 0.5 else (l + s - l * s)
        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)
    
    return r, g, b


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """값을 지정된 범위로 제한합니다.
    
    Args:
        value: 제한할 값
        min_val: 최소값
        max_val: 최대값
    
    Returns:
        제한된 값
    """
    return max(min_val, min(max_val, value))


def interpolate_color(
    color1: str, 
    color2: str, 
    t: float, 
    color_space: str = "rgb"
) -> str:
    """두 색상 사이를 보간합니다.
    
    Args:
        color1: 시작 색상 (HEX)
        color2: 종료 색상 (HEX)
        t: 보간 비율 (0.0-1.0)
        color_space: 보간 색공간 ("rgb" 또는 "hsl")
    
    Returns:
        보간된 색상 (HEX)
    """
    t = clamp(t)
    
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    
    if color_space == "hsl":
        h1, s1, l1 = rgb_to_hsl(r1, g1, b1)
        h2, s2, l2 = rgb_to_hsl(r2, g2, b2)
        
        # HSL 보간
        h = h1 + (h2 - h1) * t
        s = s1 + (s2 - s1) * t
        l = l1 + (l2 - l1) * t
        
        r, g, b = hsl_to_rgb(h, s, l)
    else:
        # RGB 보간
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
    
    return rgb_to_hex(r, g, b)


def generate_gradient(
    start_color: str,
    end_color: str,
    steps: int,
    color_space: str = "rgb"
) -> List[str]:
    """색상 그라데이션을 생성합니다.
    
    Args:
        start_color: 시작 색상 (HEX)
        end_color: 종료 색상 (HEX)
        steps: 단계 수
        color_space: 보간 색공간
    
    Returns:
        색상 리스트 (HEX)
    """
    if steps <= 1:
        return [start_color]
    
    colors = []
    for i in range(steps):
        t = i / (steps - 1)
        color = interpolate_color(start_color, end_color, t, color_space)
        colors.append(color)
    
    return colors


def adjust_brightness(hex_color: str, factor: float) -> str:
    """색상의 밝기를 조정합니다.
    
    Args:
        hex_color: HEX 색상
        factor: 밝기 조정 계수 (1.0 = 변화 없음, <1.0 = 어둡게, >1.0 = 밝게)
    
    Returns:
        조정된 색상 (HEX)
    """
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    
    # 명도 조정
    l = clamp(l * factor)
    
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b)


def adjust_saturation(hex_color: str, factor: float) -> str:
    """색상의 채도를 조정합니다.
    
    Args:
        hex_color: HEX 색상
        factor: 채도 조정 계수 (1.0 = 변화 없음, <1.0 = 채도 감소, >1.0 = 채도 증가)
    
    Returns:
        조정된 색상 (HEX)
    """
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    
    # 채도 조정
    s = clamp(s * factor)
    
    r, g, b = hsl_to_rgb(h, s, l)
    return rgb_to_hex(r, g, b)


def get_chart_colors() -> dict:
    """차트에서 사용할 기본 색상 팔레트를 반환합니다."""
    return {
        # 기본 색상
        'primary': '#3467E2',
        'secondary': '#76CCCF',
        'success': '#10b981',
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6',
        
        # 차트 색상
        'male_current': '#3467E2',
        'male_previous': '#9BB4F0',
        'female_current': '#76CCCF',
        'female_previous': '#BAE5E7',
        
        # 증감 색상
        'increase': '#10b981',
        'decrease': '#ef4444',
        'neutral': '#6b7280',
        
        # 히트맵 색상
        'heatmap_hot': '#741443',
        'heatmap_mid': '#E48356',
        'heatmap_cool': '#FFFFFF',
        
        # 막대 차트 색상
        'bar_blue': '#93c5fd',
        'bar_red': '#fca5a5',
        'bar_green': '#86efac',
        'bar_yellow': '#fde047',
        
        # 연령대별 색상 (60대+ ~ 0-9세)
        'age_60plus': '#A8BBF4',
        'age_50': '#8EABF2',
        'age_40': '#6E92ED',
        'age_30': '#3467E2',
        'age_20': '#2D58C8',
        'age_10': '#244AAD',
        'age_0': '#1C3F99',
    }


def generate_heatmap_color(intensity: float, colormap: str = 'default') -> str:
    """히트맵용 색상을 생성합니다.
    
    Args:
        intensity: 강도 (0.0-1.0)
        colormap: 컬러맵 이름
    
    Returns:
        색상 (HEX)
    """
    intensity = clamp(intensity)
    
    if colormap == 'default':
        # hot(#741443) ↔ mid(#E48356) ↔ cool(#FFFFFF)
        if intensity <= 0.5:
            t = intensity * 2
            return interpolate_color('#741443', '#E48356', t)
        else:
            t = (intensity - 0.5) * 2
            return interpolate_color('#E48356', '#FFFFFF', t)
    elif colormap == 'blue':
        # 파란색 그라데이션
        return interpolate_color('#FFFFFF', '#0066CC', intensity)
    elif colormap == 'green':
        # 초록색 그라데이션
        return interpolate_color('#FFFFFF', '#00AA44', intensity)
    else:
        # 기본 회색 그라데이션
        return interpolate_color('#FFFFFF', '#333333', intensity)