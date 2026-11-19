"""Harvest ALL GTA VI clips of a streamer (24h + 7d), download + transcribe.

  python3 harvest.py <login> <out_dir>   -> <out_dir>/clips.json (transcripts)
Then read the transcripts and pick the best moments (see clip-gta skill).
"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from daily import ytdlp, load, HISTORY, GAME
from clipper import transcribe

login, out = sys.argv[1], sys.argv[2]
used = set(load(HISTORY, {}))
listing = []
for rng in ("24hr", "7d"):
    listing += ytdlp("--flat-playlist", "--playlist-end", "100", "-j",
                     f"https://www.twitch.tv/{login}/clips?filter=clips&range={rng}")
seen, entries = set(), []
for e in listing:
    if e["url"] not in seen:
        seen.add(e["url"]); entries.append(e)
print("listed", len(entries), flush=True)

def info(e):
    r = ytdlp("-j", e["url"])
    return r[0] if r else None
with ThreadPoolExecutor(6) as ex:
    infos = [i for i in ex.map(info, entries) if i]
gta = [i for i in infos if GAME in (i.get("categories") or [])
       and i["webpage_url_basename"] not in used]
print("gta6", len(gta), flush=True)

clips = []
for n, i in enumerate(sorted(gta, key=lambda i: i["timestamp"])):
    d = f"{out}/{n:03d}"
    subprocess.run(["mkdir", "-p", d])
    subprocess.run(["yt-dlp", "-q", "-o", f"{d}/src.mp4", i["webpage_url"]])
    try:
        words = transcribe(f"{d}/src.mp4", 0, i.get("duration") or 60)
    except Exception as ex:
        print("fail", d, ex, flush=True); continue
    json.dump(words, open(f"{d}/words.json", "w"), ensure_ascii=False)
    clips.append(dict(n=n, slug=i["webpage_url_basename"], url=i["webpage_url"],
                      title=i["title"], views=i.get("view_count"), ts=i["timestamp"],
                      dur=i.get("duration"),
                      text=" ".join(f"[{w['s']:.0f}]{w['w']}" for w in words)))
    json.dump(clips, open(f"{out}/clips.json", "w"), ensure_ascii=False, indent=1)
    print("done", n, i["title"][:50], flush=True)
