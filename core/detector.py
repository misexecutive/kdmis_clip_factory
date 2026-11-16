"""
Nyro AI Clip Factory - Multi-Modal Moment Detector
Detects explosions, gunfights, clutch moments, unexpected reactions,
and high-action gameplay sequences using audio DSP and visual heuristics.
Generates both full narrative highlights (18s-45s) and punchy micro-clips (8s-12s).
"""

import json
import logging
import math
import subprocess
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class MomentEvent:
    timestamp: float
    event_type: str  # "audio_spike", "voice_peak", "visual_flash", "scene_change"
    intensity: float  # 0.0 to 1.0
    description: str


from core.clip_discovery import CandidateClip, CONTENT_CATEGORIES


class MomentDetector:
    def __init__(
        self,
        min_clip_duration: float = 8.0,
        max_clip_duration: float = 58.0,
        pre_roll_seconds: float = 3.5,
        post_roll_seconds: float = 4.5,
        energy_z_threshold: float = 1.8,
    ):
        self.min_clip_duration = min_clip_duration
        self.max_clip_duration = max_clip_duration
        self.pre_roll = pre_roll_seconds
        self.post_roll = post_roll_seconds
        self.energy_z_threshold = energy_z_threshold

    def analyze_audio_track(self, wav_path: str, window_sec: float = 0.25) -> Tuple[np.ndarray, np.ndarray, List[MomentEvent]]:
        """
        Processes 16-bit mono 16kHz WAV file to extract RMS volume curve,
        loudness jumps, and peak events.
        """
        logger.info(f"Analyzing audio dynamics for {Path(wav_path).name}...")
        with wave.open(wav_path, "rb") as wf:
            sample_rate = wf.getframerate()
            num_channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            total_frames = wf.getnframes()

            if sample_width != 2:
                raise ValueError("Expected 16-bit audio.")

            raw_bytes = wf.readframes(total_frames)

        audio_data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        samples_per_window = int(sample_rate * window_sec)
        total_windows = len(audio_data) // samples_per_window

        if total_windows == 0:
            return np.array([]), np.array([]), []

        usable_len = total_windows * samples_per_window
        reshaped = audio_data[:usable_len].reshape(total_windows, samples_per_window)
        rms = np.sqrt(np.mean(reshaped ** 2, axis=1) + 1e-9)

        time_vector = np.arange(total_windows) * window_sec

        mean_rms = np.mean(rms)
        std_rms = np.std(rms)
        z_scores = (rms - mean_rms) / (std_rms + 1e-6)

        delta_window = int(1.0 / window_sec)
        deltas = np.zeros_like(rms)
        if total_windows > delta_window:
            deltas[delta_window:] = rms[delta_window:] - rms[:-delta_window]

        events: List[MomentEvent] = []
        for i, (t, z, val, d) in enumerate(zip(time_vector, z_scores, rms, deltas)):
            if z >= self.energy_z_threshold and val > 0.05:
                intensity = float(np.clip((z - self.energy_z_threshold) / 3.0, 0.2, 1.0))
                desc = "Audio Energy Spike (Gunfire / Loud Explosion / Vocal Shout)"
                if d > 0.08:
                    desc = "Sudden High-Impact Audio Transient (Direct Hit / Ambush / Jumpscare)"
                    intensity = min(1.0, intensity + 0.15)

                events.append(MomentEvent(
                    timestamp=round(float(t), 2),
                    event_type="audio_spike",
                    intensity=round(intensity, 3),
                    description=desc,
                ))

        logger.info(f"Found {len(events)} audio spike events across {time_vector[-1]:.1f}s.")
        return time_vector, rms, events

    def detect_visual_flashes_and_scenes(self, video_path: str, max_check_seconds: Optional[float] = None) -> List[MomentEvent]:
        """
        Uses FFmpeg scene filter to catch scene changes without re-encoding.
        """
        logger.info(f"Scanning visual transitions and luminance spikes in {Path(video_path).name}...")
        events: List[MomentEvent] = []

        cmd = [
            "ffmpeg",
            "-i", str(Path(video_path).resolve()),
            "-filter_complex", "select='gt(scene,0.45)',metadata=print:key=lavfi.scene_score",
            "-f", "null",
            "-",
        ]
        if max_check_seconds:
            cmd.insert(1, "-t")
            cmd.insert(2, str(max_check_seconds))

        try:
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, check=True)
            output = res.stderr
            for line in output.splitlines():
                if "pts_time:" in line and "lavfi.scene_score" in line:
                    parts = line.split()
                    pts = 0.0
                    score = 0.5
                    for p in parts:
                        if p.startswith("pts_time:"):
                            pts = float(p.split(":")[1])
                        elif p.startswith("lavfi.scene_score="):
                            score = float(p.split("=")[1])
                    events.append(MomentEvent(
                        timestamp=round(pts, 2),
                        event_type="scene_change",
                        intensity=round(float(min(1.0, score)), 3),
                        description="Abrupt Visual Cut / Respawn / Cam Transition",
                    ))
        except Exception as e:
            logger.warning(f"Visual scene filter completed or skipped: {e}")

        logger.info(f"Visual analysis yielded {len(events)} visual cut/shift events.")
        return events

    def cluster_events_into_candidates(
        self,
        video_filename: str,
        video_duration: float,
        events: List[MomentEvent],
    ) -> List[CandidateClip]:
        """
        Clusters audio/visual events into:
        1. Full narrative highlights (18s - 45s)
        2. Punchy micro-clips (8s - 12s) for instant-kill, headshot, or jumpscare moments.
        """
        if not events:
            logger.warning("No significant events detected to form candidates.")
            return []

        events = sorted(events, key=lambda e: e.timestamp)

        # Group events within 7 seconds into clusters
        clusters: List[List[MomentEvent]] = []
        current_cluster: List[MomentEvent] = [events[0]]

        for ev in events[1:]:
            if ev.timestamp - current_cluster[-1].timestamp <= 7.0:
                current_cluster.append(ev)
            else:
                clusters.append(current_cluster)
                current_cluster = [ev]
        if current_cluster:
            clusters.append(current_cluster)

        candidates: List[CandidateClip] = []
        clip_base_stem = Path(video_filename).stem
        candidate_idx = 1

        for cluster in clusters:
            primary_event = max(cluster, key=lambda e: e.intensity)
            cluster_start = cluster[0].timestamp
            cluster_end = cluster[-1].timestamp

            # Determine category based on cluster events
            has_flash = any("flash" in e.event_type.lower() for e in cluster)
            has_bass = any("bass" in e.event_type.lower() for e in cluster)
            has_cut = any("cut" in e.event_type.lower() or "scene" in e.event_type.lower() for e in cluster)
            has_gunfire = any("gunfire" in e.description.lower() for e in cluster)
            
            if has_flash and has_bass:
                cat = "Epic Explosions"
                sec_cats = ["Cinematic Gameplay", "Immersive Realism"]
            elif has_gunfire:
                cat = "Intense Gunfights"
                sec_cats = ["Weapon Mechanics", "Satisfying Kills"]
            elif has_cut:
                cat = "Unexpected Moments"
                sec_cats = ["Unexpected Twists", "Close Calls"]
            elif has_bass:
                cat = "Satisfying Kills"
                sec_cats = ["Cinematic Gameplay"]
            else:
                cat = "Cinematic Gameplay"
                sec_cats = ["Environmental Details", "Story Moments"]

            # 1. GENERATE EXTENDED SHORT (15s – 20s)
            ext_target = 17.5
            ext_start = max(0.0, primary_event.timestamp - 9.0)
            ext_end = min(video_duration, ext_start + ext_target)
            if ext_end - ext_start < 15.0:
                ext_start = max(0.0, ext_end - 15.0)
            ext_dur = ext_end - ext_start

            clip_id_full = f"clip_{clip_base_stem}_{candidate_idx:02d}_ext"
            candidates.append(CandidateClip(
                id=clip_id_full,
                video_filename=video_filename,
                start_time=round(ext_start, 2),
                end_time=round(ext_end, 2),
                duration=round(ext_dur, 2),
                peak_timestamp=round(primary_event.timestamp, 2),
                trigger_type=primary_event.event_type,
                peak_intensity=primary_event.intensity,
                events=[asdict(e) for e in cluster],
                clip_format="full",
                category=cat,
                secondary_categories=sec_cats,
            ))

            # 2. GENERATE PUNCHY MICRO-CLIP (6s – 10s) FOR HIGH INTENSITY BURSTS
            # If peak intensity >= 0.55 or sudden transient, create an 8.5s micro clip
            if primary_event.intensity >= 0.55 or any("Sudden" in e.description for e in cluster):
                micro_start = max(0.0, primary_event.timestamp - 2.2)
                micro_end = min(video_duration, micro_start + 8.5)
                micro_dur = micro_end - micro_start

                clip_id_micro = f"clip_{clip_base_stem}_{candidate_idx:02d}_micro"
                candidates.append(CandidateClip(
                    id=clip_id_micro,
                    video_filename=video_filename,
                    start_time=round(micro_start, 2),
                    end_time=round(micro_end, 2),
                    duration=round(micro_dur, 2),
                    peak_timestamp=round(primary_event.timestamp, 2),
                    trigger_type=primary_event.event_type,
                    peak_intensity=primary_event.intensity,
                    events=[asdict(primary_event)],
                    clip_format="micro",
                    category=cat,
                    secondary_categories=sec_cats,
                ))

            candidate_idx += 1

        logger.info(f"Synthesized {len(candidates)} total candidates (Extended 15-20s + Micro 6-10s clips).")
        return candidates


if __name__ == "__main__":
    detector = MomentDetector()
    print("MomentDetector module ready.")
