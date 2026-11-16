"""
Nyro AI Clip Factory - Phase 1 Pipeline Orchestrator
Executes full ingestion, audio/visual analysis, candidate moment generation,
scoring, and SQLite storage for any OBS gameplay recording.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

from core.ingest import IngestionEngine
from core.detector import MomentDetector, CandidateClip
from core.scorer import CandidateScorer
from core.metadata import MetadataGenerator
from core.database import ClipDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("ClipFactoryPipeline")


class ClipFactoryPipeline:
    def __init__(self):
        self.ingest = IngestionEngine()
        self.detector = MomentDetector()
        self.scorer = CandidateScorer()
        self.metadata_gen = MetadataGenerator()
        self.db = ClipDatabase()

    def process_recording(self, video_path: str) -> Dict[str, Any]:
        """
        Executes end-to-end Phase 1 candidate moment detection on a video.
        """
        video_file = Path(video_path)
        logger.info(f"=== Starting Nyro AI Clip Factory on: {video_file.name} ===")

        # Step 1: Ingest & Inspect
        meta = self.ingest.probe(str(video_file))
        rec_id = self.db.save_recording(meta)

        # Step 2: Extract audio proxy
        wav_proxy = self.ingest.extract_audio_proxy(str(video_file))

        # Step 3: Analyze audio energy & transients
        time_vec, rms_curve, audio_events = self.detector.analyze_audio_track(wav_proxy)

        # Step 4: Scan visual scene cuts & transitions
        visual_events = self.detector.detect_visual_flashes_and_scenes(str(video_file))

        # Step 5: Merge and cluster events into candidate clips
        all_events = audio_events + visual_events
        candidates = self.detector.cluster_events_into_candidates(
            video_filename=meta.filename,
            video_duration=meta.duration_seconds,
            events=all_events,
        )

        # Step 6: Score and Rank Candidates
        scored_candidates = self.scorer.score_all(candidates, time_vec, rms_curve)

        # Step 7: Generate Hooks & YouTube Metadata with Episodic Series Part Sequencing
        for idx, cand in enumerate(scored_candidates, 1):
            self.metadata_gen.generate_youtube_metadata(cand, part_num=idx)

        # Step 8: Persist in SQLite
        self.db.save_candidates(rec_id, scored_candidates)

        logger.info(f"=== Processing Complete for {video_file.name}. Found {len(scored_candidates)} candidates! ===")
        return {
            "recording_id": rec_id,
            "filename": meta.filename,
            "duration": meta.duration_seconds,
            "resolution": f"{meta.width}x{meta.height}",
            "candidate_count": len(scored_candidates),
            "top_candidates": [c.to_dict() for c in scored_candidates[:5]],
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m core.pipeline <path_to_gameplay_recording>")
        sys.exit(1)

    pipe = ClipFactoryPipeline()
    result = pipe.process_recording(sys.argv[1])
    print("\n--- RESULTS SUMMARY ---")
    print(f"File: {result['filename']} ({result['duration']:.1f}s, {result['resolution']})")
    print(f"Generated {result['candidate_count']} candidate clips:")
    for idx, c in enumerate(result['top_candidates'], 1):
        print(f"\n[{idx}] {c['id']} | Score: {c['score']}/100")
        print(f"    Window: {c['start_time']}s -> {c['end_time']}s (Duration: {c['duration']}s)")
        print(f"    Peak: {c['peak_timestamp']}s ({c['trigger_type']}, intensity {c['peak_intensity']*100:.0f}%)")
        print(f"    Reasoning: {c['reasoning']}")
        print(f"    Hook Suggestion: \"{c['suggested_hooks'][0] if c['suggested_hooks'] else ''}\"")
        print(f"    YouTube Title: {c['title_suggestion']}")
