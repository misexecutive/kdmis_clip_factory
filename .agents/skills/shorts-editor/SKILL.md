---
name: shorts-editor
description: >-
  Renders upload-ready 9:16 vertical 1080x1920 YouTube Shorts using hardware-accelerated
  FFmpeg NVENC with smart background blur and original gameplay audio preservation.
---

# Shorts Editor Skill: Hardware-Accelerated 9:16 Vertical Video Renderer

This skill executes high-speed vertical rendering utilizing hardware acceleration (NVIDIA RTX NVENC `h264_nvenc`, Windows MediaFoundation `h264_mf`, or `libx264` fallback) with broadcast-level YouTube Shorts visual polish.

## Visual Formatting Standard

- **Dimensions**: 1080 x 1920 pixels (9:16 vertical aspect ratio).
- **Framerate**: 60 fps (matching high-refresh OBS gameplay recordings).
- **Background**: Centered gameplay cropped and blurred (`boxblur=luma_radius=22:luma_power=3`), dimmed by 40% (`eq=brightness=-0.12:saturation=0.9`) to provide high visual contrast.
- **Main Gameplay**: Centered 960px tall gameplay (50% screen height) preserving 16:9 field of view, surrounded by a 3px contrast border (`drawbox=color=white@0.2:t=3`).
- **Hook Pill Box**: Positioned in the upper safe zone (Y = 310). Text rendered with Arial Black (`fontfile=C\\:/Windows/Fonts/arialbd.ttf`), yellow/white coloring, backed by a semi-transparent black contrast box (`box=1:boxcolor=black@0.75:boxborderw=14`). Special characters and apostrophes safely loaded via `textfile`.
- **Series / Episodic Badge**: High-curiosity episodic badge (e.g., `⚡ PART 1`) positioned above the hook box (Y = 220) with a neon border to encourage repeat viewer returns.
- **Audio Micro-Fades**: 0.15s exponential audio fade-in (`afade=t=in:ss=0:d=0.15:curve=qsin`) and 0.25s audio fade-out (`afade=t=out:st=<out>:d=0.25:curve=hsin`) preventing audio popping at clip boundaries while preserving original game sound.

## FFmpeg Command Architecture

```powershell
ffmpeg -y -ss <start_time> -to <end_time> -i <input_video> \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=22:3,eq=brightness=-0.12:saturation=0.9[bg]; \
                   [0:v]scale=1080:960:force_original_aspect_ratio=decrease,drawbox=color=white@0.2:t=3[fg]; \
                   [bg][fg]overlay=0:(1920-960)/2[vcomp]; \
                   [vcomp]drawtext=textfile='storage/cache/hook_<id>.txt':fontfile=C\\:/Windows/Fonts/arialbd.ttf:fontsize=46:fontcolor=white:box=1:boxcolor=black@0.75:boxborderw=14:x=(1080-text_w)/2:y=310[v_hook]; \
                   [v_hook]drawtext=text='⚡ PART 1':fontfile=C\\:/Windows/Fonts/arialbd.ttf:fontsize=36:fontcolor=#00e5ff:box=1:boxcolor=black@0.8:boxborderw=10:x=(1080-text_w)/2:y=220[v_out]" \
  -map "[v_out]" -map 0:a? \
  -af "afade=t=in:ss=0:d=0.15:curve=qsin,afade=t=out:st=<out_start>:d=0.25:curve=hsin" \
  -c:v h264_mf -b:v 14M \
  -c:a aac -b:a 256k \
  storage/exports/<output_filename>.mp4
```
