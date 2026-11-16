---
name: video-effects-grading
description: >
  Professional video effects and color grading engine for gaming highlight clips.
  Builds valid FFmpeg filter chains for color grading, dynamic zoom, vignette,
  impact flash, and intro fade — all tuned for 9:16 vertical YouTube Shorts.
---

# Video Effects & Color Grading Engine

> [!NOTE]
> Module location: `core/video_fx.py`
> Class: `VideoFXEngine`

The VFX engine produces **valid FFmpeg filter chain strings** (comma-separated)
that can be injected into a `-filter_complex` graph. All filters target
**1080×1920 @ 60 fps** output.

---

## Quick Start

```python
from core.video_fx import VideoFXEngine

engine = VideoFXEngine()

# Get the complete filter chain for a candidate clip
result = engine.build_complete_vfx_chain(
    candidate_clip_dict={
        "peak_intensity": 0.9,
        "trigger_type": "audio_spike",
        "score": 88,
        "clip_format": "micro",
        "peak_timestamp": 5.0,
        "start_time": 0.0,
    },
    clip_duration=10.0,
)

ffmpeg_filters = result["vfx_filter_chain"]   # pass to -vf or filter_complex
preset_used    = result["color_preset_used"]   # e.g. "vibrant_tactical"
fx_list        = result["effects_applied"]     # ["color_grade", "dynamic_zoom", ...]
```

---

## Color Grading Presets

Five built-in presets cover common gaming aesthetics:

| Preset | Description | Key Settings |
|---|---|---|
| **vibrant_tactical** | Boosted saturation + contrast for FPS/tactical shooters (COD, Valorant) | contrast 1.15, saturation 1.35, gamma 0.95, unsharp 5:5:0.8 |
| **cyberpunk_neon** | High-contrast with pushed blues/purples, cyberpunk aesthetic | contrast 1.25, sat 1.5, blue curve push, unsharp 5:5:1.0 |
| **clean_crisp** | Natural colors with enhanced sharpness and slight contrast boost | contrast 1.08, sat 1.12, unsharp 7:7:1.2 |
| **cinematic_warm** | Warm tones with filmic contrast curve, slight green desaturation | contrast 1.18, warm gamma shift, S-curve master, unsharp 5:5:0.6 |
| **dark_moody** | Crushed blacks, reduced highlights, dramatic contrast for horror/stealth | contrast 1.3, sat 0.9, lifted blacks curve, unsharp 3:3:0.5 |

### Auto-Selection Logic

`auto_select_preset(candidate_clip_dict)` picks the best preset automatically:

1. **High intensity (>0.8) + audio_spike trigger** → `vibrant_tactical`
2. **scene_change trigger** → `cinematic_warm`
3. **Score > 85** → `cyberpunk_neon` (viral look)
4. **Micro clip format** → `clean_crisp` (clarity at short duration)
5. **Default** → `vibrant_tactical`

---

## Dynamic Zoom

`build_dynamic_zoom_filter(clip_duration, peak_offset, zoom_intensity)`

Creates a camera push-in effect with three phases:

| Phase | Frames | Behaviour |
|---|---|---|
| Buildup | 0 → peak | Gentle ramp from 1.0× to base_max |
| Punch | peak → peak+6 | Quick punch zoom to punch_max |
| Ease | after punch → end | Settle back to ease_back |

### Zoom Intensity Levels

| Level | Buildup Max | Punch Max | Ease Back |
|---|---|---|---|
| `subtle` | 1.03× | 1.06× | 1.02× |
| `medium` | 1.06× | 1.12× | 1.04× |
| `heavy` | 1.08× | 1.18× | 1.06× |

Uses FFmpeg `zoompan` with expression-based `z`, centred `x`/`y`, `d=1`, `s=1080x1920`, `fps=60`.

---

## Vignette

`build_vignette_filter(intensity)`

Applies cinematic edge darkening to focus attention on centre gameplay.

| Intensity | FFmpeg Angle |
|---|---|
| `subtle` | `PI/4` |
| `medium` | `PI/5` |
| `heavy` | `PI/6.5` |

---

## Impact Flash

`build_impact_flash_filter(peak_offset, clip_duration)`

Brief white flash (~3 frames / 0.05 s) at the peak moment using the `geq` filter.
Luma is boosted toward 255 and chroma set to neutral (128) within the flash window,
creating a dramatic emphasis on the kill/impact frame.

- `peak_offset` is relative to clip start (`peak_timestamp - start_time`).

---

## Intro Fade

`build_intro_fade_filter(fade_duration=0.3)`

Simple `fade=t=in:d=0.30` for a smooth opening. Default 0.3 s.

---

## Complete Chain Builder

`build_complete_vfx_chain(...)` assembles all effects in the correct pipeline order:

```
Color Grade → Dynamic Zoom → Vignette → Impact Flash → Fade In
```

> [!IMPORTANT]
> Color grading is applied **first** because it operates on original pixel values.
> Zoom comes before overlay composition. Fade is last so it covers the composited frame.

### Parameters

| Param | Type | Default | Description |
|---|---|---|---|
| `candidate_clip_dict` | dict | — | Clip metadata (peak_intensity, trigger_type, score, clip_format, peak_timestamp, start_time) |
| `clip_duration` | float | — | Duration of the clip in seconds |
| `color_preset` | str | `"auto"` | Preset name or `"auto"` for auto-selection |
| `enable_zoom` | bool | `True` | Include dynamic zoom |
| `enable_vignette` | bool | `True` | Include vignette |
| `enable_flash` | bool | `True` | Include impact flash |
| `enable_fade` | bool | `True` | Include intro fade |
| `zoom_intensity` | str | `"medium"` | Zoom level: subtle / medium / heavy |
| `vignette_intensity` | str | `"medium"` | Vignette level: subtle / medium / heavy |

### Return Value

```python
{
    "vfx_filter_chain": "eq=...,zoompan=...,vignette=...,geq=...,fade=...",
    "color_preset_used": "vibrant_tactical",
    "effects_applied": ["color_grade", "dynamic_zoom", "vignette", "impact_flash", "fade_in"]
}
```

---

## Utilities

- `list_presets()` → list of `{"name": str, "description": str}` for all colour presets.
- `get_color_grade_filter(preset_name)` → raw FFmpeg filter string for a single preset.
