"""
Nyro AI Clip Factory - System Configuration & Profiles
Provides centralized, configurable profiles (FAST, BALANCED, MAXIMUM_QUALITY),
hardware settings, scoring weights, vertical safe zones, and audio mastering specs.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "data" / "clip_factory_config.json"


@dataclass
class HardwareConfig:
    prefer_gpu: bool = True
    gpu_device_id: int = 0
    nvenc_preset: str = "p6"  # p1 (fastest) to p7 (highest quality)
    nvenc_tune: str = "hq"
    max_video_bitrate: str = "18M"
    target_video_bitrate: str = "14M"
    audio_bitrate: str = "256k"
    cpu_threads: int = 0  # 0 = auto


@dataclass
class RetentionScoringWeights:
    hook_potential: float = 0.15
    visual_quality: float = 0.15
    audio_quality: float = 0.10
    event_significance: float = 0.15
    payoff: float = 0.15
    emotional_impact: float = 0.10
    replay_loop_potential: float = 0.10
    originality: float = 0.05
    technical_quality: float = 0.05


@dataclass
class SafeZoneConfig:
    # YouTube Shorts safe zones in 1080x1920
    top_margin_px: int = 240       # Avoid channel header / search bar
    bottom_margin_px: int = 380    # Avoid title, sound button, description, channel name
    right_margin_px: int = 140     # Avoid like, comment, share, remix icons
    left_margin_px: int = 40


@dataclass
class ProcessingProfile:
    name: str = "MAXIMUM_QUALITY"  # FAST, BALANCED, MAXIMUM_QUALITY
    description: str = "Deep multi-pass analysis, optical flow, scene clustering, high-fidelity SFX"
    video_sample_fps: float = 8.0  # Frames per second sampled during Pass B
    optical_flow_enabled: bool = True
    audio_spectral_enabled: bool = True
    speech_vad_enabled: bool = True
    refine_scene_cuts: bool = True
    candidate_micro_range: tuple = (6.0, 10.0)
    candidate_extended_range: tuple = (15.0, 20.0)
    min_score_threshold: float = 60.0


@dataclass
class SystemConfig:
    channel_name: str = "Gamer Nyro"
    profile_name: str = "MAXIMUM_QUALITY"
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    scoring_weights: RetentionScoringWeights = field(default_factory=RetentionScoringWeights)
    safe_zones: SafeZoneConfig = field(default_factory=SafeZoneConfig)
    master_loudness_target_lufs: float = -14.0
    master_true_peak_db: float = -1.0
    master_lra: float = 11.0
    profiles: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "FAST": {
            "name": "FAST",
            "description": "Rapid preview mode using keyframes and energy spikes only",
            "video_sample_fps": 2.0,
            "optical_flow_enabled": False,
            "audio_spectral_enabled": False,
            "speech_vad_enabled": False,
            "refine_scene_cuts": False,
            "candidate_micro_range": [6.0, 10.0],
            "candidate_extended_range": [15.0, 20.0],
            "min_score_threshold": 50.0,
        },
        "BALANCED": {
            "name": "BALANCED",
            "description": "Standard production with motion heuristics and spectral analysis",
            "video_sample_fps": 4.0,
            "optical_flow_enabled": True,
            "audio_spectral_enabled": True,
            "speech_vad_enabled": True,
            "refine_scene_cuts": True,
            "candidate_micro_range": [6.0, 10.0],
            "candidate_extended_range": [15.0, 20.0],
            "min_score_threshold": 55.0,
        },
        "MAXIMUM_QUALITY": {
            "name": "MAXIMUM_QUALITY",
            "description": "Comprehensive 4-pass intelligence, fine-grained optical flow, dual-tier candidate clustering",
            "video_sample_fps": 8.0,
            "optical_flow_enabled": True,
            "audio_spectral_enabled": True,
            "speech_vad_enabled": True,
            "refine_scene_cuts": True,
            "candidate_micro_range": [6.0, 10.0],
            "candidate_extended_range": [15.0, 20.0],
            "min_score_threshold": 60.0,
        },
    })

    def get_active_profile(self) -> ProcessingProfile:
        p_dict = self.profiles.get(self.profile_name, self.profiles["MAXIMUM_QUALITY"])
        return ProcessingProfile(
            name=p_dict.get("name", "MAXIMUM_QUALITY"),
            description=p_dict.get("description", ""),
            video_sample_fps=float(p_dict.get("video_sample_fps", 8.0)),
            optical_flow_enabled=bool(p_dict.get("optical_flow_enabled", True)),
            audio_spectral_enabled=bool(p_dict.get("audio_spectral_enabled", True)),
            speech_vad_enabled=bool(p_dict.get("speech_vad_enabled", True)),
            refine_scene_cuts=bool(p_dict.get("refine_scene_cuts", True)),
            candidate_micro_range=tuple(p_dict.get("candidate_micro_range", (6.0, 10.0))),
            candidate_extended_range=tuple(p_dict.get("candidate_extended_range", (15.0, 20.0))),
            min_score_threshold=float(p_dict.get("min_score_threshold", 60.0)),
        )

    def save(self, filepath: Optional[Path] = None):
        target = filepath or CONFIG_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> "SystemConfig":
        target = filepath or CONFIG_FILE
        if not target.exists():
            instance = cls()
            instance.save(target)
            return instance
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            hw = HardwareConfig(**data.get("hardware", {}))
            weights = RetentionScoringWeights(**data.get("scoring_weights", {}))
            safe = SafeZoneConfig(**data.get("safe_zones", {}))
            return cls(
                channel_name=data.get("channel_name", "Gamer Nyro"),
                profile_name=data.get("profile_name", "MAXIMUM_QUALITY"),
                hardware=hw,
                scoring_weights=weights,
                safe_zones=safe,
                master_loudness_target_lufs=data.get("master_loudness_target_lufs", -14.0),
                master_true_peak_db=data.get("master_true_peak_db", -1.0),
                master_lra=data.get("master_lra", 11.0),
                profiles=data.get("profiles", {}),
            )
        except Exception:
            return cls()


config = SystemConfig.load()
