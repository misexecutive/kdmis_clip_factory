"""
Nyro AI Clip Factory - Autonomous Studio Director
Zero-touch end-to-end automation engine for Gamer Nyro:
1. Deep Audiovisual Inspection & Health Verification
2. Multi-Modal Candidate Detection & 6-Factor Retention Scoring
3. Autonomous VFX & Color Grading
4. Autonomous Sound Design, SFX Synchronization & -14 LUFS Mastering
5. High-Converting YouTube Copywriting (Titles, Hooks, Descriptions, SEO Tags)
6. Hardware-Accelerated Vertical 9:16 Shorts Rendering
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.ingest import IngestionEngine, VideoMetadata
from core.detector import MomentDetector, CandidateClip
from core.scorer import CandidateScorer
from core.metadata import MetadataGenerator
from core.video_fx import VideoFXEngine
from core.sound_engine import SoundDesigner
from core.renderer import VideoRenderer
from core.database import ClipDatabase
from core.aura_engine import NyroAuraEngine, EditingBlueprint
from core.packaging import CentralExportPackager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AutonomousDirector")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AutonomousDirector:
    def __init__(self, fresh_start: bool = False):
        self.ingest = IngestionEngine()
        self.detector = MomentDetector()
        self.scorer = CandidateScorer()
        self.metadata_gen = MetadataGenerator(channel_name="Gamer Nyro")
        self.vfx_engine = VideoFXEngine()
        self.sound_designer = SoundDesigner()
        self.renderer = VideoRenderer()
        self.db = ClipDatabase()
        self.aura_engine = NyroAuraEngine()
        self.packager = CentralExportPackager()

        if fresh_start:
            logger.info("Fresh start requested: purging database and audio cache...")
            self.db.purge_all()
            cache_dir = PROJECT_ROOT / "storage" / "cache"
            for f in cache_dir.glob("*_16000hz.wav"):
                try:
                    f.unlink()
                except Exception:
                    pass

    def run_autonomous_session(
        self,
        video_path: str,
        top_n: int = 3,
        color_preset: str = "auto",
        enable_vfx: bool = True,
        enable_sfx: bool = True,
        burn_series_badge: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes a zero-click autonomous studio production for an OBS recording:
        Inspects footage -> Detects highlights -> Grades colors & VFX -> Adds SFX & masters audio ->
        Renders top N 9:16 Shorts -> Writes YouTube upload metadata packages.
        """
        session_start = time.time()
        in_file = Path(video_path)
        if not in_file.exists():
            raise FileNotFoundError(f"Source video not found: {video_path}")

        print("\n" + "=" * 70)
        print(f"🎬 NYRO AI CLIP FACTORY — AUTONOMOUS STUDIO DIRECTOR")
        print(f"Source: {in_file.name} | Target Top Reels: {top_n}")
        print("=" * 70)

        # -------------------------------------------------------------
        # STEP 1: Deep Audiovisual Inspection & Health Verification
        # -------------------------------------------------------------
        print("\n[Stage 1/5] 🔍 Deep Audiovisual Inspection...")
        meta = self.ingest.probe(str(in_file))
        rec_id = self.db.save_recording(meta)
        print(f"  ✓ Resolution: {meta.width}x{meta.height} ({'16:9 Landscape' if meta.width > meta.height else 'Vertical'})")
        print(f"  ✓ Duration: {meta.duration_seconds:.1f}s ({(meta.duration_seconds / 60):.1f} min) | FPS: {meta.fps}")
        print(f"  ✓ Video Codec: {meta.video_codec} | Audio Codec: {meta.audio_codec}")
        print(f"  ✓ File Size: {meta.file_size_bytes / (1024*1024):.1f} MB")

        # -------------------------------------------------------------
        # STEP 2: Candidate Moment Detection & 6-Factor Scoring
        # -------------------------------------------------------------
        print("\n[Stage 2/5] ⚡ Extracting High-Impact Highlights...")
        wav_proxy = self.ingest.extract_audio_proxy(str(in_file))
        time_vec, rms_curve, audio_events = self.detector.analyze_audio_track(wav_proxy)
        visual_events = self.detector.detect_visual_flashes_and_scenes(str(in_file))
        all_events = audio_events + visual_events

        candidates = self.detector.cluster_events_into_candidates(
            video_filename=meta.filename,
            video_duration=meta.duration_seconds,
            events=all_events,
        )
        scored_candidates = self.scorer.score_all(candidates, time_vec, rms_curve)

        print(f"  ✓ Detected {len(scored_candidates)} candidate clips across gameplay.")

        # -------------------------------------------------------------
        # STEP 3: Generate Metadata & Select Top N
        # -------------------------------------------------------------
        print(f"\n[Stage 3/5] ✍️ Generating Viral Copywriting & Curating Top {top_n} Reels...")
        for idx, cand in enumerate(scored_candidates, 1):
            self.metadata_gen.generate_youtube_metadata(cand, part_num=idx)

        # Save all candidates to database
        self.db.save_candidates(rec_id, scored_candidates)

        top_candidates = scored_candidates[:top_n]
        if not top_candidates:
            print("  ✕ No candidates met the threshold.")
            return {"status": "no_candidates", "exported_clips": []}

        # -------------------------------------------------------------
        # STEP 4: Autonomous Editing, VFX, SFX & 9:16 Rendering
        # -------------------------------------------------------------
        print(f"\n[Stage 4/5] 🎨 Rendering Top {len(top_candidates)} Upload-Ready 9:16 Shorts (VFX + SFX)...")
        rendered_outputs = []

        for idx, cand in enumerate(top_candidates, 1):
            clip_dur = cand.duration
            is_micro = cand.clip_format == "micro" or clip_dur <= 14.0
            badge_text = f"⚡ PART {idx}" if burn_series_badge else ""
            hook_text = cand.suggested_hooks[0] if cand.suggested_hooks else "INSANE PLAY"
            out_filename = f"{cand.id}_autonomous_short.mp4"

            # Generate unique AURA editing blueprint
            blueprint = self.aura_engine.generate_blueprint(cand, deterministic_seed=idx * 100)
            active_color = color_preset
            if active_color == "auto":
                active_color = blueprint.color_grading.get("preset", "vibrant_tactical")

            print(f"\n  [{idx}/{len(top_candidates)}] Rendering {cand.id} ({clip_dur:.1f}s | Score: {cand.score:.1f}/100)")
            print(f"      • Format: {'⚡ Micro-Short' if is_micro else '🎬 Full Highlight'}")
            print(f"      • AURA Profile: {blueprint.aura_profile}")
            print(f"      • Hook Pill: \"{hook_text}\"")
            print(f"      • Color Grade: {active_color}")
            print(f"      • Sound Design: {len(blueprint.sfx_selection)} tailored SFX layers + -14 LUFS Master")

            render_path = self.renderer.render_short_9_16(
                input_video_path=str(in_file),
                start_time=cand.start_time,
                end_time=cand.end_time,
                output_filename=out_filename,
                hook_text=hook_text,
                series_badge=badge_text,
                color_preset=active_color,
                enable_vfx=enable_vfx,
                enable_sfx=enable_sfx,
                peak_timestamp=cand.peak_timestamp,
                trigger_type=cand.trigger_type,
                peak_intensity=cand.peak_intensity,
                score=cand.score,
                clip_format=cand.clip_format,
            )

            # Package into standard output/recording_name/clip_id/ structure
            clip_package_dir = self.packager.package_clip_export(
                source_recording_filename=meta.filename,
                clip_id=cand.id,
                rendered_video_path=render_path,
                candidate=cand,
                blueprint=blueprint,
                selected_hook=hook_text,
                selected_title=cand.title_suggestion,
            )

            # Update database status to 'approved' and store render path & blueprint
            rel_render_path = f"/storage/exports/{out_filename}"
            self.db.update_clip_status(
                cand.id,
                status="approved",
                selected_hook=hook_text,
                render_path=rel_render_path,
                selected_title=cand.title_suggestion,
                series_part=badge_text,
            )
            self.db.update_clip_blueprint(
                cand.id,
                aura_profile=blueprint.aura_profile,
                blueprint_dict=blueprint.to_dict(),
                category=cand.category,
                secondary_categories=cand.secondary_categories,
            )

            rendered_outputs.append({
                "clip_id": cand.id,
                "score": cand.score,
                "video_path": str(clip_package_dir / "video.mp4"),
                "package_dir": str(clip_package_dir),
                "metadata_txt": str(clip_package_dir / "metadata.txt"),
                "thumbnail_jpg": str(clip_package_dir / "thumbnail.jpg"),
                "title": cand.title_suggestion,
                "hook": hook_text,
                "series_badge": badge_text,
                "duration": clip_dur,
                "aura_profile": blueprint.aura_profile,
                "category": cand.category,
            })
            print(f"      ✓ Package Ready: {clip_package_dir.name} in output/{meta.filename.split('.')[0]}/")

        elapsed = time.time() - session_start
        print("\n" + "=" * 70)
        print(f"🎉 AUTONOMOUS PRODUCTION COMPLETE ({elapsed:.1f}s)")
        print(f"Successfully generated {len(rendered_outputs)} broadcast-quality YouTube Shorts!")
        print(f"Saved in: storage/exports/")
        print("=" * 70 + "\n")

        return {
            "status": "success",
            "session_time_seconds": round(elapsed, 2),
            "recording_id": rec_id,
            "filename": meta.filename,
            "total_candidates": len(scored_candidates),
            "exported_clips": rendered_outputs,
        }


if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "storage/raw_recordings/test.mp4"
    director = AutonomousDirector(fresh_start=False)
    res = director.run_autonomous_session(video, top_n=2)
