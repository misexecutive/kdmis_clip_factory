"""
Nyro AI Clip Factory - Dynamic Motion Graphics & Animated CTA Engine (Module 4)
Provides platform-calibrated CTA overlays (YouTube Shorts / Instagram Reels)
with animated pointing arrows, target coordinates, safe-zone verification,
and content-aware visual treatments.
"""

import logging
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger("MotionGraphics")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GFX_DIR = PROJECT_ROOT / "storage" / "assets" / "graphics"
DEFAULT_GFX_DIR.mkdir(parents=True, exist_ok=True)


# Platform Control Targets in 1080x1920 Vertical Canvas
PLATFORM_CTA_TARGETS: Dict[str, Dict[str, Any]] = {
    "youtube_shorts_like": {
        "platform": "YouTube Shorts",
        "action": "Like",
        "target_x": 960,
        "target_y": 1200,
        "arrow_start_x": 760,
        "arrow_start_y": 1180,
        "angle_degrees": 0,  # Points horizontally right towards like button
        "safe_zone": True,
    },
    "youtube_shorts_share": {
        "platform": "YouTube Shorts",
        "action": "Share",
        "target_x": 960,
        "target_y": 1540,
        "arrow_start_x": 760,
        "arrow_start_y": 1520,
        "angle_degrees": 0,  # Points right towards share button
        "safe_zone": True,
    },
    "youtube_shorts_subscribe": {
        "platform": "YouTube Shorts",
        "action": "Subscribe",
        "target_x": 720,
        "target_y": 1690,
        "arrow_start_x": 720,
        "arrow_start_y": 1540,
        "angle_degrees": 90,  # Points downwards towards subscribe pill
        "safe_zone": True,
    },
    "instagram_reels_like": {
        "platform": "Instagram Reels",
        "action": "Like",
        "target_x": 970,
        "target_y": 1310,
        "arrow_start_x": 780,
        "arrow_start_y": 1290,
        "angle_degrees": 0,
        "safe_zone": True,
    },
}


class MotionGraphicsEngine:
    """Renders professional motion graphics and platform-calibrated CTA overlays."""

    def __init__(self, gfx_dir: Optional[Path] = None):
        self.gfx_dir = gfx_dir or DEFAULT_GFX_DIR
        self.gfx_dir.mkdir(parents=True, exist_ok=True)

    def generate_arrow_asset(
        self,
        style: str = "neon_cyan",
        width: int = 160,
        height: int = 100,
    ) -> Path:
        """
        Renders a high-resolution anti-aliased RGBA arrow graphic with neon glow.
        Returns the path to the cached PNG asset.
        """
        out_path = self.gfx_dir / f"arrow_{style}_{width}x{height}.png"
        if out_path.exists() and out_path.stat().st_size > 500:
            return out_path

        # Render arrow at 2x resolution for smooth supersampled antialiasing
        scale = 2
        sw = width * scale
        sh = height * scale
        img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Color schemes
        if style == "neon_cyan":
            main_color = (0, 229, 255, 255)
            glow_color = (0, 229, 255, 120)
        elif style == "cyber_yellow":
            main_color = (255, 214, 10, 255)
            glow_color = (255, 183, 3, 120)
        elif style == "crimson_red":
            main_color = (255, 51, 102, 255)
            glow_color = (255, 51, 102, 120)
        else:
            main_color = (255, 255, 255, 255)
            glow_color = (200, 200, 200, 100)

        # Arrow geometry (pointing right)
        # Tail: rectangle from left to head base
        # Head: triangle pointing to right edge
        tail_h = int(sh * 0.35)
        tail_top = (sh - tail_h) // 2
        tail_bot = tail_top + tail_h
        head_w = int(sw * 0.45)
        shaft_w = sw - head_w

        # Draw glowing blurred shadow behind
        glow_img = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        glow_draw.rectangle([10, tail_top - 6, shaft_w + 10, tail_bot + 6], fill=glow_color)
        glow_draw.polygon([(shaft_w, 10), (sw - 10, sh // 2), (shaft_w, sh - 10)], fill=glow_color)
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=8 * scale))

        # Draw crisp foreground arrow
        draw.rectangle([20, tail_top, shaft_w + 5, tail_bot], fill=main_color)
        draw.polygon([(shaft_w, 16), (sw - 16, sh // 2), (shaft_w, sh - 16)], fill=main_color)

        # Composite glow + arrow
        composite = Image.alpha_composite(glow_img, img)
        # Downsample to target size
        final_arrow = composite.resize((width, height), Image.Resampling.LANCZOS)
        final_arrow.save(out_path, format="PNG")
        logger.info(f"Generated motion graphics asset: {out_path.name}")
        return out_path

    def build_cta_overlay_filter(
        self,
        cta_target_name: str = "youtube_shorts_like",
        clip_duration: float = 15.0,
        enter_delay_before_end: float = 3.2,
        active_duration: float = 2.4,
    ) -> Dict[str, Any]:
        """
        Produces the FFmpeg filter snippet to overlay the animated arrow
        pointing at the target platform control without obstructing gameplay.
        Uses sinusoidal bounce animation.
        """
        target = PLATFORM_CTA_TARGETS.get(cta_target_name, PLATFORM_CTA_TARGETS["youtube_shorts_like"])
        arrow_png = self.generate_arrow_asset(style="neon_cyan")

        t_start = max(1.0, clip_duration - enter_delay_before_end)
        t_end = min(clip_duration, t_start + active_duration)

        # Escape path for FFmpeg
        esc_arrow_path = str(arrow_png.resolve()).replace("\\", "/").replace(":", "\\\\:")

        # Animated bounce expression: x bounces back and forth by 25px towards target_x
        # x(t) = target_x - 170 + 25 * sin(2 * PI * (t - t_start) * 2.0)
        base_x = target["target_x"] - 180
        target_y = target["target_y"] - 50  # Center vertically with arrow height

        x_expr = f"{base_x}+25*sin(12.5*(t-{t_start:.2f}))"
        y_expr = f"{target_y}"

        # Overlay filter snippet
        filter_str = (
            f"overlay=x='{x_expr}':y='{y_expr}':"
            f"enable='between(t,{t_start:.2f},{t_end:.2f})'"
        )

        return {
            "enabled": True,
            "target": target,
            "arrow_image_path": str(arrow_png),
            "filter_string": filter_str,
            "t_start": t_start,
            "t_end": t_end,
            "duration": round(t_end - t_start, 2),
        }


if __name__ == "__main__":
    gfx = MotionGraphicsEngine()
    arrow = gfx.generate_arrow_asset("neon_cyan")
    print(f"MotionGraphicsEngine ready. Generated asset: {arrow}")
