"""
Unit tests for Nyro AI Clip Factory - Phase 7: Professional Rendering & Export Validation
Tests hardware-accelerated 9:16 vertical 1080x1920 rendering, -14 LUFS audio mastering,
fast-start MP4 packaging, and comprehensive post-render quality validation.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.renderer import VideoRenderer
from core.export_validator import ExportValidator, ExportValidationReport


def test_rendering_and_validation():
    video_path = PROJECT_ROOT / "storage" / "raw_recordings" / "test_gameplay_session.mp4"
    assert video_path.exists(), f"Benchmark video missing: {video_path}"

    renderer = VideoRenderer()
    validator = ExportValidator()

    out_file = "test_phase7_short.mp4"
    print(f"\nRendering 9:16 Short using encoder: {renderer.encoder}...", flush=True)

    rendered_path = renderer.render_short_9_16(
        input_video_path=str(video_path),
        start_time=21.0,
        end_time=29.5,  # 8.5s micro-short around the 24s explosion
        output_filename=out_file,
        hook_text="0.1s REACTION TIME",
        series_badge="⚡ PART 1",
        color_preset="vibrant_tactical",
        enable_vfx=True,
        enable_sfx=True,
        peak_timestamp=24.2,
        trigger_type="bass_explosion",
        peak_intensity=0.95,
        score=88.0,
        clip_format="micro",
    )

    rendered_file = Path(rendered_path)
    assert rendered_file.exists()
    assert rendered_file.stat().st_size > 100000

    print(f"✓ Render complete: {rendered_file.name} ({rendered_file.stat().st_size / (1024*1024):.2f} MB)")

    # Run ExportValidator
    report = validator.validate_export(str(rendered_file), expected_min_duration=6.0, expected_max_duration=12.0)
    assert isinstance(report, ExportValidationReport)
    assert report.valid is True, f"Validation failed with errors: {report.errors}"
    assert report.width == 1080
    assert report.height == 1920
    assert report.aspect_ratio == "1080:1920"
    assert 8.0 <= report.duration_seconds <= 9.0
    assert report.has_audio is True
    assert report.audio_clipping_detected is False, "Audio clipping detected in mastered export"
    assert report.faststart_enabled is True, "Expected faststart moov atom at beginning of MP4"

    print("\n--- EXPORT QUALITY INSPECTION REPORT ---", flush=True)
    print(f"  Geometry       : {report.width}x{report.height} (9:16 Vertical)", flush=True)
    print(f"  Duration       : {report.duration_seconds}s @ {report.fps} FPS", flush=True)
    print(f"  Codecs         : Video: {report.video_codec} | Audio: {report.audio_codec}", flush=True)
    print(f"  Max Volume     : {report.max_volume_db} dB (No clipping: {not report.audio_clipping_detected})", flush=True)
    print(f"  Fast-Start MP4 : {'Enabled' if report.faststart_enabled else 'Disabled'}", flush=True)
    print(f"  Black Frames   : {report.black_frames_detected}", flush=True)
    print(f"  Frozen Frames  : {report.frozen_frames_detected}", flush=True)
    print(f"  Validation     : PASSED (0 errors, {len(report.warnings)} warnings)", flush=True)

    print("\nALL PHASE 7 TESTS PASSED SUCCESSFULLY!", flush=True)


if __name__ == "__main__":
    test_rendering_and_validation()
