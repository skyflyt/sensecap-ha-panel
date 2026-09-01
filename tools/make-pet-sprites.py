#!/usr/bin/env python3
"""
Placeholder desk-pet sprites for the SenseCAP Indicator — slice 1.

Two 64x64 whole-creature sprites (egg, hatchling), drawn procedurally as pixel
art rather than generated, because slice 1 explicitly ships *placeholders*:
good enough to prove the loop, labelled replaceable, swapped by changing one
image id. Design rationale: docs/03-sprite-pipeline.md.

Format decisions, from that doc:
  * RGB565 + chroma_key => 2 bytes/px on device (8,192 B each).
    Alpha_channel would be 3 B/px, and alpha blending at 64px produces the
    soft halo that makes small sprites look muddy. Hard edges are correct here.
  * Palette locked to the panel's own colours (extracted from
    your panel config) so the pet reads as native rather than pasted on.

  ⚠️ THE BACKGROUND MUST BE GENUINELY TRANSPARENT (alpha = 0), NOT a magenta
  fill. Got this wrong on the first deploy 2026-08-24 and the panel showed a
  purple box around the egg. ESPHome's `transparency: chroma_key` does not look
  for a magic colour in the pixel data — it reads the SOURCE IMAGE'S ALPHA and
  encodes those transparent pixels as its own reserved value. A PNG with an
  opaque magenta background has nothing transparent in it, so every one of
  those magenta pixels is real image data and gets drawn.
  Alpha is written as strictly 0 or 255 — never partial — which is what keeps
  the hard edges that made chroma_key the right choice in the first place.

Run with Windows python (the same interpreter that runs your other build tooling).
    python make-pet-sprites.py
Writes ../images/pet/egg.png and ../images/pet/hatchling.png
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "images", "pet"))

S = 64
KEY = (255, 0, 255)          # chroma key — must not appear in the art

# --- palette, lifted from your panel config -----------------------------
INK      = (0x14, 0x16, 0x1A)   # near-black outline (panel bg)
SHADE    = (0x2A, 0x2F, 0x37)   # deep shadow
DIM      = (0x4B, 0x55, 0x63)   # mid shadow
GREY     = (0x6B, 0x72, 0x80)   # dim grey
MUTED    = (0x9A, 0xA0, 0xA6)   # workhorse grey
LIGHT    = (0xE8, 0xEA, 0xED)   # near-white
AMBER    = (0xF2, 0xB0, 0x1E)   # the panel accent
AMBER_D  = (0x9A, 0x67, 0x00)   # amber shadow (already in the config)
GREEN    = (0x35, 0xC7, 0x59)   # eye highlight / life


def new_canvas() -> Image.Image:
    return Image.new("RGB", (S, S), KEY)


def outline_ellipse(d: ImageDraw.ImageDraw, box, fill, ink=INK):
    """Filled ellipse with a 1px hard outline — no anti-aliasing anywhere."""
    d.ellipse(box, fill=ink)
    x0, y0, x1, y1 = box
    d.ellipse((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=fill)


def draw_egg() -> Image.Image:
    """Stage 1. A speckled egg, slightly ovoid, sitting in a shallow nest."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # body: taller than wide, narrower at the top
    outline_ellipse(d, (17, 8, 46, 54), LIGHT)
    # the top third is a touch narrower — fake it by shaving the shoulders
    d.ellipse((15, 4, 22, 22), fill=KEY)
    d.ellipse((41, 4, 48, 22), fill=KEY)
    outline_ellipse(d, (20, 6, 43, 34), LIGHT)

    # form shading: light comes from upper-left
    d.ellipse((33, 20, 45, 52), fill=MUTED)
    d.ellipse((36, 26, 45, 50), fill=GREY)
    # re-assert the outline the shading just ate
    d.ellipse((17, 8, 46, 54), outline=INK)
    d.ellipse((20, 6, 43, 34), outline=INK)

    # specks — amber, deliberately irregular
    for (sx, sy, r) in [(25, 18, 2), (33, 14, 1), (29, 27, 2), (38, 33, 1),
                        (23, 35, 1), (31, 41, 2), (39, 23, 1), (26, 47, 1)]:
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=AMBER)

    # highlight
    d.ellipse((23, 13, 27, 19), fill=LIGHT)

    # nest: a shallow dark arc under it, so the egg is standing on something
    d.ellipse((13, 47, 50, 59), fill=SHADE)
    d.ellipse((15, 49, 48, 57), fill=DIM)
    # egg sits in front of the nest's back rim
    outline_ellipse(d, (17, 8, 46, 52), LIGHT)
    d.ellipse((33, 20, 45, 50), fill=MUTED)
    d.ellipse((36, 26, 45, 48), fill=GREY)
    d.ellipse((17, 8, 46, 52), outline=INK)
    for (sx, sy, r) in [(25, 18, 2), (33, 14, 1), (29, 27, 2), (38, 33, 1),
                        (23, 35, 1), (31, 41, 2), (39, 23, 1)]:
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=AMBER)
    d.ellipse((23, 13, 27, 19), fill=LIGHT)

    return img


def draw_hatchling() -> Image.Image:
    """Stage 2. Round body, big eyes, half the shell still worn as a cap."""
    img = new_canvas()
    d = ImageDraw.Draw(img)

    # feet first, so the body overlaps them
    outline_ellipse(d, (20, 48, 30, 56), AMBER_D)
    outline_ellipse(d, (34, 48, 44, 56), AMBER_D)

    # body
    outline_ellipse(d, (16, 22, 48, 53), AMBER)
    # belly, lighter
    d.ellipse((23, 32, 41, 51), fill=LIGHT)
    d.ellipse((16, 22, 48, 53), outline=INK)
    # body shading on the right
    d.ellipse((38, 28, 47, 50), fill=AMBER_D)
    d.ellipse((16, 22, 48, 53), outline=INK)
    d.ellipse((23, 32, 41, 51), fill=LIGHT)

    # little wings
    outline_ellipse(d, (11, 32, 21, 44), AMBER)
    outline_ellipse(d, (43, 32, 53, 44), AMBER_D)

    # head merges into the body (one blob reads better at 64px than two)
    outline_ellipse(d, (19, 14, 45, 38), AMBER)
    d.ellipse((38, 18, 44, 36), fill=AMBER_D)
    d.ellipse((19, 14, 45, 38), outline=INK)

    # eyes — the single most important 6 pixels on the sprite
    d.ellipse((25, 21, 31, 28), fill=LIGHT)
    d.ellipse((34, 21, 40, 28), fill=LIGHT)
    d.ellipse((26, 23, 30, 27), fill=INK)
    d.ellipse((35, 23, 39, 27), fill=INK)
    d.point((28, 24), fill=GREEN)
    d.point((37, 24), fill=GREEN)

    # beak
    d.polygon([(30, 30), (35, 30), (32, 34)], fill=AMBER_D)
    d.polygon([(30, 30), (35, 30), (32, 34)], outline=INK)

    # shell cap — the half it just came out of, worn at a jaunty angle
    d.pieslice((17, 4, 47, 26), start=180, end=360, fill=LIGHT, outline=INK)
    # zig-zag crack line along the rim
    for x in range(18, 47, 4):
        d.line([(x, 15), (x + 2, 12), (x + 4, 15)], fill=INK)
    d.ellipse((36, 8, 46, 20), fill=MUTED)
    d.pieslice((17, 4, 47, 26), start=180, end=360, outline=INK)
    for (sx, sy) in [(24, 10), (31, 8), (38, 11)]:
        d.ellipse((sx - 1, sy - 1, sx + 1, sy + 1), fill=AMBER)

    return img


def quantise_and_cut(img: Image.Image) -> Image.Image:
    """Snap every pixel to the locked palette, then turn the KEY pixels into
    genuine alpha=0. Returns RGBA. No dithering — dithering at 64px reads as
    dirt, not shading — and alpha is binary, so edges stay hard."""
    pal = [KEY, INK, SHADE, DIM, GREY, MUTED, LIGHT, AMBER, AMBER_D, GREEN]
    src = img.load()
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dst = out.load()
    for y in range(S):
        for x in range(S):
            r, g, b = src[x, y]
            best, bd = pal[0], 1 << 30
            for c in pal:
                dr, dg, db = r - c[0], g - c[1], b - c[2]
                dist = dr * dr + dg * dg + db * db
                if dist < bd:
                    bd, best = dist, c
            # The key colour becomes real transparency, which is the ONLY thing
            # ESPHome's chroma_key mode actually looks at.
            dst[x, y] = (0, 0, 0, 0) if best == KEY else (*best, 255)
    return out


def report(name: str, img: Image.Image) -> None:
    cols, opaque, partial = {}, 0, 0
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            if a == 255:
                opaque += 1
                cols[(r, g, b)] = cols.get((r, g, b), 0) + 1
            elif a != 0:
                partial += 1
    print(f"  {name}: {len(cols)} colours, {opaque} opaque px "
          f"({opaque * 100 // (S * S)}% coverage), {partial} partial-alpha px "
          f"(MUST be 0), {S*S*2} B on device")
    assert partial == 0, f"{name}: partial alpha would soften the edges"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("egg", draw_egg), ("hatchling", draw_hatchling)):
        img = quantise_and_cut(fn())
        path = os.path.join(OUT, f"{name}.png")
        img.save(path)
        report(name, img)
        print(f"  -> {path}")


if __name__ == "__main__":
    main()
