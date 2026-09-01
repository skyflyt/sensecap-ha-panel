"""Pip extras (2026-09-01): call-state overlays + the empty pod.

    ovl_headset.png  headband over the crown, two earcups, a boom mic to the
                     grille. Shown whenever Teams reports call=1.
    ovl_talk.png     three sound arcs off the right earcup. Call + mic LIVE.
    ovl_zip.png      a red zipper across the grille. Call + mic MUTED. This is
                     the mute indicator you will actually look at.
    pod_empty.png    the dock with nobody in it and a note card. Shown on every
                     pet surface while Pip is "on a trip" (person away).

All four are full 64x64 canvases so they stack on the sprite widgets at the
same x/y. Geometry is tuned to the L3/L4 head (x20-44, y19-35, eyes y26-29);
later levels get a per-level y nudge in the YAML if they need one.

Same rules as make-pet-stages.py: palette-quantised, binary alpha, nothing on
the canvas edge. Run with WINDOWS python. Writes ../images/pet/*.png.
"""
from __future__ import annotations
import os
from PIL import Image, ImageDraw

from importlib.machinery import SourceFileLoader
HERE = os.path.dirname(os.path.abspath(__file__))
stages = SourceFileLoader("stages", os.path.join(HERE, "make-pet-stages.py")).load_module()
canvas, check_and_save = stages.canvas, stages.check_and_save
INK, SHADE, DIM, GREY, MUTED, LIGHT = (stages.INK, stages.SHADE, stages.DIM,
                                       stages.GREY, stages.MUTED, stages.LIGHT)
AMBER, AMBER_D, RED, GREEN = stages.AMBER, stages.AMBER_D, stages.RED, stages.GREEN

# L3/L4 head frame the overlays are fitted to
HX0, HX1 = 20, 44          # head left/right
HY0 = 19                   # crown
GRILLE_Y = 33              # mouth line (just under the eyes at 26-29)


def draw_headset() -> Image.Image:
    img = canvas(); d = ImageDraw.Draw(img)
    # band: a 3px arc hugging the crown, INK edge with a MUTED highlight
    d.arc((HX0 - 4, HY0 - 3, HX1 + 4, HY0 + 17), 190, 350, fill=INK, width=4)
    d.arc((HX0 - 3, HY0 - 2, HX1 + 3, HY0 + 16), 195, 345, fill=MUTED, width=1)
    # earcups: chamfered blocks either side of the head, GREY face, INK rim
    for x0 in (HX0 - 5, HX1 + 1):
        box = (x0, HY0 + 5, x0 + 4, HY0 + 15)
        d.rectangle(box, fill=INK)
        d.rectangle((box[0] + 1, box[1] + 1, box[2] - 1, box[3] - 1), fill=GREY)
        d.point((box[0] + 1, box[1] + 1), fill=LIGHT)
    # boom from the right cup down to the grille, capsule mic at the end
    d.line([(HX1 + 2, HY0 + 15), (HX1 - 2, GRILLE_Y + 3), (HX1 - 6, GRILLE_Y + 3)], fill=INK, width=2)
    d.ellipse((HX1 - 9, GRILLE_Y + 1, HX1 - 5, GRILLE_Y + 5), fill=INK)
    d.point((HX1 - 8, GRILLE_Y + 2), fill=MUTED)
    return img


def draw_talk() -> Image.Image:
    img = canvas(); d = ImageDraw.Draw(img)
    # three sound arcs off the right side of the head, GREEN = live audio
    cx, cy = HX1 + 6, HY0 + 10
    for i, r in enumerate((4, 8, 12)):
        col = GREEN if i < 2 else INK
        d.arc((cx - r, cy - r, cx + r, cy + r), 300, 60, fill=col, width=2)
        if i == 2:
            d.arc((cx - r, cy - r, cx + r, cy + r), 305, 55, fill=GREEN, width=1)
    return img


def draw_zip() -> Image.Image:
    img = canvas(); d = ImageDraw.Draw(img)
    # zipper strap across the grille: INK slab, RED tape, LIGHT teeth
    x0, x1 = HX0 + 3, HX1 - 3
    d.rectangle((x0 - 1, GRILLE_Y - 2, x1 + 1, GRILLE_Y + 3), fill=INK)
    d.rectangle((x0, GRILLE_Y - 1, x1, GRILLE_Y + 2), fill=RED)
    for x in range(x0 + 1, x1, 3):
        d.point((x, GRILLE_Y), fill=LIGHT)
        d.point((x + 1, GRILLE_Y + 1), fill=LIGHT)
    # the pull tab, off to the right
    d.rectangle((x1 + 1, GRILLE_Y - 1, x1 + 3, GRILLE_Y + 4), fill=INK)
    d.point((x1 + 2, GRILLE_Y + 1), fill=MUTED)
    return img


def draw_pod_empty() -> Image.Image:
    img = canvas(); d = ImageDraw.Draw(img)
    # dock platform, low and wide, where his feet usually are
    stages.chamfer_rect(d, (14, 46, 50, 57), SHADE, ch=3)
    stages.bevel(d, (14, 46, 50, 57), ch=3)
    # cradle ring on the platform, dim (nobody is charging)
    d.ellipse((22, 44, 42, 52), fill=INK)
    d.ellipse((24, 45, 40, 51), fill=DIM)
    d.ellipse((28, 46, 36, 50), fill=SHADE)
    # a standby lamp, amber-dark, no spark
    stages.glow_dot(d, 46, 50, 2, core=AMBER_D, halo=INK, spark=False)
    # the note card, leaning against the cradle
    card = [(30, 24), (46, 22), (47, 40), (31, 42)]
    d.polygon(card, fill=LIGHT, outline=INK)
    for i, y in enumerate((28, 32, 36)):
        d.line([(33, y + i // 2), (43 - (4 if i == 2 else 0), y - 1 + i // 2)], fill=DIM)
    # a little pushpin
    d.ellipse((37, 20, 41, 24), fill=RED); d.point((38, 21), fill=LIGHT)
    return img


def main() -> None:
    for name, fn in (("ovl_headset", draw_headset), ("ovl_talk", draw_talk),
                     ("ovl_zip", draw_zip), ("pod_empty", draw_pod_empty)):
        n = check_and_save(name, fn())
        print(f"{name}: {n} opaque px")
    # proof sheet: overlays composited on stage4, 4x, for eyeballing
    base = Image.open(os.path.join(stages.OUT, "stage4.png")).convert("RGBA")
    sheet = Image.new("RGBA", (64 * 4 * 4, 64 * 4), (0x14, 0x16, 0x1A, 255))
    for i, ovl in enumerate(("ovl_headset", "ovl_talk", "ovl_zip", "pod_empty")):
        o = Image.open(os.path.join(stages.OUT, f"{ovl}.png")).convert("RGBA")
        comp = base.copy() if ovl != "pod_empty" else Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        if ovl == "ovl_talk" or ovl == "ovl_zip":
            comp.alpha_composite(Image.open(os.path.join(stages.OUT, "ovl_headset.png")).convert("RGBA"))
        comp.alpha_composite(o)
        sheet.paste(comp.resize((256, 256), Image.NEAREST), (i * 256, 0))
    sheet.save(os.path.join(HERE, "proof-extras.png"))
    print("proof: tools/proof-extras.png")


if __name__ == "__main__":
    main()
