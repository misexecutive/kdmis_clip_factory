"""
Nyro AI Clip Factory - Database & State Store
SQLite persistent store tracking recordings, candidate clips,
approval workflow status, and export paths.
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.detector import CandidateClip
from core.ingest import VideoMetadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "clip_factory.db"


class ClipDatabase:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    filepath TEXT,
                    duration REAL,
                    width INTEGER,
                    height INTEGER,
                    fps REAL,
                    video_codec TEXT,
                    audio_codec TEXT,
                    file_size INTEGER,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clips (
                    id TEXT PRIMARY KEY,
                    recording_id INTEGER,
                    filename TEXT,
                    start_time REAL,
                    end_time REAL,
                    duration REAL,
                    peak_timestamp REAL,
                    trigger_type TEXT,
                    peak_intensity REAL,
                    score REAL,
                    score_breakdown TEXT,
                    reasoning TEXT,
                    suggested_hooks TEXT,
                    selected_hook TEXT,
                    title TEXT,
                    description TEXT,
                    tags_csv TEXT,
                    events_json TEXT,
                    clip_format TEXT DEFAULT 'full',
                    status TEXT DEFAULT 'candidate', -- 'candidate', 'approved', 'rejected', 'rendered'
                    render_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recording_id) REFERENCES recordings (id)
                )
            """)
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN clip_format TEXT DEFAULT 'full'")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN title_choices TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN series_part TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN category TEXT DEFAULT 'Cinematic Gameplay'")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN secondary_categories TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN aura_profile TEXT DEFAULT 'CINEMATIC AURA'")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN blueprint_json TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN analysis_json TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN validation_json TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE clips ADD COLUMN metadata_json TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE recordings ADD COLUMN analysis_report_json TEXT")
            except Exception:
                pass
            conn.commit()
            logger.info("Database schema initialized with Phase 1-8 columns.")

    def save_recording(self, meta: VideoMetadata) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recordings (
                    filename, filepath, duration, width, height, fps,
                    video_codec, audio_codec, file_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    filepath=excluded.filepath,
                    duration=excluded.duration,
                    width=excluded.width,
                    height=excluded.height,
                    fps=excluded.fps,
                    processed_at=CURRENT_TIMESTAMP
            """, (
                meta.filename, meta.filepath, meta.duration_seconds,
                meta.width, meta.height, meta.fps, meta.video_codec,
                meta.audio_codec, meta.file_size_bytes
            ))
            conn.commit()
            cursor.execute("SELECT id FROM recordings WHERE filename = ?", (meta.filename,))
            row = cursor.fetchone()
            return row["id"]

    def save_candidates(self, recording_id: int, candidates: List[CandidateClip]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for c in candidates:
                cursor.execute("""
                    INSERT INTO clips (
                        id, recording_id, filename, start_time, end_time, duration,
                        peak_timestamp, trigger_type, peak_intensity, score,
                        score_breakdown, reasoning, suggested_hooks, selected_hook,
                        title, title_choices, description, tags_csv, events_json,
                        clip_format, series_part, status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate', CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        start_time=excluded.start_time,
                        end_time=excluded.end_time,
                        duration=excluded.duration,
                        peak_timestamp=excluded.peak_timestamp,
                        score=excluded.score,
                        score_breakdown=excluded.score_breakdown,
                        reasoning=excluded.reasoning,
                        suggested_hooks=excluded.suggested_hooks,
                        title=excluded.title,
                        title_choices=excluded.title_choices,
                        description=excluded.description,
                        tags_csv=excluded.tags_csv,
                        events_json=excluded.events_json,
                        clip_format=excluded.clip_format,
                        series_part=excluded.series_part,
                        updated_at=CURRENT_TIMESTAMP
                """, (
                    c.id, recording_id, c.video_filename, c.start_time, c.end_time, c.duration,
                    c.peak_timestamp, c.trigger_type, c.peak_intensity, c.score,
                    json.dumps(c.score_breakdown or {}), c.reasoning,
                    json.dumps(c.suggested_hooks or []),
                    c.suggested_hooks[0] if c.suggested_hooks else "",
                    c.title_suggestion,
                    json.dumps(getattr(c, "title_choices", []) or []),
                    c.description_suggestion,
                    ", ".join(c.tags_suggestion or []),
                    json.dumps(c.events or []),
                    getattr(c, "clip_format", "full"),
                    getattr(c, "series_part", ""),
                ))
            conn.commit()
            logger.info(f"Saved {len(candidates)} candidates for recording ID {recording_id}.")

    def update_clip_status(
        self,
        clip_id: str,
        status: str,
        selected_hook: Optional[str] = None,
        render_path: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        selected_title: Optional[str] = None,
        series_part: Optional[str] = None,
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [status]
            if selected_hook is not None:
                updates.append("selected_hook = ?")
                params.append(selected_hook)
            if selected_title is not None:
                updates.append("title = ?")
                params.append(selected_title)
            if series_part is not None:
                updates.append("series_part = ?")
                params.append(series_part)
            if render_path is not None:
                updates.append("render_path = ?")
                params.append(render_path)
            if start_time is not None:
                updates.append("start_time = ?")
                params.append(start_time)
            if end_time is not None:
                updates.append("end_time = ?")
                params.append(end_time)
            if start_time is not None and end_time is not None:
                updates.append("duration = ?")
                params.append(round(end_time - start_time, 2))
            params.append(clip_id)
            query = f"UPDATE clips SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

    def get_clips_for_recording(self, recording_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if recording_id:
                cursor.execute("SELECT * FROM clips WHERE recording_id = ? ORDER BY score DESC", (recording_id,))
            else:
                cursor.execute("SELECT * FROM clips ORDER BY score DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_clip_by_id(self, clip_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recording_by_id(self, recording_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recordings WHERE id = ?", (recording_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_recording_analysis_report(self, recording_id: int, report_dict: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE recordings SET analysis_report_json = ? WHERE id = ?",
                (json.dumps(report_dict), recording_id)
            )
            conn.commit()

    def update_clip_blueprint(
        self,
        clip_id: str,
        aura_profile: str,
        blueprint_dict: Dict[str, Any],
        category: Optional[str] = None,
        secondary_categories: Optional[List[str]] = None,
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["aura_profile = ?", "blueprint_json = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [aura_profile, json.dumps(blueprint_dict)]
            if category:
                updates.append("category = ?")
                params.append(category)
            if secondary_categories is not None:
                updates.append("secondary_categories = ?")
                params.append(json.dumps(secondary_categories))
            params.append(clip_id)
            cursor.execute(f"UPDATE clips SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()

    def update_clip_validation(self, clip_id: str, validation_dict: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clips SET validation_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(validation_dict), clip_id)
            )
            conn.commit()

    def get_all_recordings(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recordings ORDER BY processed_at DESC")
            return [dict(r) for r in cursor.fetchall()]


    def purge_all(self):
        """Wipes ALL recordings and clips. Returns to a fresh empty state."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clips")
            cursor.execute("DELETE FROM recordings")
            try:
                cursor.execute("DELETE FROM sqlite_sequence")  # Reset auto-increment
            except Exception:
                pass  # Table may not exist if no auto-increment was used
            conn.commit()
        logger.info("Database purged: all recordings and clips deleted.")

    def purge_recording(self, recording_id: int):
        """Deletes a specific recording and all its candidate clips."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clips WHERE recording_id = ?", (recording_id,))
            cursor.execute("DELETE FROM recordings WHERE id = ?", (recording_id,))
            conn.commit()
        logger.info(f"Purged recording ID {recording_id} and all its clips.")

    def get_latest_recording_id(self) -> int | None:
        """Returns the ID of the most recently processed recording, or None."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM recordings ORDER BY processed_at DESC LIMIT 1")
            row = cursor.fetchone()
            return row["id"] if row else None


if __name__ == "__main__":
    db = ClipDatabase()
    print("ClipDatabase ready.")
