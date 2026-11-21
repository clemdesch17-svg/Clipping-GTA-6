#!/usr/bin/env python3
"""Find the FRESHEST GTA VI clips (last N hours) across streamers.

  python3 fresh.py <hours> <out_json> login1 login2 ...
Skips clips already used (history.json) or already harvested (work/harvest/*/clips.json).
"""
import glob, json, sys, time
from concurrent.futures import ThreadPoolExecutor
from daily import ytdlp, GAME, load, HISTORY

hours, out, logins = float(sys.argv[1]), sys.argv[2], sys.argv[3:]
seen = set(load(HISTORY, {}))
for f in glob.glob("work/harvest/*/clips.json"):
    seen |= {c["slug"] for c in json.load(open(f))}
cut = time.time() - hours * 3600

def info(url):
    r = ytdlp("-j", url)
    return r[0] if r else None

res = []
for l in logins:
    lst = ytdlp("--flat-playlist", "--playlist-end", "80", "-j",
                f"https://www.twitch.tv/{l}/clips?filter=clips&range=24hr")
    with ThreadPoolExecutor(8) as ex:
        infos = [i for i in ex.map(info, [e["url"] for e in lst]) if i]
    fresh = [i for i in infos if GAME in (i.get("categories") or []) and i["timestamp"] >= cut
             and i["webpage_url_basename"] not in seen]
    print(f"{l:14s} clips24h={len(infos):3d} gta6_frais={len(fresh)}", flush=True)
    res += [dict(login=l, url=i["webpage_url"], slug=i["webpage_url_basename"], title=i["title"],
                 views=i.get("view_count"), ts=i["timestamp"], dur=i.get("duration")) for i in fresh]
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
