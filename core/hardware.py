"""
Nyro AI Clip Factory - Hardware & Acceleration Inspector
Detects system CPU, RAM, NVIDIA GPU, VRAM, and FFmpeg NVENC/MediaFoundation encoders.
"""

import logging
import os
import shutil
import subprocess
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class HardwareReport:
    cpu_count: int
    system_os: str
    ffmpeg_available: bool
    ffmpeg_version: str
    nvenc_h264_available: bool
    nvenc_hevc_available: bool
    mediafoundation_available: bool
    libx264_available: bool
    recommended_encoder: str
    gpu_name: Optional[str] = None
    gpu_driver: Optional[str] = None
    gpu_vram_mb: Optional[int] = None
    cuda_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HardwareInspector:
    """Probes system hardware acceleration and video encoders."""

    @staticmethod
    def inspect() -> HardwareReport:
        cpu_count = os.cpu_count() or 4
        sys_os = "Windows" if os.name == "nt" else os.uname().sysname

        ffmpeg_path = shutil.which("ffmpeg")
        ffmpeg_available = ffmpeg_path is not None
        ffmpeg_ver = "unknown"
        nvenc_h264 = False
        nvenc_hevc = False
        mf_h264 = False
        libx264 = False

        if ffmpeg_available:
            try:
                res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
                lines = res.stdout.splitlines()
                if lines:
                    ffmpeg_ver = lines[0]
            except Exception:
                pass

            try:
                enc_res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=5)
                enc_out = enc_res.stdout
                nvenc_h264 = "h264_nvenc" in enc_out
                nvenc_hevc = "hevc_nvenc" in enc_out
                mf_h264 = "h264_mf" in enc_out
                libx264 = "libx264" in enc_out
            except Exception:
                pass

        # Check NVIDIA GPU via nvidia-smi
        gpu_name = None
        gpu_driver = None
        gpu_vram = None
        cuda_avail = False

        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                cmd = ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader,nounits"]
                smi_res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if smi_res.returncode == 0 and smi_res.stdout.strip():
                    parts = [p.strip() for p in smi_res.stdout.strip().split(",")]
                    if len(parts) >= 3:
                        gpu_name = parts[0]
                        gpu_driver = parts[1]
                        gpu_vram = int(float(parts[2]))
                        cuda_avail = True
            except Exception:
                pass

        # Recommend encoder based on actual working encoder
        recommended = "libx264"
        if nvenc_h264 and HardwareInspector._test_encoder("h264_nvenc"):
            recommended = "h264_nvenc"
        elif mf_h264 and HardwareInspector._test_encoder("h264_mf"):
            recommended = "h264_mf"
        elif libx264:
            recommended = "libx264"

        report = HardwareReport(
            cpu_count=cpu_count,
            system_os=sys_os,
            ffmpeg_available=ffmpeg_available,
            ffmpeg_version=ffmpeg_ver,
            nvenc_h264_available=nvenc_h264,
            nvenc_hevc_available=nvenc_hevc,
            mediafoundation_available=mf_h264,
            libx264_available=libx264,
            recommended_encoder=recommended,
            gpu_name=gpu_name,
            gpu_driver=gpu_driver,
            gpu_vram_mb=gpu_vram,
            cuda_available=cuda_avail,
        )
        return report

    @staticmethod
    def _test_encoder(encoder_name: str) -> bool:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "nullsrc=s=64x64:d=0.05",
            "-c:v", encoder_name,
            "-f", "null", "-"
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=4)
            return res.returncode == 0
        except Exception:
            return False


if __name__ == "__main__":
    rep = HardwareInspector.inspect()
    import json
    print(json.dumps(rep.to_dict(), indent=2))
