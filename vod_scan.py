#!/usr/bin/env python3
"""Scan a full Twitch VOD section to find the best moments.

  python3 vod_scan.py <vod_id> <start_s> <end_s> <out_dir>

Writes <out_dir>/segments.jsonl (transcript, VOD-absolute times) and
<out_dir>/loudness.npy (RMS per second, index = VOD second - start).
Then read the transcript and pick moments; cut them with
  yt-dlp --download-sections "*START-END" https://www.twitch.tv/videos/<id>
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

CHUNK = 600  # seconds of audio transcribed per step (keeps memory low)


def main():
    vod, start, end, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
    out.mkdir(parents=True, exist_ok=True)
    audio = out / "audio.m4a"
    if not audio.exists():
        # Full audio via yt-dlp's native HLS downloader (it goes through the
        # network proxy; ffmpeg/--download-sections does not), then trim locally.
        full = out / "full_audio.m4a"
        if not full.exists():
            subprocess.run(["yt-dlp", "-q", "-f", "Audio_Only", "-N", "8",
                            "-o", str(full), f"https://www.twitch.tv/videos/{vod}"],
                           check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-to", str(end),
                        "-i", str(full), "-c", "copy", str(audio)], check=True)
        full.unlink()
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1",
                          "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    sec = len(a) // 16000
    np.save(out / "loudness.npy",
            np.sqrt((a[:sec * 16000].reshape(sec, 16000) ** 2).mean(axis=1)))
    print(f"audio {sec}s", flush=True)

    from faster_whisper import WhisperModel
    model = WhisperModel(sys.argv[5] if len(sys.argv) > 5 else "small",
                         device="cpu", compute_type="int8", cpu_threads=4)
    seg_file = out / "segments.jsonl"
    done = 0
    if seg_file.exists():
        lines = seg_file.read_text().splitlines()
        done = json.loads(lines[-1])["chunk"] + CHUNK if lines else 0
    with seg_file.open("a") as f:
        for c in range(done, sec, CHUNK):
            segs, _ = model.transcribe(a[c * 16000:(c + CHUNK) * 16000], language="fr",
                                       vad_filter=True, condition_on_previous_text=False)
            for s in segs:
                f.write(json.dumps({"chunk": c, "t": round(start + c + s.start, 1),
                                    "e": round(start + c + s.end, 1), "x": s.text.strip()},
                                   ensure_ascii=False) + "\n")
            f.flush()
            print(f"chunk {c}/{sec}", flush=True)


if __name__ == "__main__":
    main()
