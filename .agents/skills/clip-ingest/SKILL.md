---
name: clip-ingest
description: >-
  Inspects OBS gameplay recordings (MKV/MP4), extracts audio/video stream parameters,
  and generates 16kHz mono audio proxies for rapid multi-modal analysis.
---

# Clip Ingest Skill: Video Inspection & Audio Extraction

This skill standardizes the ingestion and verification of incoming gameplay recordings before any editing or candidate detection takes place.

## Workflow

1. **Stream Inspection**:
   Use `ffprobe` to determine video dimensions, aspect ratio, frame rate, container format, and audio channel configuration:
   ```powershell
   ffprobe -v error -show_entries format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate -of json <input_file>
   ```

2. **Audio Proxy Extraction**:
   Demux audio to a standardized 16kHz 16-bit mono PCM WAV file for rapid digital signal processing:
   ```powershell
   ffmpeg -y -i <input_video> -vn -acodec pcm_s16le -ar 16000 -ac 1 storage/cache/<filename>_16000hz.wav
   ```

3. **Validation Criteria**:
   - Duration must be >= 30 seconds.
   - Video stream must contain valid width and height.
   - Audio stream must contain audible sound channels (prevent processing muted gameplay).

4. **Python API Usage**:
   ```python
   from core.ingest import IngestionEngine
   engine = IngestionEngine()
   meta = engine.probe("storage/raw_recordings/session1.mp4")
   wav_path = engine.extract_audio_proxy("storage/raw_recordings/session1.mp4")
   ```
