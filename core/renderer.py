"""
Nyro AI Clip Factory - Hardware-Accelerated 9:16 Vertical Renderer
Renders high-quality 1080x1920 YouTube Shorts with adaptive hardware encoding
(NVIDIA NVENC, Windows MediaFoundation, or multi-threaded libx264).
Includes:
- Prominent 960px tall centered gameplay (50% screen height)
- Broadcast-grade framing border & subtle cinematic vignette
- Advanced Color Grading presets (vibrant_tactical, cyberpunk_neon, clean_crisp, etc.)
- Contrast-enhanced dark pill hook banner (100% legibility)
- Optional Episodic Series Badge (e.g. '⚡ PART 1')
- Procedural Sound Design (tension risers, impact bass drops, whoosh transitions)
- EBU R128 (-14 LUFS) broadcast loudness mastering & pop-free micro-fades
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.video_fx import VideoFXEngine
from core.sound_engine import SoundDesigner
from core.export_validator import ExportValidator, ExportValidationReport
from core.motion_graphics import MotionGraphicsEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXPORTS_DIR = PROJECT_ROOT / "storage" / "exports"
DEFAULT_CACHE_DIR = PROJECT_ROOT / "storage" / "cache"
DEFAULT_SFX_DIR = PROJECT_ROOT / "storage" / "sfx"

WINDOWS_FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("C:/Windows/Fonts/segoeuib.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]


class VideoRenderer:
    def __init__(self, exports_dir: Optional[str] = None, cache_dir: Optional[str] = None):
        self.exports_dir = Path(exports_dir) if exports_dir else DEFAULT_EXPORTS_DIR
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.font_path = self._find_usable_font()
        self.encoder = self._detect_best_encoder()
        self.vfx_engine = VideoFXEngine()
        self.sound_designer = SoundDesigner(str(DEFAULT_SFX_DIR))
        self.validator = ExportValidator()
        self.gfx_engine = MotionGraphicsEngine()

    def _find_usable_font(self) -> Optional[str]:
        for f in WINDOWS_FONT_CANDIDATES:
            if f.exists():
                # Format for FFmpeg fontfile without quotes: C\\:/Windows/Fonts/arialbd.ttf
                escaped = str(f.resolve()).replace("\\", "/").replace(":", "\\\\:")
                logger.info(f"Using font for hooks: {escaped}")
                return escaped
        return None

    def _detect_best_encoder(self) -> str:
        test_encoders = ["h264_nvenc", "h264_mf", "libx264"]
        for enc in test_encoders:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.1",
                "-c:v", enc,
                "-f", "null", "-"
            ]
            try:
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                if res.returncode == 0:
                    logger.info(f"Hardware/Software encoder validated: {enc}")
                    return enc
            except Exception:
                continue

        logger.warning("Defaulting to libx264 encoder.")
        return "libx264"

    def render_short_9_16(
        self,
        input_video_path: str,
        start_time: float,
        end_time: float,
        output_filename: str,
        hook_text: Optional[str] = None,
        series_badge: Optional[str] = None,
        gameplay_height: int = 960,
        color_preset: str = "auto",
        enable_vfx: bool = True,
        enable_sfx: bool = True,
        peak_timestamp: Optional[float] = None,
        trigger_type: Optional[str] = "audio_spike",
        peak_intensity: Optional[float] = 1.0,
        score: Optional[float] = 85.0,
        clip_format: Optional[str] = "full",
    ) -> str:
        """
        Renders an upload-ready 9:16 (1080x1920) vertical video clip with broadcast polish:
        - Blurred background fill
        - Prominent 960px tall gameplay window with crisp separation border
        - Professional color grading tailored for tactical gaming
        - Subtle cinematic vignette focusing viewer eye on center crosshairs
        - Semi-transparent contrast pill box behind hook text
        - Optional series badge (e.g. '⚡ PART 1')
        - Procedural tension riser & impact bass drop SFX
        - Smooth audio in/out micro-fades and -14 LUFS loudness mastering
        """
        in_path = Path(input_video_path)
        out_path = self.exports_dir / output_filename
        duration = max(0.5, end_time - start_time)

        logger.info(
            f"Rendering 9:16 Short: {out_path.name} ({duration:.1f}s from {start_time:.1f}s to {end_time:.1f}s) "
            f"using {self.encoder} with gameplay height {gameplay_height}px | VFX: {enable_vfx} | SFX: {enable_sfx}"
        )

        fg_y_offset = (1920 - gameplay_height) // 2

        # 1. Color Grading & Video FX
        fg_filter = f"[0:v]scale=-1:{gameplay_height}:force_original_aspect_ratio=increase,crop=1080:{gameplay_height}"
        selected_preset = color_preset
        if enable_vfx:
            if color_preset == "auto":
                selected_preset = self.vfx_engine.auto_select_preset({
                    "peak_intensity": peak_intensity or 1.0,
                    "trigger_type": trigger_type or "audio_spike",
                    "score": score or 85.0,
                    "clip_format": clip_format or "full",
                })
            grade_filter = self.vfx_engine.get_color_grade_filter(selected_preset)
            fg_filter += f",{grade_filter}"
            logger.info(f"Color Grading: Applied '{selected_preset}' preset to foreground gameplay.")

        fg_filter += f",drawbox=x=0:y=0:w=1080:h={gameplay_height}:color=white@0.20:t=3[fg];"

        # 2. Background blur + Foreground overlay + subtle vignette
        filter_graph = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:3[bg];"
            f"{fg_filter}"
            f"[bg][fg]overlay=0:{fg_y_offset}"
        )

        if enable_vfx:
            filter_graph += ",vignette=PI/5.5[v_base]"
        else:
            filter_graph += "[v_base]"

        current_v_label = "[v_base]"

        # 3. Optional Series Badge (e.g. '⚡ PART 1')
        if series_badge and series_badge.strip() and self.font_path:
            clean_badge = series_badge.strip().upper()
            badge_y = max(160, fg_y_offset - 240)
            badge_filter = (
                f";{current_v_label}drawtext=fontfile={self.font_path}:text='{clean_badge}':"
                f"fontsize=28:fontcolor=0x00e5ff:box=1:boxcolor=black@0.75:boxborderw=8:"
                f"x=(w-text_w)/2:y={badge_y}[v_badge]"
            )
            filter_graph += badge_filter
            current_v_label = "[v_badge]"
            logger.info(f"Applying series badge: '{clean_badge}' at y={badge_y}")

        # 4. Hook text with semi-transparent contrast pill box
        if hook_text and hook_text.strip() and self.font_path:
            clean_hook = hook_text.strip()
            hook_file = self.cache_dir / f"hook_{Path(output_filename).stem}.txt"
            hook_file.write_text(clean_hook, encoding="utf-8")
            esc_hook_file = str(hook_file.resolve()).replace("\\", "/").replace(":", "\\\\:")

            hook_y_pos = max(240, fg_y_offset - 150)
            drawtext_filter = (
                f";{current_v_label}drawtext=fontfile={self.font_path}:textfile={esc_hook_file}:"
                f"fontsize=44:fontcolor=white:box=1:boxcolor=black@0.70:boxborderw=14:"
                f"borderw=2:bordercolor=black:x=(w-text_w)/2:y={hook_y_pos}[v_hook]"
            )
            filter_graph += drawtext_filter
            current_v_label = "[v_hook]"
            logger.info(f"Applying hook overlay pill: '{clean_hook}' at y={hook_y_pos}")

        # 5. Audio FX & Sound Design
        audio_fade_out_st = max(0.1, duration - 0.25)
        sfx_inputs: List[Dict[str, Any]] = []
        has_sfx = False

        if enable_sfx:
            try:
                actual_peak = peak_timestamp if peak_timestamp is not None else (start_time + duration * 0.6)
                cand_meta = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "peak_timestamp": actual_peak,
                    "trigger_type": trigger_type or "audio_spike",
                    "peak_intensity": peak_intensity or 1.0,
                    "score": score or 85.0,
                    "clip_format": clip_format or "full",
                }
                audio_plan = self.sound_designer.design_audio_for_clip(cand_meta, duration)
                placements = audio_plan.get("sfx_placements", [])
                for pl in placements:
                    p_file = self.sound_designer.sfx_dir / pl["sfx_file"]
                    if p_file.exists() and p_file.stat().st_size > 0:
                        sfx_inputs.append(pl)

                if sfx_inputs:
                    has_sfx = True
            except Exception as e:
                logger.warning(f"Audio sound design planning error: {e}")

        # Assemble FFmpeg Command
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", f"{start_time:.3f}",
            "-to", f"{end_time:.3f}",
            "-i", str(in_path.resolve()),
        ]

        if has_sfx:
            # Add each SFX file as an additional input
            for pl in sfx_inputs:
                sfx_path = (self.sound_designer.sfx_dir / pl["sfx_file"]).resolve()
                cmd.extend(["-i", str(sfx_path)])

            # Build audio filter graph
            audio_filter_parts = [
                "[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[gameplay]"
            ]
            sfx_labels = []
            for i, pl in enumerate(sfx_inputs, 1):
                label = f"sfx{i}"
                delay_ms = max(0, int(self.sound_designer._resolve_offset_ms(pl, start_time, end_time, duration)))
                vol = pl.get("volume", 0.4)
                audio_filter_parts.append(
                    f"[{i}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
                    f"volume={vol},adelay={delay_ms}|{delay_ms}[{label}]"
                )
                sfx_labels.append(f"[{label}]")

            n_inputs = 1 + len(sfx_labels)
            mix_inputs = "[gameplay]" + "".join(sfx_labels)
            weights = " ".join(["1"] * n_inputs)
            audio_filter_parts.append(
                f"{mix_inputs}amix=inputs={n_inputs}:duration=first:dropout_transition=0:weights={weights}[mixed]"
            )
            # Compression + Loudness Normalization (-14 LUFS) + Micro-fades
            audio_filter_parts.append(
                f"[mixed]acompressor=threshold=0.08:ratio=3:attack=5:release=120:makeup=1.5,"
                f"loudnorm=I=-14:LRA=11:TP=-1,"
                f"afade=t=in:ss=0:d=0.15,afade=t=out:st={audio_fade_out_st:.2f}:d=0.25[a_master]"
            )

            filter_graph += ";" + ";".join(audio_filter_parts)
            cmd.extend([
                "-filter_complex", filter_graph,
                "-map", current_v_label,
                "-map", "[a_master]",
            ])
        else:
            # Standard audio micro-fade filter
            audio_filter = f"afade=t=in:ss=0:d=0.15,afade=t=out:st={audio_fade_out_st:.2f}:d=0.25"
            cmd.extend([
                "-filter_complex", filter_graph,
                "-map", current_v_label,
                "-map", "0:a?",
                "-af", audio_filter,
            ])

        cmd.extend(["-c:v", self.encoder])
        if self.encoder == "h264_nvenc":
            cmd.extend(["-preset", "p6", "-tune", "hq", "-b:v", "14M", "-maxrate", "18M", "-bufsize", "25M"])
        elif self.encoder == "h264_mf":
            cmd.extend(["-b:v", "12M"])
        else:  # libx264
            cmd.extend(["-preset", "veryfast", "-crf", "19"])

        # Preserved high-fidelity AAC audio + broadcast pixel format & faststart
        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "aac",
            "-b:a", "256k",
            "-ar", "48000",
            str(out_path.resolve()),
        ])

        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Render failed with {self.encoder}: {e.stderr}")
            if self.encoder != "libx264":
                logger.warning("Falling back to reliable libx264 software encoder...")
                self.encoder = "libx264"
                return self.render_short_9_16(
                    input_video_path, start_time, end_time, output_filename,
                    hook_text=hook_text, series_badge=series_badge, gameplay_height=gameplay_height,
                    color_preset=color_preset, enable_vfx=enable_vfx, enable_sfx=enable_sfx,
                    peak_timestamp=peak_timestamp, trigger_type=trigger_type,
                    peak_intensity=peak_intensity, score=score, clip_format=clip_format
                )
            raise e

        val_report = self.verify_export_quality(str(out_path))
        if not val_report.get("valid", True):
            raise ValueError(f"Export validation failed: {val_report.get('errors')}")

        logger.info(f"Render verified & ready: {out_path.name}")
        return str(out_path.resolve())

    def verify_export_quality(self, exported_video_path: str) -> Dict[str, Any]:
        report = self.validator.validate_export(exported_video_path)
        return report.to_dict()


if __name__ == "__main__":
    renderer = VideoRenderer()
    print(f"VideoRenderer ready. Selected Encoder: {renderer.encoder}")
