"""
Nyro AI Clip Factory - Master Command-Line Interface (CLI) (Module 9)
Provides unified production commands:
- python main.py analyze --input "recording.mp4"       (Deep 4-pass audiovisual inspection)
- python main.py discover --input "recording.mp4"      (Multi-dimensional clip candidate discovery)
- python main.py export --input "recording.mp4" [--clip-id <id>] (Hardware 9:16 export & metadata packaging)
- python main.py metadata --input "recording.mp4"      (Generate YouTube copywriting packages)
- python main.py validate --input "output/recording"   (Post-render broadcast quality inspection)
- python main.py pipeline --input "recording.mp4"      (Complete zero-touch end-to-end studio production)
- python main.py start [--port 8000]                   (Auto-ingest + launch dashboard + open browser)
- python main.py server [--port 8000]                  (Dashboard server)
- python main.py list                                  (List all candidate clips)
- python main.py reset                                 (Purge database and cache)
"""

import argparse
import json
import logging
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import config
from core.hardware import HardwareInspector
from core.deep_intelligence import DeepIntelligenceEngine
from core.clip_discovery import IntelligentClipDiscoveryEngine, MultiDimensionalScorer, CandidateClip
from core.aura_engine import NyroAuraEngine
from core.sfx_manager import SFXLibraryManager
from core.renderer import VideoRenderer
from core.export_validator import ExportValidator
from core.packaging import CentralExportPackager
from core.database import ClipDatabase
from core.director import AutonomousDirector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("NyroCLI")


def resolve_video_path(video_input: str) -> Path:
    p = Path(video_input)
    if p.is_file():
        return p.resolve()
    root_p = PROJECT_ROOT / p
    if root_p.is_file():
        return root_p.resolve()
    storage_p = PROJECT_ROOT / "storage" / "raw_recordings" / p.name
    if storage_p.is_file():
        return storage_p.resolve()
    raise FileNotFoundError(f"Video file not found: '{video_input}'")


def cmd_analyze(args):
    """Runs Deep 4-Pass Audiovisual Intelligence (Pass A, B, C, D)."""
    vid = resolve_video_path(args.input)
    engine = DeepIntelligenceEngine()
    rep_dir = PROJECT_ROOT / "data" / "reports"
    report = engine.analyze_recording(str(vid), save_report_dir=rep_dir)
    print("\n" + "=" * 70)
    print("✓ DEEP AUDIOTVISUAL ANALYSIS REPORT")
    print("=" * 70)
    print(f"Source: {report.source_filename} ({report.resolution} @ {report.fps}fps, {report.duration_seconds}s)")
    print(f"Visual Events: {len(report.visual_events)} | Scene Boundaries: {len(report.scene_boundaries)}")
    print(f"Audio Events: {len(report.audio_events)} | Dynamic Range: {report.audio_dynamic_range_db} dB")
    print(f"Synthesized Contextual Moments: {len(report.contextual_moments)}")
    for idx, m in enumerate(report.contextual_moments[:5], 1):
        print(f"  [{idx}] Category: '{m['primary_category']}' | Window: {m['start_time']}s-{m['end_time']}s | Peak: {m['peak_timestamp']}s | Confidence: {m['confidence']*100:.0f}%")
        if m["reasons_for_selection"]:
            print(f"      Reasons: {m['reasons_for_selection'][0]}")
    print("=" * 70)


def cmd_discover(args):
    """Discovers and ranks candidate clips across 15 retention dimensions."""
    vid = resolve_video_path(args.input)
    engine = DeepIntelligenceEngine()
    report = engine.analyze_recording(str(vid))

    wav_proxy = engine.ingest.extract_audio_proxy(str(vid))
    import soundfile as sf
    y, sr = sf.read(wav_proxy)
    if y.ndim > 1:
        y = y.mean(axis=1)
    # Fast RMS curve
    win = int(0.25 * sr)
    n_win = len(y) // win
    rms = np.sqrt(np.mean(y[:n_win*win].reshape(n_win, win)**2, axis=1) + 1e-9) if n_win > 0 else np.array([0.1])
    time_vec = np.arange(n_win) * 0.25

    discovery = IntelligentClipDiscoveryEngine()
    candidates = discovery.discover_candidates(
        video_filename=report.source_filename,
        video_duration=report.duration_seconds,
        visual_events=report.visual_events,
        audio_events=report.audio_events,
        time_vector=time_vec,
        rms_curve=rms,
    )

    db = ClipDatabase()
    rec_id = db.save_recording(engine.ingest.probe(str(vid)))
    db.save_candidates(rec_id, candidates)

    print("\n" + "=" * 70)
    print(f"✓ DISCOVERED {len(candidates)} HIGH-IMPACT CANDIDATES")
    print("=" * 70)
    for idx, c in enumerate(candidates, 1):
        fmt = "⚡ MICRO (6-10s)" if c.clip_format == "micro" else "🎬 EXTENDED (15-20s)"
        print(f"[{idx}] {c.id} {fmt} | Score: {c.score}/100 | Category: '{c.category}'")
        print(f"    Window: {c.start_time}s -> {c.end_time}s ({c.duration}s) | Peak: {c.peak_timestamp}s")
        print(f"    Hook: \"{c.suggested_hooks[0] if c.suggested_hooks else ''}\"")
        print(f"    Reasoning: {c.reasoning}")
    print("=" * 70)


def cmd_export(args):
    """Renders 9:16 vertical Short and creates standardized output/ metadata bundle."""
    vid = resolve_video_path(args.input)
    db = ClipDatabase()
    clips = db.get_clips_for_recording()
    if not clips:
        # Run discovery first
        cmd_discover(args)
        clips = db.get_clips_for_recording()

    targets = []
    if args.clip_id:
        targets = [c for c in clips if c["id"] == args.clip_id]
        if not targets:
            print(f"[Error] Clip ID '{args.clip_id}' not found.")
            sys.exit(1)
    else:
        # Export top approved or top candidates
        targets = sorted(clips, key=lambda x: x.get("score", 0), reverse=True)[:args.top]

    renderer = VideoRenderer()
    aura_engine = NyroAuraEngine()
    packager = CentralExportPackager()

    print(f"\n[Export] Rendering & Packaging {len(targets)} Shorts...")
    for idx, t in enumerate(targets, 1):
        c_dur = round(t["end_time"] - t["start_time"], 2)
        cand = CandidateClip(
            id=t["id"],
            video_filename=t["filename"],
            start_time=t["start_time"],
            end_time=t["end_time"],
            duration=c_dur,
            peak_timestamp=t.get("peak_timestamp", 0.0),
            trigger_type=t.get("trigger_type", "audio_spike"),
            peak_intensity=t.get("peak_intensity", 0.8),
            events=[],
            clip_format=t.get("clip_format", "micro"),
            category=t.get("category", "Cinematic Gameplay"),
            score=t.get("score", 80.0),
            title_suggestion=t.get("title", ""),
            suggested_hooks=[t.get("selected_hook") or "INSANE PLAY"],
        )

        blueprint = aura_engine.generate_blueprint(cand, deterministic_seed=idx * 77)
        out_name = f"{cand.id}_vertical.mp4"
        hook = t.get("selected_hook") or (cand.suggested_hooks[0] if cand.suggested_hooks else "")

        render_path = renderer.render_short_9_16(
            input_video_path=str(vid),
            start_time=cand.start_time,
            end_time=cand.end_time,
            output_filename=out_name,
            hook_text=hook,
            series_badge=t.get("series_part") or f"⚡ PART {idx}",
            color_preset=blueprint.color_grading.get("preset", "vibrant_tactical"),
            enable_vfx=True,
            enable_sfx=True,
            peak_timestamp=cand.peak_timestamp,
            trigger_type=cand.trigger_type,
            peak_intensity=cand.peak_intensity,
            score=cand.score,
            clip_format=cand.clip_format,
        )

        package_dir = packager.package_clip_export(
            source_recording_filename=vid.name,
            clip_id=cand.id,
            rendered_video_path=render_path,
            candidate=cand,
            blueprint=blueprint,
            selected_hook=hook,
            selected_title=cand.title_suggestion,
        )
        print(f"  ✓ [{idx}/{len(targets)}] Export Complete: {package_dir}")


def cmd_validate(args):
    """Inspects rendered video exports for broadcast compliance."""
    target_path = Path(args.input)
    validator = ExportValidator()

    if target_path.is_file():
        files = [target_path]
    elif target_path.is_dir():
        files = list(target_path.glob("**/video.mp4"))
        if not files:
            files = list(target_path.glob("*.mp4"))
    else:
        print(f"[Error] Target '{args.input}' not found.")
        sys.exit(1)

    print(f"\n[Validator] Inspecting {len(files)} export(s)...")
    for f in files:
        rep = validator.validate_export(str(f))
        status = "✓ PASSED" if rep.valid else "✕ FAILED"
        print(f"{status}: {f.name} ({rep.width}x{rep.height}, {rep.duration_seconds}s, Max Vol: {rep.max_volume_db}dB, Faststart: {rep.faststart_enabled})")
        if rep.errors:
            print(f"   Errors: {rep.errors}")
        if rep.warnings:
            print(f"   Warnings: {rep.warnings}")


def cmd_pipeline(args):
    """Executes the complete zero-touch studio production end-to-end."""
    vid = resolve_video_path(args.input)
    director = AutonomousDirector(fresh_start=args.fresh)
    director.run_autonomous_session(
        video_path=str(vid),
        top_n=args.top,
        color_preset=args.preset,
        enable_vfx=not args.no_vfx,
        enable_sfx=not args.no_sfx,
    )


def open_browser_delayed(url: str, delay: float = 1.2):
    def _open():
        time.sleep(delay)
        print(f"\n[Clip Factory] Opening dashboard: {url}\n")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="Nyro AI Clip Factory — Master Video Production Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    p_an = subparsers.add_parser("analyze", help="Perform Deep 4-Pass audiovisual intelligence")
    p_an.add_argument("--input", required=True, help="Input video recording path or filename")

    # discover command
    p_dis = subparsers.add_parser("discover", help="Discover and score dual-tier candidate moments")
    p_dis.add_argument("--input", required=True, help="Input video recording path or filename")

    # export command
    p_exp = subparsers.add_parser("export", help="Render vertical Shorts and write standardized output package")
    p_exp.add_argument("--input", required=True, help="Input video recording path or filename")
    p_exp.add_argument("--clip-id", default=None, help="Specific clip ID to export")
    p_exp.add_argument("--top", type=int, default=3, help="Top N clips to export (default: 3)")

    # metadata command
    p_meta = subparsers.add_parser("metadata", help="Generate viral copywriting packages for recording")
    p_meta.add_argument("--input", required=True, help="Input video recording path or filename")

    # validate command
    p_val = subparsers.add_parser("validate", help="Validate broadcast compliance of exported videos")
    p_val.add_argument("--input", required=True, help="Export video or directory path")

    # pipeline command (Autonomous Director)
    p_pipe = subparsers.add_parser("pipeline", help="Complete end-to-end autonomous production")
    p_pipe.add_argument("--input", required=True, help="Input video recording path or filename")
    p_pipe.add_argument("--top", type=int, default=3, help="Top N clips to render (default: 3)")
    p_pipe.add_argument("--fresh", action="store_true", help="Fresh start")
    p_pipe.add_argument("--preset", default="auto", help="Color grading preset")
    p_pipe.add_argument("--no-vfx", action="store_true", help="Disable VFX")
    p_pipe.add_argument("--no-sfx", action="store_true", help="Disable SFX")

    # start command (1-click master UI)
    p_start = subparsers.add_parser("start", help="Auto-ingest + launch dashboard + open browser")
    p_start.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    p_start.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    p_start.add_argument("--fresh", action="store_true", help="Fresh start")

    # server command
    p_serv = subparsers.add_parser("server", help="Launch dashboard server")
    p_serv.add_argument("--port", type=int, default=8000)
    p_serv.add_argument("--host", default="127.0.0.1")

    # list command
    subparsers.add_parser("list", help="List all candidate clips in database")

    # reset command
    subparsers.add_parser("reset", help="Purge database and cache")

    args = parser.parse_args()

    import numpy as np

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "discover":
        cmd_discover(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "metadata":
        cmd_discover(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    elif args.command == "start":
        import uvicorn
        if args.fresh:
            ClipDatabase().purge_all()
        url = f"http://{args.host}:{args.port}"
        open_browser_delayed(url)
        uvicorn.run("web.app:app", host=args.host, port=args.port, reload=False)
    elif args.command == "server":
        import uvicorn
        uvicorn.run("web.app:app", host=args.host, port=args.port, reload=False)
    elif args.command == "list":
        db = ClipDatabase()
        clips = db.get_clips_for_recording()
        print(f"\nTotal Candidates Recorded: {len(clips)}")
        for c in clips:
            fmt = "⚡ MICRO" if c.get("clip_format") == "micro" else "🎬 EXTENDED"
            cat = c.get("category", "Cinematic")
            print(f"- {c['id']} ({fmt}) | Cat: '{cat}' | Score: {c['score']} | Status: {c['status']}")
            print(f"  Hook: \"{c['selected_hook']}\" | Title: {c['title']}")
    elif args.command == "reset":
        db = ClipDatabase()
        db.purge_all()
        print("✓ Database purged.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
