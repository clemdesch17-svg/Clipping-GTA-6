#!/usr/bin/env python3
"""Cut any passage of a public Twitch VOD, and locate a clip inside its VOD.

  python3 vod_cut.py cut <vod_id> <start_s> <end_s> <out.mp4>
  python3 vod_cut.py locate <clip.mp4> <vod_audio.m4a> <audio_offset_s> <guess_s>

`cut` fetches only the HLS segments it needs with Python (goes through the
network proxy, unlike ffmpeg), then trims them precisely.
`locate` finds where a clip sits in the VOD by matching audio loudness
envelopes around a guess (e.g. the clip creation time), returns VOD seconds.
"""
import os
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np

CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA if os.path.exists(CA) else None)


def fetch(url):
    with urllib.request.urlopen(url, context=CTX, timeout=60) as r:
        return r.read()


def playlist(vod_id, fmt="1080p50/1080p60/1080p/best"):
    url = subprocess.run(["yt-dlp", "-g", "-f", fmt, f"https://www.twitch.tv/videos/{vod_id}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    base = url.rsplit("/", 1)[0] + "/"
    segs, t, dur = [], 0.0, None
    for line in fetch(url).decode().splitlines():
        if line.startswith("#EXTINF:"):
            dur = float(line[8:].split(",")[0])
        elif line and not line.startswith("#") and dur is not None:
            segs.append((t, dur, line if line.startswith("http") else base + line))
            t += dur
            dur = None
    return segs


def cut(vod_id, start, end, out):
    segs = [s for s in playlist(vod_id) if s[0] + s[1] > start and s[0] < end]
    with tempfile.TemporaryDirectory() as tmp:
        ts = Path(tmp) / "part.ts"
        with ts.open("wb") as f:
            for _, _, url in segs:
                f.write(fetch(url))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start - segs[0][0]:.3f}",
                        "-i", str(ts), "-t", f"{end - start:.3f}", "-c:v", "libx264",
                        "-preset", "fast", "-crf", "17", "-c:a", "aac", "-b:a", "192k",
                        out], check=True)


def envelope(path, ss=None, t=None, rate=50):
    cmd = ["ffmpeg", "-v", "error"]
    if ss is not None:
        cmd += ["-ss", str(ss), "-t", str(t)]
    cmd += ["-i", path, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"]
    a = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout,
                      np.int16).astype(np.float32)
    hop = 8000 // rate
    n = len(a) // hop
    e = np.log1p(np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(axis=1)))
    return (e - e.mean()) / (e.std() + 1e-6)


def locate(clip, vod_audio, audio_offset, guess, before=180, after=60, rate=50):
    c = envelope(clip, rate=rate)
    w0 = max(guess - before - audio_offset, 0)
    v = envelope(vod_audio, ss=w0, t=before + after + len(c) / rate, rate=rate)
    scores = np.correlate(v, c, mode="valid") / len(c)
    k = int(np.argmax(scores))
    return audio_offset + w0 + k / rate, float(scores[k])


if __name__ == "__main__":
    if sys.argv[1] == "cut":
        cut(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5])
    else:
        print(locate(sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])))
