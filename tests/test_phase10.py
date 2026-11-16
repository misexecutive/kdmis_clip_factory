"""
Tests for Phase 10: Complete End-to-End Pipeline & Output Bundle Verification
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from core.export_validator import ExportValidator

def test_output_bundle_integrity():
    output_base = Path("output/test_gameplay_session")
    assert output_base.exists(), f"Output directory {output_base} does not exist"

    clip_dirs = [d for d in output_base.iterdir() if d.is_dir()]
    assert len(clip_dirs) >= 2, f"Expected at least 2 exported clip directories, found {len(clip_dirs)}"

    required_files = [
        "video.mp4",
        "metadata.txt",
        "metadata.json",
        "editing_blueprint.json",
        "analysis_report.json",
        "assets_manifest.json",
        "thumbnail.jpg",
    ]

    validator = ExportValidator()

    for clip_dir in clip_dirs:
        print(f"\n[Verifying Bundle]: {clip_dir.name}")
        for rf in required_files:
            target_file = clip_dir / rf
            assert target_file.exists(), f"Missing required file '{rf}' in {clip_dir}"
            assert target_file.stat().st_size > 0, f"File '{rf}' in {clip_dir} is empty (0 bytes)"
            print(f"  ✓ Found {rf} ({target_file.stat().st_size} bytes)")

        # Validate JSON structures
        with open(clip_dir / "metadata.json", "r", encoding="utf-8") as f:
            meta = json.load(f)
            assert "title" in meta
            assert "hook_text" in meta
            assert "category" in meta

        with open(clip_dir / "editing_blueprint.json", "r", encoding="utf-8") as f:
            bp = json.load(f)
            assert "aura_profile" in bp
            assert "color_grading" in bp
            assert "sfx_selection" in bp

        with open(clip_dir / "assets_manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
            assert "clip_sfx_assets" in manifest

        # Validate video broadcast quality
        rep = validator.validate_export(str(clip_dir / "video.mp4"))
        assert rep.valid, f"Validation failed for {clip_dir / 'video.mp4'}: {rep.errors}"
        assert rep.width == 1080 and rep.height == 1920, f"Expected 1080x1920, got {rep.width}x{rep.height}"
        assert rep.faststart_enabled, "Faststart MP4 (moov atom at start) not enabled"
        print(f"  ✓ Quality Validation: 1080x1920 @ {rep.fps}fps, {rep.duration_seconds}s, Max Vol: {rep.max_volume_db}dB, Faststart: {rep.faststart_enabled}")

    print("\nALL OUTPUT BUNDLES VERIFIED WITH 100% INTEGRITY & BROADCAST COMPLIANCE!")

if __name__ == "__main__":
    test_output_bundle_integrity()
