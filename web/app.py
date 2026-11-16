"""
Nyro AI Clip Factory - Web Dashboard Application
FastAPI server providing video streaming, candidate approval/rejection,
rendering controls, and YouTube metadata export for Gamer Nyro.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.database import ClipDatabase
from core.pipeline import ClipFactoryPipeline
from core.renderer import VideoRenderer
from core.aura_engine import NyroAuraEngine, AURA_PROFILES
from core.clip_discovery import CONTENT_CATEGORIES, CandidateClip
from core.packaging import CentralExportPackager
from core.hardware import HardwareInspector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger("ClipFactoryWeb")

app = FastAPI(title="Nyro AI Clip Factory Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = ClipDatabase()
pipeline = ClipFactoryPipeline()
renderer = VideoRenderer()
aura_engine = NyroAuraEngine()
packager = CentralExportPackager()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR = PROJECT_ROOT / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mount static, storage, and output endpoints
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")


class ApprovalRequest(BaseModel):
    selected_hook: Optional[str] = None
    selected_title: Optional[str] = None
    series_badge: Optional[str] = None
    custom_start: Optional[float] = None
    custom_end: Optional[float] = None
    render_now: bool = True


class IngestRequest(BaseModel):
    filename: str


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Nyro AI Clip Factory</h1><p>Static index.html not found.</p>")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/api/recordings")
def list_recordings():
    """Lists all processed recordings."""
    return db.get_all_recordings()


@app.get("/api/available_raw_files")
def list_available_raw_files():
    """Scans storage/raw_recordings for video files ready to ingest."""
    raw_dir = STORAGE_DIR / "raw_recordings"
    raw_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for ext in ["*.mp4", "*.mkv", "*.mov", "*.ts"]:
        for p in raw_dir.glob(ext):
            files.append({
                "filename": p.name,
                "filepath": str(p.resolve()),
                "size_mb": round(p.stat().st_size / (1024 * 1024), 2),
                "modified": p.stat().st_mtime,
            })
    return files


@app.get("/api/clips")
def list_clips(status: Optional[str] = None, recording_id: Optional[int] = None):
    """Lists clips with parsed JSON fields."""
    raw_clips = db.get_clips_for_recording(recording_id)
    results = []
    for c in raw_clips:
        if status and c["status"] != status:
            continue
        c_dict = dict(c)
        try:
            c_dict["score_breakdown"] = json.loads(c_dict.get("score_breakdown") or "{}")
            c_dict["suggested_hooks"] = json.loads(c_dict.get("suggested_hooks") or "[]")
            c_dict["title_choices"] = json.loads(c_dict.get("title_choices") or "[]")
            c_dict["events"] = json.loads(c_dict.get("events_json") or "[]")
        except Exception:
            pass
        results.append(c_dict)
    return results


@app.post("/api/ingest")
def trigger_ingest(req: IngestRequest, bg_tasks: BackgroundTasks):
    """Triggers Phase 1 analysis for a file in storage/raw_recordings/."""
    target_path = STORAGE_DIR / "raw_recordings" / req.filename
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"File {req.filename} not found in storage/raw_recordings/")

    try:
        summary = pipeline.process_recording(str(target_path))
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/clips/{clip_id}/approve")
def approve_clip(clip_id: str, req: ApprovalRequest):
    """Marks clip as approved, saves hook selection, renders 9:16 vertical Short, and packages full bundle."""
    clips = db.get_clips_for_recording()
    target = next((c for c in clips if c["id"] == clip_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Clip not found")

    selected_hook = req.selected_hook or target.get("selected_hook") or ""
    selected_title = req.selected_title or target.get("title") or ""
    series_badge = req.series_badge or ""
    start_time = req.custom_start if req.custom_start is not None else target["start_time"]
    end_time = req.custom_end if req.custom_end is not None else target["end_time"]
    clip_dur = round(end_time - start_time, 2)

    # Reconstruct CandidateClip object
    candidate = CandidateClip(
        id=clip_id,
        video_filename=target["filename"],
        start_time=start_time,
        end_time=end_time,
        duration=clip_dur,
        peak_timestamp=target.get("peak_timestamp", start_time + clip_dur / 2),
        trigger_type=target.get("trigger_type", "audio_spike"),
        peak_intensity=target.get("peak_intensity", 0.8),
        events=[],
        clip_format=target.get("clip_format", "micro" if clip_dur <= 12.0 else "full"),
        category=target.get("category", "Cinematic Gameplay"),
        score=target.get("score", 80.0),
        title_suggestion=selected_title,
        suggested_hooks=[selected_hook],
        series_part=series_badge,
    )

    # Generate tailored AURA editing blueprint
    blueprint = aura_engine.generate_blueprint(candidate)
    active_color = blueprint.color_grading.get("preset", "vibrant_tactical")

    render_path = None
    if req.render_now:
        raw_file = STORAGE_DIR / "raw_recordings" / target["filename"]
        out_filename = f"{clip_id}_vertical.mp4"
        try:
            render_path = renderer.render_short_9_16(
                input_video_path=str(raw_file),
                start_time=start_time,
                end_time=end_time,
                output_filename=out_filename,
                hook_text=selected_hook,
                series_badge=series_badge,
                color_preset=active_color,
                enable_vfx=True,
                enable_sfx=True,
                peak_timestamp=candidate.peak_timestamp,
                trigger_type=candidate.trigger_type,
                peak_intensity=candidate.peak_intensity,
                score=candidate.score,
                clip_format=candidate.clip_format,
            )

            # Package into standard output/<recording>/<clip_id>/ bundle
            package_dir = packager.package_clip_export(
                source_recording_filename=target["filename"],
                clip_id=clip_id,
                rendered_video_path=render_path,
                candidate=candidate,
                blueprint=blueprint,
                selected_hook=selected_hook,
                selected_title=selected_title,
            )

            rel_render_path = f"/storage/exports/{out_filename}"
            rec_stem = Path(target["filename"]).stem
            rel_package_video = f"/output/{rec_stem}/{clip_id}/video.mp4"
            rel_thumbnail = f"/output/{rec_stem}/{clip_id}/thumbnail.jpg"

            db.update_clip_status(
                clip_id, "approved",
                selected_hook=selected_hook,
                render_path=rel_render_path,
                start_time=start_time,
                end_time=end_time,
                selected_title=selected_title,
                series_part=series_badge,
            )
            db.update_clip_blueprint(
                clip_id,
                aura_profile=blueprint.aura_profile,
                blueprint_dict=blueprint.to_dict(),
                category=candidate.category,
            )

            return {
                "status": "approved",
                "clip_id": clip_id,
                "render_url": rel_render_path,
                "package_video_url": rel_package_video,
                "thumbnail_url": rel_thumbnail,
                "selected_hook": selected_hook,
                "selected_title": selected_title,
                "series_badge": series_badge,
                "aura_profile": blueprint.aura_profile,
                "category": candidate.category,
                "start_time": start_time,
                "end_time": end_time,
                "duration": clip_dur,
                "output_dir": str(package_dir),
            }
        except Exception as e:
            logger.error(f"Render failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")
    else:
        db.update_clip_status(
            clip_id, "approved",
            selected_hook=selected_hook,
            start_time=start_time,
            end_time=end_time,
            selected_title=selected_title,
            series_part=series_badge,
        )
        return {"status": "approved", "clip_id": clip_id}


@app.get("/api/categories")
def get_categories():
    """Returns the 16 standard gaming content categories."""
    return {"categories": CONTENT_CATEGORIES}


@app.get("/api/aura_profiles")
def get_aura_profiles():
    """Returns the 7 NYRO AURA profiles."""
    return {"profiles": AURA_PROFILES}


@app.get("/api/hardware")
def get_hardware_info():
    """Returns system acceleration and GPU hardware report."""
    return HardwareInspector.inspect().to_dict()


@app.get("/api/clips/{clip_id}/blueprint")
def get_clip_blueprint(clip_id: str):
    """Returns the individual JSON editing blueprint for a clip."""
    clip = db.get_clip_by_id(clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    bp_raw = clip.get("blueprint_json")
    if bp_raw:
        try:
            return json.loads(bp_raw)
        except Exception:
            pass
    # Generate on the fly if not yet in database
    cand = CandidateClip(
        id=clip_id,
        video_filename=clip["filename"],
        start_time=clip["start_time"],
        end_time=clip["end_time"],
        duration=clip["duration"],
        peak_timestamp=clip.get("peak_timestamp", 0.0),
        trigger_type=clip.get("trigger_type", "audio_spike"),
        peak_intensity=clip.get("peak_intensity", 0.8),
        events=[],
        clip_format=clip.get("clip_format", "micro"),
        category=clip.get("category", "Cinematic Gameplay"),
        score=clip.get("score", 80.0),
    )
    bp = aura_engine.generate_blueprint(cand)
    return bp.to_dict()


class BatchExportRequest(BaseModel):
    recording_id: Optional[int] = None
    top_k: Optional[int] = 3
    top_n: Optional[int] = None


@app.post("/api/batch_export")
def batch_export_clips(req: Optional[BatchExportRequest] = None, top_n: int = Query(default=3)):
    """Batch renders and packages the top N clips from database."""
    k = req.top_k if (req and req.top_k) else (req.top_n if req else top_n)
    rec_id = req.recording_id if req else None
    clips = db.get_clips_for_recording(rec_id)
    candidates = sorted(clips, key=lambda x: x.get("score", 0), reverse=True)[:k]
    results = []
    out_dirs = []
    for c in candidates:
        app_req = ApprovalRequest(
            selected_hook=c.get("selected_hook"),
            selected_title=c.get("title"),
            series_badge=c.get("series_part"),
            render_now=True,
        )
        try:
            res = approve_clip(c["id"], app_req)
            results.append(res)
            if "output_dir" in res:
                out_dirs.append(res["output_dir"])
        except Exception as e:
            results.append({"clip_id": c["id"], "error": str(e)})
    return {
        "batch_count": len(results),
        "rendered_count": len(out_dirs),
        "output_directories": out_dirs,
        "exports": results,
    }


@app.post("/api/clips/{clip_id}/reject")
def reject_clip(clip_id: str):
    """Marks candidate clip as rejected."""
    db.update_clip_status(clip_id, "rejected")
    return {"status": "rejected", "clip_id": clip_id}


@app.post("/api/reset")
def reset_database():
    """Purges ALL recordings and clips for a fresh start."""
    db.purge_all()
    # Also clean cache files (audio proxies)
    cache_dir = STORAGE_DIR / "cache"
    for f in cache_dir.glob("*_16000hz.wav"):
        try:
            f.unlink()
        except Exception:
            pass
    return {"status": "reset", "message": "Database and cache purged. Ready for fresh session."}


@app.delete("/api/recordings/{recording_id}")
def delete_recording(recording_id: int):
    """Deletes a specific recording and its clips."""
    db.purge_recording(recording_id)
    return {"status": "deleted", "recording_id": recording_id}


@app.get("/api/latest_recording_id")
def get_latest_recording():
    """Returns the latest recording ID for auto-selection."""
    latest_id = db.get_latest_recording_id()
    return {"latest_recording_id": latest_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=False)
