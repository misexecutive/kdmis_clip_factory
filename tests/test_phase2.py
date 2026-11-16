"""
Unit tests for Nyro AI Clip Factory - Phase 2: Deep Audiovisual Intelligence
Tests 4-pass analysis: Pass A (Technical), Pass B (Visual/Optical Flow),
Pass C (Audio/Spectral/Sub-bass), Pass D (Contextual Fusion & JSON Report).
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.deep_intelligence import DeepIntelligenceEngine, DeepAnalysisReport
from core.config import config


def test_deep_intelligence():
    video_path = PROJECT_ROOT / "storage" / "raw_recordings" / "test_gameplay_session.mp4"
    assert video_path.exists(), f"Benchmark video missing: {video_path}"

    engine = DeepIntelligenceEngine()
    profile = config.get_active_profile()

    print(f"\nRunning 4-Pass Deep Intelligence on {video_path.name} (Profile: {profile.name})...", flush=True)
    t0 = time.time()
    report = engine.analyze_recording(str(video_path), profile=profile)
    total_time = time.time() - t0

    assert isinstance(report, DeepAnalysisReport)
    assert report.duration_seconds > 50.0
    assert report.resolution == "1920x1080"
    assert report.fps == 60.0
    assert len(report.audio_events) > 0, "Expected audio events in benchmark video around 24s-26s"
    assert len(report.contextual_moments) > 0, "Expected contextual moments generated"
    assert "pass_a_technical_s" in report.pass_timings
    assert "pass_b_visual_s" in report.pass_timings
    assert "pass_c_audio_s" in report.pass_timings
    assert "pass_d_contextual_s" in report.pass_timings

    # Verify report JSON serialization
    report_file = PROJECT_ROOT / "data" / "test_deep_report.json"
    report.save_json(report_file)
    assert report_file.exists() and report_file.stat().st_size > 500

    print(f"\n--- ACTUAL PASS TIMINGS ---", flush=True)
    print(f"  Pass A (Technical Inspection) : {report.pass_timings['pass_a_technical_s']:.3f}s", flush=True)
    print(f"  Pass B (Visual & Optical Flow): {report.pass_timings['pass_b_visual_s']:.3f}s", flush=True)
    print(f"  Pass C (Multi-Band Audio DSP) : {report.pass_timings['pass_c_audio_s']:.3f}s", flush=True)
    print(f"  Pass D (Contextual Fusion)    : {report.pass_timings['pass_d_contextual_s']:.3f}s", flush=True)
    print(f"  Total Processing Time         : {total_time:.3f}s (Realtime factor: {(report.duration_seconds / total_time):.2f}x)", flush=True)

    print(f"\n--- PASS RESULTS ---", flush=True)
    print(f"✓ Technical Pass: {report.resolution} @ {report.fps}fps, {report.duration_seconds}s", flush=True)
    print(f"✓ Visual Pass: {len(report.visual_events)} visual events, avg motion: {report.average_visual_motion}", flush=True)
    print(f"✓ Audio Pass: {len(report.audio_events)} audio events, dynamic range: {report.audio_dynamic_range_db} dB", flush=True)
    print(f"✓ Contextual Pass: {len(report.contextual_moments)} contextual moments synthesized", flush=True)

    top_moment = report.contextual_moments[0]
    print(f"  Top Moment: [{top_moment['primary_category']}] Peak at {top_moment['peak_timestamp']}s, "
          f"Confidence: {top_moment['confidence']*100:.0f}%, Fusion Score: {top_moment['fusion_score']}", flush=True)

    report_file.unlink(missing_ok=True)
    print("\nALL PHASE 2 TESTS PASSED SUCCESSFULLY!", flush=True)


if __name__ == "__main__":
    test_deep_intelligence()
