#!/usr/bin/env python3
"""
Static site generator for dylanzickus.com project pages.

Usage:
    python build/build.py

Reads markdown + frontmatter from content/, renders through the shared
template in build/page_template.html (build/home_template.html for the
homepage), and writes static HTML to website/. Also copies each section's
images/ folder to the matching spot under website/.

Requires: pip install markdown pyyaml
"""
import html
import os
import re
import shutil
import sys
from pathlib import Path

try:
    import yaml
    import markdown as md
except ImportError:
    sys.exit(
        "Missing dependencies. Run:\n"
        "    python -m pip install markdown pyyaml"
    )

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
BUILD = ROOT / "build"
OUT = ROOT / "website"

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?", re.DOTALL)
MD_LINK_RE = re.compile(r'href="(?:\./)?([\w\-]+)\.md"')


def parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, text[m.end():]


LEADING_H1_RE = re.compile(r"\A\s*#\s+[^\n]+\n+")


def strip_leading_h1(body: str) -> str:
    """The page template already renders `title` as the big hero H1, so drop
    a redundant leading '# ...' line from the markdown body if present."""
    return LEADING_H1_RE.sub("", body, count=1)


def render_markdown(body: str) -> str:
    out = md.markdown(
        body,
        extensions=["fenced_code", "tables", "sane_lists", "attr_list"],
    )
    # internal links between markdown docs (e.g. "./jellyfin.md") -> ".html"
    out = MD_LINK_RE.sub(r'href="\1.html"', out)
    return out


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def relhref(from_dir: Path, to_path: Path) -> str:
    rel = os.path.relpath(to_path, start=from_dir)
    return rel.replace(os.sep, "/")


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_template(name: str) -> str:
    return read_file(BUILD / name)


def fill(template: str, values: dict) -> str:
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    return out


# ── Discover content ─────────────────────────────────────────────────────

def discover_sections():
    sections = []
    for d in sorted(CONTENT.iterdir()):
        if not d.is_dir():
            continue
        index_md = d / "index.md"
        if not index_md.exists():
            print(f"  WARN: {d} has no index.md, skipping")
            continue
        fm, body = parse_frontmatter(read_file(index_md))
        fm.setdefault("order", 999)

        subpages = []
        for f in sorted(d.glob("*.md")):
            if f.name == "index.md":
                continue
            sfm, sbody = parse_frontmatter(read_file(f))
            subpages.append({"slug": f.stem, "fm": sfm, "body": sbody})

        sections.append({
            "slug": d.name,
            "fm": fm,
            "body": body,
            "subpages": subpages,
            "images_dir": d / "images",
        })
    sections.sort(key=lambda s: s["fm"].get("order", 999))
    return sections


# ── Shared bits: nav, pills, tags, cards ────────────────────────────────

def build_nav_links(sections, from_dir: Path, active_slug: str) -> str:
    items = []
    home_class = ' class="active"' if active_slug == "" else ""
    home_href = relhref(from_dir, OUT / "index.html")
    items.append(f'    <li><a href="{home_href}"{home_class}>Home</a></li>')
    for sec in sections:
        label = esc(sec["fm"].get("nav_label", sec["fm"]["title"]))
        href = relhref(from_dir, OUT / sec["slug"] / "index.html")
        active = " class=\"active\"" if sec["slug"] == active_slug else ""
        items.append(f'    <li><a href="{href}"{active}>{label}</a></li>')
    return "\n".join(items)


def build_pills(pills) -> str:
    if not pills:
        return ""
    spans = "\n".join(f'      <span class="pill">{esc(p)}</span>' for p in pills)
    return f'    <div class="hero-pills">\n{spans}\n    </div>'


def build_tags(tags) -> str:
    if not tags:
        return ""
    return "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)


def build_breadcrumb(from_dir: Path, crumbs) -> str:
    # crumbs: list of (label, path_or_None). None path = current page (no link)
    parts = []
    for i, (label, path) in enumerate(crumbs):
        if path is not None:
            parts.append(f'<a href="{relhref(from_dir, path)}">{esc(label)}</a>')
        else:
            parts.append(f'<span class="current">{esc(label)}</span>')
        if i < len(crumbs) - 1:
            parts.append('<span class="sep">/</span>')
    return f'<div class="breadcrumb">\n  {" ".join(parts)}\n</div>'


def collection_card(href: str, fm: dict) -> str:
    icon = esc(fm.get("icon", "\U0001f527"))
    icon_color = fm.get("icon_color", "")
    icon_class = f' {icon_color}' if icon_color else ""
    badge = fm.get("badge", "")
    badge_html = f'<span class="ccard-count">{esc(badge)}</span>' if badge else ""
    tags_html = build_tags(fm.get("tags"))
    return f'''    <a class="collection-card" href="{href}">
      <div class="ccard-top">
        <div class="ccard-icon{icon_class}">{icon}</div>
        {badge_html}
      </div>
      <div class="ccard-title">{esc(fm.get("card_title", fm["title"]))}</div>
      <div class="ccard-desc">{esc(fm.get("description", ""))}</div>
      <div class="ccard-tags">{tags_html}</div>
      <div class="ccard-arrow">View page →</div>
    </a>'''


# ── Page rendering ──────────────────────────────────────────────────────

def render_page(*, sections, active_slug, out_path: Path, fm: dict, body_html: str,
                 crumbs, section_grid_html=""):
    out_dir = out_path.parent
    title = fm["title"]
    tpl = load_template("page_template.html")
    values = {
        "TITLE": esc(f'{title} — Dylan Zickus'),
        "META_DESCRIPTION": esc(fm.get("description", "")),
        "ASSET_PREFIX": relhref(out_dir, OUT) + "/" if relhref(out_dir, OUT) != "." else "",
        "HOME_HREF": relhref(out_dir, OUT / "index.html"),
        "NAV_LINKS": build_nav_links(sections, out_dir, active_slug),
        "BREADCRUMB": build_breadcrumb(out_dir, crumbs) if crumbs else "",
        "EYEBROW": esc(fm.get("eyebrow", f'dylanzickus.com  /  {title}')),
        "HEADING": fm.get("heading_html", esc(title)),
        "DESCRIPTION": esc(fm.get("description", "")),
        "PILLS": build_pills(fm.get("pills")),
        "BODY": body_html,
        "SECTION_GRID": section_grid_html,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(fill(tpl, values), encoding="utf-8")


def build_section(sections, sec):
    slug = sec["slug"]
    fm = sec["fm"]
    out_dir = OUT / slug
    index_out = out_dir / "index.html"

    section_grid_html = ""
    if sec["subpages"]:
        cards = "\n".join(
            collection_card(f'{sp["slug"]}.html', sp["fm"])
            for sp in sec["subpages"]
        )
        section_grid_html = (
            '\n  <div class="section-header"><span class="section-label">'
            'Pages in this section</span></div>\n'
            f'  <div class="collection-grid">\n{cards}\n  </div>'
        )

    render_page(
        sections=sections,
        active_slug=slug,
        out_path=index_out,
        fm=fm,
        body_html=render_markdown(strip_leading_h1(sec["body"])),
        crumbs=[("dylanzickus.com", OUT / "index.html"), (fm["title"], None)],
        section_grid_html=section_grid_html,
    )

    for sp in sec["subpages"]:
        sp_out = out_dir / f'{sp["slug"]}.html'
        render_page(
            sections=sections,
            active_slug=slug,
            out_path=sp_out,
            fm=sp["fm"],
            body_html=render_markdown(strip_leading_h1(sp["body"])),
            crumbs=[
                ("dylanzickus.com", OUT / "index.html"),
                (fm["title"], index_out),
                (sp["fm"]["title"], None),
            ],
        )

    if sec["images_dir"].exists() and any(sec["images_dir"].iterdir()):
        dest = out_dir / "images"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(sec["images_dir"], dest)


# ── Homepage ─────────────────────────────────────────────────────────────

def build_homepage(sections, home_cfg):
    tpl = load_template("home_template.html")
    hero = home_cfg.get("hero", {})

    collection_cards = "\n".join(
        collection_card(relhref(OUT, OUT / s["slug"] / "index.html"), s["fm"])
        for s in sections
    )

    other_builds = home_cfg.get("other_builds", [])
    other_cards = []
    for item in other_builds:
        other_cards.append(f'''    <div class="project-card">
      <div class="pcard-top">
        <span class="pcard-title">{esc(item["title"])}</span>
        <span class="status-badge {esc(item.get("status", "wip"))}">{esc(item.get("status_label", ""))}</span>
      </div>
      <div class="pcard-desc">{esc(item.get("description", ""))}</div>
    </div>''')

    stack = home_cfg.get("core_stack", [])
    stack_items = "\n".join(
        f'''    <div class="stack-item">
      <div class="stack-key">{esc(i["key"])}</div>
      <div class="stack-val">{esc(i["value"])}</div>
    </div>''' for i in stack
    )

    pills = "\n".join(f'      <span class="pill">{esc(p)}</span>' for p in hero.get("pills", []))

    values = {
        "NAV_LINKS": build_nav_links(sections, OUT, ""),
        "EYEBROW": esc(hero.get("eyebrow", "")),
        "HEADING": hero.get("heading_html", esc(hero.get("heading", ""))),
        "DESCRIPTION": esc(hero.get("description", "")),
        "PILLS": pills,
        "COLLECTION_CARDS": collection_cards,
        "OTHER_BUILD_CARDS": "\n".join(other_cards),
        "STACK_ITEMS": stack_items,
    }
    (OUT / "index.html").write_text(fill(tpl, values), encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    print(f"Building site from {CONTENT} -> {OUT}")

    home_yaml = CONTENT / "home.yaml"
    if not home_yaml.exists():
        sys.exit(f"Missing {home_yaml}")
    home_cfg = yaml.safe_load(read_file(home_yaml)) or {}

    sections = discover_sections()
    print(f"  Found {len(sections)} section(s): {', '.join(s['slug'] for s in sections)}")

    OUT.mkdir(parents=True, exist_ok=True)

    assets_dir = OUT / "assets"
    assets_dir.mkdir(exist_ok=True)
    shutil.copyfile(BUILD / "style.css", assets_dir / "style.css")

    build_homepage(sections, home_cfg)
    for sec in sections:
        build_section(sections, sec)

    print("Done.")


if __name__ == "__main__":
    main()
