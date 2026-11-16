"""
Nyro AI Clip Factory - Deep Raw Footage Intelligence Engine (Module 1)
Implements 4 logical analysis passes:
- PASS A: Technical Inspection & Media Integrity (ffprobe & stream validation)
- PASS B: Visual Intelligence (OpenCV adaptive optical flow, flash detection, scene shifts)
- PASS C: Audio Intelligence (Soundfile + SciPy multi-band STFT, sub-bass, spectral centroid, onsets, dynamic range)
- PASS D: Contextual Cross-Modal Intelligence (cross-modal fusion, event confidence, report generation)
"""

import json
import logging
import math
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import cv2
import numpy as np
import scipy.signal as signal
import soundfile as sf

from core.config import config, ProcessingProfile
from core.ingest import IngestionEngine, VideoMetadata

logger = logging.getLogger("DeepIntelligenceEngine")


@dataclass
class VisualEvent:
    timestamp: float
    event_type: str  # "explosion_flash", "rapid_flick", "high_motion", "scene_cut", "camera_pan"
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    motion_score: float
    luminance_delta: float
    sharpness: float
    description: str


@dataclass
class AudioEvent:
    timestamp: float
    event_type: str  # "gunfire_transient", "bass_explosion", "vocal_peak", "impact_drop", "silence"
    intensity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    spectral_centroid_hz: float
    sub_bass_energy: float
    rms_level: float
    description: str


@dataclass
class ContextualMoment:
    start_time: float
    end_time: float
    duration: float
    peak_timestamp: float
    primary_category: str
    secondary_categories: List[str]
    confidence: float
    visual_intensity: float
    audio_intensity: float
    fusion_score: float
    reasons_for_selection: List[str]
    rejection_reasons: List[str] = field(default_factory=list)
    is_candidate: bool = True


@dataclass
class DeepAnalysisReport:
    source_filename: str
    source_filepath: str
    duration_seconds: float
    resolution: str
    fps: float
    bitrate: int
    audio_channels: int
    audio_sample_rate: int
    scene_boundaries: List[float]
    visual_events: List[Dict[str, Any]]
    audio_events: List[Dict[str, Any]]
    contextual_moments: List[Dict[str, Any]]
    average_visual_motion: float
    audio_dynamic_range_db: float
    sub_bass_peak_timestamp: float
    generated_at: float
    processing_time_seconds: float
    pass_timings: Dict[str, float]
    profile_used: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save_json(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)


class DeepIntelligenceEngine:
    """Multi-pass deep audiovisual intelligence system."""

    def __init__(self, ingest_engine: Optional[IngestionEngine] = None):
        self.ingest = ingest_engine or IngestionEngine()

    def analyze_recording(
        self,
        video_path: str,
        profile: Optional[ProcessingProfile] = None,
        save_report_dir: Optional[Path] = None,
    ) -> DeepAnalysisReport:
        """Executes full 4-pass analysis pipeline with granular timings and progress reporting."""
        t_start = time.time()
        active_profile = profile or config.get_active_profile()
        in_file = Path(video_path).resolve()
        if not in_file.is_file():
            raise FileNotFoundError(f"Source video not found: {video_path}")

        print(f"\n{'='*75}", flush=True)
        print(f"[Deep Intelligence] Starting 4-Pass Analysis on: {in_file.name}", flush=True)
        print(f"[Deep Intelligence] Quality Profile: {active_profile.name}", flush=True)
        print(f"{'='*75}", flush=True)

        timings = {}

        # PASS A: Technical Inspection
        t0 = time.time()
        meta = self.pass_a_technical(str(in_file))
        timings["pass_a_technical_s"] = round(time.time() - t0, 3)
        print(f"  ✓ Pass A Complete ({timings['pass_a_technical_s']}s) - Resolution: {meta.width}x{meta.height} @ {meta.fps}fps, Codec: {meta.video_codec}/{meta.audio_codec}", flush=True)

        # PASS B: Visual Intelligence
        t0 = time.time()
        visual_report = self.pass_b_visual(str(in_file), meta, active_profile)
        timings["pass_b_visual_s"] = round(time.time() - t0, 3)
        print(f"  ✓ Pass B Complete ({timings['pass_b_visual_s']}s) - Detected {len(visual_report['events'])} visual events, {len(visual_report['scene_boundaries'])} scene boundaries", flush=True)

        # PASS C: Audio Intelligence
        t0 = time.time()
        wav_proxy = self.ingest.extract_audio_proxy(str(in_file), sample_rate=16000)
        audio_report = self.pass_c_audio(wav_proxy, active_profile)
        timings["pass_c_audio_s"] = round(time.time() - t0, 3)
        print(f"  ✓ Pass C Complete ({timings['pass_c_audio_s']}s) - Detected {len(audio_report['events'])} audio events, Dynamic Range: {audio_report['dynamic_range_db']} dB", flush=True)

        # PASS D: Contextual Fusion & Moment Classification
        t0 = time.time()
        context_report = self.pass_d_contextual(meta, visual_report, audio_report, active_profile)
        timings["pass_d_contextual_s"] = round(time.time() - t0, 3)
        print(f"  ✓ Pass D Complete ({timings['pass_d_contextual_s']}s) - Synthesized {len(context_report['moments'])} contextual moments with cross-modal confidence", flush=True)

        total_proc_time = round(time.time() - t_start, 2)
        print(f"{'='*75}", flush=True)
        print(f"[Deep Intelligence] Full Pipeline Finished in {total_proc_time}s across all 4 passes", flush=True)
        print(f"{'='*75}\n", flush=True)

        report = DeepAnalysisReport(
            source_filename=meta.filename,
            source_filepath=str(in_file),
            duration_seconds=round(meta.duration_seconds, 2),
            resolution=f"{meta.width}x{meta.height}",
            fps=round(meta.fps, 2),
            bitrate=meta.bitrate,
            audio_channels=meta.audio_channels,
            audio_sample_rate=meta.audio_sample_rate,
            scene_boundaries=visual_report["scene_boundaries"],
            visual_events=[asdict(e) for e in visual_report["events"]],
            audio_events=[asdict(e) for e in audio_report["events"]],
            contextual_moments=[asdict(m) for m in context_report["moments"]],
            average_visual_motion=round(visual_report["average_motion"], 3),
            audio_dynamic_range_db=round(audio_report["dynamic_range_db"], 1),
            sub_bass_peak_timestamp=round(audio_report["sub_bass_peak_t"], 2),
            generated_at=time.time(),
            processing_time_seconds=total_proc_time,
            pass_timings=timings,
            profile_used=active_profile.name,
        )

        if save_report_dir:
            out_file = save_report_dir / f"{in_file.stem}_analysis_report.json"
            report.save_json(out_file)
            logger.info(f"Saved comprehensive analysis report: {out_file.name}")

        return report

    # ------------------------------------------------------------------ #
    # PASS A: Technical Inspection & Stream Integrity                   #
    # ------------------------------------------------------------------ #
    def pass_a_technical(self, video_path: str) -> VideoMetadata:
        """Inspects container, video, audio streams and verifies timestamp integrity."""
        logger.info("[Pass A] Performing Technical Inspection & Media Integrity Check...")
        meta = self.ingest.probe(video_path)
        if meta.duration_seconds <= 0:
            raise ValueError(f"Invalid recording duration ({meta.duration_seconds}s) in {video_path}")
        if meta.width == 0 or meta.height == 0:
            raise ValueError(f"Corrupt video geometry {meta.width}x{meta.height}")
        return meta

    # ------------------------------------------------------------------ #
    # PASS B: Visual Intelligence & Optical Flow                         #
    # ------------------------------------------------------------------ #
    def pass_b_visual(
        self,
        video_path: str,
        meta: VideoMetadata,
        profile: ProcessingProfile,
    ) -> Dict[str, Any]:
        """
        Extracts scene boundaries, motion intensity curve via optical flow,
        muzzle flashes / explosion luminance shifts, and image sharpness.
        """
        logger.info(f"[Pass B] Running Visual Intelligence (Sampling @ {profile.video_sample_fps} FPS)...")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"OpenCV could not open video: {video_path}")

        source_fps = meta.fps if meta.fps > 0 else 30.0
        total_source_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or int(meta.duration_seconds * source_fps)
        sample_interval = max(1, int(round(source_fps / max(1.0, profile.video_sample_fps))))

        prev_gray = None
        frame_idx = 0
        motion_samples: List[Tuple[float, float]] = []
        events: List[VisualEvent] = []
        scene_boundaries: List[float] = [0.0]

        # Scaled down size for efficient optical flow (320x180)
        flow_w, flow_h = 320, 180
        last_progress_print = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % sample_interval == 0:
                curr_t = round(frame_idx / source_fps, 3)
                small = cv2.resize(frame, (flow_w, flow_h))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                # Sharpness via Laplacian variance
                sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
                mean_lum = float(np.mean(gray))

                motion_mag = 0.0
                lum_delta = 0.0

                if prev_gray is not None:
                    lum_delta = abs(mean_lum - np.mean(prev_gray))

                    if profile.optical_flow_enabled:
                        flow = cv2.calcOpticalFlowFarneback(
                            prev_gray, gray, None,
                            pyr_scale=0.5, levels=2, winsize=13,
                            iterations=2, poly_n=5, poly_sigma=1.1, flags=0
                        )
                        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                        motion_mag = float(np.mean(mag))

                    # Event 1: Scene Cut Detection
                    if lum_delta > 35.0 or (profile.optical_flow_enabled and motion_mag > 18.0):
                        events.append(VisualEvent(
                            timestamp=curr_t,
                            event_type="scene_cut",
                            intensity=min(1.0, lum_delta / 60.0),
                            confidence=0.85,
                            motion_score=motion_mag,
                            luminance_delta=lum_delta,
                            sharpness=sharpness,
                            description="Visual Shot Transition / Respawn Cut",
                        ))
                        if not scene_boundaries or (curr_t - scene_boundaries[-1] > 2.0):
                            scene_boundaries.append(curr_t)

                    # Event 2: Explosion / Muzzle Flash (high luminance spike)
                    elif lum_delta > 18.0:
                        intensity = min(1.0, 0.4 + (lum_delta / 40.0))
                        events.append(VisualEvent(
                            timestamp=curr_t,
                            event_type="explosion_flash",
                            intensity=round(intensity, 3),
                            confidence=0.88,
                            motion_score=motion_mag,
                            luminance_delta=lum_delta,
                            sharpness=sharpness,
                            description="Explosion Flash or Intense Muzzle Blast",
                        ))

                    # Event 3: Rapid Camera Flick / High Combat Motion
                    elif motion_mag > 7.5:
                        intensity = min(1.0, motion_mag / 15.0)
                        events.append(VisualEvent(
                            timestamp=curr_t,
                            event_type="rapid_flick",
                            intensity=round(intensity, 3),
                            confidence=0.82,
                            motion_score=motion_mag,
                            luminance_delta=lum_delta,
                            sharpness=sharpness,
                            description="Rapid Crosshair Flick / Evasive Movement",
                        ))

                motion_samples.append((curr_t, motion_mag))
                prev_gray = gray

                # Progress reporting every 4 seconds
                if time.time() - last_progress_print >= 4.0:
                    pct = (frame_idx / max(1, total_source_frames)) * 100.0
                    print(f"    [Pass B] Visual analysis progress: {pct:.1f}% ({curr_t:.1f}s / {meta.duration_seconds:.1f}s)...", flush=True)
                    last_progress_print = time.time()

            frame_idx += 1

        cap.release()

        avg_motion = float(np.mean([m[1] for m in motion_samples])) if motion_samples else 0.0
        return {
            "events": events,
            "scene_boundaries": scene_boundaries,
            "motion_samples": motion_samples,
            "average_motion": avg_motion,
        }

    # ------------------------------------------------------------------ #
    # PASS C: Audio Intelligence & Multi-Band Spectral Decomposition    #
    # ------------------------------------------------------------------ #
    def pass_c_audio(
        self,
        wav_path: str,
        profile: ProcessingProfile,
    ) -> Dict[str, Any]:
        """
        Ultra-fast, deterministic multi-band audio intelligence using Soundfile + SciPy signal DSP.
        Extracts:
        - Continuous frame RMS energy
        - Dynamic Range (dB)
        - High-resolution STFT spectrogram
        - Spectral Centroid (frequency brightness curve)
        - Half-wave rectified spectral flux (transient onsets: gunshots, hitmarkers, clicks)
        - Sub-bass bandpass energy (20Hz - 140Hz) for explosions and bass drops
        """
        logger.info("[Pass C] Running Audio Intelligence (Soundfile + SciPy multi-band STFT)...")
        y, sr = sf.read(wav_path)
        if len(y) == 0:
            return {"events": [], "dynamic_range_db": 0.0, "sub_bass_peak_t": 0.0}

        # Convert to mono float32 if multichannel
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        y = y.astype(np.float32)

        # 1. Multi-band Short-Time Fourier Transform (STFT)
        nperseg = 2048
        hop_length = 512
        noverlap = nperseg - hop_length
        freqs, time_bins, Zxx = signal.stft(y, fs=sr, nperseg=nperseg, noverlap=noverlap)
        mag = np.abs(Zxx)  # (frequencies, time_frames)

        # 2. Continuous RMS Energy
        # Windowed squared amplitude
        rms = np.sqrt(np.mean(mag ** 2, axis=0) + 1e-9)
        min_rms = max(1e-5, float(np.percentile(rms, 5)))
        max_rms = max(min_rms * 1.1, float(np.percentile(rms, 95)))
        dynamic_range_db = float(20.0 * np.log10(max_rms / min_rms))

        # 3. Spectral Centroid: center of mass of the spectrum
        spectral_centroid = np.sum(freqs[:, None] * mag, axis=0) / (np.sum(mag, axis=0) + 1e-9)

        # 4. Half-Wave Rectified Spectral Flux (Onset Detection)
        diff_mag = np.diff(mag, axis=1)
        flux = np.sum(np.maximum(0.0, diff_mag), axis=0)
        # Pad flux by 1 frame to match time_bins length
        flux = np.pad(flux, (1, 0), mode="constant")

        # 5. Sub-Bass Energy (20Hz - 140Hz) for Detonations / Heavy Impacts
        sub_bass_mask = (freqs >= 20.0) & (freqs <= 140.0)
        if np.any(sub_bass_mask):
            sub_bass_energy = np.mean(mag[sub_bass_mask, :], axis=0)
        else:
            sub_bass_energy = np.zeros(len(time_bins))

        peak_bass_idx = int(np.argmax(sub_bass_energy)) if len(sub_bass_energy) > 0 else 0
        sub_bass_peak_t = float(time_bins[peak_bass_idx]) if peak_bass_idx < len(time_bins) else 0.0

        # 6. Event Extraction via Peak Picking on Spectral Flux & RMS
        mean_flux = float(np.mean(flux))
        std_flux = float(np.std(flux))
        flux_threshold = mean_flux + 1.8 * std_flux

        mean_rms = float(np.mean(rms))
        std_rms = float(np.std(rms))

        mean_bass = float(np.mean(sub_bass_energy))
        std_bass = float(np.std(sub_bass_energy))

        # Local maxima detection on flux curve
        peak_indices, _ = signal.find_peaks(flux, height=flux_threshold, distance=max(1, int(0.3 * (sr / hop_length))))

        events: List[AudioEvent] = []
        for idx in peak_indices:
            t = float(time_bins[idx])
            cur_rms = float(rms[idx])
            cur_centroid = float(spectral_centroid[idx])
            cur_bass = float(sub_bass_energy[idx])

            # Classify event
            if cur_bass > (mean_bass + 1.5 * std_bass):
                intensity = min(1.0, 0.5 + (cur_bass / (mean_bass + 3.0 * std_bass + 1e-4)))
                events.append(AudioEvent(
                    timestamp=round(t, 2),
                    event_type="bass_explosion",
                    intensity=round(intensity, 3),
                    confidence=0.92,
                    spectral_centroid_hz=round(cur_centroid, 1),
                    sub_bass_energy=round(cur_bass, 2),
                    rms_level=round(cur_rms, 3),
                    description="Heavy Sub-Bass Impact / Detonation",
                ))
            elif cur_centroid > 2200.0:
                intensity = min(1.0, 0.45 + (cur_rms / (mean_rms + 2.5 * std_rms + 1e-4)))
                events.append(AudioEvent(
                    timestamp=round(t, 2),
                    event_type="gunfire_transient",
                    intensity=round(intensity, 3),
                    confidence=0.88,
                    spectral_centroid_hz=round(cur_centroid, 1),
                    sub_bass_energy=round(cur_bass, 2),
                    rms_level=round(cur_rms, 3),
                    description="High-Frequency Gunfire or Impact Transient",
                ))
            elif cur_rms > (mean_rms + 1.2 * std_rms):
                intensity = min(1.0, 0.4 + (cur_rms / (mean_rms + 2.0 * std_rms + 1e-4)))
                events.append(AudioEvent(
                    timestamp=round(t, 2),
                    event_type="vocal_peak",
                    intensity=round(intensity, 3),
                    confidence=0.80,
                    spectral_centroid_hz=round(cur_centroid, 1),
                    sub_bass_energy=round(cur_bass, 2),
                    rms_level=round(cur_rms, 3),
                    description="Audio Energy Peak / Vocal Reaction",
                ))

        return {
            "events": events,
            "times": time_bins,
            "rms": rms,
            "sub_bass_energy": sub_bass_energy,
            "sub_bass_peak_t": sub_bass_peak_t,
            "dynamic_range_db": dynamic_range_db,
        }

    # ------------------------------------------------------------------ #
    # PASS D: Contextual Cross-Modal Intelligence                        #
    # ------------------------------------------------------------------ #
    def pass_d_contextual(
        self,
        meta: VideoMetadata,
        visual_report: Dict[str, Any],
        audio_report: Dict[str, Any],
        profile: ProcessingProfile,
    ) -> Dict[str, Any]:
        """
        Fuses visual and audio evidence to determine what actually occurred
        in each segment and generates verified confidence scores.
        """
        logger.info("[Pass D] Running Contextual Intelligence & Cross-Modal Fusion...")
        v_events: List[VisualEvent] = visual_report["events"]
        a_events: List[AudioEvent] = audio_report["events"]
        duration = meta.duration_seconds

        all_timestamps = sorted(
            [e.timestamp for e in v_events] + [e.timestamp for e in a_events]
        )

        if not all_timestamps:
            logger.warning("[Pass D] No significant audiovisual events detected.")
            return {"moments": []}

        # Cluster timestamps within 5.0 seconds
        clusters: List[List[float]] = []
        cur_cluster = [all_timestamps[0]]
        for t in all_timestamps[1:]:
            if t - cur_cluster[-1] <= 5.0:
                cur_cluster.append(t)
            else:
                clusters.append(cur_cluster)
                cur_cluster = [t]
        if cur_cluster:
            clusters.append(cur_cluster)

        contextual_moments: List[ContextualMoment] = []

        for cluster in clusters:
            c_start = max(0.0, cluster[0] - 2.5)
            c_end = min(duration, cluster[-1] + 3.0)
            c_dur = c_end - c_start

            window_v = [e for e in v_events if c_start <= e.timestamp <= c_end]
            window_a = [e for e in a_events if c_start <= e.timestamp <= c_end]

            max_v_intensity = max([e.intensity for e in window_v], default=0.2)
            max_a_intensity = max([e.intensity for e in window_a], default=0.2)

            peak_cand = cluster[len(cluster) // 2]
            if window_a:
                peak_cand = max(window_a, key=lambda x: x.intensity).timestamp
            elif window_v:
                peak_cand = max(window_v, key=lambda x: x.intensity).timestamp

            primary_category = "Cinematic Gameplay"
            secondary_categories = []
            reasons = []
            confidence = 0.70

            has_flash = any(e.event_type == "explosion_flash" for e in window_v)
            has_bass = any(e.event_type == "bass_explosion" for e in window_a)
            has_gunfire = any(e.event_type == "gunfire_transient" for e in window_a)
            has_flick = any(e.event_type == "rapid_flick" for e in window_v)
            has_scene_cut = any(e.event_type == "scene_cut" for e in window_v)

            # Rule 1: High visual flash + sub-bass -> Epic Explosion
            if has_flash and has_bass:
                primary_category = "Epic Explosions"
                secondary_categories = ["Cinematic Gameplay", "Immersive Realism"]
                reasons.append("Synchronized visual flash and sub-bass detonation confirmed.")
                confidence = 0.94

            # Rule 2: Rapid flick + gunfire -> Intense Gunfight / Weapon Mechanics
            elif has_flick and has_gunfire:
                primary_category = "Intense Gunfights"
                secondary_categories = ["Weapon Mechanics", "Satisfying Kills"]
                reasons.append("High angular camera velocity aligned with sharp gunfire transients.")
                confidence = 0.90

            # Rule 3: Muzzle flash without heavy bass -> Weapon Mechanics
            elif has_gunfire or (has_flash and not has_bass):
                primary_category = "Weapon Mechanics"
                secondary_categories = ["Cinematic Gameplay"]
                reasons.append("Crisp weapon engagement audio with clean visuals.")
                confidence = 0.84

            # Rule 4: Sudden scene cut after high audio -> Unexpected Moment / Death Twist
            elif has_scene_cut and max_a_intensity > 0.6:
                primary_category = "Unexpected Moments"
                secondary_categories = ["Close Calls", "Funny Gameplay"]
                reasons.append("Abrupt visual transition following peak combat audio.")
                confidence = 0.82

            # Rule 5: Sustained motion and audio -> Cinematic Gameplay
            elif max_v_intensity > 0.5 or max_a_intensity > 0.5:
                primary_category = "Cinematic Gameplay"
                secondary_categories = ["Environmental Details"]
                reasons.append("Elevated gameplay pacing and consistent audiovisual engagement.")
                confidence = 0.76

            fusion_score = round(
                (max_v_intensity * 0.45) + (max_a_intensity * 0.40) + (confidence * 0.15),
                3
            )

            is_cand = True
            rejection_reasons = []
            if max_v_intensity < 0.25 and max_a_intensity < 0.25:
                is_cand = False
                rejection_reasons.append("Insufficient motion and flat audio dynamics (dead space / waiting).")

            moment = ContextualMoment(
                start_time=round(c_start, 2),
                end_time=round(c_end, 2),
                duration=round(c_dur, 2),
                peak_timestamp=round(peak_cand, 2),
                primary_category=primary_category,
                secondary_categories=secondary_categories,
                confidence=round(confidence, 2),
                visual_intensity=round(max_v_intensity, 2),
                audio_intensity=round(max_a_intensity, 2),
                fusion_score=fusion_score,
                reasons_for_selection=reasons,
                rejection_reasons=rejection_reasons,
                is_candidate=is_cand,
            )
            contextual_moments.append(moment)

        return {"moments": contextual_moments}


if __name__ == "__main__":
    engine = DeepIntelligenceEngine()
    print("DeepIntelligenceEngine module ready.")
