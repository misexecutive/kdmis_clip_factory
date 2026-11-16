---
name: moment-detector
description: >-
  Detects candidate gaming highlights, gunfire/explosion audio spikes, and visual scene shifts,
  clustering them into dual-tier candidates (Full Highlights 18s-35s and Micro-Shorts 8s-12s)
  and scoring retention across 6 dimensions.
---

# Moment Detector Skill: Multi-Modal Detection & Scoring

This skill identifies high-impact moments from gameplay audio and visual energy curves, clustering them into dual-tier candidate YouTube Shorts:
1. **Full Highlights (18s - 35s)**: Complete combat engagements featuring buildup, engagement, climax, and aftermath.
2. **Micro-Shorts (8s - 12s)**: Ultra-dense reflex clips, instant collateral kills, or sudden jump scares with maximum loop/replay potential.

## 6-Factor Scoring Formula

Every candidate is evaluated on a 0-100 scale:
- **Opening Impact (0-20)**: Energy and audio transients in the first 2.5 seconds to stop viewer swipe-aways.
- **Curiosity / Buildup (0-15)**: Tension contrast between pre-roll approach and the climax.
- **Retention & Pacing (0-20)**: Action density throughout the clip body; absence of dead silence.
- **Climax / Payoff (0-20)**: Intensity and timing of the peak moment (optimally at 60-85% mark).
- **Replay Potential (0-15)**: Sudden twists, rapid reflex shots, or unexpected outcomes.
- **Audiovisual Quality (0-10)**: Clean audio dynamics without severe clipping or distortion.

## Python API Usage

```python
from core.detector import MomentDetector
from core.scorer import CandidateScorer

detector = MomentDetector()
time_vec, rms_curve, audio_events = detector.analyze_audio_track(wav_proxy)
visual_events = detector.detect_visual_flashes_and_scenes(video_path)

candidates = detector.cluster_events_into_candidates(
    video_filename=filename,
    video_duration=duration,
    events=audio_events + visual_events
)

scorer = CandidateScorer()
ranked_candidates = scorer.score_all(candidates, time_vec, rms_curve)
```
