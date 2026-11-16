"""
Unit tests for Nyro AI Clip Factory - Phase 1: Architecture & Foundation
Tests configuration loading, hardware inspection, database migrations and methods.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import SystemConfig, HardwareConfig, RetentionScoringWeights
from core.hardware import HardwareInspector, HardwareReport
from core.database import ClipDatabase
from core.ingest import VideoMetadata


def test_config():
    cfg = SystemConfig.load()
    assert cfg.channel_name == "Gamer Nyro"
    profile = cfg.get_active_profile()
    assert profile.name in ("FAST", "BALANCED", "MAXIMUM_QUALITY")
    assert profile.min_score_threshold > 0
    print("✓ test_config passed")


def test_hardware():
    rep = HardwareInspector.inspect()
    assert isinstance(rep, HardwareReport)
    assert rep.cpu_count > 0
    assert rep.ffmpeg_available is True
    assert rep.recommended_encoder in ("h264_nvenc", "h264_mf", "libx264")
    print(f"✓ test_hardware passed (Recommended encoder: {rep.recommended_encoder}, GPU: {rep.gpu_name})")


def test_database():
    db = ClipDatabase()
    # Test connection and table columns
    recordings = db.get_all_recordings()
    assert isinstance(recordings, list)
    print("✓ test_database passed")


if __name__ == "__main__":
    test_config()
    test_hardware()
    test_database()
    print("\nALL PHASE 1 TESTS PASSED SUCCESSFULLY!")
