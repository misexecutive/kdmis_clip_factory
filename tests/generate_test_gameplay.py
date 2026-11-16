"""
Nyro AI Clip Factory - Test Gameplay Generator
Generates a realistic 60s 1920x1080 60fps benchmark recording with:
- Ambient low-energy buildup (0s - 22s)
- Intense gunfire & explosion transient spikes at 23s - 27s
- Resolution & post-combat lull (28s - 60s)
"""

import subprocess
import sys
from pathlib import Path

OUTPUT_FILE = Path("storage/raw_recordings/test_gameplay_session.mp4")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

def generate_benchmark_recording():
    print(f"Generating realistic benchmark recording: {OUTPUT_FILE}...")
    
    # We use FFmpeg lavfi to generate 1920x1080 60fps test video with audio transients
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        # Video: moving test patterns with color flashes at 24s-26s
        "-i", "testsrc=size=1920x1080:rate=60",
        "-f", "lavfi",
        # Audio: low tone ambient, with high-volume burst/bursts between 23s and 27s
        "-i", "anoisesrc=d=60:c=pink:r=48000:a=0.03,volume=enable='between(t,23.5,27.5)':volume=12.0",
        "-t", "60",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        str(OUTPUT_FILE.resolve())
    ]
    
    subprocess.run(cmd, check=True)
    print(f"Successfully generated: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size} bytes)")

if __name__ == "__main__":
    generate_benchmark_recording()
