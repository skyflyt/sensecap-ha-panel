#!/usr/bin/env python3
"""
Draw the desk pet's EIGHT level sprites — one per level, the same creature
growing up.

Skylar, 2026-08-27: "the sprite itself getting upgraded/changed with each level.
like its growing up and gaining strength, size, abilities and accessories with
each level." The first attempt layered a ring and a hat over one static
hatchling; that is decoration, not growth.

These are DRAWN, not generated. I had no text-to-image tool in the loop (see
docs/03-sprite-pipeline.md §2 step 1), and a procedural ladder has one
property a generated one does not: every stage is the same construction with
different numbers, so stage 6 is provably stage 3 grown rather than a different
animal that happens to look similar. That is the exact problem §3 of the sprites
doc spends four mechanisms trying to solve.

Construction, shared by every stage and scaled by it:
    feet -> body -> wings -> head -> eyes -> beak -> crest -> tail -> horns
Later features simply switch on; nothing is ever removed. So the silhouette
accumulates, which is what reads as "growing up" rather than "changing".

Level 1 is the egg and is deliberately not part of the ladder.

Format notes carried over from make-pet-sprites.py: RGB565 + chroma_key (2 B/px
on device), transparency is REAL alpha (ESPHome reads the source alpha, not a
magic colour), and alpha is strictly 0 or 255 so edges stay hard.

Run with WINDOWS python. Writes ../images/pet/stage1..8.png
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "images", "pet"))

S = 64
KEY = (255, 0, 255)

INK     = (0x14, 0x16, 0x1A)
SHADE   = (0x2A, 0x2F, 0x37)
DIM     = (0x4B, 0x55, 0x63)
GREY    = (0x6B, 0x72, 0x80)
MUTED   = (0x9A, 0xA0, 0xA6)
LIGHT   = (0xE8, 0xEA, 0xED)
AMBER   = (0xF2, 0xB0, 0x1E)
AMBER_D = (0x9A, 0x67, 0x00)
GOLD    = (0xFF, 0xD2, 0x4A)
GREEN   = (0x35, 0xC7, 0x59)
RED     = (0xE5, 0x48, 0x4D)
BLUE    = (0x25, 0x63, 0xEB)

PALETTE = [KEY, INK, SHADE, DIM, GREY, MUTED, LIGHT, AMBER, AMBER_D, GOLD,
           GREEN, RED, BLUE]


def canvas() -> Image.Image:
    return Image.new("RGB", (S, S), KEY)


def oe(d, box, fill, ink=INK):
    """Outlined ellipse — 1 px hard edge, no anti-aliasing anywhere."""
    d.ellipse(box, fill=ink)
    x0, y0, x1, y1 = box
    if x1 - x0 > 2 and y1 - y0 > 2:
        d.ellipse((x0 + 1, y0 + 1, x1 - 1, y1 - 1), fill=fill)


def draw_egg() -> Image.Image:
    """Level 1. Unhatched, and deliberately outside the growth ladder."""
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse((13, 47, 50, 59), fill=SHADE)      # nest
    d.ellipse((15, 49, 48, 57), fill=DIM)
    oe(d, (17, 10, 46, 54), LIGHT)
    d.ellipse((34, 22, 45, 52), fill=MUTED)      # form shading
    d.ellipse((37, 28, 45, 50), fill=GREY)
    d.ellipse((17, 10, 46, 54), outline=INK)
    for (sx, sy, r) in [(25, 20, 2), (33, 16, 1), (29, 29, 2), (38, 35, 1),
                        (23, 37, 1), (31, 43, 2), (39, 25, 1)]:
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=AMBER)
    d.ellipse((23, 15, 27, 21), fill=LIGHT)      # highlight
    return img


def draw_stage(n: int) -> Image.Image:
    """Levels 2-8. One construction, eight sets of numbers."""
    t = (n - 2) / 6.0                       # 0.0 at L2 .. 1.0 at L8
    img = canvas()
    d = ImageDraw.Draw(img)

    body_w = int(26 + 22 * t)               # 26 -> 48
    body_h = int(22 + 20 * t)               # 22 -> 42
    head_r = int(11 + 6 * t)                # 11 -> 17
    cx, base = 32, 58                       # feet stand on y58

    body_top = base - body_h
    head_cy = body_top - head_r + int(4 + 2 * t)

    # Elder colouring: the creature itself warms toward gold.
    skin = AMBER if n < 7 else GOLD
    skin_d = AMBER_D if n < 7 else AMBER

    # ── tail (L5+) — behind everything
    if n >= 5:
        tl = int(10 + 10 * t)
        d.polygon([(cx + body_w // 2 - 2, base - body_h // 2),
                   (cx + body_w // 2 + tl, base - body_h // 2 - tl // 2),
                   (cx + body_w // 2 + tl - 3, base - body_h // 2 + tl // 3)],
                  fill=skin_d, outline=INK)

    # ── feet
    fw = int(8 + 4 * t)
    oe(d, (cx - body_w // 3 - fw // 2, base - 6, cx - body_w // 3 + fw // 2, base + 2), AMBER_D)
    oe(d, (cx + body_w // 3 - fw // 2, base - 6, cx + body_w // 3 + fw // 2, base + 2), AMBER_D)

    # ── body
    oe(d, (cx - body_w // 2, body_top, cx + body_w // 2, base - 2), skin)
    d.ellipse((cx + 2, body_top + 4, cx + body_w // 2 - 1, base - 4), fill=skin_d)
    d.ellipse((cx - body_w // 2, body_top, cx + body_w // 2, base - 2), outline=INK)
    belly_w = int(body_w * 0.55)
    d.ellipse((cx - belly_w // 2, body_top + body_h // 3,
               cx + belly_w // 2, base - 4), fill=LIGHT)

    # ── wings — grow from stubs to spread
    ww = int(8 + 12 * t)
    wh = int(10 + 14 * t)
    wy = body_top + body_h // 4
    oe(d, (cx - body_w // 2 - ww + 3, wy, cx - body_w // 2 + 4, wy + wh), skin)
    oe(d, (cx + body_w // 2 - 4, wy, cx + body_w // 2 + ww - 3, wy + wh), skin_d)

    # ── head
    oe(d, (cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r), skin)
    d.ellipse((cx + 2, head_cy - head_r + 2, cx + head_r - 1, head_cy + head_r - 2), fill=skin_d)
    d.ellipse((cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r), outline=INK)

    # ── crest (L4+) — the "getting fancier" signal
    if n >= 4:
        ch = int(4 + 7 * t)
        for i, dx in enumerate((-4, 0, 4)):
            h = ch - abs(dx) // 2
            d.polygon([(cx + dx - 2, head_cy - head_r + 1),
                       (cx + dx, head_cy - head_r - h),
                       (cx + dx + 2, head_cy - head_r + 1)],
                      fill=GOLD if n >= 7 else AMBER, outline=INK)

    # ── horns (L7+)
    if n >= 7:
        for sx in (-1, 1):
            d.polygon([(cx + sx * (head_r - 3), head_cy - head_r + 3),
                       (cx + sx * (head_r + 4), head_cy - head_r - 6),
                       (cx + sx * (head_r - 1), head_cy - head_r - 1)],
                      fill=LIGHT, outline=INK)

    # ── eyes — grow a little, and light up at the top of the ladder
    er = int(3 + 1.5 * t)
    ex = int(head_r * 0.45)
    for sx in (-1, 1):
        d.ellipse((cx + sx * ex - er, head_cy - er - 1,
                   cx + sx * ex + er, head_cy + er - 1), fill=LIGHT)
        d.ellipse((cx + sx * ex - er + 1, head_cy - er,
                   cx + sx * ex + er - 1, head_cy + er - 2), fill=INK)
        d.point((cx + sx * ex, head_cy - 1), fill=GREEN if n >= 6 else LIGHT)

    # ── beak
    bw = int(3 + 2 * t)
    d.polygon([(cx - bw, head_cy + er + 1), (cx + bw, head_cy + er + 1),
               (cx, head_cy + er + 1 + bw)], fill=AMBER_D, outline=INK)

    # ── shell cap, L2 only — the just-hatched marker
    if n == 2:
        d.pieslice((cx - head_r - 3, head_cy - head_r - 10,
                    cx + head_r + 3, head_cy - head_r + 8),
                   start=180, end=360, fill=LIGHT, outline=INK)
        for x in range(cx - head_r - 2, cx + head_r + 2, 4):
            d.line([(x, head_cy - head_r - 1), (x + 2, head_cy - head_r - 4),
                    (x + 4, head_cy - head_r - 1)], fill=INK)

    # ── scarf (L5+) and sash (L8) — earned kit, drawn ON the creature
    if n >= 5:
        d.rectangle((cx - head_r - 1, head_cy + head_r - 2,
                     cx + head_r + 1, head_cy + head_r + 2), fill=RED, outline=INK)
    if n >= 8:
        d.line([(cx - body_w // 2 + 3, body_top + body_h // 2),
                (cx + body_w // 2 - 3, body_top + 4)], fill=BLUE, width=3)

    return img


def quantise_and_cut(img: Image.Image) -> Image.Image:
    src = img.load()
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dst = out.load()
    for y in range(S):
        for x in range(S):
            r, g, b = src[x, y]
            best, bd = PALETTE[0], 1 << 30
            for c in PALETTE:
                dr, dg, db = r - c[0], g - c[1], b - c[2]
                v = dr * dr + dg * dg + db * db
                if v < bd:
                    bd, best = v, c
            dst[x, y] = (0, 0, 0, 0) if best == KEY else (*best, 255)
    return out


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    stages = [draw_egg()] + [draw_stage(n) for n in range(2, 9)]
    prev = None
    for i, raw in enumerate(stages, start=1):
        img = quantise_and_cut(raw)
        path = os.path.join(OUT, f"stage{i}.png")
        img.save(path)
        px = img.load()
        opaque = sum(1 for y in range(S) for x in range(S) if px[x, y][3] == 255)
        partial = sum(1 for y in range(S) for x in range(S) if 0 < px[x, y][3] < 255)
        assert partial == 0, f"stage{i}: partial alpha would soften the edges"
        grew = "" if prev is None else ("  +%d px" % (opaque - prev))
        print(f"  stage{i}: {opaque:4d} opaque px{grew}")
        prev = opaque
    print(f"\n  {len(stages)} sprites -> {OUT}")
    print(f"  flash: {len(stages)} x 8192 = {len(stages) * 8192:,} B at 64x64 chroma_key")


if __name__ == "__main__":
    main()
