import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("[Diag] Step 0: Imports...", flush=True)
import soundfile as sf
import numpy as np
import librosa
print("[Diag] Imports done", flush=True)

cache_dir = PROJECT_ROOT / "storage" / "cache"
wav_files = list(cache_dir.glob("test_gameplay_session_*_16000hz.wav"))
if not wav_files:
    print("[Diag] No wav found!", flush=True)
    sys.exit(1)

wav_path = str(wav_files[0])
print(f"[Diag] Target wav: {wav_path}", flush=True)

t0 = time.time()
print("[Diag] Step 1: Loading wav via soundfile...", flush=True)
y, sr = sf.read(wav_path)
print(f"[Diag] sf.read done in {time.time() - t0:.3f}s, samples: {len(y)}, sr: {sr}", flush=True)

t0 = time.time()
print("[Diag] Step 2: Testing librosa.load...", flush=True)
y_lib, sr_lib = librosa.load(wav_path, sr=16000, mono=True)
print(f"[Diag] librosa.load done in {time.time() - t0:.3f}s", flush=True)

frame_len = 2048
hop_len = 512

t0 = time.time()
print("[Diag] Step 3: Computing RMS...", flush=True)
rms = librosa.feature.rms(y=y_lib, frame_length=frame_len, hop_length=hop_len)[0]
print(f"[Diag] RMS done in {time.time() - t0:.3f}s, frames: {len(rms)}", flush=True)

t0 = time.time()
print("[Diag] Step 4: Computing Spectral Centroid...", flush=True)
sc = librosa.feature.spectral_centroid(y=y_lib, sr=sr_lib, n_fft=frame_len, hop_length=hop_len)[0]
print(f"[Diag] Spectral Centroid done in {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
print("[Diag] Step 5: Computing Onset Strength...", flush=True)
onset_env = librosa.onset.onset_strength(y=y_lib, sr=sr_lib, hop_length=hop_len)
print(f"[Diag] Onset strength done in {time.time() - t0:.3f}s", flush=True)

t0 = time.time()
print("[Diag] Step 6: Computing Onset Detect...", flush=True)
onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr_lib, hop_length=hop_len, backtrack=False)
print(f"[Diag] Onset detect done in {time.time() - t0:.3f}s, count: {len(onset_frames)}", flush=True)

t0 = time.time()
print("[Diag] Step 7: Computing STFT...", flush=True)
stft = np.abs(librosa.stft(y_lib, n_fft=frame_len, hop_length=hop_len))
print(f"[Diag] STFT done in {time.time() - t0:.3f}s, shape: {stft.shape}", flush=True)

t0 = time.time()
print("[Diag] Step 8: Simulating event loop from core/deep_intelligence.py...", flush=True)
times = librosa.frames_to_time(np.arange(len(rms)), sr=sr_lib, hop_length=hop_len)
onset_times = librosa.frames_to_time(onset_frames, sr=sr_lib, hop_length=hop_len)
print(f"[Diag] onset_times count: {len(onset_times)}, times count: {len(times)}", flush=True)

mean_rms = float(np.mean(rms))
std_rms = float(np.std(rms))
freqs = librosa.fft_frequencies(sr=sr_lib, n_fft=frame_len)
sub_bass_mask = (freqs >= 20) & (freqs <= 140)
sub_bass_energy = np.mean(stft[sub_bass_mask, :], axis=0) if np.any(sub_bass_mask) else np.zeros(len(times))
mean_bass = float(np.mean(sub_bass_energy))
std_bass = float(np.std(sub_bass_energy))

events = []
loop_t0 = time.time()
for idx_ot, ot in enumerate(onset_times):
    # find closest frame index
    idx = int(np.argmin(np.abs(times - ot)))
    cur_rms = float(rms[idx])
    cur_centroid = float(sc[idx])
    cur_bass = float(sub_bass_energy[idx])
print(f"[Diag] Event loop done in {time.time() - loop_t0:.3f}s for {len(onset_times)} onsets", flush=True)

print("[Diag] ALL DIAGNOSTIC STEPS FINISHED SUCCESSFULLY!", flush=True)
