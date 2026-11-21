#!/usr/bin/env python3
"""Download + transcribe a list of clips (from fresh.py) into work/harvest/fresh_<login>/."""
import json, os, subprocess, sys
from clipper import transcribe
items = json.load(open(sys.argv[1]))
by = {}
for it in items:
    by.setdefault(it["login"], []).append(it)
for login, lst in by.items():
    out = f"work/harvest/fresh_{login}"
    os.makedirs(out, exist_ok=True)
    clips = []
    for n, i in enumerate(sorted(lst, key=lambda x: x["ts"])):
        d = f"{out}/{n:03d}"; os.makedirs(d, exist_ok=True)
        subprocess.run(["yt-dlp", "-q", "-o", f"{d}/src.mp4", i["url"]])
        try:
            words = transcribe(f"{d}/src.mp4", 0, i.get("dur") or 60)
        except Exception as e:
            print("fail", d, e, flush=True); continue
        json.dump(words, open(f"{d}/words.json", "w"), ensure_ascii=False)
        clips.append(dict(n=n, slug=i["slug"], url=i["url"], title=i["title"], views=i["views"],
                          ts=i["ts"], dur=i["dur"],
                          text=" ".join(f"[{w['s']:.0f}]{w['w']}" for w in words)))
        json.dump(clips, open(f"{out}/clips.json", "w"), ensure_ascii=False, indent=1)
        print("done", login, n, flush=True)
