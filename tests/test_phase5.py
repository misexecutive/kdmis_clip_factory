"""
Unit tests for Nyro AI Clip Factory - Phase 5: NYRO AURA ENGINE
Tests 7 foundational profiles, deterministic seed reproducibility,
customized editorial strategies, and JSON blueprint serialization.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.aura_engine import NyroAuraEngine, EditingBlueprint, AURA_PROFILES
from core.clip_discovery import CandidateClip


def test_aura_engine():
    engine = NyroAuraEngine()
    assert len(AURA_PROFILES) == 7

    # Case 1: Epic Explosion -> CINEMATIC AURA
    c_exp = CandidateClip(
        id="clip_exp_01",
        video_filename="gameplay.mp4",
        start_time=10.0,
        end_time=27.5,
        duration=17.5,
        peak_timestamp=19.0,
        trigger_type="bass_explosion",
        peak_intensity=0.95,
        events=[],
        clip_format="full",
        category="Epic Explosions",
        score=88.5,
    )
    bp_exp = engine.generate_blueprint(c_exp, deterministic_seed=42)
    assert bp_exp.aura_profile == "CINEMATIC AURA"
    assert bp_exp.color_grading["preset"] == "cinematic_warm"
    assert bp_exp.zoom_strategy["enabled"] is True
    assert bp_exp.audio_treatment["sub_bass_enhancement"] is True
    print(f"✓ Epic Explosion mapped to: {bp_exp.aura_profile} (Color: {bp_exp.color_grading['preset']})")

    # Case 2: Weapon Mechanics -> REALISM or MINIMAL (Preserve raw fidelity, no artificial drone)
    c_wep = CandidateClip(
        id="clip_wep_01",
        video_filename="gameplay.mp4",
        start_time=5.0,
        end_time=13.5,
        duration=8.5,
        peak_timestamp=9.0,
        trigger_type="gunfire_transient",
        peak_intensity=0.70,
        events=[],
        clip_format="micro",
        category="Weapon Mechanics",
        score=72.0,
    )
    bp_wep = engine.generate_blueprint(c_wep, deterministic_seed=42)
    assert bp_wep.aura_profile in ("MINIMAL AURA", "REALISM AURA")
    assert bp_wep.zoom_strategy["enabled"] is False  # Pure raw fidelity
    print(f"✓ Weapon Mechanics mapped to: {bp_wep.aura_profile} (Zoom: {bp_wep.zoom_strategy['enabled']})")

    # Case 3: Intense Gunfights -> CHAOS AURA
    c_chaos = CandidateClip(
        id="clip_chaos_01",
        video_filename="gameplay.mp4",
        start_time=2.0,
        end_time=19.5,
        duration=17.5,
        peak_timestamp=11.0,
        trigger_type="rapid_flick",
        peak_intensity=0.88,
        events=[],
        clip_format="full",
        category="Intense Gunfights",
        score=85.0,
    )
    bp_chaos = engine.generate_blueprint(c_chaos, deterministic_seed=99)
    assert bp_chaos.aura_profile == "CHAOS AURA"
    assert bp_chaos.color_grading["preset"] == "vibrant_tactical"
    assert bp_chaos.zoom_strategy["intensity"] in ("medium", "heavy")
    print(f"✓ Intense Gunfight mapped to: {bp_chaos.aura_profile} (Zoom: {bp_chaos.zoom_strategy['intensity']})")

    # Case 4: Deterministic Reproducibility
    bp1 = engine.generate_blueprint(c_exp, deterministic_seed=12345)
    bp2 = engine.generate_blueprint(c_exp, deterministic_seed=12345)
    assert bp1.to_dict() == bp2.to_dict(), "Expected identical blueprints with same seed"
    print("✓ Deterministic seed reproducibility verified.")

    # Case 5: JSON Blueprint Serialization
    out_bp_path = PROJECT_ROOT / "data" / "test_blueprint.json"
    bp1.save_json(out_bp_path)
    assert out_bp_path.exists()
    with open(out_bp_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["aura_profile"] == "CINEMATIC AURA"
    assert "editorial_rationale" in loaded
    out_bp_path.unlink(missing_ok=True)
    print("✓ JSON blueprint serialization verified.")

    print("\nALL PHASE 5 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_aura_engine()
