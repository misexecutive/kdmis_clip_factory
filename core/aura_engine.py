"""
Nyro AI Clip Factory - NYRO AURA ENGINE (Module 5)
Synthesizes unique, content-aware editing blueprints for every individual clip.
Profiles:
- CINEMATIC AURA: Dramatic pacing, atmospheric contrast, controlled widescreen push, subtle whooshes.
- REALISM AURA: Pristine uncompressed fidelity, zero artificial distractions, mechanical emphasis.
- CHAOS AURA: High-energy zooms, tactical color grade, aggressive impact flash, multi-layered SFX.
- COMEDY AURA: Snappy timing, humorous text emphasis, comedic glitch accents.
- SUSPENSE AURA: Extended tension drone buildup, delayed payoff release, vignette focus.
- SATISFACTION AURA: Frame-perfect kill snap zoom, crisp hitmarker sound, immediate reward.
- MINIMAL AURA: Pure original gameplay preservation with clean vertical reframing only.
Every decision is saved into an individual JSON editing blueprint (editing_blueprint.json).
"""

import hashlib
import json
import logging
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.clip_discovery import CandidateClip

logger = logging.getLogger("AuraEngine")

AURA_PROFILES = [
    "CINEMATIC AURA",
    "REALISM AURA",
    "CHAOS AURA",
    "COMEDY AURA",
    "SUSPENSE AURA",
    "SATISFACTION AURA",
    "MINIMAL AURA",
]


@dataclass
class EditingBlueprint:
    clip_id: str
    aura_profile: str
    seed: int
    category: str
    secondary_categories: List[str]
    opening_strategy: Dict[str, Any]
    crop_strategy: Dict[str, Any]
    zoom_strategy: Dict[str, Any]
    color_grading: Dict[str, Any]
    audio_treatment: Dict[str, Any]
    sfx_selection: List[Dict[str, Any]]
    motion_graphics: Dict[str, Any]
    text_treatment: Dict[str, Any]
    transition_strategy: Dict[str, Any]
    ending_strategy: Dict[str, Any]
    editorial_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save_json(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class NyroAuraEngine:
    """The master editorial director producing tailored editing blueprints."""

    def __init__(self):
        logger.info("NYRO AURA ENGINE initialised with 7 foundational profiles.")

    def select_aura_profile(self, candidate: CandidateClip) -> str:
        """Determines the most authentic AURA profile for the gameplay context."""
        cat = candidate.category
        dur = candidate.duration
        score = candidate.score
        intensity = candidate.peak_intensity
        events = candidate.events or []
        has_cut = any("cut" in e.get("event_type", "").lower() for e in events)

        # 1. Comedy / Funny moments
        if cat in ("Funny Gameplay", "NPC Reactions"):
            return "COMEDY AURA"

        # 2. Weapon mechanics & realistic graphics -> Realism or Minimal
        elif cat in ("Weapon Mechanics", "Realistic Graphics", "Immersive Realism"):
            if score > 85:
                return "REALISM AURA"
            else:
                return "MINIMAL AURA"

        # 3. Epic explosions & cinematic moments
        elif cat in ("Epic Explosions", "Cinematic Gameplay", "Story Moments"):
            return "CINEMATIC AURA"

        # 4. Intense gunfights & chaos
        elif cat in ("Intense Gunfights", "Vehicle Crashes"):
            return "CHAOS AURA"

        # 5. Satisfying kills & close calls
        elif cat in ("Satisfying Kills", "Close Calls"):
            return "SATISFACTION AURA"

        # 6. Unexpected moments & twists
        elif cat in ("Unexpected Moments", "Unexpected Twists"):
            return "SUSPENSE AURA"

        # Default fallback based on intensity
        if intensity > 0.8:
            return "CHAOS AURA"
        return "CINEMATIC AURA"

    def generate_blueprint(
        self,
        candidate: CandidateClip,
        deterministic_seed: Optional[int] = None,
    ) -> EditingBlueprint:
        """
        Synthesizes a complete individual JSON editing blueprint for this specific clip.
        Every single effect and parameter is justified by the footage.
        """
        # Deterministic seed from clip id if not supplied
        if deterministic_seed is None:
            h = int(hashlib.md5(candidate.id.encode("utf-8")).hexdigest(), 16)
            seed = h % 1000000
        else:
            seed = deterministic_seed

        rng = random.Random(seed)
        profile_name = self.select_aura_profile(candidate)

        # Base properties
        dur = candidate.duration
        peak_t = candidate.peak_timestamp
        start_t = candidate.start_time
        peak_offset = peak_t - start_t
        is_micro = candidate.clip_format == "micro" or dur <= 12.0

        # Build individual strategies based on AURA profile:

        # 1. Color Grading Strategy
        if profile_name == "CINEMATIC AURA":
            color_preset = "cinematic_warm"
            vignette = "subtle"  # PI/4
        elif profile_name == "REALISM AURA":
            color_preset = "clean_crisp"
            vignette = "none"
        elif profile_name == "CHAOS AURA":
            color_preset = "vibrant_tactical"
            vignette = "medium"  # PI/5
        elif profile_name == "COMEDY AURA":
            color_preset = "clean_crisp"
            vignette = "subtle"
        elif profile_name == "SUSPENSE AURA":
            color_preset = "dark_moody"
            vignette = "heavy"  # PI/6.5
        elif profile_name == "SATISFACTION AURA":
            color_preset = "cyberpunk_neon" if candidate.score > 82 else "vibrant_tactical"
            vignette = "medium"
        else:  # MINIMAL AURA
            color_preset = "clean_crisp"
            vignette = "none"

        # 2. Crop & Framing Strategy
        # Standard 960px tall gameplay window centered at y=480 (50% screen height)
        crop_strat = {
            "mode": "smart_center_960",
            "gameplay_height_px": 960,
            "y_offset_px": 480,
            "background_blur_sigma": 25 if profile_name != "MINIMAL AURA" else 35,
            "border_enabled": True,
            "border_color": "white@0.20",
            "border_width_px": 3,
        }

        # 3. Dynamic Zoom Strategy
        if profile_name == "CHAOS AURA":
            zoom_strat = {
                "enabled": True,
                "intensity": "heavy" if is_micro else "medium",
                "peak_offset_s": round(peak_offset, 2),
                "punch_frames": 6,
                "rationale": "High-velocity camera punch timed to the combat climax",
            }
        elif profile_name == "SATISFACTION AURA":
            zoom_strat = {
                "enabled": True,
                "intensity": "medium",
                "peak_offset_s": round(peak_offset, 2),
                "punch_frames": 4,
                "rationale": "Micro snap-zoom focusing crosshair impact at elimination",
            }
        elif profile_name == "CINEMATIC AURA":
            zoom_strat = {
                "enabled": True,
                "intensity": "subtle",
                "peak_offset_s": round(peak_offset, 2),
                "punch_frames": 8,
                "rationale": "Slow cinematic push-in elevating scene tension",
            }
        else:
            zoom_strat = {
                "enabled": False,
                "intensity": "none",
                "peak_offset_s": round(peak_offset, 2),
                "punch_frames": 0,
                "rationale": "Static crop to preserve raw visual fidelity",
            }

        # 4. Opening Strategy
        opening_strat = {
            "hook_entrance_delay_s": 0.2,
            "hook_sound": "whoosh_transition.wav" if profile_name != "MINIMAL AURA" else None,
            "hook_sound_volume": 0.40,
            "fade_in_duration_s": 0.15,
        }

        # 5. Audio Treatment Strategy
        audio_strat = {
            "target_loudness_lufs": -14.0,
            "true_peak_limit_db": -1.0,
            "lra": 11.0,
            "compressor_enabled": True,
            "gameplay_sidechain_duck_db": -6.0 if profile_name in ("CHAOS AURA", "CINEMATIC AURA") else -4.0,
            "sub_bass_enhancement": True if profile_name in ("CINEMATIC AURA", "CHAOS AURA") else False,
        }

        # 6. SFX Selection Strategy
        sfx_list = []
        if profile_name != "MINIMAL AURA":
            # Hook whoosh
            sfx_list.append({
                "sfx_file": "whoosh_transition.wav",
                "offset_s": 0.2,
                "relative_to": "start",
                "volume": 0.40,
                "role": "hook_entrance",
            })
            # Tension buildup riser
            if profile_name in ("CINEMATIC AURA", "SUSPENSE AURA", "CHAOS AURA") and not is_micro:
                sfx_list.append({
                    "sfx_file": "riser_cinematic.wav",
                    "offset_s": -1.9,
                    "relative_to": "peak",
                    "volume": 0.35,
                    "role": "climax_buildup",
                })
            # Climax impact
            if profile_name in ("CINEMATIC AURA", "CHAOS AURA", "SATISFACTION AURA"):
                sfx_list.append({
                    "sfx_file": "impact_bass_drop.wav",
                    "offset_s": 0.0,
                    "relative_to": "peak",
                    "volume": 0.50 if candidate.score > 85 else 0.45,
                    "role": "climax_impact",
                })
            # Hitmarker snap
            if profile_name in ("SATISFACTION AURA", "CHAOS AURA") or candidate.category == "Weapon Mechanics":
                sfx_list.append({
                    "sfx_file": "hitmarker_snap.wav",
                    "offset_s": 0.02,
                    "relative_to": "peak",
                    "volume": 0.45,
                    "role": "kill_confirmation",
                })
            # Glitch outro transition
            if profile_name == "CHAOS AURA" and dur > 6.0:
                sfx_list.append({
                    "sfx_file": "glitch_stutter.wav",
                    "offset_s": -0.5,
                    "relative_to": "end",
                    "volume": 0.35,
                    "role": "outro_transition",
                })

        # 7. Motion Graphics & CTA Strategy
        # CTA arrow is an optional, editorial addition
        cta_enabled = (profile_name in ("SATISFACTION AURA", "CHAOS AURA") and candidate.score >= 78.0)
        motion_gfx = {
            "animated_cta_arrow": cta_enabled,
            "cta_target": "youtube_shorts_like_button",
            "cta_enter_s": max(1.0, dur - 3.5) if cta_enabled else 0.0,
            "cta_duration_s": 2.2 if cta_enabled else 0.0,
            "cta_color": "0x00e5ff",
            "safe_zone_compliant": True,
        }

        # 8. Text Treatment Strategy
        text_strat = {
            "font_size_px": 44 if is_micro else 42,
            "font_color": "white",
            "pill_box_enabled": True,
            "pill_box_color": "black@0.70",
            "pill_border_width_px": 14,
            "y_pos_px": 330,  # Positioned above gameplay, compliant with safe zones
            "series_badge_enabled": bool(candidate.series_part),
            "series_badge_text": candidate.series_part or "",
            "series_badge_color": "0x00e5ff",
        }

        # 9. Transition & Ending Strategy
        trans_strat = {
            "intro_transition": "instant_cut",
            "outro_transition": "audio_micro_fade",
            "fade_out_duration_s": 0.25,
            "seamless_loop_hint": is_micro,
        }

        # Editorial Rationale
        rationale = (
            f"Tailored under {profile_name} for category '{candidate.category}' (Score: {candidate.score:.1f}/100). "
            f"Color grading '{color_preset}' enhances atmospheric contrast, dynamic zoom '{zoom_strat['intensity']}' "
            f"maintains center-crosshair focus, and audio loudness mastered to -14 LUFS."
        )

        blueprint = EditingBlueprint(
            clip_id=candidate.id,
            aura_profile=profile_name,
            seed=seed,
            category=candidate.category,
            secondary_categories=candidate.secondary_categories or [],
            opening_strategy=opening_strat,
            crop_strategy=crop_strat,
            zoom_strategy=zoom_strat,
            color_grading={
                "preset": color_preset,
                "vignette": vignette,
            },
            audio_treatment=audio_strat,
            sfx_selection=sfx_list,
            motion_graphics=motion_gfx,
            text_treatment=text_strat,
            transition_strategy=trans_strat,
            ending_strategy={"loop_blend": is_micro, "audio_fade_s": 0.25},
            editorial_rationale=rationale,
        )

        candidate.aura_profile = profile_name
        return blueprint


if __name__ == "__main__":
    engine = NyroAuraEngine()
    print("NyroAuraEngine ready with 7 distinct AURA profiles.")
