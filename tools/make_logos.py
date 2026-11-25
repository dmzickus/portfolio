#!/usr/bin/env python3
"""
Generate the Spotty Connection logo set into build/static/brand/.

    python tools/make_logos.py path/to/SchibstedGrotesk-700.ttf

Only needed when the logo changes; the generated SVG/PNG files are committed.
Needs: fonttools, cairosvg (pip install fonttools cairosvg).

The mark: a Wi-Fi symbol whose outer arc has dropped out in the middle.
"""
import math
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = Path(__file__).resolve().parent.parent / "build" / "static" / "brand"
NAVY, TEAL, AMBER, INK, DIM = "#1b2440", "#4fd1c5", "#f6ad55", "#eef1f7", "#4a5781"

# ── mark geometry (100×100 box) ─────────────────────────────────────────
CX, CY = 50, 80
SPAN = 46            # degrees either side of vertical
STROKE = 9.5


def pt(r, deg):
    a = math.radians(deg - 90)          # 0deg = straight up
    return CX + r * math.cos(a), CY + r * math.sin(a)


def arc(r, a0, a1):
    x0, y0 = pt(r, a0)
    x1, y1 = pt(r, a1)
    large = 1 if abs(a1 - a0) > 180 else 0
    return f"M{x0:.2f} {y0:.2f}A{r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}"


def mark_paths(c_arc, c_dot, c_drop=None):
    """Return the SVG elements of the mark. c_drop: colour for the faint
    'ghost' of the dropped segment (None = omitted)."""
    gap = 15
    parts = [
        f'<circle cx="{CX}" cy="{CY - 1}" r="6.5" fill="{c_dot}"/>',
        f'<path class="arc a1" d="{arc(22, -SPAN, SPAN)}"/>',
        f'<path class="arc a2" d="{arc(39, -SPAN, SPAN)}"/>',
        f'<path class="arc a3l" d="{arc(56, -SPAN, -gap)}"/>',
        f'<path class="arc a3r" d="{arc(56, gap, SPAN)}"/>',
    ]
    if c_drop:
        parts.insert(1, f'<path d="{arc(56, -gap + 7, gap - 7)}" stroke="{c_drop}" '
                        f'stroke-width="{STROKE}" stroke-linecap="round" fill="none"/>')
    g = (f'<g fill="none" stroke="{c_arc}" stroke-width="{STROKE}" '
         f'stroke-linecap="round">{"".join(p for p in parts if "arc" in p)}</g>')
    others = "".join(p for p in parts if "arc" not in p)
    return others + g


# ── wordmark from the font ──────────────────────────────────────────────

def text_path(font_path, text, size, tracking=-0.02):
    font = TTFont(font_path)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    scale = size / upm
    pen = SVGPathPen(gs)
    x = 0.0
    for ch in text:
        gname = cmap[ord(ch)]
        tp = TransformPen(pen, (scale, 0, 0, -scale, x, 0))
        gs[gname].draw(tp)
        x += gs[gname].width * scale + tracking * size
    return pen.getCommands(), x - tracking * size


def svg(w, h, body, bg=None):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}">{rect}{body}</svg>\n')


def main():
    font = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)

    # mark only
    for name, ca, cd, drop, bg in [
        ("mark", TEAL, AMBER, None, None),
        ("mark-mono-light", INK, INK, None, None),
        ("mark-mono-dark", NAVY, NAVY, None, None),
    ]:
        (OUT / f"{name}.svg").write_text(svg(100, 100, mark_paths(ca, cd, drop), bg))

    # favicon / app tile: mark on a navy rounded square
    tile = (f'<rect width="100" height="100" rx="22" fill="{NAVY}"/>'
            f'<g transform="translate(9 4) scale(.82)">{mark_paths(TEAL, AMBER)}</g>')
    (OUT / "favicon.svg").write_text(svg(100, 100, tile))

    # primary lockup: mark + "spotty connection" + "dylan zickus"
    word, ww = text_path(font, "spotty connection", 46)
    sub, sw = text_path(font, "dylan zickus", 21, tracking=0.01)
    W = int(108 + ww + 8)
    H = 100

    def lockup(ca, cd, ct, cs):
        return (f'<g transform="translate(0 2) scale(.96)">{mark_paths(ca, cd)}</g>'
                f'<path transform="translate(104 60)" fill="{ct}" d="{word}"/>'
                f'<path transform="translate(106 88)" fill="{cs}" d="{sub}"/>')

    (OUT / "logo-primary.svg").write_text(svg(W, H, lockup(TEAL, AMBER, INK, "#a9b3cc")))
    (OUT / "logo-primary-on-navy.svg").write_text(
        svg(W + 40, H + 40, f'<g transform="translate(20 20)">{lockup(TEAL, AMBER, INK, "#a9b3cc")}</g>', NAVY))
    (OUT / "logo-primary-mono-light.svg").write_text(svg(W, H, lockup(INK, INK, INK, INK)))
    (OUT / "logo-primary-mono-dark.svg").write_text(svg(W, H, lockup(NAVY, NAVY, NAVY, NAVY)))

    # secondary lockup: compact, single line, for the site header
    word2, w2 = text_path(font, "spotty connection", 30)
    W2 = int(58 + w2 + 4)
    sec = (f'<g transform="translate(0 0) scale(.5)">{mark_paths(TEAL, AMBER)}</g>'
           f'<path transform="translate(56 37)" fill="{INK}" d="{word2}"/>')
    (OUT / "logo-secondary.svg").write_text(svg(W2, 50, sec))

    # PNGs: apple touch icon + social preview card
    import cairosvg
    cairosvg.svg2png(bytestring=svg(100, 100, tile).encode(), write_to=str(OUT / "apple-touch-icon.png"),
                     output_width=180, output_height=180)
    og_scale = 1.55
    og = (f'<rect width="1200" height="630" fill="{NAVY}"/>'
          f'<g transform="translate({600 - W * og_scale / 2:.0f} 240) scale({og_scale})">'
          f'{lockup(TEAL, AMBER, INK, "#a9b3cc")}</g>')
    cairosvg.svg2png(bytestring=svg(1200, 630, og).encode(), write_to=str(OUT / "og-card.png"))
    print("wrote", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
