"""Pip time-lapse: grab one frame of the panel. Runs inside the HA core
container via shell_command.pip_capture every 10 minutes (07-22, PC unlocked).

Install as /homeassistant/pip/capture.py. Frames land in
/config/pip/frames/<YYYY-MM-DD>/<HHMM>.png at 240x240 (a quarter of the
pixels, GIF-friendly). Silent on failure: a missed frame is not an incident.
"""
import io, os, sys, time, urllib.request
from datetime import datetime

PANEL = "http://CHANGE_ME_panel_ip:8080/screenshot"   # your panel, e.g. http://192.168.4.1:8080 on its fallback AP
ROOT = "/config/pip/frames"

def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        print("Pillow missing"); return 1
    try:
        data = urllib.request.urlopen(PANEL, timeout=15).read()
    except Exception as e:  # panel asleep, rebooting, whatever — skip
        print("skip:", e); return 0
    now = datetime.now()
    d = os.path.join(ROOT, now.strftime("%Y-%m-%d"))
    os.makedirs(d, exist_ok=True)
    im = Image.open(io.BytesIO(data)).convert("RGB").resize((240, 240), Image.LANCZOS)
    path = os.path.join(d, now.strftime("%H%M") + ".png")
    im.save(path, optimize=True)
    print("frame", path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
