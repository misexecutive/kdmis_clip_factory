# NYRO AI CLIP FACTORY — ULTIMATE EDITION
### Autonomous AI Video Processing & YouTube Shorts Studio for Gamer Nyro

**Nyro AI Clip Factory** is a professional, high-performance, autonomous gaming content production studio. It transforms raw OBS gameplay recordings (1080p/4K 60fps) into high-retention, broadcast-quality 9:16 vertical YouTube Shorts and Instagram Reels without manual timeline clicking.

---

## 🏛️ System Architecture

```
Raw OBS Recording (MP4/MKV)
        │
        ▼
[Module 1: Deep 4-Pass Audiovisual Intelligence]
  ├── Pass A: Technical Inspection & Codec Validation
  ├── Pass B: Farneback Dense Optical Flow & Luminance Flash Detection
  ├── Pass C: SciPy High-Res Multi-Band STFT, Sub-Bass & Spectral Flux
  └── Pass D: Contextual Fusion & Confidence Synthesis ──> analysis_report.json
        │
        ▼
[Module 2: 15-Dimensional Discovery & Categorization]
  ├── 15 Retention Dimensions (Hook, Visual, Audio, Payoff, Loop, etc.)
  ├── 16 Gaming Categories (Epic Explosions, Weapon Mechanics, Satisfying Kills, etc.)
  └── Dual-Tier Extraction (6-10s Micro-Shorts & 15-20s Extended Shorts) + IoU Deduplication
        │
        ▼
[Module 5: NYRO AURA ENGINE]
  ├── 7 Distinct AURA Profiles (CINEMATIC, REALISM, CHAOS, COMEDY, SUSPENSE, SATISFACTION, MINIMAL)
  └── Individualized Editing Blueprints ──> editing_blueprint.json
        │
        ▼
[Module 3 & 4: SFX Library & Sound Design Engine]
  ├── 20 SFX Categories (Explosions, Weapon Clicks, Bass Drops, Whooshes, Hitmarkers)
  ├── Verified CC0 / Public Domain Provenance + SHA-256 Checksums ──> assets_manifest.json
  └── EBU R128 Broadcast Loudness Mastering (-14 LUFS, -1.0 dB True Peak)
        │
        ▼
[Module 6: Motion Graphics & Platform Safe Zones]
  ├── Supersampled Neon Glow Call-to-Action (Like/Subscribe/Share)
  └── Guaranteed YouTube Shorts & Instagram Reels UI Clear Zones
        │
        ▼
[Module 7 & 8: Hardware-Accelerated 9:16 Vertical Renderer]
  ├── NVIDIA NVENC / Windows MediaFoundation (`h264_mf`) / `libx264`
  ├── Centered 960px Tall Gameplay + Blurred Ambient Wings + Color Grading
  └── Automated Post-Render Quality Inspection (Resolution, Black/Freeze Frames, Moov Atom)
        │
        ▼
[Standard Output Bundle: output/<recording_name>/<clip_id>/]
  ├── video.mp4 (1080x1920 60fps Fast-Start MP4)
  ├── metadata.txt (Human-readable YouTube upload copy)
  ├── metadata.json (Structured SEO metadata & tags)
  ├── editing_blueprint.json (Deterministic AURA editing recipe)
  ├── analysis_report.json (4-pass audiovisual DSP report)
  ├── assets_manifest.json (SFX copyright & SHA-256 provenance)
  └── thumbnail.jpg (High-impact 1080x1920 poster frame)
```

---

## ⚡ Core Modules

### 1. Deep Raw Footage Intelligence (Module 1)
- **Pass A (Technical Inspection)**: Media integrity check, container format, video/audio stream properties, resolution, FPS, and timestamps.
- **Pass B (Visual Intelligence)**: Dense Farneback optical flow motion magnitude, sudden visual transitions, camera pan speed, and luminance flash spikes.
- **Pass C (Audio Intelligence)**: High-resolution SciPy STFT, sub-bass energy isolation (20–140 Hz for explosions), spectral centroid brightness, and half-wave rectified spectral flux onset detection. Operates in 0.07s without Numba recursion freezes.
- **Pass D (Contextual Intelligence)**: Cross-modal fusion synthesizing confidence scores, gameplay pacing, and editorial justifications.

### 2. Context-Aware Clip Discovery & Scoring (Module 2)
- **15 Retention Dimensions**: Hook Potential (15%), Visual Impact (15%), Audio Quality (10%), Event Significance (15%), Payoff Quality (15%), Emotional Impact (10%), Replay/Loop Potential (10%), Originality (5%), Technical Quality (5%).
- **16 Gaming Categories**:
  - `Cinematic Gameplay`, `Unexpected Moments`, `Epic Explosions`, `Realistic Graphics`,
  - `Weapon Mechanics`, `Intense Gunfights`, `Funny Gameplay`, `NPC Reactions`,
  - `Vehicle Crashes`, `Close Calls`, `Character Interactions`, `Story Moments`,
  - `Satisfying Kills`, `Unexpected Twists`, `Immersive Realism`, `Environmental Details`.
- **Dual-Tier Format**:
  - `Micro-Shorts` (6–10s): High-tempo, instant gratification, seamless loop potential.
  - `Extended Shorts` (15–20s): Setup, rising tension, climax payoff.
- **Overlap Deduplication**: Filters candidate moments sharing >60% temporal IoU.

### 3. Legal SFX Library & Provenance (Module 3 & 4)
- 20 distinct sound categories with verifiable legal metadata:
  - Source URL, License (CC0 1.0 Universal / Public Domain), Date, and SHA-256 Checksums.
- Category-aware sound design rules:
  - `Weapon Mechanics`: Suppresses artificial sub-bass/risers to preserve authentic weapon reload and cycling audio.
  - `Epic Explosions`: Automatically places sub-bass drops at peak timestamps.
  - `Satisfying Kills`: Accentuates hitmarkers and subtle payoff whooshes.

### 4. NYRO AURA ENGINE (Module 5)
Synthesizes unique editing decisions per clip based on 7 foundational profiles:
1. `CINEMATIC AURA`: Atmospheric letterbox push, subtle vignettes, soft whooshes.
2. `REALISM AURA`: Zero artificial visual noise, raw uncompressed game audio fidelity.
3. `CHAOS AURA`: Rapid dynamic push punches, high-contrast tactical grading, impact flashes.
4. `COMEDY AURA`: Snappy comedic zoom snaps and timing emphasis.
5. `SUSPENSE AURA`: Slow tension riser buildup, dark corner vignettes.
6. `SATISFACTION AURA`: Exact kill-frame snap zooms, crisp hitmarkers.
7. `MINIMAL AURA`: Clean vertical framing with original gameplay preservation.

### 5. Platform Safe Zones & Dynamic Motion Graphics (Module 6)
- **YouTube Shorts Safe Zone**: Top 15% and bottom 20% reserved for channel avatar, sound title, and navigation UI.
- **Instagram Reels Safe Zone**: Right edge 120px reserved for Like, Comment, and Share action buttons.
- **Neon Glow Call-to-Action**: RGBA neon glow arrows generated via supersampled Pillow drawing, synchronized with sinusoidal floating motion.

### 6. Standardized Output Bundle (Module 7)
Every exported clip is cleanly packaged into:
```
output/<recording_name>/<clip_id>/
├── video.mp4
├── metadata.txt
├── metadata.json
├── editing_blueprint.json
├── analysis_report.json
├── assets_manifest.json
└── thumbnail.jpg
```

---

## 🚀 CLI Commands

The unified CLI (`main.py`) provides commands for every stage of production:

```bash
# 1. Zero-touch end-to-end autonomous studio production (top 2 Shorts)
python main.py pipeline --input "storage/raw_recordings/gameplay.mp4" --top 2

# 2. Deep 4-pass audiovisual inspection
python main.py analyze --input "storage/raw_recordings/gameplay.mp4"

# 3. Discover and score dual-tier candidate moments across 15 dimensions
python main.py discover --input "storage/raw_recordings/gameplay.mp4"

# 4. Export vertical Shorts with AURA blueprints & standard bundles
python main.py export --input "storage/raw_recordings/gameplay.mp4" --top 3

# 5. Generate tailored YouTube copywriting and SEO metadata
python main.py metadata --input "storage/raw_recordings/gameplay.mp4"

# 6. Post-render broadcast compliance & quality validation
python main.py validate --input "output/gameplay"

# 7. Launch web dashboard and auto-open browser
python main.py start --port 8000

# 8. List all discovered candidate clips in database
python main.py list

# 9. Purge database and audio cache for a fresh session
python main.py reset
```

---

## 🌐 Web Dashboard

Start the studio dashboard:
```bash
python main.py server --port 8000
```
Open `http://127.0.0.1:8000` to access:
- **Interactive 9:16 Video Player**: Live hook pill previews and YouTube Safe Zone toggles.
- **AURA Blueprint Viewer**: Direct modal inspection of the generated editing blueprint.
- **Batch Export**: One-click batch rendering of top candidate clips.
- **Timeline Trimmer**: Interactive fine-tuning of start and end timestamps.
- **SEO & Copywriting**: One-click copy buttons for YouTube titles, descriptions, and CSV tags.

---

## 🧪 Comprehensive Verification Suite

Run all test suites across Phases 1 through 10:
```bash
python tests/test_phase1.py   # Architecture & Hardware Inspection
python tests/test_phase2.py   # Deep 4-Pass Audiovisual Intelligence
python tests/test_phase3.py   # 15D Retention Scoring & Dual-Tier Discovery
python tests/test_phase4.py   # SFX Library & SHA-256 Provenance
python tests/test_phase5.py   # NYRO AURA ENGINE & Deterministic Seed
python tests/test_phase6.py   # Motion Graphics & UI Safe Zones
python tests/test_phase7.py   # Hardware 9:16 Rendering & Quality Validation
python tests/test_phase8.py   # Centralized Export Packager
python tests/test_phase9.py   # Unified CLI & API Endpoints
python tests/test_phase10.py  # End-to-End Output Bundle Integrity & Compliance
```
