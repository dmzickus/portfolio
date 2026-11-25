#!/usr/bin/env python3
"""
Build the site and screenshot pages locally — a preview without waiting for a deploy.

    python tools/preview.py /                      # homepage, desktop + mobile
    python tools/preview.py / /ops-agent/ /projects/
    python tools/preview.py --compare /ops-agent/  # live site (before) next to local build (after)
    python tools/preview.py --full /resume/        # full-page instead of first screen
    python tools/preview.py --no-build /           # reuse the existing website/ build

Writes PNGs to preview/ (git-ignored) and prints their paths.
Needs: the build requirements, plus playwright and a Chromium/Chrome binary
(pip install playwright && python -m playwright install chromium, if no Chrome is installed).
"""
import argparse
import functools
import http.server
import shutil
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "preview"
LIVE = "https://dylanzickus.com"
SIZES = {"desktop": (1280, 900), "mobile": (390, 844)}
CHROMES = ["/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]


def serve(directory: Path) -> str:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=str(directory))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"


def slug(path: str) -> str:
    s = path.strip("/").replace("/", "_") or "home"
    return s.replace(".html", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=["/"])
    ap.add_argument("--compare", action="store_true", help="also screenshot the live site and stitch before|after")
    ap.add_argument("--full", action="store_true", help="full-page screenshots (default: first ~2 screens)")
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--only", choices=list(SIZES), help="just desktop or just mobile")
    args = ap.parse_args()

    if not args.no_build:
        r = subprocess.run([sys.executable, str(ROOT / "build" / "build.py"), "--no-pdf"], capture_output=True, text=True)
        print(r.stdout.strip().splitlines()[-1] if r.stdout else "", r.stderr.strip())
        if r.returncode:
            sys.exit("build failed")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("pip install playwright  (then: python -m playwright install chromium, if no Chrome is installed)")

    OUT.mkdir(exist_ok=True)
    local = serve(ROOT / "website")
    exe = next((c for c in CHROMES if Path(c).exists()), None)
    made = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe, args=["--no-sandbox"]) if exe else p.chromium.launch()
        sizes = {args.only: SIZES[args.only]} if args.only else SIZES
        for path in args.paths:
            for name, (w, h) in sizes.items():
                shots = []
                for label, base in ([("live", LIVE)] if args.compare else []) + [("local", local)]:
                    pg = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                    errors = []
                    pg.on("pageerror", lambda e: errors.append(str(e)))
                    try:
                        pg.goto(base + path, wait_until="networkidle", timeout=20000)
                    except Exception as e:  # live page may not exist yet
                        print(f"  {label} {path}: {e.__class__.__name__}")
                        pg.close()
                        continue
                    pg.wait_for_timeout(1800)  # let the logo animation finish
                    f = OUT / f"{slug(path)}-{name}-{label}.png"
                    if args.full:
                        pg.screenshot(path=str(f), full_page=True)
                    else:
                        pg.screenshot(path=str(f), clip={"x": 0, "y": 0, "width": w,
                                                         "height": min(h * 2, pg.evaluate("document.body.scrollHeight"))})
                    if errors:
                        print(f"  JS errors on {label} {path}: {errors}")
                    shots.append(f)
                    pg.close()
                if args.compare and len(shots) == 2:
                    made.append(stitch(shots, OUT / f"{slug(path)}-{name}-compare.png"))
                else:
                    made.extend(shots)
        browser.close()
    for f in made:
        print(f)


def stitch(files, dest):
    """Side by side: live (before) | local (after)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return files[-1]
    ims = [Image.open(f) for f in files]
    gap, bar = 24, 28
    w = sum(i.width for i in ims) + gap
    h = max(i.height for i in ims) + bar
    out = Image.new("RGB", (w, h), (15, 17, 23))
    d = ImageDraw.Draw(out)
    x = 0
    for im, label in zip(ims, ["BEFORE (live)", "AFTER (local)"]):
        d.text((x + 8, 8), label, fill=(79, 209, 197))
        out.paste(im, (x, bar))
        x += im.width + gap
    out.save(dest)
    return dest


if __name__ == "__main__":
    main()
