#!/usr/bin/env python3
"""Daily clip production: top GTA Twitch clips -> vertical TikTok videos.

  python3 daily.py prepare    # fetch + download + facecam + transcription
  # (edit work/<date>/manifest.json: "hook" + "description" per clip)
  python3 daily.py render     # build videos into output/<date>/<streamer>/

Streamers live in streamers.json; already used clips in history.json
(committed, so a clip is never posted twice).
"""
import argparse
import datetime as dt
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STREAMERS = ROOT / "streamers.json"
HISTORY = ROOT / "history.json"
GAME = "Grand Theft Auto VI"
SAME_MOMENT_S = 90          # clips created this close together = same moment
MAX_LEN = 45                # seconds; target length is 30–45 s


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def ytdlp(*args):
    out = subprocess.run(["yt-dlp", *args], capture_output=True, text=True)
    return [json.loads(l) for l in out.stdout.splitlines() if l.startswith("{")]


def top_clips(login, wanted, used, period="7d", scan=40, check=12):
    """Most viewed GTA clips of a channel, skipping used ones and duplicates."""
    listing = ytdlp("--flat-playlist", "--playlist-end", str(scan), "-j",
                    f"https://www.twitch.tv/{login}/clips?filter=clips&range={period}")
    picked = []
    ranked = sorted(listing, key=lambda e: -(e.get("view_count") or 0))
    for entry in ranked[:check]:      # only the top ones: keeps the daily scan fast
        slug = entry["url"].rstrip("/").split("/")[-1]
        if slug in used:
            continue
        info = ytdlp("-j", entry["url"])
        if not info or not GAME in (info[0].get("categories") or []):
            continue
        info = info[0]
        if any(abs(info["timestamp"] - p["timestamp"]) < SAME_MOMENT_S for p in picked):
            continue
        picked.append({"slug": slug, "url": entry["url"], "title": info["title"],
                       "views": info.get("view_count"), "timestamp": info["timestamp"],
                       "duration": info.get("duration"), "streamer": info.get("channel", login)})
        if len(picked) >= wanted:
            break
    return picked


def default_hook(title, streamer):
    t = re.sub(r"\s+", " ", title).strip()
    if len(t) < 6 or "LIVE" in t.upper() or len(t) > 45:
        return f"{streamer} sur GTA 6"
    return t


def default_description(clip):
    tag = re.sub(r"\W", "", clip["streamer"].lower())
    return (f"{clip['hook']} 😂🔥\n🎥 Twitch : {clip['streamer']}\n"
            f"#gta6 #gtavi #gta6fr #{tag} #twitchfr #streamerfr #gaming #fyp #pourtoi")


def prepare(date):
    from clipper import transcribe
    from facecam import detect

    streamers = load(STREAMERS, [])
    used = set(load(HISTORY, {}))
    work = ROOT / "work" / date
    work.mkdir(parents=True, exist_ok=True)
    manifest = []
    for s in streamers:
        if not s.get("active", True):
            continue
        clips = top_clips(s["login"], s.get("per_day", 5), used)
        print(f"{s['login']}: {len(clips)} clip(s)")
        for i, c in enumerate(clips, 1):
            d = work / s["login"] / f"{i:02d}"
            d.mkdir(parents=True, exist_ok=True)
            src = d / "src.mp4"
            if not src.exists():
                subprocess.run(["yt-dlp", "-q", "-o", str(src), c["url"]], check=True)
            words = transcribe(str(src), 0, c["duration"] or 60)
            save(d / "words.json", words)
            c.update(dir=str(d.relative_to(ROOT)), facecam=detect(str(src), s.get("facecams", [])),
                     transcript=" ".join(w["w"] for w in words))
            c["hook"] = default_hook(c["title"], c["streamer"])
            c["description"] = default_description(c)
            manifest.append(c)
            print(f"  {i:02d} {c['views']} vues | cam={c['facecam']} | {c['title']}")
    save(work / "manifest.json", manifest)
    print(f"-> {work / 'manifest.json'}")


def render(date, manifest_path=None):
    from clipper import render as render_clip

    work = ROOT / "work" / date
    manifest = load(Path(manifest_path) if manifest_path else work / "manifest.json", [])
    history = load(HISTORY, {})
    for c in manifest:
        d = ROOT / c["dir"]
        out_dir = ROOT / "output" / date / c["streamer"]
        out_dir.mkdir(parents=True, exist_ok=True)
        name = Path(c["dir"]).name
        words = json.loads((d / "words.json").read_text())
        start = c.get("start", 0)
        end = min(c.get("end") or c["duration"] or 60, start + MAX_LEN)
        words = [dict(w, s=w["s"] - start, e=w["e"] - start)
                 for w in words if start <= w["s"] < end]
        render_clip(str(d / "src.mp4"), str(out_dir / f"{name}.mp4"),
                    start, end, c["facecam"], c["hook"], words,
                    kicker=f"{c['streamer']} · Twitch")
        (out_dir / f"{name}.txt").write_text(c["description"] + "\n")
        history[c["slug"]] = {"date": date, "streamer": c["streamer"]}
        print(f"OK {out_dir / name}.mp4")
    save(HISTORY, history)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("step", choices=["prepare", "render"])
    p.add_argument("--date", default=dt.date.today().isoformat())
    p.add_argument("--manifest", help="render this manifest instead of work/<date>/manifest.json")
    a = p.parse_args()
    if a.step == "render":
        render(a.date, a.manifest)
    else:
        prepare(a.date)


if __name__ == "__main__":
    main()
