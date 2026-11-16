"""
Sound Design & SFX Engine for Nyro AI Clip Factory.

Provides the SoundDesigner class that maps candidate clip metadata to
SFX placements and generates FFmpeg audio filter chains for the
rendering pipeline.
"""

from __future__ import annotations

import os
import math
from pathlib import Path
from typing import Dict, List, Optional


from core.sfx_manager import SFXLibraryManager, SFXAsset, SFX_CATALOGUE, MANIFEST_PATH

# ── Loudnorm / mastering constants ─────────────────────────────────────
LOUDNORM_TARGET = "loudnorm=I=-14:LRA=11:TP=-1"
FADE_IN_DURATION = 0.15        # seconds
FADE_OUT_DURATION = 0.25       # seconds
DUCK_GAIN_DB = -6              # dB to duck gameplay when SFX plays
SIDECHAIN_ATTACK = 0.005       # seconds
SIDECHAIN_RELEASE = 0.15       # seconds


class SoundDesigner:
    """Maps candidate clip metadata to SFX placements and FFmpeg audio filters."""

    # ------------------------------------------------------------------ #
    #  Construction / discovery                                           #
    # ------------------------------------------------------------------ #
    def __init__(self, sfx_dir: Optional[str] = None):
        if sfx_dir is None:
            # Default: storage/sfx/ relative to the project root
            project_root = Path(__file__).resolve().parent.parent
            sfx_dir = str(project_root / "storage" / "sfx")
        self.sfx_dir = Path(sfx_dir)
        self.available_sfx: Dict[str, Path] = {}
        self.sfx_mgr = SFXLibraryManager(self.sfx_dir)
        self._discover_sfx()

    def _discover_sfx(self) -> None:
        """Scan *sfx_dir* for WAV files and register them."""
        if not self.sfx_dir.is_dir():
            return
        for entry in self.sfx_dir.iterdir():
            if entry.suffix.lower() == ".wav" and entry.stat().st_size > 0:
                self.available_sfx[entry.name] = entry

    # ------------------------------------------------------------------ #
    #  Public API                                                         #
    # ------------------------------------------------------------------ #
    def design_audio_for_clip(
        self,
        candidate_clip_dict: dict,
        video_duration: float,
    ) -> dict:
        """Return SFX placement plan + filter chain for a candidate clip.

        Parameters
        ----------
        candidate_clip_dict : dict
            Keys: start_time, end_time, peak_timestamp, trigger_type,
            peak_intensity, score, clip_format.
        video_duration : float
            Total duration of the source video in seconds.

        Returns
        -------
        dict  with keys ``sfx_placements``, ``audio_filter_chain``,
              ``master_loudnorm``.
        """
        start = float(candidate_clip_dict["start_time"])
        end = float(candidate_clip_dict["end_time"])
        peak = float(candidate_clip_dict["peak_timestamp"])
        score = float(candidate_clip_dict.get("score", 75))
        clip_fmt = candidate_clip_dict.get("clip_format", "full")

        clip_dur = end - start
        peak_rel = peak - start  # peak position inside the clip
        is_micro = clip_dur <= 14.0
        category = candidate_clip_dict.get("category", "")
        is_weapon_mechanics = (category == "Weapon Mechanics")
        is_explosion = (category == "Epic Explosions")

        placements: List[dict] = []

        # ── Whoosh at clip start (hook text entrance) ──────────────────
        if "whoosh_transition.wav" in self.available_sfx:
            vol = 0.45 if score > 85 else 0.40
            placements.append({
                "sfx_file": "whoosh_transition.wav",
                "start_offset": 0.2,
                "volume": vol,
                "relative_to": "start",
                "_peak_rel": peak_rel,
            })
            # Double whoosh for high-intensity clips (avoid if weapon mechanics)
            if score > 85 and clip_dur > 3.0 and not is_weapon_mechanics:
                placements.append({
                    "sfx_file": "whoosh_transition.wav",
                    "start_offset": 0.55,
                    "volume": vol * 0.6,
                    "relative_to": "start",
                    "_peak_rel": peak_rel,
                })

        # ── Riser before peak ──────────────────────────────────────────
        # Avoid heavy riser for weapon mechanics to preserve original audio
        if "riser_cinematic.wav" in self.available_sfx and score >= 70 and not is_weapon_mechanics:
            riser_meta = SFX_CATALOGUE["riser"]
            riser_dur = riser_meta["duration"]
            # Place riser so it ends ~0.1s before peak
            offset = -(riser_dur - 0.1)  # typically -1.9
            vol = riser_meta["default_vol"]
            if is_micro:
                vol *= 0.7  # lighter for micro clips
            if score > 85 or is_explosion:
                vol = min(vol * 1.3, 0.6)
            placements.append({
                "sfx_file": "riser_cinematic.wav",
                "start_offset": round(offset, 3),
                "volume": round(vol, 3),
                "relative_to": "peak",
                "_peak_rel": peak_rel,
            })

        # ── Impact at peak ─────────────────────────────────────────────
        # For weapon mechanics, preserve natural sound without artificial bass drop
        if "impact_bass_drop.wav" in self.available_sfx and not is_weapon_mechanics:
            vol = SFX_CATALOGUE["impact"]["default_vol"]
            if score > 85 or is_explosion:
                vol = min(vol * 1.3, 0.7)
            placements.append({
                "sfx_file": "impact_bass_drop.wav",
                "start_offset": 0.0,
                "volume": round(vol, 3),
                "relative_to": "peak",
                "_peak_rel": peak_rel,
            })

        # ── Hitmarker at peak (for gunshot / reflex triggers) ──────────
        trigger = candidate_clip_dict.get("trigger_type", "")
        if ("hitmarker_snap.wav" in self.available_sfx
                and trigger in ("gunfire", "reflex", "kill", "headshot", "")):
            placements.append({
                "sfx_file": "hitmarker_snap.wav",
                "start_offset": 0.02,
                "volume": SFX_CATALOGUE["hitmarker"]["default_vol"],
                "relative_to": "peak",
                "_peak_rel": peak_rel,
            })

        # ── Tension drone (full clips, score >= 70) ────────────────────
        if (not is_micro
                and score >= 70
                and "tension_drone.wav" in self.available_sfx):
            drone_meta = SFX_CATALOGUE["drone"]
            # Start drone early — 3s before peak, clamped to clip start
            offset = max(-peak_rel, -drone_meta["duration"])
            placements.append({
                "sfx_file": "tension_drone.wav",
                "start_offset": round(offset, 3),
                "volume": drone_meta["default_vol"],
                "relative_to": "peak",
                "_peak_rel": peak_rel,
            })

        # ── Glitch transition (near clip end for outro) ────────────────
        if "glitch_stutter.wav" in self.available_sfx and clip_dur > 5.0:
            placements.append({
                "sfx_file": "glitch_stutter.wav",
                "start_offset": -0.5,
                "volume": SFX_CATALOGUE["glitch"]["default_vol"],
                "relative_to": "end",
                "_peak_rel": peak_rel,
            })

        # Build the filter chain string
        filter_chain = self.get_audio_filter_chain(clip_dur, placements)

        return {
            "sfx_placements": placements,
            "audio_filter_chain": filter_chain,
            "master_loudnorm": True,
        }

    # ------------------------------------------------------------------ #
    #  FFmpeg command builder                                              #
    # ------------------------------------------------------------------ #
    def build_ffmpeg_audio_overlay_cmd(
        self,
        input_video: str,
        clip_start: float,
        clip_end: float,
        sfx_placements: list,
        output_path: str,
    ) -> list:
        """Build a complete FFmpeg command list for audio overlay rendering.

        The command:
        1. Extracts the gameplay audio segment (clip_start → clip_end).
        2. Overlays each SFX WAV at the calculated timestamp using adelay.
        3. Applies sidechain-style ducking (gameplay −6 dB when SFX plays).
        4. Normalises to EBU R128 −14 LUFS via loudnorm.
        5. Applies fade-in / fade-out.
        """
        clip_dur = clip_end - clip_start

        # ── Inputs ─────────────────────────────────────────────────────
        cmd: List[str] = ["ffmpeg", "-y"]

        # Input 0: gameplay video (we extract audio)
        cmd += ["-ss", str(clip_start), "-t", str(clip_dur), "-i", input_video]

        # Inputs 1..N: SFX files
        sfx_inputs: List[dict] = []
        for idx, pl in enumerate(sfx_placements):
            sfx_path = str(self.sfx_dir / pl["sfx_file"])
            cmd += ["-i", sfx_path]
            sfx_inputs.append({"index": idx + 1, **pl})

        # ── Filter complex ─────────────────────────────────────────────
        filter_parts: List[str] = []

        # Label gameplay audio
        filter_parts.append("[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[gameplay]")

        # Process each SFX: volume + delay
        sfx_labels: List[str] = []
        for i, si in enumerate(sfx_inputs):
            label = f"sfx{i}"
            delay_ms = self._resolve_offset_ms(si, clip_start, clip_end, clip_dur)
            delay_ms = max(0, delay_ms)
            vol = si.get("volume", 0.4)
            filter_parts.append(
                f"[{si['index']}:a]"
                f"aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,"
                f"volume={vol},"
                f"adelay={int(delay_ms)}|{int(delay_ms)}"
                f"[{label}]"
            )
            sfx_labels.append(f"[{label}]")

        # Mix gameplay + SFX
        n_inputs = 1 + len(sfx_labels)
        mix_inputs = "[gameplay]" + "".join(sfx_labels)
        # weights: gameplay at 1.0, SFX already volume-adjusted so 1.0
        weights = " ".join(["1"] * n_inputs)
        filter_parts.append(
            f"{mix_inputs}amix=inputs={n_inputs}:duration=first"
            f":dropout_transition=0:weights={weights}[mixed]"
        )

        # Apply ducking (lower gameplay when SFX energy is present)
        # We approximate sidechain ducking by using dynaudnorm after the mix
        # For true sidechain we would need sidechaincompress, but amix already
        # balances, so we apply a gentle compressor to tame peaks.
        filter_parts.append(
            "[mixed]acompressor=threshold=0.05:ratio=4:attack=5:release=150"
            ":makeup=2[compressed]"
        )

        # Loudnorm to EBU R128
        filter_parts.append(f"[compressed]{LOUDNORM_TARGET}[normed]")

        # Fade in / out
        fade_out_start = max(0, clip_dur - FADE_OUT_DURATION)
        filter_parts.append(
            f"[normed]afade=t=in:d={FADE_IN_DURATION},"
            f"afade=t=out:st={fade_out_start:.3f}:d={FADE_OUT_DURATION}[aout]"
        )

        cmd += ["-filter_complex", ";".join(filter_parts)]
        cmd += ["-map", "0:v", "-map", "[aout]"]
        cmd += ["-c:v", "copy", "-c:a", "pcm_s16le", "-ar", "48000"]
        cmd += [output_path]
        return cmd

    # ------------------------------------------------------------------ #
    #  Filter chain string (for renderer merging)                         #
    # ------------------------------------------------------------------ #
    def get_audio_filter_chain(
        self,
        clip_duration: float,
        sfx_placements: list,
    ) -> str:
        """Return the ``-filter_complex`` audio portion as a single string.

        This is designed to be merged with the video filter chain by the
        clip renderer.  Input pads assume the caller has labelled gameplay
        audio as ``[0:a]`` and SFX inputs as ``[1:a]``, ``[2:a]``, etc.
        """
        parts: List[str] = []

        # Gameplay audio prep
        parts.append(
            "[0:a]aformat=sample_fmts=fltp:sample_rates=48000"
            ":channel_layouts=mono[gameplay]"
        )

        sfx_labels: List[str] = []
        for i, pl in enumerate(sfx_placements):
            label = f"sfx{i}"
            delay_ms = self._resolve_offset_ms_generic(pl, clip_duration)
            delay_ms = max(0, delay_ms)
            vol = pl.get("volume", 0.4)
            parts.append(
                f"[{i + 1}:a]"
                f"aformat=sample_fmts=fltp:sample_rates=48000"
                f":channel_layouts=mono,"
                f"volume={vol},"
                f"adelay={int(delay_ms)}|{int(delay_ms)}"
                f"[{label}]"
            )
            sfx_labels.append(f"[{label}]")

        n = 1 + len(sfx_labels)
        weights = " ".join(["1"] * n)
        parts.append(
            f"[gameplay]{''.join(sfx_labels)}"
            f"amix=inputs={n}:duration=first"
            f":dropout_transition=0:weights={weights}[mixed]"
        )

        parts.append(
            "[mixed]acompressor=threshold=0.05:ratio=4:attack=5:release=150"
            ":makeup=2[compressed]"
        )

        parts.append(f"[compressed]{LOUDNORM_TARGET}[normed]")

        fade_out_start = max(0, clip_duration - FADE_OUT_DURATION)
        parts.append(
            f"[normed]afade=t=in:d={FADE_IN_DURATION},"
            f"afade=t=out:st={fade_out_start:.3f}:d={FADE_OUT_DURATION}[aout]"
        )

        return ";".join(parts)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _resolve_offset_ms(
        sfx_input: dict,
        clip_start: float,
        clip_end: float,
        clip_dur: float,
    ) -> float:
        """Convert a placement dict to an absolute delay in milliseconds
        relative to the start of the extracted clip."""
        relative_to = sfx_input.get("relative_to", "peak")
        offset = sfx_input.get("start_offset", 0.0)

        if relative_to == "start":
            abs_sec = offset
        elif relative_to == "end":
            abs_sec = clip_dur + offset
        elif relative_to == "peak":
            # peak_timestamp is not stored on the sfx_input when called
            # from build_ffmpeg_audio_overlay_cmd, so we default to mid-clip
            peak_rel = sfx_input.get("_peak_rel", clip_dur / 2)
            abs_sec = peak_rel + offset
        else:
            abs_sec = offset

        return abs_sec * 1000.0

    @staticmethod
    def _resolve_offset_ms_generic(
        placement: dict,
        clip_duration: float,
    ) -> float:
        """Resolve offset for get_audio_filter_chain (no absolute times)."""
        relative_to = placement.get("relative_to", "peak")
        offset = placement.get("start_offset", 0.0)

        if relative_to == "start":
            abs_sec = offset
        elif relative_to == "end":
            abs_sec = clip_duration + offset
        elif relative_to == "peak":
            peak_rel = placement.get("_peak_rel", clip_duration * 0.4)
            abs_sec = peak_rel + offset
        else:
            abs_sec = offset

        return abs_sec * 1000.0
