"""
Unit tests for Nyro AI Clip Factory - Phase 8: Centralized Metadata & Export Bundler
Tests the mandatory output folder structure:
output/<recording_name>/<clip_id>/
  ├── video.mp4
  ├── metadata.txt
  ├── metadata.json
  ├── editing_blueprint.json
  ├── analysis_report.json
  ├── assets_manifest.json
  └── thumbnail.jpg
"""

import json
import sys
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.packaging import CentralExportPackager
from core.clip_discovery import CandidateClip
from core.aura_engine import NyroAuraEngine


def test_export_packaging():
    packager = CentralExportPackager()
    aura_engine = NyroAuraEngine()

    # Use the test short rendered in Phase 7
    rendered_file = PROJECT_ROOT / "storage" / "exports" / "test_phase7_short.mp4"
    assert rendered_file.exists(), f"Rendered video missing: {rendered_file}"

    candidate = CandidateClip(
        id="clip_001",
        video_filename="test_gameplay_session.mp4",
        start_time=21.0,
        end_time=29.5,
        duration=8.5,
        peak_timestamp=24.2,
        trigger_type="bass_explosion",
        peak_intensity=0.95,
        events=[],
        clip_format="micro",
        category="Epic Explosions",
        score=88.0,
    )
    blueprint = aura_engine.generate_blueprint(candidate, deterministic_seed=42)

    clip_dir = packager.package_clip_export(
        source_recording_filename="test_gameplay_session.mp4",
        clip_id="clip_001",
        rendered_video_path=str(rendered_file),
        candidate=candidate,
        blueprint=blueprint,
        selected_hook="0.1s REACTION TIME",
        selected_title="The Cleanest Detonation In Gaming History",
    )

    assert clip_dir.exists(), f"Clip directory missing: {clip_dir}"
    assert clip_dir.name == "clip_001"
    assert clip_dir.parent.name == "test_gameplay_session"

    # Check the 7 required files
    expected_files = [
        "video.mp4",
        "metadata.txt",
        "metadata.json",
        "editing_blueprint.json",
        "analysis_report.json",
        "assets_manifest.json",
        "thumbnail.jpg",
    ]
    for fn in expected_files:
        fp = clip_dir / fn
        assert fp.exists(), f"Required file missing from bundle: {fn}"
        assert fp.stat().st_size > 0, f"File is empty: {fn}"

    # Verify metadata.txt content format
    txt_content = (clip_dir / "metadata.txt").read_text(encoding="utf-8")
    assert "TITLE:\nThe Cleanest Detonation In Gaming History" in txt_content
    assert "DESCRIPTION:" in txt_content
    assert "HASHTAGS:" in txt_content
    assert "TAGS (CSV):" in txt_content
    assert "HOOK TEXT:\n0.1s REACTION TIME" in txt_content
    assert "CATEGORY:\nEpic Explosions" in txt_content
    assert "AURA PROFILE:\nCINEMATIC AURA" in txt_content
    assert "METADATA RATIONALE:" in txt_content

    # Verify thumbnail.jpg
    with Image.open(clip_dir / "thumbnail.jpg") as img:
        assert img.size == (1080, 1920)
        assert img.format == "JPEG"

    print("\n--- STANDARDIZED EXPORT BUNDLE VERIFIED ---", flush=True)
    print(f"Directory: {clip_dir}", flush=True)
    for fn in expected_files:
        size = (clip_dir / fn).stat().st_size
        print(f"  ├── {fn:<22} ({size} bytes)", flush=True)

    print("\nALL PHASE 8 TESTS PASSED SUCCESSFULLY!", flush=True)


if __name__ == "__main__":
    test_export_packaging()
