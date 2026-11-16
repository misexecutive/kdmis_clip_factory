"""
Nyro AI Clip Factory - Video Effects & Color Grading Engine
Professional FFmpeg filter chain builder for gaming highlight clips.
Produces valid comma-separated FFmpeg video filter syntax for integration
with the renderer's filter_complex graph.
"""

import logging
import math
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Target output specs (matching renderer)
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
OUTPUT_FPS = 60


class VideoFXEngine:
    """Professional video effects and color grading engine using FFmpeg filter chains."""

    # ===== COLOR GRADING PRESETS =====
    COLOR_PRESETS: Dict[str, Dict[str, str]] = {
        "vibrant_tactical": {
            "description": "Boosted saturation + contrast for FPS/tactical shooters (COD, Valorant)",
            "filter": "eq=contrast=1.15:saturation=1.35:gamma=0.95:gamma_r=1.02:gamma_b=0.97,unsharp=5:5:0.8",
        },
        "cyberpunk_neon": {
            "description": "High-contrast with pushed blues/purples, cyberpunk aesthetic",
            "filter": (
                "eq=contrast=1.25:saturation=1.5:brightness=0.03,"
                "curves=blue='0/0 0.25/0.35 0.5/0.6 1/1':red='0/0 0.5/0.45 1/0.9',"
                "unsharp=5:5:1.0"
            ),
        },
        "clean_crisp": {
            "description": "Natural colors with enhanced sharpness and slight contrast boost",
            "filter": "eq=contrast=1.08:saturation=1.12:gamma=1.0,unsharp=7:7:1.2",
        },
        "cinematic_warm": {
            "description": "Warm tones with filmic contrast curve, slight desaturation of greens",
            "filter": (
                "eq=contrast=1.18:saturation=1.1:brightness=-0.02"
                ":gamma_r=1.08:gamma_g=0.98:gamma_b=0.92,"
                "curves=master='0/0 0.15/0.08 0.5/0.52 0.85/0.92 1/1',"
                "unsharp=5:5:0.6"
            ),
        },
        "dark_moody": {
            "description": "Crushed blacks, reduced highlights, dramatic contrast for horror/stealth games",
            "filter": (
                "eq=contrast=1.3:saturation=0.9:brightness=-0.06:gamma=0.85,"
                "curves=master='0/0.05 0.3/0.18 0.7/0.72 1/0.92',"
                "unsharp=3:3:0.5"
            ),
        },
    }

    # Zoom intensity presets: (base_max, punch_max, ease_back)
    _ZOOM_LEVELS = {
        "subtle": (1.03, 1.06, 1.02),
        "medium": (1.06, 1.12, 1.04),
        "heavy":  (1.08, 1.18, 1.06),
    }

    # Vignette angle presets (smaller angle = heavier darkening)
    _VIGNETTE_ANGLES = {
        "subtle": "PI/4",
        "medium": "PI/5",
        "heavy":  "PI/6.5",
    }

    def __init__(self) -> None:
        logger.info("VideoFXEngine initialised — %d color presets available", len(self.COLOR_PRESETS))

    # ------------------------------------------------------------------
    # Color grading
    # ------------------------------------------------------------------
    def get_color_grade_filter(self, preset_name: str = "vibrant_tactical") -> str:
        """Returns the FFmpeg filter string for a color grading preset."""
        if preset_name not in self.COLOR_PRESETS:
            logger.warning("Unknown preset '%s', falling back to vibrant_tactical", preset_name)
            preset_name = "vibrant_tactical"
        return self.COLOR_PRESETS[preset_name]["filter"]

    def auto_select_preset(self, candidate_clip_dict: dict) -> str:
        """
        Automatically selects the best color preset based on clip characteristics.

        Selection priority (first match wins):
        1. High intensity (>0.8) + audio_spike trigger → vibrant_tactical
        2. scene_change trigger → cinematic_warm
        3. Score > 85 → cyberpunk_neon (viral look)
        4. Micro clip format → clean_crisp (clarity at short duration)
        5. Default → vibrant_tactical
        """
        intensity = candidate_clip_dict.get("peak_intensity", 0.0)
        trigger = candidate_clip_dict.get("trigger_type", "")
        score = candidate_clip_dict.get("score", 0)
        clip_format = candidate_clip_dict.get("clip_format", "")

        if intensity > 0.8 and trigger == "audio_spike":
            preset = "vibrant_tactical"
        elif trigger == "scene_change":
            preset = "cinematic_warm"
        elif score > 85:
            preset = "cyberpunk_neon"
        elif clip_format == "micro":
            preset = "clean_crisp"
        else:
            preset = "vibrant_tactical"

        logger.info("Auto-selected color preset: %s (intensity=%.2f, trigger=%s, score=%s, format=%s)",
                     preset, intensity, trigger, score, clip_format)
        return preset

    # ------------------------------------------------------------------
    # Dynamic zoom
    # ------------------------------------------------------------------
    def build_dynamic_zoom_filter(
        self,
        clip_duration: float,
        peak_offset: float,
        zoom_intensity: str = "medium",
    ) -> str:
        """
        Builds an FFmpeg zoompan filter that creates a dynamic camera push-in effect.

        Phases:
        - Buildup (frames 0 → peak_frame): gentle ramp from 1.0x to base_max
        - Punch  (peak_frame → peak_frame + 6): quick punch to punch_max
        - Ease   (after punch → end): settle back to ease_back

        Uses expression-based keyframes with `on` (current frame number).
        """
        if zoom_intensity not in self._ZOOM_LEVELS:
            logger.warning("Unknown zoom_intensity '%s', using 'medium'", zoom_intensity)
            zoom_intensity = "medium"

        base_max, punch_max, ease_back = self._ZOOM_LEVELS[zoom_intensity]
        total_frames = max(1, int(clip_duration * OUTPUT_FPS))
        peak_frame = max(1, int(peak_offset * OUTPUT_FPS))
        punch_end = min(peak_frame + 6, total_frames)

        # Build a piecewise zoom expression using FFmpeg's if() syntax.
        # Phase 1  : 1.0 + (base_max-1) * on / peak_frame
        # Phase 2  : base_max + (punch_max - base_max) * (on - peak_frame) / 6
        # Phase 3  : punch_max - (punch_max - ease_back) * (on - punch_end) / (total_frames - punch_end)
        buildup_slope = base_max - 1.0
        punch_slope = punch_max - base_max
        ease_range = total_frames - punch_end if total_frames > punch_end else 1
        ease_slope = punch_max - ease_back

        zoom_expr = (
            f"if(lt(on\\,{peak_frame})\\,"
            f"1+{buildup_slope:.6f}*on/{peak_frame}\\,"
            f"if(lt(on\\,{punch_end})\\,"
            f"{base_max:.6f}+{punch_slope:.6f}*(on-{peak_frame})/6\\,"
            f"{punch_max:.6f}-{ease_slope:.6f}*(on-{punch_end})/{ease_range}"
            f"))"
        )

        zoompan_filter = (
            f"zoompan=z='{zoom_expr}'"
            f":x='iw/2-(iw/zoom/2)'"
            f":y='ih/2-(ih/zoom/2)'"
            f":d=1"
            f":s={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}"
            f":fps={OUTPUT_FPS}"
        )

        logger.info("Dynamic zoom built: intensity=%s, peak_frame=%d/%d, levels=%.2f→%.2f→%.2f",
                     zoom_intensity, peak_frame, total_frames, base_max, punch_max, ease_back)
        return zoompan_filter

    # ------------------------------------------------------------------
    # Vignette
    # ------------------------------------------------------------------
    def build_vignette_filter(self, intensity: str = "medium") -> str:
        """
        Returns FFmpeg vignette filter string.
        Adds cinematic edge darkening to focus viewer attention on center gameplay.
        """
        if intensity not in self._VIGNETTE_ANGLES:
            logger.warning("Unknown vignette intensity '%s', using 'medium'", intensity)
            intensity = "medium"
        angle = self._VIGNETTE_ANGLES[intensity]
        return f"vignette=angle={angle}"

    # ------------------------------------------------------------------
    # Impact flash
    # ------------------------------------------------------------------
    def build_impact_flash_filter(self, peak_offset: float, clip_duration: float) -> str:
        """
        Creates a brief white flash (~3 frames / 0.05s) at the peak moment.
        Uses the geq filter with a time-based brightness expression that spikes
        luma values for frames within the flash window.
        """
        flash_start = max(0.0, peak_offset - 0.025)
        flash_end = min(clip_duration, peak_offset + 0.025)

        # geq runs per-pixel. We boost luma toward 255 during the flash window
        # and leave chroma at neutral (128).  The gte/lte combo gates the flash
        # to a 0.05 s window.
        luma_expr = (
            f"if(between(T\\,{flash_start:.4f}\\,{flash_end:.4f})\\,"
            f"clip(lum(X\\,Y)*0.3+200\\,0\\,255)\\,"
            f"lum(X\\,Y))"
        )
        cb_expr = (
            f"if(between(T\\,{flash_start:.4f}\\,{flash_end:.4f})\\,128\\,cb(X\\,Y))"
        )
        cr_expr = (
            f"if(between(T\\,{flash_start:.4f}\\,{flash_end:.4f})\\,128\\,cr(X\\,Y))"
        )

        geq_filter = f"geq=lum_expr='{luma_expr}':cb_expr='{cb_expr}':cr_expr='{cr_expr}'"
        logger.info("Impact flash built: window=%.4f–%.4f s", flash_start, flash_end)
        return geq_filter

    # ------------------------------------------------------------------
    # Intro fade
    # ------------------------------------------------------------------
    def build_intro_fade_filter(self, fade_duration: float = 0.3) -> str:
        """Returns a fade=t=in filter for a smooth clip opening."""
        return f"fade=t=in:d={fade_duration:.2f}"

    # ------------------------------------------------------------------
    # Complete VFX chain builder
    # ------------------------------------------------------------------
    def build_complete_vfx_chain(
        self,
        candidate_clip_dict: dict,
        clip_duration: float,
        color_preset: str = "auto",
        enable_zoom: bool = True,
        enable_vignette: bool = True,
        enable_flash: bool = True,
        enable_fade: bool = True,
        zoom_intensity: str = "medium",
        vignette_intensity: str = "medium",
    ) -> Dict[str, Any]:
        """
        Builds the COMPLETE video filter chain combining all VFX in correct order:
        1. Color grading (first — operates on raw pixel values)
        2. Dynamic zoom (zoompan — before overlay composition)
        3. Vignette (edge darkening)
        4. Impact flash (at peak moment)
        5. Fade in (smooth opening)

        Returns dict with vfx_filter_chain, color_preset_used, and effects_applied.
        """
        filters: List[str] = []
        effects_applied: List[str] = []

        # Derive peak offset from candidate dict
        peak_ts = candidate_clip_dict.get("peak_timestamp", 0.0)
        start_ts = candidate_clip_dict.get("start_time", 0.0)
        peak_offset = max(0.0, peak_ts - start_ts)
        # Clamp to clip duration
        peak_offset = min(peak_offset, clip_duration)

        # --- 1. Color grading ---
        if color_preset == "auto":
            color_preset = self.auto_select_preset(candidate_clip_dict)
        color_filter = self.get_color_grade_filter(color_preset)
        filters.append(color_filter)
        effects_applied.append("color_grade")

        # --- 2. Dynamic zoom ---
        if enable_zoom:
            zoom_filter = self.build_dynamic_zoom_filter(clip_duration, peak_offset, zoom_intensity)
            filters.append(zoom_filter)
            effects_applied.append("dynamic_zoom")

        # --- 3. Vignette ---
        if enable_vignette:
            vig_filter = self.build_vignette_filter(vignette_intensity)
            filters.append(vig_filter)
            effects_applied.append("vignette")

        # --- 4. Impact flash ---
        if enable_flash:
            flash_filter = self.build_impact_flash_filter(peak_offset, clip_duration)
            filters.append(flash_filter)
            effects_applied.append("impact_flash")

        # --- 5. Fade in ---
        if enable_fade:
            fade_filter = self.build_intro_fade_filter()
            filters.append(fade_filter)
            effects_applied.append("fade_in")

        vfx_chain = ",".join(filters)

        logger.info("Complete VFX chain built: %d effects, preset=%s, peak_offset=%.2f s",
                     len(effects_applied), color_preset, peak_offset)

        return {
            "vfx_filter_chain": vfx_chain,
            "color_preset_used": color_preset,
            "effects_applied": effects_applied,
        }

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def list_presets(self) -> list:
        """Returns list of available color grading preset names and descriptions."""
        return [
            {"name": name, "description": data["description"]}
            for name, data in self.COLOR_PRESETS.items()
        ]


if __name__ == "__main__":
    engine = VideoFXEngine()
    print("=== Presets ===")
    for p in engine.list_presets():
        print(f"  {p['name']}: {p['description']}")
    print()
    sample = {
        "peak_intensity": 0.9,
        "trigger_type": "audio_spike",
        "score": 88,
        "clip_format": "micro",
        "peak_timestamp": 5.0,
        "start_time": 0.0,
    }
    result = engine.build_complete_vfx_chain(sample, 10.0)
    print("=== Complete VFX Chain ===")
    print(f"  Preset: {result['color_preset_used']}")
    print(f"  Effects: {result['effects_applied']}")
    print(f"  Filter chain:\n  {result['vfx_filter_chain']}")
