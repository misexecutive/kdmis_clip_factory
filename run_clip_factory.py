"""
Nyro AI Clip Factory - Master CLI Entrypoint
Provides easy-to-use commands for Gamer Nyro:
  - python run_clip_factory.py start [--port 8000]   (Auto-ingest + launch dashboard + open browser)
  - python run_clip_factory.py ingest <video_file>   (Ingest specific file)
  - python run_clip_factory.py server [--port 8000]  (Launch dashboard server)
  - python run_clip_factory.py list                  (List all candidate clips)
  - python run_clip_factory.py render <clip_id>      (Render 9:16 vertical Short)
"""

import argparse
import sys
import threading
import time
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.pipeline import ClipFactoryPipeline
from core.database import ClipDatabase
from core.renderer import VideoRenderer
from core.director import AutonomousDirector


def resolve_video_path(video_input: str) -> Path:
    """
    Intelligently locates the target video whether given as:
    - Relative to current terminal working directory
    - Relative to project root
    - Just the bare filename inside storage/raw_recordings/
    - Absolute file path
    """
    p = Path(video_input)
    if p.is_file():
        return p.resolve()

    root_p = PROJECT_ROOT / p
    if root_p.is_file():
        return root_p.resolve()

    storage_p = PROJECT_ROOT / "storage" / "raw_recordings" / p.name
    if storage_p.is_file():
        return storage_p.resolve()

    raise FileNotFoundError(
        f"Video file not found: '{video_input}'.\n"
        f"Checked:\n"
        f"  1. {p.resolve()}\n"
        f"  2. {root_p.resolve()}\n"
        f"  3. {storage_p.resolve()}"
    )


def auto_ingest_all_raw_files():
    """Scans storage/raw_recordings/ and automatically processes any new videos."""
    raw_dir = PROJECT_ROOT / "storage" / "raw_recordings"
    raw_dir.mkdir(parents=True, exist_ok=True)
    db = ClipDatabase()
    existing_recordings = {r["filename"] for r in db.get_all_recordings()}

    video_exts = ("*.mp4", "*.mkv", "*.mov", "*.ts")
    raw_files = []
    for ext in video_exts:
        raw_files.extend(list(raw_dir.glob(ext)))

    unprocessed = [f for f in raw_files if f.name not in existing_recordings]

    if not unprocessed:
        print(f"\n[Clip Factory] All {len(raw_files)} recordings in storage/raw_recordings/ are already processed.")
        return

    print(f"\n[Clip Factory] Found {len(unprocessed)} new recording(s) to process:")
    pipeline = ClipFactoryPipeline()
    for vid in unprocessed:
        print(f" -> Ingesting: {vid.name} ({vid.stat().st_size / (1024*1024):.1f} MB)...")
        try:
            summary = pipeline.process_recording(str(vid))
            print(f"    ✓ Detected {summary['candidate_count']} candidate clips.")
        except Exception as e:
            print(f"    ✕ Ingestion failed for {vid.name}: {e}")


def open_browser_delayed(url: str, delay: float = 1.2):
    def _open():
        time.sleep(delay)
        print(f"\n[Clip Factory] Launching dashboard in your default browser: {url}\n")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="Nyro AI Clip Factory - AI Video Automation for Gamer Nyro")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Start subcommand (1-click master workflow)
    start_p = subparsers.add_parser("start", help="Auto-ingest raw recordings and open interactive dashboard")
    start_p.add_argument("--port", type=int, default=8000, help="Port to bind server (default 8000)")
    start_p.add_argument("--host", default="127.0.0.1", help="Host address (default 127.0.0.1)")
    start_p.add_argument("--fresh", action="store_true", help="Wipe database and cache before starting (clean slate)")

    # Ingest subcommand
    ingest_p = subparsers.add_parser("ingest", help="Ingest and detect candidate moments from an OBS recording")
    ingest_p.add_argument("video_path", help="Path or filename of MKV/MP4 gameplay recording")

    # Server subcommand
    server_p = subparsers.add_parser("server", help="Launch the local review dashboard")
    server_p.add_argument("--port", type=int, default=8000, help="Port to bind server (default 8000)")
    server_p.add_argument("--host", default="127.0.0.1", help="Host address (default 127.0.0.1)")

    # List subcommand
    list_p = subparsers.add_parser("list", help="List all candidate clips and scores in database")

    # Render subcommand
    render_p = subparsers.add_parser("render", help="Render approved 9:16 vertical Short")
    render_p.add_argument("clip_id", help="Candidate Clip ID (e.g. clip_session_01)")
    render_p.add_argument("--hook", help="Custom hook text overlay")
    render_p.add_argument("--series", help="Episodic series badge overlay (e.g. 'PART 1')")

    # Auto subcommand (Zero-Click Autonomous Production)
    auto_p = subparsers.add_parser("auto", help="Zero-touch autonomous editing: inspects, detects, grades, adds SFX, and renders top Reels")
    auto_p.add_argument("video_path", nargs="?", default=None, help="Path or filename of raw recording (default: latest in storage/raw_recordings)")
    auto_p.add_argument("--top", type=int, default=3, help="Number of top Reels to render (default: 3)")
    auto_p.add_argument("--fresh", action="store_true", help="Wipe previous database and cache before starting")
    auto_p.add_argument("--preset", default="auto", choices=["auto", "vibrant_tactical", "cyberpunk_neon", "clean_crisp", "cinematic_warm", "dark_moody"], help="Color grading preset (default: auto)")
    auto_p.add_argument("--no-vfx", action="store_true", help="Disable visual effects & color grading")
    auto_p.add_argument("--no-sfx", action="store_true", help="Disable sound effects & loudnorm mastering")

    # Reset subcommand
    reset_p = subparsers.add_parser("reset", help="Purge all data and start fresh")

    args = parser.parse_args()

    if args.command == "start":
        import uvicorn
        print("=" * 65)
        print("   NYRO AI CLIP FACTORY - GAMER NYRO AUTONOMOUS STUDIO")
        print("=" * 65)
        # Step 0: Fresh start if requested
        if args.fresh:
            print("[Clip Factory] --fresh flag detected. Purging database and cache for clean slate...")
            db_instance = ClipDatabase()
            db_instance.purge_all()
            cache_dir = PROJECT_ROOT / "storage" / "cache"
            for f in cache_dir.glob("*_16000hz.wav"):
                try:
                    f.unlink()
                except Exception:
                    pass
            print("[Clip Factory] ✓ Fresh start ready.")

        # Step 1: Auto-scan and process new recordings
        auto_ingest_all_raw_files()

        # Step 2: Open browser
        url = f"http://{args.host}:{args.port}"
        open_browser_delayed(url)

        # Step 3: Run FastAPI server
        uvicorn.run("web.app:app", host=args.host, port=args.port, reload=False)

    elif args.command == "ingest":
        resolved_path = resolve_video_path(args.video_path)
        print(f"\n[Clip Factory] Ingesting recording: {resolved_path}")
        pipeline = ClipFactoryPipeline()
        summary = pipeline.process_recording(str(resolved_path))
        print("\n=== INGESTION & CANDIDATE DETECTION COMPLETE ===")
        print(f"File: {summary['filename']} | Duration: {summary['duration']:.1f}s | Resolution: {summary['resolution']}")
        print(f"Detected Candidates: {summary['candidate_count']}")
        for idx, c in enumerate(summary["top_candidates"], 1):
            format_tag = "⚡ [MICRO 8-12s]" if c.get("clip_format") == "micro" or c.get("duration", 0) <= 14.0 else "🎬 [HIGHLIGHT]"
            print(f"\n[{idx}] {c['id']} {format_tag} - Score: {c['score']}/100")
            print(f"    Window: {c['start_time']}s -> {c['end_time']}s ({c['duration']}s)")
            print(f"    Peak: {c['peak_timestamp']}s ({c['trigger_type']})")
            print(f"    Reasoning: {c['reasoning']}")
            print(f"    Hook: \"{c['suggested_hooks'][0] if c['suggested_hooks'] else ''}\"")
            print(f"    Title: {c['title_suggestion']}")

    elif args.command == "server":
        import uvicorn
        print(f"\n=== Starting Nyro AI Clip Factory Dashboard on http://{args.host}:{args.port} ===")
        print("Open the link in your browser to preview, score, select hooks, and approve clips.")
        uvicorn.run("web.app:app", host=args.host, port=args.port, reload=False)

    elif args.command == "list":
        db = ClipDatabase()
        clips = db.get_clips_for_recording()
        print(f"\nTotal Candidates Recorded: {len(clips)}")
        for c in clips:
            fmt = "⚡ MICRO" if c.get("clip_format") == "micro" or c.get("duration", 0) <= 14.0 else "🎬 FULL"
            print(f"- {c['id']} ({fmt}) | Score: {c['score']} | Status: {c['status']} | Window: {c['start_time']}s-{c['end_time']}s ({c['duration']}s)")
            print(f"  Hook: \"{c['selected_hook']}\" | Title: {c['title']}")

    elif args.command == "render":
        db = ClipDatabase()
        clips = db.get_clips_for_recording()
        target = next((c for c in clips if c["id"] == args.clip_id), None)
        if not target:
            print(f"Error: Clip {args.clip_id} not found in database.")
            sys.exit(1)

        renderer = VideoRenderer()
        hook = args.hook or target.get("selected_hook") or ""
        series_badge = args.series or target.get("series_part") or ""
        in_video = PROJECT_ROOT / "storage" / "raw_recordings" / target["filename"]
        out_file = f"{target['id']}_vertical.mp4"

        print(f"Rendering 9:16 vertical Short for {target['id']} (960px tall gameplay + hook: '{hook}' + series: '{series_badge}')...")
        render_path = renderer.render_short_9_16(
            input_video_path=str(in_video),
            start_time=target["start_time"],
            end_time=target["end_time"],
            output_filename=out_file,
            hook_text=hook,
            series_badge=series_badge,
            gameplay_height=960,
        )
        db.update_clip_status(target["id"], "approved", selected_hook=hook, series_part=series_badge, render_path=render_path)
        print(f"Render complete: {render_path}")

    elif args.command == "auto":
        target_video = args.video_path
        if not target_video:
            # Find the newest raw recording in storage/raw_recordings/
            raw_dir = PROJECT_ROOT / "storage" / "raw_recordings"
            video_files = []
            for ext in ("*.mp4", "*.mkv", "*.mov", "*.ts"):
                video_files.extend(list(raw_dir.glob(ext)))
            if not video_files:
                print("\n[Error] No video files found in storage/raw_recordings/!")
                print("Please drop an OBS recording into storage/raw_recordings/ or specify a path.")
                sys.exit(1)
            video_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            target_video = str(video_files[0])
            print(f"[Clip Factory] Auto-selected latest recording: {Path(target_video).name}")

        resolved_path = resolve_video_path(target_video)
        director = AutonomousDirector(fresh_start=args.fresh)
        director.run_autonomous_session(
            video_path=str(resolved_path),
            top_n=args.top,
            color_preset=args.preset,
            enable_vfx=not args.no_vfx,
            enable_sfx=not args.no_sfx,
        )

    elif args.command == "reset":
        db = ClipDatabase()
        db.purge_all()
        cache_dir = PROJECT_ROOT / "storage" / "cache"
        for f in cache_dir.glob("*_16000hz.wav"):
            try:
                f.unlink()
            except Exception:
                pass
        print("[Clip Factory] ✓ Database and cache purged. Ready for fresh session.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
