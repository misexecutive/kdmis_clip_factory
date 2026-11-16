"""
Nyro AI Clip Factory - Core Ingestion Engine
Handles video metadata probing and fast proxy audio extraction.
"""

import json
import logging
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    filepath: str
    filename: str
    duration_seconds: float
    width: int
    height: int
    aspect_ratio: str
    fps: float
    video_codec: str
    audio_codec: Optional[str]
    audio_channels: int
    audio_sample_rate: int
    bitrate: int
    file_size_bytes: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_DIR = PROJECT_ROOT / "storage" / "cache"


class IngestionEngine:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def probe(self, video_path: str) -> VideoMetadata:
        """Inspects video file using ffprobe and extracts rich stream metadata."""
        path = Path(video_path)
        if not path.is_file():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate",
            "-of", "json",
            str(path.resolve()),
        ]

        logger.info(f"Probing video stream: {path.name}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)

        video_stream = None
        audio_stream = None

        for stream in probe_data.get("streams", []):
            if stream.get("codec_type") == "video" and not video_stream:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and not audio_stream:
                audio_stream = stream

        if not video_stream:
            raise ValueError(f"No video stream found in {video_path}")

        # Compute FPS
        r_fps = video_stream.get("r_frame_rate", "30/1")
        try:
            num, den = map(int, r_fps.split("/"))
            fps = round(num / den, 3) if den != 0 else 30.0
        except Exception:
            fps = 30.0

        duration = float(probe_data.get("format", {}).get("duration", 0.0))
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        aspect_ratio = f"{width}:{height}" if height > 0 else "unknown"

        meta = VideoMetadata(
            filepath=str(path.resolve()),
            filename=path.name,
            duration_seconds=duration,
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            fps=fps,
            video_codec=video_stream.get("codec_name", "unknown"),
            audio_codec=audio_stream.get("codec_name") if audio_stream else None,
            audio_channels=int(audio_stream.get("channels", 0)) if audio_stream else 0,
            audio_sample_rate=int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
            bitrate=int(probe_data.get("format", {}).get("bit_rate", 0)),
            file_size_bytes=int(probe_data.get("format", {}).get("size", path.stat().st_size)),
        )

        logger.info(
            f"Successfully probed {meta.filename}: {meta.width}x{meta.height} @ {meta.fps}fps, "
            f"Duration: {meta.duration_seconds:.2f}s, Audio: {meta.audio_codec} ({meta.audio_channels}ch)"
        )
        return meta

    def extract_audio_proxy(self, video_path: str, sample_rate: int = 16000) -> str:
        """
        Extracts a fast 16kHz mono 16-bit PCM WAV for audio spike and speech analysis.
        Reuses cached file if source timestamp matches.
        """
        path = Path(video_path)
        cache_filename = f"{path.stem}_{path.stat().st_mtime_ns}_{sample_rate}hz.wav"
        output_wav = self.cache_dir / cache_filename

        if output_wav.exists() and output_wav.stat().st_size > 0:
            logger.info(f"Using cached audio proxy: {output_wav.name}")
            return str(output_wav.resolve())

        logger.info(f"Extracting 16kHz mono audio proxy from {path.name}...")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(path.resolve()),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            str(output_wav.resolve()),
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        logger.info(f"Audio proxy generated: {output_wav.name} ({output_wav.stat().st_size} bytes)")
        return str(output_wav.resolve())


if __name__ == "__main__":
    import sys
    engine = IngestionEngine()
    if len(sys.argv) > 1:
        m = engine.probe(sys.argv[1])
        print(json.dumps(m.to_dict(), indent=2))
        wav = engine.extract_audio_proxy(sys.argv[1])
        print(f"Proxy audio: {wav}")
    else:
        print("Usage: python ingest.py <video_file>")
