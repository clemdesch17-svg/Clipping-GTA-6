"""Render the on-video hook title as a PNG (pink neon box, white italic text,
full-colour emojis). libass can't draw colour emojis, Pillow can."""
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
BRAND = json.loads((ROOT / "brand.json").read_text())
TEXT_FONT = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
EMOJI_NATIVE = 109                      # NotoColorEmoji bitmap strike size
# Owner-supplied emoji images (from their iPhone keyboard) take priority
# over Noto; add more by dropping PNGs in branding/emoji + map.json.
EMOJI_DIR = ROOT / "branding" / "emoji"
EMOJI_MAP = json.loads((EMOJI_DIR / "map.json").read_text()) if (EMOJI_DIR / "map.json").exists() else {}

# Emoji sequences (incl. ZWJ, variation selectors, skin tones, flags).
EMOJI_RE = re.compile(
    "(?:[\U0001F1E6-\U0001F1FF]{2}"
    "|[\U0001F300-\U0001FAFF☀-➿⬀-⯿←-⇿⌀-⏿]"
    "[️\U0001F3FB-\U0001F3FF]*(?:‍[\U0001F300-\U0001FAFF☀-➿][️]?)*)")


def _rgb(hex_rgb):
    return tuple(int(hex_rgb[i:i + 2], 16) for i in (0, 2, 4))


class _Runs:
    def __init__(self, size):
        self.font = ImageFont.truetype(TEXT_FONT, size)
        self.emoji_font = ImageFont.truetype(EMOJI_FONT, EMOJI_NATIVE)
        self.size = size
        self.emoji_px = int(size * 1.15)

    def split(self, text):
        out, pos = [], 0
        for m in EMOJI_RE.finditer(text):
            if m.start() > pos:
                out.append(("t", text[pos:m.start()]))
            out.append(("e", m.group()))
            pos = m.end()
        if pos < len(text):
            out.append(("t", text[pos:]))
        return out

    def width(self, text):
        return sum(self.font.getlength(s) if k == "t" else self.emoji_px + 4
                   for k, s in self.split(text))

    def emoji_image(self, seq):
        """Emoji glyph(s) as RGBA: custom PNGs when every char has one, else Noto."""
        chars = [c for c in seq if c not in "\uFE0F\u200D" and not "\U0001F3FB" <= c <= "\U0001F3FF"]
        if chars and all(c in EMOJI_MAP for c in chars):
            parts = [Image.open(EMOJI_DIR / f"{EMOJI_MAP[c]}.png").convert("RGBA") for c in chars]
            h = max(p.height for p in parts)
            out = Image.new("RGBA", (sum(p.width for p in parts), h), (0, 0, 0, 0))
            x = 0
            for p in parts:
                out.alpha_composite(p, (x, (h - p.height) // 2))
                x += p.width
            return out
        g = Image.new("RGBA", (EMOJI_NATIVE * 2, EMOJI_NATIVE * 2), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((0, 0), seq, font=self.emoji_font, embedded_color=True)
        return g

    def draw(self, img, x, y, text, fill, shadow):
        d = ImageDraw.Draw(img)
        for kind, s in self.split(text):
            if kind == "t":
                d.text((x + 4, y + 4), s, font=self.font, fill=shadow)
                d.text((x, y), s, font=self.font, fill=fill)
                x += self.font.getlength(s)
            else:
                g = self.emoji_image(s)
                bbox = g.getbbox() if g else None
                if bbox:
                    g = g.crop(bbox)
                    g = g.resize((self.emoji_px, int(self.emoji_px * g.height / g.width)),
                                 Image.LANCZOS)
                    img.alpha_composite(g, (int(x + 2), int(y + self.size * 0.55 - g.height / 2)))
                x += self.emoji_px + 4


def render_title(text, out_png, max_w=940, size=62):
    """Write the title card PNG, return its (width, height)."""
    runs = _Runs(size)
    # Upper-case the text only (emojis untouched) BEFORE measuring/wrapping.
    text = "".join(s.upper() if k == "t" else s for k, s in runs.split(text))
    text = re.sub(r"\b(GTA|GTA VI) (\d+|VI)\b", "\\1\u00a0\\2", text)   # never orphan the "6"
    words = []
    for w in filter(None, text.split(" ")):   # split(" "): keep no-break spaces
        # Emoji / punctuation-only words (😂, », !, ?) stay glued to the previous
        # word so they never start a line on their own.
        if words and not any(ch.isalnum() for ch in EMOJI_RE.sub("", w)):
            words[-1] += "\u00a0" + w
        else:
            words.append(w)
    lines, cur = [], ""
    for w in words:
        cand = f"{cur} {w}".strip()
        if cur and runs.width(cand) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    lines.append(cur)

    pad_x, pad_y, gap = 34, 20, 10
    line_h = int(size * 1.25)
    w = int(max(runs.width(l) for l in lines)) + 2 * pad_x
    h = line_h * len(lines) + gap * (len(lines) - 1) + 2 * pad_y
    img = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pink, cyan = _rgb(BRAND["pink"]), _rgb(BRAND["cyan"])
    d.rounded_rectangle((10, 10, w + 10, h + 10), radius=22, fill=cyan + (255,))   # neon offset
    d.rounded_rectangle((0, 0, w, h), radius=22, fill=pink + (255,))
    y = pad_y
    for l in lines:
        lx = (w - runs.width(l)) / 2
        runs.draw(img, lx, y - size * 0.12, l, (255, 255, 255), _rgb(BRAND["purple"]) + (160,))
        y += line_h + gap
    img.save(out_png)
    return img.size
