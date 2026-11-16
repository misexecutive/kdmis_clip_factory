"""
Unit tests for Nyro AI Clip Factory - Phase 6: Dynamic Motion Graphics & CTA System
Tests RGBA animated arrow rendering, platform targets, safe-zone positioning,
and FFmpeg overlay expression generation.
"""

import sys
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.motion_graphics import MotionGraphicsEngine, PLATFORM_CTA_TARGETS
from core.config import config


def test_motion_graphics():
    gfx = MotionGraphicsEngine()

    # Test arrow asset generation
    arrow_path = gfx.generate_arrow_asset(style="neon_cyan", width=160, height=100)
    assert arrow_path.exists()
    assert arrow_path.stat().st_size > 500

    # Verify PNG image mode and alpha channel
    with Image.open(arrow_path) as img:
        assert img.size == (160, 100)
        assert img.mode == "RGBA"
        # Check non-empty alpha channel
        extrema = img.getextrema()
        assert extrema[3][1] > 0  # Alpha channel has opaque/translucent pixels

    print(f"✓ Motion graphics RGBA asset verified: {arrow_path.name} ({img.size[0]}x{img.size[1]})")

    # Test Platform CTA targets
    assert "youtube_shorts_like" in PLATFORM_CTA_TARGETS
    assert "youtube_shorts_share" in PLATFORM_CTA_TARGETS
    assert "instagram_reels_like" in PLATFORM_CTA_TARGETS

    # Test overlay filter generation
    overlay_plan = gfx.build_cta_overlay_filter(
        cta_target_name="youtube_shorts_like",
        clip_duration=15.0,
        enter_delay_before_end=3.0,
        active_duration=2.2,
    )
    assert overlay_plan["enabled"] is True
    assert "overlay=" in overlay_plan["filter_string"]
    assert "enable='between(t," in overlay_plan["filter_string"]
    assert overlay_plan["t_start"] == 12.0
    assert overlay_plan["t_end"] == 14.2

    # Verify safe-zone compliance
    safe = config.safe_zones
    target = overlay_plan["target"]
    assert target["target_y"] > safe.top_margin_px, "Target violates top safe-zone margin"
    assert target["target_y"] < (1920 - safe.bottom_margin_px + 200), "Target violates bottom margin"
    print(f"✓ Platform CTA overlay verified: {target['platform']} '{target['action']}' @ ({target['target_x']}, {target['target_y']})")
    print(f"  Overlay Filter: {overlay_plan['filter_string']}")

    print("\nALL PHASE 6 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_motion_graphics()
