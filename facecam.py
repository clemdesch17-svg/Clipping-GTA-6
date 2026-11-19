#!/usr/bin/env python3
"""Find the streamer's facecam rectangle in a 16:9 stream clip.

Idea: the facecam is the only face that stays at the same place across the
whole clip (game characters move), and its borders are *static* edges
(gameplay edges average out over time).

Returns (x, y, w, h) in 1920x1080 coordinates, or None.
"""
import subprocess
import sys

import cv2
import numpy as np

SRC_W, SRC_H = 1920, 1080
SCALE = 2                       # analyse at 960x540
CAM_ASPECT = 1080 / 640         # aspect of the facecam band in the output
STATIC_STD = 12                 # temporal std below which a pixel is "static"
MIN_FACE_MOTION = 4             # temporal std a live face must exceed
STATIC_FRAC = 0.5               # share of static pixels needed to grow a side


def sample_frames(src, n=14):
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", src], capture_output=True, text=True, check=True).stdout)
    w, h = SRC_W // SCALE, SRC_H // SCALE
    frames = []
    for i in range(n):
        t = dur * (i + 0.5) / n
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1",
             "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
            capture_output=True, check=True).stdout
        if len(raw) == w * h:
            frames.append(np.frombuffer(raw, np.uint8).reshape(h, w))
    return frames


def stable_face(frames):
    """Face position seen in most frames at (nearly) the same place."""
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = []
    std = np.stack([f.astype(np.float32) for f in frames]).std(axis=0)
    for f in frames:
        # Upscale x2 so small facecams (face ~12 px at analysis size) are found.
        big = cv2.resize(f, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        for (x, y, w, h) in cascade.detectMultiScale(big, 1.1, 5, minSize=(24, 24)):
            x, y, w, h = x / 2, y / 2, w / 2, h / 2
            # A real streamer moves; overlays/avatars (static images) don't.
            if std[int(y):int(y + h), int(x):int(x + w)].mean() < MIN_FACE_MOTION:
                continue
            faces.append((x + w / 2, y + h / 2, w))
    best, best_hits = None, 0
    for cx, cy, w in faces:
        hits = [g for g in faces if abs(g[0] - cx) < 30 and abs(g[1] - cy) < 30]
        if len(hits) > best_hits:
            best_hits = len(hits)
            best = tuple(np.median(np.array(hits), axis=0))
    if best is None or best_hits < max(3, len(frames) * 0.35):
        return None
    return best


def find_box(frames, face):
    """Grow a rectangle from the face while its border strips stay 'static'.

    The webcam room barely changes over the clip, gameplay changes a lot,
    so the facecam shows up as a low temporal-variance rectangle.
    """
    cx, cy, fw = face
    h, w = frames[0].shape
    std = np.stack([f.astype(np.float32) for f in frames]).std(axis=0)
    static = cv2.GaussianBlur(std, (9, 9), 0) < STATIC_STD

    # Fill the (moving) streamer silhouette, then keep the static blob
    # that contains the face.
    k = int(fw * 2) | 1
    mask = cv2.morphologyEx(static.astype(np.uint8), cv2.MORPH_CLOSE,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    lab = labels[int(cy), int(cx)]
    if lab == 0:
        return None
    x, y, bw, bh, _ = stats[lab]
    return x, y, bw, bh


def to_band(box, face):
    """Shrink the box to the output band aspect, centred on the face."""
    x, y, w, h = box
    cx, cy, _ = face
    if w / h > CAM_ASPECT:
        nw = h * CAM_ASPECT
        x = min(max(cx - nw / 2, x), x + w - nw)
        w = nw
    else:
        # Too tall: usually chat / alerts glued under the cam -> keep the top.
        h = w / CAM_ASPECT
    x, y, w, h = (int(round(v * SCALE / 2) * 2) for v in (x, y, w, h))
    return x, y, w, h


def face_hits(frames, box):
    """Number of frames with a (moving) face inside `box` (1920x1080 coords)."""
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    x, y, w, h = (v // SCALE for v in box)
    crops = [f[y:y + h, x:x + w] for f in frames]
    if not crops or crops[0].size == 0:
        return 0
    std = np.stack([c.astype(np.float32) for c in crops]).std(axis=0)
    hits = 0
    for c in crops:
        big = cv2.resize(c, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        for (fx, fy, fw, fh) in cascade.detectMultiScale(big, 1.1, 5, minSize=(30, 30)):
            fx, fy, fw, fh = (v // 3 for v in (fx, fy, fw, fh))
            if std[fy:fy + fh, fx:fx + fw].mean() >= MIN_FACE_MOTION:
                hits += 1
                break
    return hits


def generic(frames):
    face = stable_face(frames)
    if face is None:
        return None
    box = find_box(frames, face)
    if box is None:
        return None
    x, y, w, h = box
    fh, fw = frames[0].shape
    area = w * h / (fw * fh)
    if not (0.015 < area < 0.35) or not (0.8 < w / max(h, 1) < 3):
        return None
    return tuple(int(v) for v in to_band((x, y, w, h), face))


def detect(src, known=()):
    """Facecam box: generic detection first; if it fails (calm gameplay,
    in-game faces), fall back to the streamer's known boxes that contain a
    live face (most hits, then the tightest box)."""
    frames = sample_frames(src)
    if len(frames) < 4:
        return None
    box = generic(frames)
    if box or not known:
        return box
    need = max(3, len(frames) * 0.3)
    scored = [(face_hits(frames, b), -b[2] * b[3], tuple(b)) for b in known]
    scored = [sc for sc in scored if sc[0] >= need]
    return max(scored)[2] if scored else None


if __name__ == "__main__":
    print(detect(sys.argv[1]))
