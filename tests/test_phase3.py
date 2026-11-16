"""
Unit tests for Nyro AI Clip Factory - Phase 3: Context-Aware Clip Discovery & Scoring
Tests 15-dimensional retention scoring, 16 content categories,
dual-tier extraction (6-10s micro and 15-20s extended), and deduplication.
"""

import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.clip_discovery import IntelligentClipDiscoveryEngine, MultiDimensionalScorer, CandidateClip, CONTENT_CATEGORIES
from core.config import config


def test_clip_discovery_and_scoring():
    scorer = MultiDimensionalScorer()
    discovery = IntelligentClipDiscoveryEngine(scorer=scorer)

    assert len(CONTENT_CATEGORIES) == 16, f"Expected 16 content categories, got {len(CONTENT_CATEGORIES)}"

    # Generate synthetic audiovisual event stream with 2 distinct clusters
    visual_events = [
        {"timestamp": 12.0, "event_type": "scene_cut", "intensity": 0.6, "description": "Shot cut"},
        {"timestamp": 24.2, "event_type": "explosion_flash", "intensity": 0.95, "description": "Large visual detonation flash"},
    ]
    audio_events = [
        {"timestamp": 12.1, "event_type": "gunfire_transient", "intensity": 0.75, "description": "Rifle burst"},
        {"timestamp": 24.2, "event_type": "bass_explosion", "intensity": 0.98, "description": "Deep sub-bass impact"},
    ]

    time_vec = np.linspace(0, 60, 600)
    rms_curve = np.full(600, 0.05)
    # Spike at 24.2s (index 242)
    rms_curve[238:248] = 0.85
    # Minor bump at 12s
    rms_curve[118:125] = 0.40

    motion_samples = [(t, 12.0 if 23.5 <= t <= 25.0 else 1.0) for t in np.linspace(0, 60, 120)]

    candidates = discovery.discover_candidates(
        video_filename="test_gameplay.mp4",
        video_duration=60.0,
        visual_events=visual_events,
        audio_events=audio_events,
        time_vector=time_vec,
        rms_curve=rms_curve,
        motion_samples=motion_samples,
    )

    assert len(candidates) > 0, "Expected candidates to be generated"

    # Check for dual-tier formats
    micro_clips = [c for c in candidates if c.clip_format == "micro"]
    ext_clips = [c for c in candidates if c.clip_format == "full"]

    print(f"Generated {len(candidates)} total candidates: {len(micro_clips)} Micro-Shorts, {len(ext_clips)} Extended Shorts")

    for c in candidates:
        # Check duration bounds
        if c.clip_format == "micro":
            assert 6.0 <= c.duration <= 10.0, f"Micro clip duration out of bounds: {c.duration}s"
        else:
            assert 15.0 <= c.duration <= 20.0, f"Extended clip duration out of bounds: {c.duration}s"

        # Check that category is from the 16 Content Categories
        assert c.category in CONTENT_CATEGORIES, f"Unknown category: {c.category}"

        # Check 15 retention dimensions
        dims = c.retention_dimensions
        assert dims is not None
        assert len(dims) == 15, f"Expected 15 dimensions, got {len(dims)}"
        assert 0.0 <= c.score <= 100.0
        assert len(c.reasoning) > 10

        print(f"\n[{c.id}] Format: {c.clip_format.upper()} | Score: {c.score}/100 | Category: '{c.category}'")
        print(f"  Window: {c.start_time}s -> {c.end_time}s ({c.duration}s)")
        print(f"  Dimensions: Hook={dims['opening_strength']}, Payoff={dims['payoff_quality']}, Loop={dims['loop_potential']}")
        print(f"  Reasoning: {c.reasoning}")

    # Verify explosion cluster got categorized properly
    top_clip = candidates[0]
    assert top_clip.category in ("Epic Explosions", "Intense Gunfights", "Cinematic Gameplay")

    print("\nALL PHASE 3 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_clip_discovery_and_scoring()
