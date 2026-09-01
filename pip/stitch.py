"""Pip time-lapse: stitch today's frames into a GIF. Runs nightly (23:30) via
shell_command.pip_stitch, or by hand: python3 stitch.py [YYYY-MM-DD].

Output: /config/www/pip/<date>.gif and latest.gif, served by HA at
http://<ha>:8123/local/pip/<date>.gif. Frames older than 7 days and GIFs
older than 30 days are pruned. A day with fewer than 4 frames is skipped.
"""
import os, sys, shutil, time
from datetime import datetime

FRAMES = "/config/pip/frames"
OUT = "/config/www/pip"
FRAME_MS = 160          # ~6 fps: a 10-hour day of 60 frames plays in ~10 s
HOLD_LAST_MS = 1200

def prune() -> None:
    now = time.time()
    if os.path.isdir(FRAMES):
        for d in os.listdir(FRAMES):
            p = os.path.join(FRAMES, d)
            if os.path.isdir(p) and now - os.path.getmtime(p) > 7 * 86400:
                shutil.rmtree(p, ignore_errors=True)
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            p = os.path.join(OUT, f)
            if f.endswith(".gif") and f != "latest.gif" and now - os.path.getmtime(p) > 30 * 86400:
                os.remove(p)

def main() -> int:
    from PIL import Image
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    d = os.path.join(FRAMES, day)
    if not os.path.isdir(d):
        print("no frames for", day); prune(); return 0
    files = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    if len(files) < 4:
        print("too few frames:", len(files)); prune(); return 0
    frames = [Image.open(os.path.join(d, f)).convert("RGB").quantize(colors=128, method=Image.MEDIANCUT)
              for f in files]
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, day + ".gif")
    durations = [FRAME_MS] * (len(frames) - 1) + [HOLD_LAST_MS]
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True, disposal=1)
    shutil.copyfile(out, os.path.join(OUT, "latest.gif"))
    print("gif", out, len(frames), "frames", os.path.getsize(out) // 1024, "KB")
    prune()
    return 0

if __name__ == "__main__":
    sys.exit(main())
