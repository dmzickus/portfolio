#!/usr/bin/env python3
"""
Static site generator for dylanzickus.com.

    python build/build.py            # build website/ from content/
    python build/build.py --strict   # also fail on content warnings (CI uses this)
    python build/build.py --no-pdf   # skip resume PDFs (no WeasyPrint needed)

Content model (see README.md and content/_template/index.md):
  content/site.yaml         site name, intro, links, featured projects
  content/resume.yaml       resume (HTML page + one PDF per focus)
  content/<slug>/index.md   a project (has `status`) or a plain page (`type: page`)
  content/<slug>/<sub>.md   optional sub-pages of a project
  content/<slug>/images/    images, copied as-is
Folders starting with "_" are ignored.
"""
import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

try:
    import markdown as md
    import yaml
except ImportError:
    sys.exit("Missing dependencies. Run:  python -m pip install -r build/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
BUILD = ROOT / "build"
STATIC = BUILD / "static"
TEMPLATES = BUILD / "templates"
OUT = ROOT / "website"
SITE_URL = "https://dylanzickus.com"

STATUSES = {
    # key: (label, bars lit, description used in the legend)
    "live":     ("Live", 4, "Running and in use"),
    "building": ("Building", 3, "Actively being built"),
    "dormant":  ("Dormant", 2, "Works, but not in use"),
    "retired":  ("Retired", 1, "Taken down or replaced"),
    "planned":  ("Planned", 0, "An idea, not built yet"),
}
AREAS = {
    "homelab":  "Homelab",
    "embedded": "Embedded & smart home",
    "software": "Software",
    "other":    "Other",
}
FOCUSES = {"infra": "Infrastructure", "embedded": "Embedded", "fullstack": "Full-stack"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?", re.DOTALL)
LEADING_H1_RE = re.compile(r"\A\s*#\s+[^\n]+\n+")
MD_LINK_RE = re.compile(r'href="(?:\./)?([\w\-]+)\.md"')

WARNINGS: list[str] = []


def warn(msg):
    WARNINGS.append(msg)
    print(f"  WARN: {msg}")


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def parse(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def render_md(body: str) -> str:
    body = LEADING_H1_RE.sub("", body, count=1)
    out = md.markdown(body, extensions=["fenced_code", "tables", "sane_lists", "attr_list", "md_in_html"])
    return MD_LINK_RE.sub(r'href="\1.html"', out)


def inline_md(text: str) -> str:
    """Markdown for one-liners (links, emphasis, code) without a wrapping <p>."""
    out = md.markdown(str(text or ""))
    return re.sub(r"\A<p>(.*)</p>\Z", r"\1", out.strip(), flags=re.DOTALL)


def parse_date(v):
    """'2026-11', '2026-11-17', '2026', or a date -> (sortable tuple, label)."""
    if v is None:
        return None
    if isinstance(v, (dt.date, dt.datetime)):
        return (v.year, v.month, v.day), f"{MONTHS[v.month - 1]} {v.year}"
    s = str(v).strip()
    m = re.fullmatch(r"(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?", s)
    if not m:
        warn(f"unparseable date {s!r}")
        return None
    y, mo, d = int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0)
    return (y, mo, d), (f"{MONTHS[mo - 1]} {y}" if mo else str(y))


def month_label(key):
    return MONTHS[key[1] - 1] if key[1] else ""


# ── components ──────────────────────────────────────────────────────────

AREA_ACCENT = {"homelab": "teal", "embedded": "amber", "software": "blue", "other": "pink"}
TAG_COLORS: dict[str, str] = {}   # filled from site.yaml: tag (lowercase) -> colour name


def bars(status: str) -> str:
    _, lit, _ = STATUSES.get(status, STATUSES["planned"])
    spans = "".join(f'<i class="{"on" if i < lit else "off"}"></i>' for i in range(4))
    return f'<span class="bars bars-{status}" aria-hidden="true">{spans}</span>'


def badge(status: str) -> str:
    label = STATUSES.get(status, STATUSES["planned"])[0]
    marquee = SHOWTIME_LABELS.get(status, label)
    return (f'<span class="badge badge-{status}">{bars(status)}<span class="house-only">{label}</span>'
            f'<span class="show-only">{marquee}</span></span>')


# Showtime mode renames statuses like a theater marquee.
SHOWTIME_LABELS = {"live": "Now showing", "building": "Coming soon", "dormant": "Intermission",
                   "retired": "Final curtain", "planned": "In production"}


def tag_list(tags, cls="tags") -> str:
    if not tags:
        return ""
    return f'<ul class="{cls}">' + "".join(
        f'<li class="tag tag-{TAG_COLORS.get(t.lower(), "grey")}">{esc(t)}</li>' for t in tags) + "</ul>"


def cover(p, cls="") -> str:
    """Project image: images/cover.* if present, otherwise a labelled placeholder."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        if (p["dir"] / "images" / f"cover.{ext}").exists():
            return (f'<div class="cover {cls}"><img src="/{p["slug"]}/images/cover.{ext}" '
                    f'alt="{esc(p.get("cover_alt", p["title"]))}" loading="lazy"></div>')
    accent = AREA_ACCENT.get(p["area"], "teal")
    return (f'<div class="cover cover-ph ph-{accent} {cls}" role="img" aria-label="Photo coming soon">'
            f'<span class="ph-icon" aria-hidden="true">{esc(p.get("icon", "🔧"))}</span>'
            f'<span class="ph-note">photo coming soon</span></div>')


def data_attrs(p, extra_text="") -> str:
    search = " ".join([p["title"], p.get("summary", ""), " ".join(p.get("tags", [])),
                       AREAS.get(p["area"], ""), extra_text]).lower()
    tags = "|".join(t.lower() for t in p.get("tags", []))
    return (f'data-area="{esc(p["area"])}" data-status="{esc(p["status"])}" '
            f'data-tags="{esc(tags)}" data-search="{esc(search)}"')


def filter_bar(projects) -> str:
    areas = "".join(
        f'<button type="button" data-filter="area" data-value="{k}" aria-pressed="false">{v}</button>'
        for k, v in AREAS.items() if any(p["area"] == k for p in projects))
    statuses = "".join(
        f'<button type="button" data-filter="status" data-value="{k}" aria-pressed="false" title="{esc(d)}">'
        f'{bars(k)}{label}</button>'
        for k, (label, _, d) in STATUSES.items() if any(p["status"] == k for p in projects))
    return f'''<div class="filters" data-filters>
  <label class="search"><span class="visually-hidden">Filter by tag or word</span>
    <input type="search" placeholder="Filter by tag or word… (docker, mqtt, esp32)" data-search-input autocomplete="off"></label>
  <div class="filter-row" role="group" aria-label="Area">{areas}</div>
  <div class="filter-row" role="group" aria-label="Status">{statuses}</div>
  <p class="filter-empty" data-empty hidden>Nothing matches. <button type="button" data-clear>Clear filters</button></p>
</div>'''


def mini_card(p) -> str:
    return f'''<li class="mcard"><a href="/{p["slug"]}/">{cover(p, "cover-thumb")}
      <span class="mcard-title">{bars(p["status"])}{esc(p.get("short_title", p["title"]))}</span></a></li>'''


# ── page shell ─────────────────────────────────────────────────────────

NAV = [("/projects/", "Projects"), ("/resume/", "Resume"), ("/about/", "About")]


def shell(site, *, title, desc, body, path, body_class="", og_type="website", crumb=""):
    tpl = read(TEMPLATES / "base.html")
    nav = "".join(
        f'<a href="{h}"{" aria-current=\"page\"" if path.startswith(h) else ""}>{l}</a>' for h, l in NAV)
    if crumb:
        nav = nav.replace('<a href="/projects/" aria-current="page">Projects</a>',
                          f'<a href="/projects/">Projects</a><span class="nav-sep">/</span>'
                          f'<span class="nav-here">{esc(crumb)}</span>')
    full_title = title if title == site["name"] else f"{title} · {site['name']}"
    vals = {
        "TITLE": esc(full_title),
        "DESC": esc(desc or site["description"]),
        "CANONICAL": esc(SITE_URL + path),
        "OG_TYPE": og_type,
        "NAV": nav,
        "BODY": body,
        "BODY_CLASS": body_class,
        "SOCIAL": social_links(site),
        "YEAR": str(dt.date.today().year),
    }
    out = tpl
    for k, v in vals.items():
        out = out.replace("{{" + k + "}}", v)
    return out


ICONS = {
    "github": '<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/>',
    "email": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 6L2 7"/>',
    "resume": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8M8 9h2"/>',
}


def social_links(site) -> str:
    out = []
    for l in site["links"]:
        ic = ICONS.get(l.get("icon", ""), "")
        svg = (f'<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" '
               f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ic}</svg>') if ic else ""
        out.append(f'<a href="{esc(l["url"])}">{svg}<span>{esc(l["label"])}</span></a>')
    return "".join(out)


def write(path: str, text: str):
    p = OUT / path.lstrip("/")
    if path.endswith("/"):
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def latest_key(p):
    """Most recent timeline date (or start) — 'what's been happening' order for the carousel."""
    keys = [parse_date(e.get("date"))[0] for e in p["timeline"] if parse_date(e.get("date"))]
    today = dt.date.today()
    keys = [k for k in keys if k[:2] <= (today.year, today.month)] or keys
    return max(keys) if keys else (p["_start"] or ((0, 0, 0), ""))[0]


# ── homepage ──────────────────────────────────────────────────────────

def build_home(site, projects):
    visible = [p for p in projects if not p.get("hidden")]
    # carousel: chronological by start date, oldest → newest; the page opens scrolled to the newest
    order = sorted(visible, key=lambda p: ((p["_start"] or ((9999, 0, 0), ""))[0], p["title"]))
    years = []
    slides = []
    for p in order:
        y = (p["_start"] or ((0, 0, 0), ""))[0][0]
        if y and y not in years:
            years.append(y)
        slides.append(f'''<li class="slide" {data_attrs(p)} data-year="{y}">
        <a href="/{p["slug"]}/">
          <h3>{esc(p.get("short_title", p["title"]))}</h3>
          <div class="slide-card">
            {cover(p, "cover-slide")}
            <p class="slide-desc">{esc(p.get("summary", ""))}</p>
            <p class="slide-meta">{badge(p["status"])}<span>{esc(project_date_range(p))}</span></p>
          </div>
        </a>
      </li>''')
    scrub = "".join(f'<button type="button" data-year-jump="{y}">{y}</button>' for y in years)
    links = "".join(f'<li><a href="{esc(l["url"])}">{esc(l["label"])}<span class="arrow" aria-hidden="true">→</span></a></li>'
                    for l in site["hero_links"])
    body = f'''
<section class="home-hero">
  <div class="hero-bg" aria-hidden="true"></div>
  <button type="button" class="hero-mark" aria-label="Poke the signal">{read(STATIC / "brand" / "mark.svg")}</button>
  <h1>{esc(site["person"])}</h1>
  <p class="hero-tag show-only">Now showing. Mostly.</p>
  <p class="home-intro">{inline_md(site["intro"])}</p>
  <ul class="home-links">{links}</ul>
</section>

<section class="carousel-wrap" aria-labelledby="carousel-h">
  <div class="section-header"><h2 class="section-label" id="carousel-h">Project timeline</h2></div>
  <div class="carousel" data-carousel>
    <button type="button" class="car-btn car-prev" data-car-prev aria-label="Earlier projects"></button>
    <div class="car-viewport" data-car-viewport tabindex="0" aria-label="Projects, oldest to newest. Scroll sideways.">
      <ol class="car-track" data-car-track>{"".join(slides)}</ol>
    </div>
    <button type="button" class="car-btn car-next" data-car-next aria-label="Later projects"></button>
  </div>
  <div class="scrubber" data-scrubber aria-label="Jump to year">{scrub}<span class="scrub-signal" aria-hidden="true">{bars("live")}</span></div>
</section>

<section class="home-social">{social_links(site)}</section>'''
    write("/", shell(site, title=site["name"], desc=site["description"], body=body, path="/", body_class="home"))


# ── projects: vertical timeline ───────────────────────────────────────

def build_projects_index(site, projects):
    visible = [p for p in projects if not p.get("hidden")]
    by_year = {}
    for p in visible:
        y = (p["_start"] or ((0, 0, 0), ""))[0][0]
        by_year.setdefault(y, []).append(p)
    groups = []
    for y in sorted(by_year, reverse=True):
        rows = []
        for p in sorted(by_year[y], key=lambda p: (latest_key(p), p["title"]), reverse=True):
            rows.append(f'''<li class="vrow" {data_attrs(p)}>
          <a class="vrow-img" href="/{p["slug"]}/" tabindex="-1" aria-hidden="true">{cover(p, "cover-thumb")}</a>
          <div class="vrow-body">
            <h3><a href="/{p["slug"]}/">{esc(p["title"])}</a></h3>
            <p class="vrow-meta"><span>{esc(project_date_range(p))}</span>{badge(p["status"])}</p>
            {tag_list(p["tags"][:5])}
            <p class="vrow-desc">{esc(p.get("summary", ""))}</p>
          </div>
        </li>''')
        groups.append(f'<section class="vyear" data-group><h2 class="vyear-label">{y or "—"}</h2><ol>{"".join(rows)}</ol></section>')
    legend = "".join(f'<li>{badge(k)}<span>{esc(d)}</span></li>' for k, (_, _, d) in STATUSES.items())
    body = f'''
<section class="page-top">
  <h1>Projects</h1>
  <p class="page-intro">Everything I've built, newest first. The signal bars show whether it's still running.</p>
  <ul class="legend">{legend}</ul>
  {filter_bar(visible)}
</section>
<section class="vtimeline" data-list>{"".join(groups)}</section>'''
    write("/projects/", shell(site, title="Projects", desc="Homelab, embedded and software projects by Dylan Zickus.",
                              body=body, path="/projects/", body_class="projects"))


# ── project pages ─────────────────────────────────────────────────────

H2_SPLIT = re.compile(r"(?=<h2[ >])")


def sectioned(body_html: str, words: int) -> str:
    """Long write-ups: every <h2> section becomes a collapsible block (first two open)."""
    parts = H2_SPLIT.split(body_html)
    if words < 700 or len(parts) < 4:
        return body_html
    out = [parts[0]]
    for i, s in enumerate(parts[1:]):
        m = re.match(r"<h2[^>]*>(.*?)</h2>", s, re.S)
        title, rest = (m.group(1), s[m.end():]) if m else ("", s)
        out.append(f'<details class="sec"{" open" if i < 2 else ""}><summary><h2>{title}</h2></summary>{rest}</details>')
    return "".join(out)


def build_project(site, p, projects):
    log = ""
    if p["timeline"]:
        evs = sorted(p["timeline"], key=lambda e: (parse_date(e.get("date")) or ((0, 0, 0), ""))[0])
        log = '<ol class="changelog">' + "".join(
            f'<li><time>{esc((parse_date(e.get("date")) or (None, ""))[1])}</time> · {inline_md(e.get("text", ""))}</li>'
            for e in evs) + "</ol>"

    facts = [badge(p["status"])]
    if project_date_range(p):
        facts.append(f"<span>{esc(project_date_range(p))}</span>")
    if p.get("role"):
        facts.append(f"<span>{esc(p['role'])}</span>")
    links = "".join(f'<a class="btn" href="{esc(l["url"])}">{esc(l["label"])} ↗</a>' for l in p.get("links", []))
    hl = ""
    if p.get("highlights"):
        hl = '<ul class="highlights">' + "".join(f"<li>{esc(h)}</li>" for h in p["highlights"]) + "</ul>"
    stack = (f'<p class="stack"><span class="label">Stack</span> {esc(" · ".join(p["stack"]))}</p>'
             if p.get("stack") else "")

    sub_nav = ""
    if p["subpages"]:
        sub_nav = ('<h2 class="small-h">More on this project</h2><ul class="sublist">'
                   + "".join(f'<li><a href="/{p["slug"]}/{s["slug"]}.html">{esc(s.get("title", s["slug"]))}</a> '
                             f'<span>{esc(s.get("summary", ""))}</span></li>' for s in p["subpages"]) + "</ul>")

    tags = {t.lower() for t in p["tags"]}
    rel = sorted((q for q in projects if q is not p and not q.get("hidden")),
                 key=lambda q: (-(len(tags & {t.lower() for t in q["tags"]}) + (2 if q["area"] == p["area"] else 0)),
                                q["title"]))[:3]
    words = len(re.findall(r"\w+", p["body"]))
    body = f'''
<article class="project">
  {cover(p, "cover-hero")}
  <h1>{esc(p["title"])}</h1>
  <p class="project-facts">{"".join(facts)}</p>
  {tag_list(p["tags"])}
  <p class="project-summary">{esc(p.get("summary", ""))}</p>
  {hl}
  {stack}
  {f'<details class="evolved" open><summary>How it evolved ({len(p["timeline"])})</summary>{log}</details>' if log else ""}
  {f'<p class="project-links">{links}</p>' if links else ""}
  <hr>
  <div class="md-body">{sectioned(render_md(p["body"]), words)}</div>
  {sub_nav}
  <hr>
  <h2 class="small-h">Related</h2>
  <ul class="related">{"".join(mini_card(q) for q in rel)}</ul>
</article>'''
    write(f"/{p['slug']}/", shell(site, title=p["title"], desc=p.get("summary"), body=body,
                                  path=f"/{p['slug']}/", body_class="project-page", og_type="article",
                                  crumb=p.get("short_title", p["title"])))

    for s in p["subpages"]:
        sbody = (f'<article class="project"><p class="crumbs"><a href="/{p["slug"]}/">← {esc(p["title"])}</a></p>'
                 f'<h1>{esc(s.get("title", s["slug"]))}</h1><p class="project-summary">{esc(s.get("summary", ""))}</p>'
                 f'<hr><div class="md-body">{render_md(s["body"])}</div></article>')
        write(f"/{p['slug']}/{s['slug']}.html", shell(
            site, title=s.get("title", s["slug"]), desc=s.get("summary"), body=sbody,
            path=f"/{p['slug']}/{s['slug']}.html", body_class="project-page", crumb=p.get("short_title", p["title"])))
    copy_images(p)


def copy_images(item):
    src = item["dir"] / "images"
    if src.exists():
        shutil.copytree(src, OUT / item["slug"] / "images", dirs_exist_ok=True)
    for f in item["dir"].iterdir():   # loose downloadable folders (e.g. firmware/)
        if f.is_dir() and f.name != "images":
            shutil.copytree(f, OUT / item["slug"] / f.name, dirs_exist_ok=True)


def build_page(site, pg):
    body = (f'<article class="project"><h1>{esc(pg["title"])}</h1>'
            + (f'<p class="project-summary">{esc(pg["summary"])}</p>' if pg.get("summary") else "")
            + f'<hr><div class="md-body">{render_md(pg["body"])}</div></article>')
    write(f"/{pg['slug']}/", shell(site, title=pg["title"], desc=pg.get("summary"),
                                   body=body, path=f"/{pg['slug']}/", body_class="plain-page"))
    copy_images(pg)


# ── content discovery ──────────────────────────────────────────────────

def discover():
    projects, pages = [], []
    for d in sorted(CONTENT.iterdir()):
        if not d.is_dir() or d.name.startswith(("_", ".")):
            continue
        idx = d / "index.md"
        if not idx.exists():
            warn(f"{d.name}/ has no index.md, skipped")
            continue
        fm, body = parse(read(idx))
        item = dict(fm)
        item["slug"] = d.name
        item["body"] = body
        item["dir"] = d
        item["subpages"] = []
        for f in sorted(d.glob("*.md")):
            if f.name == "index.md":
                continue
            sfm, sbody = parse(read(f))
            item["subpages"].append({**sfm, "slug": f.stem, "body": sbody})
        if fm.get("type") == "page":
            pages.append(item)
            continue
        # project validation / defaults
        if "title" not in fm:
            warn(f"{d.name}: missing title")
            item["title"] = d.name
        if item.get("status") not in STATUSES:
            warn(f"{d.name}: status {item.get('status')!r} not one of {list(STATUSES)}")
            item["status"] = "planned"
        if item.get("area") not in AREAS:
            warn(f"{d.name}: area {item.get('area')!r} not one of {list(AREAS)}")
            item["area"] = "other"
        if not item.get("summary"):
            warn(f"{d.name}: missing summary")
        item.setdefault("tags", [])
        item.setdefault("timeline", [])
        for f in item.get("focus", []) or []:
            if f not in FOCUSES:
                warn(f"{d.name}: focus {f!r} not one of {list(FOCUSES)}")
        item["_start"] = parse_date(item.get("started"))
        item["_end"] = parse_date(item.get("ended"))
        projects.append(item)
    return projects, pages


def project_date_range(p):
    s, e = p["_start"], p["_end"]
    if not s:
        return ""
    if e:
        return f"{s[1]} – {e[1]}" if s[1] != e[1] else s[1]
    if p["status"] in ("live", "building"):
        return f"{s[1]} – now"
    return s[1]


def sort_projects(projects):
    area_rank = {k: i for i, k in enumerate(AREAS)}
    return sorted(projects, key=lambda p: (area_rank[p["area"]], p.get("rank", 50),
                                           tuple(-x for x in (p["_start"] or ((0, 0, 0), ""))[0])))


# ── resume ────────────────────────────────────────────────────────────

def resume_html(r, focus=None, for_pdf=False):
    """focus=None: all items, file order. Otherwise items matching the focus come
    first within each section. The web page renders once and JS reorders."""
    def order(items):
        if not focus:
            return items
        return sorted(items, key=lambda it: 0 if focus in (it.get("focus") or []) else 1)

    def fattr(it):
        return f' data-focus="{esc(" ".join(it.get("focus") or []))}"'

    c = r["contact"]
    contact_bits = [esc(c["location"]),
                    f'<a href="mailto:{esc(c["email"])}">{esc(c["email"])}</a>'] + [
        f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in c["links"]]
    out = [f'<header class="r-head"><h1>{esc(r["name"])}</h1>'
           f'<p class="r-contact">{" <span aria-hidden=\"true\">/</span> ".join(contact_bits)}</p></header>']

    ed = r["education"]
    out.append(f'''<section class="r-sec"><h2>Education</h2>
  <div class="r-item"><div class="r-line"><strong>{esc(ed["school"])}</strong><span>{esc(ed["when"])}</span></div>
  <div class="r-line r-sub"><span>{esc(ed["degree"])}</span><span>{esc(ed["detail"])}</span></div>
  <p class="r-course">{esc(ed["coursework"])}</p></div></section>''')

    sk = "".join(f'<li class="r-skill"{fattr(g)}><strong>{esc(g["label"])}:</strong> {esc(", ".join(g["items"]))}</li>'
                 for g in order(r["skills"]))
    out.append(f'<section class="r-sec"><h2>Skills</h2><ul class="r-skills" data-sortable>{sk}</ul></section>')

    def items(sec_key, title):
        if not r.get(sec_key):
            return ""
        lis = []
        for it in order(r[sec_key]):
            where = f'<span>{esc(it.get("when", ""))}</span>'
            name = esc(it["name"])
            if it.get("url"):
                name = f'<a href="{esc(it["url"])}">{name}</a>'
            sub = f' <em class="r-sub">{esc(it["sub"])}</em>' if it.get("sub") else ""
            bl = "".join(f"<li>{inline_md(b)}</li>" for b in it.get("bullets", []))
            bl_html = f'<ul class="r-bullets">{bl}</ul>' if bl else ""
            line = f' <span class="r-oneline">{inline_md(it["line"])}</span>' if it.get("line") else ""
            lis.append(f'<li class="r-item"{fattr(it)}><div class="r-line"><span class="r-what"><strong>{name}</strong>'
                       f'{sub}{line}</span>{where}</div>{bl_html}</li>')
        return f'<section class="r-sec"><h2>{title}</h2><ul class="r-items" data-sortable>{"".join(lis)}</ul></section>'

    out.append(items("projects", "Projects"))
    out.append(items("experience", "Experience"))
    out.append(items("leadership", "Experience & leadership" if not r.get("experience") else "Leadership & activities"))
    return "\n".join(out)


def build_resume(site, r, make_pdf):
    radios = "".join(
        f'<label><input type="radio" name="focus" value="{k}"{" checked" if k == "all" else ""}>'
        f'<span>{v}</span></label>'
        for k, v in [("all", "Everything"), *FOCUSES.items()])
    pdf_links = "".join(
        f'<a class="pdf-link" data-pdf-for="{k}" href="/resume/{r["pdf_name"]}{"" if k == "all" else "-" + k}.pdf"'
        f'{"" if k == "all" else " hidden"}>Download PDF{"" if k == "all" else " (" + FOCUSES[k].lower() + " first)"}</a>'
        for k in ["all", *FOCUSES])
    body = f'''
<section class="page-top">
  <h1>Resume</h1>
  <p class="page-intro">Pick what to show first. The PDF matches your choice.</p>
</section>
<section class="resume-wrap">
<div class="resume-tools">
  <fieldset class="focus-switch" data-focus-switch>
    <legend>Show first</legend>
    {radios}
  </fieldset>
  <p class="pdf-links">{pdf_links}</p>
</div>
<article class="resume" data-resume>
{resume_html(r)}
</article>
</section>'''
    write("/resume/", shell(site, title="Resume", desc=f"Resume of {r['name']}.", body=body,
                            path="/resume/", body_class="resume-page"))
    if not make_pdf:
        return
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        warn("WeasyPrint not installed; resume PDFs skipped (pip install weasyprint)")
        return
    css = read(BUILD / "resume-print.css").replace("FONTDIR", (STATIC / "fonts").as_uri())
    for k in ["all", *FOCUSES]:
        doc = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(r["name"])} — Resume</title></head>' \
              f'<body class="pdf"><article class="resume">{resume_html(r, None if k == "all" else k, True)}</article></body></html>'
        name = f'{r["pdf_name"]}{"" if k == "all" else "-" + k}.pdf'
        rendered = HTML(string=doc, base_url=str(OUT)).render(stylesheets=[CSS(string=css)])
        if len(rendered.pages) > 1:
            warn(f"resume PDF {name} runs to {len(rendered.pages)} pages")
        rendered.write_pdf(OUT / "resume" / name)


# ── extras ────────────────────────────────────────────────────────────

def build_404(site):
    body = ('<section class="page-top"><h1>Signal lost</h1><p class="page-intro">That page doesn\'t exist, or it moved '
            'when the site was rebuilt. Try the <a href="/">homepage</a> or the <a href="/projects/">project timeline</a>.'
            '</p></section>')
    (OUT / "404.html").write_text(shell(site, title="Page not found", desc="", body=body, path="/404.html"), "utf-8")


ROBOTS = """#
#        _.-~~-._
#     .-~  _..._  ~-.        spotty connection
#         .-~ ~-.            dylanzickus.com
#            (o)
#
# Hi, robot. Everything here is yours to read, except /signal-lost/.
# Well-behaved crawlers never go there. Crawlers that ignore this file
# end up in a maze of nonsense pages that only link to each other.
#
User-agent: *
Disallow: /signal-lost/
Allow: /

Sitemap: {site}/sitemap.xml
"""

TRAP_WORDS = ("signal packet carrier mesh beacon relay tunnel subnet uplink router jitter latency "
              "handshake checksum broadcast frequency antenna bandwidth static noise drift echo "
              "lizard spotty modem dial-up squelch ping lost found buffer gateway").split()


def build_trap(n_pages=48):
    """A static honeypot: /signal-lost/ and a maze of pages that only link to each other.
    It's disallowed in robots.txt and linked invisibly, so only rude crawlers find it."""
    import hashlib
    import random
    rng = random.Random(42)
    ids = [hashlib.sha1(str(i).encode()).hexdigest()[:10] for i in range(n_pages)]

    def babble(k):
        words = [rng.choice(TRAP_WORDS) for _ in range(k)]
        return " ".join(words).capitalize() + "."

    def page(title, links):
        paras = "".join(f"<p>{babble(rng.randint(14, 30))} {babble(rng.randint(10, 22))}</p>" for _ in range(3))
        nav = "".join(f'<li><a href="/signal-lost/{x}/">{babble(3)[:-1]}</a></li>' for x in links)
        return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="robots" content="noindex, nofollow, noarchive"><title>{esc(title)}</title>
<style>body{{background:#0f1117;color:#8f8a85;font:16px/1.6 monospace;max-width:40rem;margin:3rem auto;padding:0 1rem}}a{{color:#4fd1c5}}</style>
</head><body><h1>{esc(title)}</h1>
<p><em>If you're a person: you found the scraper trap. Hi! <a href="/">Head back home</a>.
If you're a crawler that ignored robots.txt: enjoy the maze.</em></p>
{paras}<ul>{nav}</ul></body></html>"""

    write("/signal-lost/", page("Signal lost", rng.sample(ids, 6)))
    for i in ids:
        write(f"/signal-lost/{i}/", page(babble(4)[:-1], rng.sample(ids, 6)))


def build_sitemap(paths):
    urls = "".join(f"<url><loc>{SITE_URL}{p}</loc></url>" for p in paths)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        "utf-8")
    (OUT / "robots.txt").write_text(ROBOTS.format(site=SITE_URL), "utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit non-zero on content warnings")
    ap.add_argument("--no-pdf", action="store_true", help="skip resume PDFs")
    args = ap.parse_args()

    print(f"Building {CONTENT} -> {OUT}")
    site = yaml.safe_load(read(CONTENT / "site.yaml"))
    for colour, tags in (site.get("tag_colors") or {}).items():
        for tg in tags:
            TAG_COLORS[str(tg).lower()] = colour
    resume = yaml.safe_load(read(CONTENT / "resume.yaml"))
    projects, pages = discover()
    projects = sort_projects(projects)
    slugs = {p["slug"] for p in projects}
    for f in site.get("featured", []):
        if f not in slugs:
            warn(f"site.yaml featured slug {f!r} doesn't exist")
    for i, s in enumerate(site.get("featured", [])):
        for p in projects:
            if p["slug"] == s:
                p["featured"] = i + 1

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(STATIC, OUT / "assets", ignore=shutil.ignore_patterns("CNAME"))
    shutil.copy(STATIC / "CNAME", OUT / "CNAME")
    shutil.copy(STATIC / "brand" / "favicon.svg", OUT / "favicon.svg")
    shutil.copytree(BUILD / "brand", OUT / "brand", dirs_exist_ok=True)  # standalone brand-kit page at /brand/

    build_home(site, projects)
    build_projects_index(site, projects)
    for p in projects:
        build_project(site, p, projects)
    for pg in pages:
        build_page(site, pg)
    build_resume(site, resume, make_pdf=not args.no_pdf)
    build_404(site)
    build_trap()
    for old, new in (site.get("redirects") or {}).items():
        write(old, f'<!doctype html><meta charset="utf-8"><title>Moved</title>'
                   f'<link rel="canonical" href="{esc(SITE_URL + new)}">'
                   f'<meta http-equiv="refresh" content="0; url={esc(new)}">'
                   f'<p>This page moved to <a href="{esc(new)}">{esc(new)}</a>.</p>')

    public = ["/", "/projects/", "/resume/"] + [f"/{p['slug']}/" for p in projects if not p.get("hidden")] + \
             [f"/{pg['slug']}/" for pg in pages if not pg.get("hidden")]
    build_sitemap(public)
    (OUT / "projects.json").write_text(json.dumps([
        {"slug": p["slug"], "title": p["title"], "status": p["status"], "area": p["area"],
         "tags": p["tags"], "summary": p.get("summary", ""), "focus": p.get("focus", [])}
        for p in projects if not p.get("hidden")], indent=1), "utf-8")

    print(f"  {len(projects)} projects, {len(pages)} pages, {len(WARNINGS)} warning(s)")
    if args.strict and WARNINGS:
        sys.exit("Strict mode: fix the warnings above.")
    print("Done.")


if __name__ == "__main__":
    main()
