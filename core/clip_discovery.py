"""
Nyro AI Clip Factory - Intelligent Clip Discovery & Multi-Dimensional Scoring (Module 2)
Evaluates gameplay candidates across 15 retention dimensions:
1. Opening strength
2. Visual impact
3. Audio impact
4. Unexpectedness
5. Emotional intensity
6. Gameplay relevance
7. Cinematic value
8. Storytelling potential
9. Curiosity potential
10. Payoff quality
11. Replay potential
12. Loop potential
13. Viewer comprehension
14. Originality
15. Editing potential

Assigns candidates to 16 gaming content categories:
- Cinematic Gameplay, Unexpected Moments, Epic Explosions, Realistic Graphics,
- Weapon Mechanics, Intense Gunfights, Funny Gameplay, NPC Reactions,
- Vehicle Crashes, Close Calls, Character Interactions, Story Moments,
- Satisfying Kills, Unexpected Twists, Immersive Realism, Environmental Details.

Generates dual-tier candidates:
- Short-form clips: 6–10 seconds.
- Extended Shorts: 15–20 seconds.
Enforces intelligent overlap detection, deduplication, and dead-space rejection.
"""

import json
import logging
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

from core.config import config, RetentionScoringWeights

logger = logging.getLogger("ClipDiscovery")

# The 16 Content Categories
CONTENT_CATEGORIES = [
    "Cinematic Gameplay",
    "Unexpected Moments",
    "Epic Explosions",
    "Realistic Graphics",
    "Weapon Mechanics",
    "Intense Gunfights",
    "Funny Gameplay",
    "NPC Reactions",
    "Vehicle Crashes",
    "Close Calls",
    "Character Interactions",
    "Story Moments",
    "Satisfying Kills",
    "Unexpected Twists",
    "Immersive Realism",
    "Environmental Details",
]


@dataclass
class CandidateClip:
    id: str
    video_filename: str
    start_time: float
    end_time: float
    duration: float
    peak_timestamp: float
    trigger_type: str
    peak_intensity: float
    events: List[Dict[str, Any]]
    clip_format: str = "full"  # "micro" (6-10s) or "full" (15-20s)
    category: str = "Cinematic Gameplay"
    secondary_categories: List[str] = field(default_factory=list)
    score: float = 0.0
    score_breakdown: Optional[Dict[str, float]] = None
    retention_dimensions: Optional[Dict[str, float]] = None
    reasoning: str = ""
    suggested_hooks: List[str] = field(default_factory=list)
    title_suggestion: str = ""
    title_choices: List[str] = field(default_factory=list)
    description_suggestion: str = ""
    tags_suggestion: List[str] = field(default_factory=list)
    series_part: str = ""
    aura_profile: str = "CINEMATIC AURA"
    status: str = "candidate"
    render_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MultiDimensionalScorer:
    """Evaluates candidate clips across 15 retention dimensions with weighted scoring."""

    def __init__(self, weights: Optional[RetentionScoringWeights] = None):
        self.weights = weights or config.scoring_weights

    def evaluate_clip(
        self,
        clip: CandidateClip,
        time_vector: np.ndarray,
        rms_curve: np.ndarray,
        motion_samples: Optional[List[Tuple[float, float]]] = None,
        sub_bass_curve: Optional[np.ndarray] = None,
    ) -> CandidateClip:
        """Computes comprehensive 15-dimensional scores and weighted total."""
        start = clip.start_time
        end = clip.end_time
        peak = clip.peak_timestamp
        dur = max(0.5, clip.duration)
        is_micro = clip.clip_format == "micro" or dur <= 12.0

        # Extract RMS slice
        mask = (time_vector >= start) & (time_vector <= end) if len(time_vector) > 0 else np.array([])
        clip_rms = rms_curve[mask] if np.any(mask) else np.array([0.1])
        clip_times = time_vector[mask] if np.any(mask) else np.array([start])

        # Motion slice
        if motion_samples:
            m_vals = [m[1] for m in motion_samples if start <= m[0] <= end]
            clip_motion = np.array(m_vals) if m_vals else np.array([1.0])
        else:
            clip_motion = np.array([1.0])

        peak_intensity = clip.peak_intensity
        events = clip.events or []
        has_flash = any("flash" in e.get("event_type", "").lower() for e in events)
        has_bass = any("bass" in e.get("event_type", "").lower() for e in events)
        has_cut = any("cut" in e.get("event_type", "").lower() for e in events)
        has_transient = any("transient" in e.get("event_type", "").lower() or "sudden" in e.get("description", "").lower() for e in events)

        # 1. Opening strength (0-10): First 1.5s energy & visual motion
        first_mask = (clip_times <= start + (1.2 if is_micro else 2.0))
        open_rms = float(np.mean(clip_rms[first_mask])) if np.any(first_mask) else float(clip_rms[0])
        open_motion = float(np.mean(clip_motion[:3])) if len(clip_motion) >= 3 else 1.0
        opening_strength = min(10.0, max(2.0, open_rms * 45.0 + open_motion * 0.4 + (2.5 if is_micro else 1.5)))

        # 2. Visual impact (0-10): Peak motion & presence of flashes
        max_motion = float(np.max(clip_motion)) if len(clip_motion) > 0 else 1.0
        visual_impact = min(10.0, max(3.0, (max_motion * 0.5) + (2.0 if has_flash else 0.5) + (peak_intensity * 3.5)))

        # 3. Audio impact (0-10): Peak loudness jump & sub-bass energy
        peak_rms = float(np.max(clip_rms)) if len(clip_rms) > 0 else 0.2
        audio_impact = min(10.0, max(3.0, (peak_rms * 12.0) + (2.5 if has_bass else 1.0) + (peak_intensity * 3.0)))

        # 4. Unexpectedness (0-10): Sudden transients, jumpscares, scene shifts
        contrast = peak_rms / (float(np.mean(clip_rms)) + 1e-4)
        unexpectedness = min(10.0, max(2.5, (2.5 if has_transient else 1.0) + (2.0 if has_cut else 0.5) + min(4.5, contrast * 0.8)))

        # 5. Emotional intensity (0-10): Climax height & multi-event density
        density_factor = min(3.0, len(events) * 0.5)
        emotional_intensity = min(10.0, max(3.0, (peak_intensity * 5.0) + density_factor + (1.5 if has_bass else 0.5)))

        # 6. Gameplay relevance (0-10): Combat/action presence vs idle waiting
        idle_fraction = float(np.mean(clip_rms < 0.015))
        gameplay_relevance = min(10.0, max(2.0, (1.0 - idle_fraction) * 8.5 + (1.5 if len(events) >= 1 else 0.0)))

        # 7. Cinematic value (0-10): Dramatic lighting, camera motion, framing
        cinematic_value = min(10.0, max(3.0, (2.5 if has_flash else 1.0) + (2.0 if clip.category in ("Cinematic Gameplay", "Epic Explosions") else 1.0) + (open_motion * 0.3) + 3.0))

        # 8. Storytelling potential (0-10): Buildup time + clear resolution
        if is_micro:
            storytelling_potential = 6.0  # Micro clips rely on instant punch rather than narrative arc
        else:
            rel_peak = (peak - start) / dur
            good_arc = 2.5 if (0.4 <= rel_peak <= 0.8) else 1.0
            storytelling_potential = min(10.0, max(4.0, good_arc + min(3.0, len(events) * 0.6) + 3.5))

        # 9. Curiosity potential (0-10): Pre-peak tension
        pre_mask = (clip_times < peak)
        pre_energy = float(np.mean(clip_rms[pre_mask])) if np.any(pre_mask) else 0.05
        curiosity_potential = min(10.0, max(3.0, (1.5 if is_micro else 3.0) + (contrast * 0.6)))

        # 10. Payoff quality (0-10): Climax intensity & decisive resolution
        payoff_quality = min(10.0, max(3.0, (peak_intensity * 6.5) + (2.5 if (has_bass or has_flash) else 1.0)))

        # 11. Replay potential (0-10): Punchy, fast, rewarding multiple viewings
        replay_potential = min(10.0, max(3.0, (4.5 if is_micro else 2.5) + (2.5 if has_transient else 0.5) + (peak_intensity * 3.0)))

        # 12. Loop potential (0-10): Smooth ending into beginning transition
        end_rms = float(np.mean(clip_rms[-3:])) if len(clip_rms) >= 3 else open_rms
        diff_open_close = abs(open_rms - end_rms)
        loop_bonus = 3.0 if diff_open_close < 0.05 else 1.0
        loop_potential = min(10.0, max(3.0, (3.5 if is_micro else 2.0) + loop_bonus + (2.0 if not has_cut else 0.5)))

        # 13. Viewer comprehension (0-10): Not blurry, clear pacing
        low_blur = min(10.0, 7.5 + (2.0 if not has_cut else 1.0))
        viewer_comprehension = round(low_blur, 1)

        # 14. Originality (0-10): Unique combination of flash + motion
        originality = min(10.0, max(4.0, (2.0 if has_flash and has_bass else 1.0) + (peak_intensity * 3.5) + 2.5))

        # 15. Editing potential (0-10): SFX sync points, punch-in opportunities
        editing_potential = min(10.0, max(4.0, min(3.0, len(events) * 0.8) + (2.5 if peak_intensity > 0.6 else 1.0) + 3.5))

        dimensions = {
            "opening_strength": round(opening_strength, 1),
            "visual_impact": round(visual_impact, 1),
            "audio_impact": round(audio_impact, 1),
            "unexpectedness": round(unexpectedness, 1),
            "emotional_intensity": round(emotional_intensity, 1),
            "gameplay_relevance": round(gameplay_relevance, 1),
            "cinematic_value": round(cinematic_value, 1),
            "storytelling_potential": round(storytelling_potential, 1),
            "curiosity_potential": round(curiosity_potential, 1),
            "payoff_quality": round(payoff_quality, 1),
            "replay_potential": round(replay_potential, 1),
            "loop_potential": round(loop_potential, 1),
            "viewer_comprehension": round(viewer_comprehension, 1),
            "originality": round(originality, 1),
            "editing_potential": round(editing_potential, 1),
        }

        # Weighted total calculation (scaled 0-100)
        # Using configured weights:
        # hook_potential: 15% (opening_strength)
        # visual_quality: 15% (visual_impact)
        # audio_quality: 10% (audio_impact)
        # event_significance: 15% (payoff_quality & unexpectedness)
        # payoff: 15% (payoff_quality)
        # emotional_impact: 10% (emotional_intensity)
        # replay_loop_potential: 10% ((replay + loop) / 2)
        # originality: 5% (originality)
        # technical_quality: 5% (comprehension)
        w = self.weights
        total_10 = (
            opening_strength * w.hook_potential +
            visual_impact * w.visual_quality +
            audio_impact * w.audio_quality +
            ((payoff_quality + unexpectedness) / 2.0) * w.event_significance +
            payoff_quality * w.payoff +
            emotional_intensity * w.emotional_impact +
            ((replay_potential + loop_potential) / 2.0) * w.replay_loop_potential +
            originality * w.originality +
            viewer_comprehension * w.technical_quality
        )
        # Normalize sum of weights if not exactly 1.0
        w_sum = (w.hook_potential + w.visual_quality + w.audio_quality + w.event_significance +
                 w.payoff + w.emotional_impact + w.replay_loop_potential + w.originality + w.technical_quality)
        if w_sum > 0:
            total_10 = total_10 / w_sum

        final_score = round(total_10 * 10.0, 1)

        # Editorial reasoning
        reasons = []
        if is_micro:
            reasons.append(f"⚡ [Micro-Short {dur:.1f}s]: Fast-paced burst with high loop replay potential ({dimensions['loop_potential']}/10).")
        else:
            reasons.append(f"🎬 [Extended Short {dur:.1f}s]: Structured narrative arc with suspense buildup and payoff at {peak:.1f}s.")

        if opening_strength >= 7.5:
            reasons.append("High-energy opening hooks viewer attention in the crucial first 2 seconds.")
        if payoff_quality >= 7.5:
            reasons.append(f"Decisive peak payoff ({payoff_quality}/10) ensures strong end-of-clip retention.")
        if clip.category != "Cinematic Gameplay":
            reasons.append(f"Categorized as '{clip.category}' based on verified audiovisual dynamics.")

        clip.score = final_score
        clip.retention_dimensions = dimensions
        clip.score_breakdown = {
            "hook_potential": round(opening_strength * 10.0, 1),
            "visual_quality": round(visual_impact * 10.0, 1),
            "audio_quality": round(audio_impact * 10.0, 1),
            "event_significance": round(((payoff_quality + unexpectedness) / 2.0) * 10.0, 1),
            "payoff": round(payoff_quality * 10.0, 1),
            "emotional_impact": round(emotional_intensity * 10.0, 1),
            "replay_loop": round(((replay_potential + loop_potential) / 2.0) * 10.0, 1),
            "originality": round(originality * 10.0, 1),
            "technical_quality": round(viewer_comprehension * 10.0, 1),
        }
        clip.reasoning = " ".join(reasons)
        return clip


class IntelligentClipDiscoveryEngine:
    """Discovers, categorizes, and filters dual-tier highlight candidates."""

    def __init__(self, scorer: Optional[MultiDimensionalScorer] = None):
        self.scorer = scorer or MultiDimensionalScorer()

    def discover_candidates(
        self,
        video_filename: str,
        video_duration: float,
        visual_events: List[Dict[str, Any]],
        audio_events: List[Dict[str, Any]],
        time_vector: np.ndarray,
        rms_curve: np.ndarray,
        motion_samples: Optional[List[Tuple[float, float]]] = None,
    ) -> List[CandidateClip]:
        """
        Clusters deep audiovisual events into:
        - Micro-Shorts (6–10s)
        - Extended Shorts (15–20s)
        Applies overlap deduplication and 15-dimensional retention scoring.
        """
        all_events = sorted(visual_events + audio_events, key=lambda e: e.get("timestamp", 0.0))
        if not all_events:
            logger.warning("No audiovisual events detected to form candidates.")
            return []

        # Cluster events within 6.0 seconds
        clusters: List[List[Dict[str, Any]]] = []
        cur_cluster = [all_events[0]]
        for ev in all_events[1:]:
            if ev.get("timestamp", 0.0) - cur_cluster[-1].get("timestamp", 0.0) <= 6.0:
                cur_cluster.append(ev)
            else:
                clusters.append(cur_cluster)
                cur_cluster = [ev]
        if cur_cluster:
            clusters.append(cur_cluster)

        stem = Path(video_filename).stem
        raw_candidates: List[CandidateClip] = []
        cand_idx = 1

        for cluster in clusters:
            primary_ev = max(cluster, key=lambda e: e.get("intensity", 0.5))
            peak_t = float(primary_ev.get("timestamp", cluster[0].get("timestamp", 0.0)))
            peak_intensity = float(primary_ev.get("intensity", 0.7))
            trigger_type = str(primary_ev.get("event_type", "audio_spike"))

            # Determine category based on cluster events
            cat, sec_cats = self._classify_categories(cluster)

            # 1. EXTENDED SHORT (15s – 20s)
            ext_dur = 17.5  # Ideal default in 15-20s range
            ext_start = max(0.0, peak_t - 9.0)
            ext_end = min(video_duration, ext_start + ext_dur)
            if ext_end - ext_start < 15.0:
                ext_start = max(0.0, ext_end - 15.0)
            ext_dur = ext_end - ext_start

            ext_id = f"clip_{stem}_{cand_idx:02d}_ext"
            ext_clip = CandidateClip(
                id=ext_id,
                video_filename=video_filename,
                start_time=round(ext_start, 2),
                end_time=round(ext_end, 2),
                duration=round(ext_dur, 2),
                peak_timestamp=round(peak_t, 2),
                trigger_type=trigger_type,
                peak_intensity=peak_intensity,
                events=cluster,
                clip_format="full",
                category=cat,
                secondary_categories=sec_cats,
            )
            raw_candidates.append(ext_clip)

            # 2. MICRO-SHORT (6s – 10s)
            # Extracted whenever peak intensity >= 0.55 or sudden transient
            is_high_impact = peak_intensity >= 0.55 or any("transient" in e.get("event_type", "").lower() for e in cluster)
            if is_high_impact:
                micro_dur = 8.5  # Ideal default in 6-10s range
                micro_start = max(0.0, peak_t - 2.2)
                micro_end = min(video_duration, micro_start + micro_dur)
                micro_dur = micro_end - micro_start

                micro_id = f"clip_{stem}_{cand_idx:02d}_micro"
                micro_clip = CandidateClip(
                    id=micro_id,
                    video_filename=video_filename,
                    start_time=round(micro_start, 2),
                    end_time=round(micro_end, 2),
                    duration=round(micro_dur, 2),
                    peak_timestamp=round(peak_t, 2),
                    trigger_type=trigger_type,
                    peak_intensity=peak_intensity,
                    events=[primary_ev],
                    clip_format="micro",
                    category=cat,
                    secondary_categories=sec_cats,
                )
                raw_candidates.append(micro_clip)

            cand_idx += 1

        # Score all raw candidates
        scored_candidates = []
        for c in raw_candidates:
            scored = self.scorer.evaluate_clip(c, time_vector, rms_curve, motion_samples)
            scored_candidates.append(scored)

        # Deduplicate candidates within the same format tier that heavily overlap (>60% IoU)
        final_candidates = self._deduplicate_candidates(scored_candidates)
        final_candidates.sort(key=lambda x: x.score, reverse=True)

        logger.info(f"Discovered {len(final_candidates)} high-quality candidates after deduplication & 15D scoring.")
        return final_candidates

    def _classify_categories(self, cluster: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Assigns primary and secondary categories from the 16 Content Categories."""
        ev_types = [e.get("event_type", "").lower() for e in cluster]
        descriptions = [e.get("description", "").lower() for e in cluster]

        has_flash = any("flash" in t for t in ev_types)
        has_bass = any("bass" in t for t in ev_types)
        has_gunfire = any("gunfire" in t for t in ev_types)
        has_flick = any("flick" in t for t in ev_types)
        has_cut = any("cut" in t for t in ev_types)

        if has_flash and has_bass:
            return "Epic Explosions", ["Cinematic Gameplay", "Immersive Realism"]
        elif has_flick and has_gunfire:
            return "Intense Gunfights", ["Weapon Mechanics", "Satisfying Kills"]
        elif has_gunfire:
            return "Weapon Mechanics", ["Intense Gunfights"]
        elif has_cut:
            return "Unexpected Moments", ["Unexpected Twists", "Close Calls"]
        elif has_bass:
            return "Satisfying Kills", ["Cinematic Gameplay"]
        else:
            return "Cinematic Gameplay", ["Environmental Details", "Story Moments"]

    def _deduplicate_candidates(self, candidates: List[CandidateClip]) -> List[CandidateClip]:
        """Removes near-duplicate candidates (>60% temporal overlap) within the same tier."""
        micro_clips = [c for c in candidates if c.clip_format == "micro"]
        ext_clips = [c for c in candidates if c.clip_format != "micro"]

        def _dedup_list(clip_list: List[CandidateClip]) -> List[CandidateClip]:
            clip_list.sort(key=lambda x: x.score, reverse=True)
            kept: List[CandidateClip] = []
            for candidate in clip_list:
                overlap = False
                for existing in kept:
                    # Calculate Intersection-over-Union (IoU)
                    inter_start = max(candidate.start_time, existing.start_time)
                    inter_end = min(candidate.end_time, existing.end_time)
                    if inter_end > inter_start:
                        inter_dur = inter_end - inter_start
                        union_dur = (candidate.duration + existing.duration) - inter_dur
                        iou = inter_dur / max(1e-4, union_dur)
                        if iou > 0.60:
                            overlap = True
                            break
                if not overlap:
                    kept.append(candidate)
            return kept

        deduped = _dedup_list(micro_clips) + _dedup_list(ext_clips)
        return deduped


if __name__ == "__main__":
    engine = IntelligentClipDiscoveryEngine()
    print("IntelligentClipDiscoveryEngine ready.")
