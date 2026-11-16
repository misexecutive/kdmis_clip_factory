---
name: clip-director
description: >
  Autonomous end-to-end studio director that automatically inspects raw gameplay,
  detects peak moments, color grades, synchronizes SFX, masters audio to -14 LUFS,
  generates YouTube copywriting, and renders vertical 9:16 Shorts without manual UI clicking.
---

# Autonomous Studio Director Skill

> [!NOTE]
> Module location: `core/director.py`  
> Class: `AutonomousDirector`  
> CLI Command: `python run_clip_factory.py auto [--top N] [--fresh]`

The Autonomous Director provides a zero-touch pipeline for high-volume content creators (like Gamer Nyro). It automates all editing decisions, visual enhancements, sound design, and copywriting, outputting ready-to-upload YouTube Shorts in broadcast quality.

---

## 5-Stage Autonomous Pipeline

1. **Audiovisual Inspection**: Probes stream resolution, duration, framerate, audio dynamic range, and stream health.
2. **Multi-Modal Moment Detection**: Analyzes audio transients and visual shifts, ranking moments via 6-factor retention scoring (Opening Impact, Curiosity, Pacing, Climax, Replay, Audiovisual Quality).
3. **Autonomous Visual Effects (VFX)**:
   - Evaluates gameplay style and applies tailored color grading presets (`vibrant_tactical`, `cyberpunk_neon`, `clean_crisp`, etc.).
   - Adds cinematic vignette to focus viewer eyes on crosshairs.
   - Burns high-contrast hook text pills and episodic series badges (e.g. `⚡ PART 1`) within YouTube Shorts safe zones.
4. **Autonomous Sound Design (SFX)**:
   - Places tension risers 1.8s prior to climax.
   - Triggers sub-bass impact drops at the peak moment.
   - Synchronizes whoosh sound effects for hook entrances.
   - Ducks gameplay audio smoothly under SFX.
   - Masters complete audio output to EBU R128 (`-14 LUFS`) broadcast loudness.
5. **Copywriting & Upload Package**:
   - Generates 3 distinct YouTube title angles (Action/Skill, Viral Curiosity, Episodic Series).
   - Generates subscription CTA descriptions and comma-separated SEO tags.
   - Writes upload package files (`_upload_pack.txt`) directly next to rendered MP4s.

---

## CLI Usage

```powershell
# Autonomously process latest OBS recording and produce top 3 Shorts
python run_clip_factory.py auto --top 3

# Start completely fresh (wipes previous test data) and produce top 5 Shorts
python run_clip_factory.py auto --video "storage/raw_recordings/gameplay.mp4" --top 5 --fresh

# Specify color grading preset
python run_clip_factory.py auto --preset cyberpunk_neon
```
