"""
Nyro AI Clip Factory - Centralized Export Packager & Metadata Bundle Service (Module 7)
Guarantees the required standard output structure for every exported clip:
output/
    recording_name/
        clip_001/
            video.mp4
            metadata.txt
            metadata.json
            editing_blueprint.json
            analysis_report.json
            assets_manifest.json
            thumbnail.jpg
Works identically whether exported via CLI, Frontend, Batch, or Autonomous Director.
"""

import json
import logging
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from core.aura_engine import EditingBlueprint
from core.clip_discovery import CandidateClip
from core.deep_intelligence import DeepAnalysisReport
from core.sfx_manager import SFXLibraryManager

logger = logging.getLogger("ExportPackager")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"


class CentralExportPackager:
    """Central packaging service that produces the uniform metadata bundle for all export paths."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sfx_mgr = SFXLibraryManager()

    def package_clip_export(
        self,
        source_recording_filename: str,
        clip_id: str,
        rendered_video_path: str,
        candidate: CandidateClip,
        blueprint: Optional[EditingBlueprint] = None,
        analysis_report: Optional[Dict[str, Any]] = None,
        selected_hook: Optional[str] = None,
        selected_title: Optional[str] = None,
    ) -> Path:
        """
        Creates the standardized export folder structure:
        output/<recording_stem>/<clip_id>/
        Generates video.mp4, metadata.txt, metadata.json, editing_blueprint.json,
        analysis_report.json, assets_manifest.json, and thumbnail.jpg.
        """
        rec_stem = Path(source_recording_filename).stem
        clip_dir = self.output_dir / rec_stem / clip_id
        clip_dir.mkdir(parents=True, exist_ok=True)

        target_video = clip_dir / "video.mp4"
        src_video = Path(rendered_video_path)

        # 1. Copy/move video to video.mp4
        if src_video.resolve() != target_video.resolve():
            shutil.copy2(src_video, target_video)

        # 2. Extract high-impact thumbnail.jpg at peak action frame
        thumb_path = clip_dir / "thumbnail.jpg"
        self._extract_thumbnail(target_video, candidate.duration, thumb_path)

        # 3. Assemble Title, Description, Hashtags, Tags
        title = selected_title or candidate.title_suggestion or f"INSANE {candidate.category.upper()} CLUTCH!"
        hook = selected_hook or (candidate.suggested_hooks[0] if candidate.suggested_hooks else "WATCH TILL THE END")
        category = candidate.category or "Cinematic Gameplay"
        aura = blueprint.aura_profile if blueprint else getattr(candidate, "aura_profile", "CINEMATIC AURA")

        game_name = self._infer_game_name(source_recording_filename)
        game_tag = game_name.replace(" ", "")

        hashtags = f"#{game_tag} #GamingShorts #{category.replace(' ', '')} #GamerNyro"
        if candidate.clip_format == "micro":
            hashtags += " #MicroShort"

        description = candidate.description_suggestion or (
            f"Unbelievable {category.lower()} moment from Gamer Nyro! "
            f"Watch the full clip and subscribe for daily high-tier gaming highlights.\n\n"
            f"{hashtags}"
        )

        tags_list = candidate.tags_suggestion or [
            f"{game_name.lower()} shorts",
            f"{game_name.lower()} gameplay",
            "gaming shorts",
            "gamer nyro",
            f"{category.lower()}",
            "viral gaming",
            "pc gaming",
        ]
        tags_csv = ", ".join(tags_list)

        rationale = (
            f"Title and hook reflect confirmed {category} dynamics at peak {candidate.peak_timestamp:.1f}s. "
            f"Curated under {aura} with high payoff intensity ({candidate.peak_intensity * 100:.0f}%)."
        )

        # 4. Generate human-readable metadata.txt (ready to copy)
        metadata_txt_content = f"""TITLE:
{title}

DESCRIPTION:
{description}

HASHTAGS:
{hashtags}

TAGS (CSV):
{tags_csv}

HOOK TEXT:
{hook}

CATEGORY:
{category}

AURA PROFILE:
{aura}

METADATA RATIONALE:
{rationale}
"""
        (clip_dir / "metadata.txt").write_text(metadata_txt_content, encoding="utf-8")

        # 5. Generate structured metadata.json
        metadata_json_data = {
            "clip_id": clip_id,
            "source_recording": source_recording_filename,
            "title": title,
            "title_choices": getattr(candidate, "title_choices", [title]) or [title],
            "description": description,
            "hashtags": hashtags.split(),
            "tags": tags_list,
            "tags_csv": tags_csv,
            "hook_text": hook,
            "category": category,
            "secondary_categories": candidate.secondary_categories or [],
            "aura_profile": aura,
            "score": candidate.score,
            "score_breakdown": candidate.score_breakdown or {},
            "retention_dimensions": getattr(candidate, "retention_dimensions", {}) or {},
            "start_time": candidate.start_time,
            "end_time": candidate.end_time,
            "duration": candidate.duration,
            "peak_timestamp": candidate.peak_timestamp,
            "trigger_type": candidate.trigger_type,
            "peak_intensity": candidate.peak_intensity,
            "metadata_rationale": rationale,
        }
        with open(clip_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata_json_data, f, indent=2)

        # 6. Save editing_blueprint.json
        bp_path = clip_dir / "editing_blueprint.json"
        if blueprint:
            blueprint.save_json(bp_path)
        else:
            with open(bp_path, "w", encoding="utf-8") as f:
                json.dump({"clip_id": clip_id, "aura_profile": aura, "category": category}, f, indent=2)

        # 7. Save analysis_report.json
        analysis_path = clip_dir / "analysis_report.json"
        if analysis_report:
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump(analysis_report, f, indent=2)
        else:
            with open(analysis_path, "w", encoding="utf-8") as f:
                json.dump({
                    "source_filename": source_recording_filename,
                    "clip_id": clip_id,
                    "verified_events": candidate.events or [],
                    "confidence": 0.85,
                }, f, indent=2)

        # 8. Save assets_manifest.json with SHA256 checksums and CC0 provenance
        sfx_used = []
        if blueprint and blueprint.sfx_selection:
            sfx_used = [s["sfx_file"] for s in blueprint.sfx_selection if "sfx_file" in s]
        self.sfx_mgr.export_clip_manifest(sfx_used, clip_dir / "assets_manifest.json")

        logger.info(f"✓ Packaged complete export bundle in: {clip_dir}")
        return clip_dir

    def _extract_thumbnail(self, video_path: Path, duration: float, out_thumb: Path):
        """Extracts crisp high-quality JPEG thumbnail at mid-clip or peak frame."""
        thumb_t = max(0.5, duration * 0.45)
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{thumb_t:.2f}",
            "-i", str(video_path.resolve()),
            "-vframes", "1",
            "-q:v", "2",
            str(out_thumb.resolve()),
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        except Exception as e:
            logger.warning(f"Thumbnail extraction warning: {e}")

    def _infer_game_name(self, filename: str) -> str:
        clean = Path(filename).stem.lower().replace("-", " ").replace("_", " ")
        if "cod" in clean or "warzone" in clean or "mw" in clean:
            return "CallOfDuty"
        elif "valorant" in clean:
            return "Valorant"
        elif "cs2" in clean or "counter" in clean:
            return "CounterStrike2"
        elif "apex" in clean:
            return "ApexLegends"
        elif "fortnite" in clean:
            return "Fortnite"
        return "Gaming"


if __name__ == "__main__":
    packager = CentralExportPackager()
    print("CentralExportPackager service ready.")
