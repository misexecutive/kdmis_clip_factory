---
name: sound-design-sfx
description: >
  Autonomous sound design and audio mastering engine for gaming highlight clips.
  Places tension risers, impact bass drops, whoosh transitions, and hitmarkers
  around detected climax peaks with audio ducking and EBU R128 (-14 LUFS) mastering.
---

# Sound Design & SFX Engine

> [!NOTE]
> Module location: `core/sound_engine.py`  
> Class: `SoundDesigner`  
> SFX bank location: `storage/sfx/`

The Sound Design engine procedurally generates and synchronizes royalty-free audio effects to match the emotional arc of gameplay highlight clips, mastering the resulting mix to YouTube's broadcast standard (**-14 LUFS**).

---

## Quick Start

```python
from core.sound_engine import SoundDesigner

designer = SoundDesigner()

# Design audio placement plan and filter chain
audio_plan = designer.design_audio_for_clip(
    candidate_clip_dict={
        "start_time": 10.0,
        "end_time": 25.0,
        "peak_timestamp": 20.0,
        "trigger_type": "audio_spike",
        "peak_intensity": 0.95,
        "score": 88.5,
        "clip_format": "full",
    },
    video_duration=120.0,
)

print("SFX Placements:", audio_plan["sfx_placements"])
print("Master Loudnorm:", audio_plan["master_loudnorm"])
```

---

## Royalty-Free SFX Catalogue (`storage/sfx/`)

All sound effects are pre-rendered at 48kHz 16-bit PCM WAV:

| SFX Asset | Duration | Role & Trigger | Default Vol |
|---|---|---|---|
| `riser_cinematic.wav` | 2.0s | Rising tension sweep placed 1.8s before climax peak | 0.35 |
| `impact_bass_drop.wav` | 0.5s | Sub-bass punch at peak climax / kill timestamp | 0.50 |
| `whoosh_transition.wav` | 0.4s | Fast noise sweep at clip opening (0.2s) for hook entrance | 0.40 |
| `hitmarker_snap.wav` | 0.15s | Sharp mechanical snap confirmation on reflex/gunfire peaks | 0.45 |
| `tension_drone.wav` | 3.0s | Sub-drone for buildup in full highlights (>14s, score >= 70) | 0.25 |
| `glitch_stutter.wav` | 0.3s | Digital audio stutter for outro transitions | 0.40 |

---

## Audio Mastering Standards

1. **Broadcast Loudness**: Masters to EBU R128 `loudnorm=I=-14:LRA=11:TP=-1` for optimal playback volume without YouTube compression throttling.
2. **Sidechain Ducking**: Gameplay audio is smoothly dipped -6dB when prominent sound effects trigger to preserve crisp impact.
3. **Anti-Pop Micro-Fades**: 0.15s fade-in and 0.25s fade-out at clip boundaries.
