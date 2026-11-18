#!/usr/bin/env python3
"""Turn a 16:9 stream clip into a vertical TikTok clip (1080x1920).

Layout: streamer facecam on top, gameplay below, word-by-word subtitles,
optional hook title.

Usage:
  python3 clipper.py INPUT.mp4 OUTPUT.mp4 --start 0 --end 28 \
      --facecam 0,0,400,225 --title "SA 1ERE BAGARRE SUR GTA 6"
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

W, H = 1080, 1920
BRAND = json.loads((Path(__file__).resolve().parent / "brand.json").read_text())
FONT = BRAND["font"]


def ass_color(hex_rgb, alpha="00"):
    """'FF2D95' -> '&H00952DFF' (ASS is AABBGGRR)."""
    r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()


PINK, CYAN, PURPLE = (ass_color(BRAND[k]) for k in ("pink", "cyan", "purple"))
WHITE = "&H00FFFFFF"
WORDS_PER_LINE = 3
# Phrases Whisper invents on music / silence.
HALLUCINATIONS = ("amara.org", "sous-titres réalisés", "sous -titres réalisés",
                  "merci d'avoir regardé", "abonnez-vous")


def run(cmd):
    subprocess.run(cmd, check=True)


def transcribe(src, start, end, model_size="small"):
    """Word-level timestamps (relative to `start`) using faster-whisper."""
    from faster_whisper import WhisperModel

    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(start), "-to", str(end), "-i", src,
         "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        check=True, capture_output=True).stdout
    audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio, language="fr", word_timestamps=True,
                                   vad_filter=True)
    words = []
    for seg in segments:
        if any(h in seg.text.lower() for h in HALLUCINATIONS):
            continue
        for w in seg.words:
            txt = w.word.strip()
            if not txt:
                continue
            # Whisper splits "c'était" / "fais-la" into two tokens: glue them.
            if words and (txt[0] in "'’-" or words[-1]["w"][-1] in "'’"):
                words[-1].update(w=words[-1]["w"] + txt, e=w.end)
            else:
                words.append({"w": txt, "s": w.start, "e": w.end})
    return words


def ts(t):
    t = max(t, 0)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def build_ass(words, title, sub_y, title_y, kicker=""):
    """Vice City Néon: white italic subs with purple outline + cyan shadow,
    active word in neon pink, pink title box with a cyan kicker above."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{FONT},92,{WHITE},{WHITE},{PURPLE},{CYAN},-1,-1,0,0,100,100,1,0,1,8,5,5,50,50,0,1
Style: Title,{FONT},60,{WHITE},{WHITE},{PINK},{PINK},-1,-1,0,0,100,100,1,0,3,20,0,5,70,70,0,1
Style: Kicker,{FONT},34,{CYAN},{CYAN},{PURPLE},{PURPLE},-1,-1,0,0,100,100,4,0,1,5,0,5,60,60,0,1
Style: Handle,{FONT},30,&H40FFFFFF,&H40FFFFFF,&H80000000,&H80000000,-1,-1,0,0,100,100,1,0,1,2,0,9,30,30,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 2,{ts(0)},{ts(9999)},Handle,,0,0,0,,{BRAND['handle']}"]
    if title:
        lines.append(f"Dialogue: 1,{ts(0)},{ts(9999)},Title,,0,0,0,,"
                     f"{{\\pos({W // 2},{title_y})}}{title.upper()}")
    if kicker:
        lines.append(f"Dialogue: 1,{ts(0)},{ts(9999)},Kicker,,0,0,0,,"
                     f"{{\\pos({W // 2},{title_y - 78})}}▶ {kicker.upper()}")

    # Group words into short chunks; break on long pauses.
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= WORDS_PER_LINE or w["s"] - cur[-1]["e"] > 0.6):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)

    for c, chunk in enumerate(chunks):
        next_start = chunks[c + 1][0]["s"] if c + 1 < len(chunks) else 1e9
        for i, w in enumerate(chunk):
            # Never let a chunk linger over the next one (avoids overlapping text).
            end = chunk[i + 1]["s"] if i + 1 < len(chunk) else min(w["e"] + 0.25, next_start)
            parts = []
            for j, x in enumerate(chunk):
                txt = x["w"].upper()
                if j == i:
                    txt = f"{{\\c{PINK}}}{txt}{{\\r}}"
                parts.append(txt)
            pop = "{\\fad(0,0)\\t(0,80,\\fscx105\\fscy105)\\t(80,160,\\fscx100\\fscy100)}" if i == 0 else ""
            lines.append(f"Dialogue: 0,{ts(w['s'])},{ts(end)},Sub,,0,0,0,,"
                         f"{{\\pos({W // 2},{sub_y})}}{pop}{' '.join(parts)}")
    return head + "\n".join(lines) + "\n"


GRADE = "eq=saturation=1.2:contrast=1.06"     # punchier gameplay colours


def layout(facecam):
    """Return (filter graph ending in [base], subtitle y, title y)."""
    pink, cyan = "0x" + BRAND["pink"], "0x" + BRAND["cyan"]
    if facecam:
        # Facecam band on top, gameplay below (centre crop, avoids side cams),
        # neon pink/cyan separator between the two.
        fx, fy, fw, fh = facecam
        cam_h = round(W * fh / fw / 2) * 2
        game_h = H - cam_h
        crop_w = round(1080 * W / game_h / 2) * 2
        vf = (f"[0:v]scale=1920:1080,split[a][b];"
              f"[a]crop={fw}:{fh}:{fx}:{fy},scale={W}:{cam_h}[cam];"
              f"[b]crop={crop_w}:1080:(in_w-{crop_w})/2:0,scale={W}:{game_h},{GRADE}[game];"
              f"[cam][game]vstack,"
              f"drawbox=y={cam_h - 5}:w={W}:h=10:color={pink}:t=fill,"
              f"drawbox=y={cam_h + 5}:w={W}:h=4:color={cyan}:t=fill[base]")
        return vf, cam_h + int(game_h * 0.62), cam_h
    # No facecam: 4:5 gameplay crop on a blurred, purple-tinted background.
    game_h = 1350
    top = (H - game_h) // 2
    vf = (f"[0:v]scale=1920:1080,split[a][b];"
          f"[a]crop=608:1080,scale={W}:{H},boxblur=30:2,eq=brightness=-0.2[bg];"
          f"[b]crop=864:1080,scale={W}:{game_h},{GRADE}[game];"
          f"[bg][game]overlay=0:{top},"
          f"drawbox=y={top - 8}:w={W}:h=8:color={pink}:t=fill,"
          f"drawbox=y={top + game_h}:w={W}:h=8:color={cyan}:t=fill[base]")
    return vf, top + int(game_h * 0.72), top


def render(src, out, start, end, facecam, title, words, kicker=""):
    vf, sub_y, title_y = layout(facecam)
    dur = end - start
    bar = 14
    with tempfile.TemporaryDirectory() as tmp:
        ass = Path(tmp) / "subs.ass"
        ass.write_text(build_ass(words, title, sub_y=sub_y, title_y=title_y,
                                 kicker=kicker), encoding="utf-8")
        # Neon progress bar filling up along the bottom edge (retention).
        graph = (f"{vf};color=c=0x{BRAND['pink']}:s={W}x{bar}:d={dur}[bar];"
                 f"[base][bar]overlay=x='-w+w*t/{dur:.3f}':y={H - bar}:eof_action=pass,"
                 f"ass={ass}[v]")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-to", str(end),
             "-i", src, "-filter_complex", graph,
             "-map", "[v]", "-map", "0:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "23",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", out])


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--start", type=float, default=0)
    p.add_argument("--end", type=float, required=True)
    p.add_argument("--facecam", default="auto",
                   help="x,y,w,h in the 1920x1080 source, 'auto' or 'none'")
    p.add_argument("--title", default="")
    p.add_argument("--kicker", default="", help="small line above the title")
    p.add_argument("--words", help="cached word timestamps JSON (skip Whisper)")
    a = p.parse_args()

    if a.words and Path(a.words).exists():
        words = json.loads(Path(a.words).read_text())
    else:
        words = transcribe(a.input, a.start, a.end)
        if a.words:
            Path(a.words).write_text(json.dumps(words, ensure_ascii=False))
    if a.facecam == "auto":
        from facecam import detect
        cam = detect(a.input)
    elif a.facecam == "none":
        cam = None
    else:
        cam = [int(v) for v in a.facecam.split(",")]
    render(a.input, a.output, a.start, a.end, cam, a.title, words, a.kicker)
    print(f"OK -> {a.output}")


if __name__ == "__main__":
    main()
