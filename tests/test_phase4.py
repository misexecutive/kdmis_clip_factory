"""
Unit tests for Nyro AI Clip Factory - Phase 4: SFX Library & License-Aware Asset Management
Tests 20-category SFX organization, SHA-256 checksums, CC0/Public Domain licensing records,
and category-sensitive sound design rules.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.sfx_manager import SFXLibraryManager, SFXAsset, SFX_20_CATEGORIES
from core.sound_engine import SoundDesigner


def test_sfx_library_manager():
    mgr = SFXLibraryManager()
    assert len(mgr.assets) >= 6, f"Expected at least 6 assets, got {len(mgr.assets)}"
    assert len(SFX_20_CATEGORIES) == 20

    # Verify manifest file exists
    assert mgr.manifest_file.exists()
    with open(mgr.manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert manifest_data["library_name"] == "Nyro AI Clip Factory SFX Suite"
    assert "assets" in manifest_data

    # Verify checksums and licensing
    for asset in mgr.assets.values():
        assert len(asset.sha256) == 64, f"Invalid SHA-256 for {asset.filename}"
        assert "CC0" in asset.license or "Public Domain" in asset.license
        assert asset.attribution_required is False
        assert Path(asset.filepath).exists()

    print(f"✓ SFXLibraryManager loaded {len(mgr.assets)} verified CC0 assets with SHA-256 checksums.")


def test_intelligent_sound_design_rules():
    designer = SoundDesigner()

    # Case 1: Epic Explosion clip
    explosion_clip = {
        "start_time": 10.0,
        "end_time": 28.0,
        "peak_timestamp": 20.0,
        "trigger_type": "bass_explosion",
        "peak_intensity": 0.95,
        "score": 88.0,
        "clip_format": "full",
        "category": "Epic Explosions",
    }
    plan_exp = designer.design_audio_for_clip(explosion_clip, video_duration=60.0)
    exp_files = [p["sfx_file"] for p in plan_exp["sfx_placements"]]
    assert "impact_bass_drop.wav" in exp_files
    assert "riser_cinematic.wav" in exp_files
    print(f"✓ Epic Explosions received low-end impact and riser reinforcement: {exp_files}")

    # Case 2: Weapon Mechanics clip (must preserve weapon audio and avoid heavy overlays)
    weapon_clip = {
        "start_time": 5.0,
        "end_time": 13.5,
        "peak_timestamp": 9.0,
        "trigger_type": "gunfire_transient",
        "peak_intensity": 0.70,
        "score": 75.0,
        "clip_format": "micro",
        "category": "Weapon Mechanics",
    }
    plan_wep = designer.design_audio_for_clip(weapon_clip, video_duration=60.0)
    wep_files = [p["sfx_file"] for p in plan_wep["sfx_placements"]]
    # Must NOT contain heavy bass drop or heavy riser
    assert "impact_bass_drop.wav" not in wep_files
    assert "riser_cinematic.wav" not in wep_files
    print(f"✓ Weapon Mechanics preserved original weapon audio without artificial bass/riser overlays: {wep_files}")

    # Case 3: Export per-clip manifest
    test_manifest_path = PROJECT_ROOT / "data" / "test_clip_assets_manifest.json"
    designer.sfx_mgr.export_clip_manifest(exp_files, test_manifest_path)
    assert test_manifest_path.exists()
    with open(test_manifest_path, "r", encoding="utf-8") as f:
        clip_manifest = json.load(f)
    assert len(clip_manifest["clip_sfx_assets"]) == len(set(exp_files))
    test_manifest_path.unlink(missing_ok=True)
    print("✓ Per-clip assets_manifest.json export verified.")

    print("\nALL PHASE 4 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_sfx_library_manager()
    test_intelligent_sound_design_rules()
