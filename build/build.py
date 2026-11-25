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

def bars(status: str, size: str = "") -> str:
    label, lit, _ = STATUSES.get(status, STATUSES["planned"])
    spans = "".join(f'<i class="{"on" if i < lit else "off"}"></i>' for i in range(4))
    cls = f"bars bars-{status}" + (f" bars-{size}" if size else "")
    return f'<span class="{cls}" aria-hidden="true">{spans}</span>'


def status_pill(status: str) -> str:
    label = STATUSES.get(status, STATUSES["planned"])[0]
    return f'<span class="status status-{status}">{bars(status)}<span>{label}</span></span>'


def tag_list(tags, cls="tags") -> str:
    if not tags:
        return ""
    return f'<ul class="{cls}">' + "".join(f"<li>{esc(t)}</li>" for t in tags) + "</ul>"


def data_attrs(p, extra_text="") -> str:
    search = " ".join([p["title"], p.get("summary", ""), " ".join(p.get("tags", [])),
                       AREAS.get(p["area"], ""), extra_text]).lower()
    tags = "|".join(t.lower() for t in p.get("tags", []))
    return (f'data-area="{esc(p["area"])}" data-status="{esc(p["status"])}" '
            f'data-tags="{esc(tags)}" data-search="{esc(search)}"')


def filter_bar(projects, with_tags: bool) -> str:
    areas = "".join(
        f'<button type="button" data-filter="area" data-value="{k}" aria-pressed="false">{v}</button>'
        for k, v in AREAS.items() if any(p["area"] == k for p in projects))
    statuses = "".join(
        f'<button type="button" data-filter="status" data-value="{k}" aria-pressed="false" title="{esc(d)}">'
        f'{bars(k)}<span>{label}</span></button>'
        for k, (label, _, d) in STATUSES.items() if any(p["status"] == k for p in projects))
    tags_html = ""
    if with_tags:
        counts = {}
        for p in projects:
            for t in p.get("tags", []):
                counts[t] = counts.get(t, 0) + 1
        common = sorted((t for t, c in counts.items() if c >= 2), key=lambda t: (-counts[t], t.lower()))
        tags_html = ('<div class="filter-row filter-tags" role="group" aria-label="Tags">'
                     + "".join(f'<button type="button" data-filter="tag" data-value="{esc(t.lower())}" '
                               f'aria-pressed="false">{esc(t)}</button>' for t in common) + "</div>")
    return f'''<div class="filters" data-filters>
  <label class="search"><span class="visually-hidden">Search projects</span>
    <input type="search" placeholder="Search: Docker, MQTT, ESP32…" data-search-input autocomplete="off"></label>
  <div class="filter-row" role="group" aria-label="Area">{areas}</div>
  <div class="filter-row" role="group" aria-label="Status">{statuses}</div>
  {tags_html}
  <p class="filter-empty" data-empty hidden>Nothing matches. <button type="button" data-clear>Clear filters</button></p>
</div>'''


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


# ── page shell ─────────────────────────────────────────────────────────

NAV = [("/", "Timeline"), ("/projects/", "Projects"), ("/resume/", "Resume"), ("/about/", "About")]


def shell(site, *, title, desc, body, path, body_class="", og_type="website"):
    tpl = read(TEMPLATES / "base.html")
    nav = "".join(
        f'<a href="{h}"{" aria-current=\"page\"" if (path == h or (h != "/" and path.startswith(h))) else ""}>{l}</a>'
        for h, l in NAV)
    full_title = title if title == site["name"] else f"{title} · {site['name']}"
    vals = {
        "TITLE": esc(full_title),
        "DESC": esc(desc or site["description"]),
        "CANONICAL": esc(SITE_URL + path),
        "OG_TYPE": og_type,
        "NAV": nav,
        "BODY": body,
        "BODY_CLASS": body_class,
        "YEAR": str(dt.date.today().year),
        "FOOTER_LINKS": " ".join(f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in site["links"]),
        "BUILD_DATE": dt.date.today().isoformat(),
    }
    out = tpl
    for k, v in vals.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def write(path: str, text: str):
    p = OUT / path.lstrip("/")
    if path.endswith("/"):
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ── homepage: intro + featured + timeline ──────────────────────────────

def timeline_events(projects):
    events = []
    for p in projects:
        if p.get("hidden"):
            continue
        for ev in p["timeline"]:
            d = parse_date(ev.get("date"))
            if not d:
                warn(f"{p['slug']}: timeline entry without a valid date: {ev}")
                continue
            events.append({"key": d[0], "label": d[1], "text": ev.get("text", ""), "p": p})
    events.sort(key=lambda e: (e["key"], e["p"]["title"]), reverse=True)
    return events


def build_home(site, projects):
    today = dt.date.today()
    now_key = (today.year, today.month, today.day)
    feats = [p for p in projects if p.get("featured")]
    feats.sort(key=lambda p: p["featured"])

    featured = "".join(f'''
      <li>
        <a class="feature" href="/{p["slug"]}/">
          <span class="feature-head">{bars(p["status"])}<span class="feature-title">{esc(p.get("short_title", p["title"]))}</span></span>
          <span class="feature-sum">{esc(p.get("summary", ""))}</span>
        </a>
      </li>''' for p in feats)

    events = timeline_events(projects)

    def grouped(evs, newest_first=True):
        """[(month_key, [(project, [event, ...]), ...]), ...] — one row per project per month."""
        months = {}
        for e in evs:
            months.setdefault(e["key"][:2], []).append(e)
        out = []
        # year-only entries ("2027") sort after that year's months going forward, before them going back
        for mk in sorted(months, key=lambda k: (k[0], k[1] or (13 if not newest_first else 0)), reverse=newest_first):
            per = {}
            for e in sorted(months[mk], key=lambda e: e["key"]):
                per.setdefault(e["p"]["slug"], []).append(e)
            rows = sorted(per.values(), key=lambda es: max(x["key"] for x in es), reverse=True)
            out.append((mk, [(es[0]["p"], es) for es in rows]))
        return out

    def row_html(mk, p, es, first, show_year):
        label = ""
        if first:
            label = MONTHS[mk[1] - 1] if mk[1] else ("" if not show_year else str(mk[0]))
            if show_year and mk[1]:
                label = f"{MONTHS[mk[1] - 1]} <span>{mk[0]}</span>" if mk[0] != today.year else label
        texts = [inline_md(e["text"]) for e in es]
        body = (f"<p>{texts[0]}</p>" if len(texts) == 1
                else "<ul>" + "".join(f"<li>{x}</li>" for x in texts) + "</ul>")
        return f'''
        <li class="event{" event-first" if first else ""}" {data_attrs(p, " ".join(e["text"] for e in es))}>
          <time>{label}</time>
          <div class="event-body">
            <a class="event-project" href="/{p["slug"]}/">{bars(p["status"])}<span>{esc(p.get("short_title", p["title"]))}</span></a>
            {body}
          </div>
        </li>'''

    upcoming = [e for e in events if e["key"][:2] > now_key[:2]]
    past = [e for e in events if e not in upcoming]
    groups = []
    if upcoming:
        rows = "".join(row_html(mk, p, es, i == 0, True)
                       for mk, prs in grouped(upcoming, newest_first=False) for i, (p, es) in enumerate(prs))
        groups.append(f'<section class="year" data-group><h3>Coming up</h3><ol>{rows}</ol></section>')
    by_year = {}
    for mk, prs in grouped(past):
        by_year.setdefault(mk[0], []).append((mk, prs))
    for y in sorted(by_year, reverse=True):
        rows = "".join(row_html(mk, p, es, i == 0, False) for mk, prs in by_year[y] for i, (p, es) in enumerate(prs))
        groups.append(f'<section class="year" data-group><h3>{y}</h3><ol>{rows}</ol></section>')

    intro = site["intro"]
    links = "".join(f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in site["hero_links"])
    body = f'''
<section class="hero">
  <div class="hero-mark" aria-hidden="true">{read(STATIC / "brand" / "mark.svg")}</div>
  <div class="hero-text">
    <h1>{esc(site["person"])}</h1>
    <p class="hero-lede">{inline_md(intro)}</p>
    <p class="hero-links">{links}</p>
  </div>
</section>

<section class="featured" aria-labelledby="featured-h">
  <h2 id="featured-h">Start here</h2>
  <ol class="feature-list">{featured}</ol>
</section>

<section class="timeline-wrap" aria-labelledby="timeline-h">
  <div class="section-head">
    <h2 id="timeline-h">Timeline</h2>
    <p>What I built and when, newest first. The bars next to each project show its status.</p>
  </div>
  <div class="timeline-grid">
    <div class="timeline" data-list>{"".join(groups)}</div>
    <aside class="timeline-filters">{filter_bar(projects, with_tags=False)}</aside>
  </div>
</section>'''
    write("/", shell(site, title=site["name"], desc=site["description"], body=body, path="/", body_class="home"))


# ── projects index ────────────────────────────────────────────────────

def build_projects_index(site, projects):
    rows = []
    for area, label in AREAS.items():
        items = [p for p in projects if p["area"] == area and not p.get("hidden")]
        if not items:
            continue
        lis = "".join(f'''
      <li class="proj" {data_attrs(p)}>
        <a href="/{p["slug"]}/">
          <span class="proj-head">{bars(p["status"])}<span class="proj-title">{esc(p["title"])}</span>
            <span class="proj-when">{esc(project_date_range(p))}</span></span>
          <span class="proj-sum">{esc(p.get("summary", ""))}</span>
        </a>
        {tag_list(p["tags"])}
      </li>''' for p in items)
        rows.append(f'<section class="area" data-group><h2>{label}</h2><ul class="proj-list">{lis}</ul></section>')

    legend = "".join(f'<li>{bars(k)}<span><strong>{l}</strong> {esc(d)}</span></li>'
                     for k, (l, _, d) in STATUSES.items())
    body = f'''
<header class="page-head">
  <h1>Projects</h1>
  <p class="lede">Everything on the site, grouped by area. Filter by status or tag, or search.</p>
  <ul class="legend">{legend}</ul>
</header>
{filter_bar([p for p in projects if not p.get("hidden")], with_tags=True)}
<div data-list>{"".join(rows)}</div>'''
    write("/projects/", shell(site, title="Projects", desc="Homelab, embedded and software projects by Dylan Zickus.",
                              body=body, path="/projects/", body_class="projects"))


# ── project pages ─────────────────────────────────────────────────────

def project_aside(p):
    facts = []
    facts.append(f'<dt>Status</dt><dd>{status_pill(p["status"])}</dd>')
    when = project_date_range(p)
    if when:
        facts.append(f"<dt>When</dt><dd>{esc(when)}</dd>")
    if p.get("role"):
        facts.append(f"<dt>Role</dt><dd>{esc(p['role'])}</dd>")
    if p.get("stack"):
        facts.append(f"<dt>Stack</dt><dd>{esc(', '.join(p['stack']))}</dd>")
    if p.get("links"):
        facts.append("<dt>Links</dt><dd>" + "<br>".join(
            f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in p["links"]) + "</dd>")
    return f'<dl class="facts">{"".join(facts)}</dl>'


def project_timeline(p):
    if not p["timeline"]:
        return ""
    evs = sorted(p["timeline"], key=lambda e: (parse_date(e.get("date")) or ((0, 0, 0), ""))[0])
    items = "".join(
        f'<li><time>{esc((parse_date(e.get("date")) or (None, ""))[1])}</time><p>{inline_md(e.get("text", ""))}</p></li>'
        for e in evs)
    return f'<section class="ptl" aria-labelledby="ptl-h"><h2 id="ptl-h">How it evolved</h2><ol>{items}</ol></section>'


def related(p, projects):
    tags = {t.lower() for t in p["tags"]}
    scored = []
    for q in projects:
        if q is p or q.get("hidden"):
            continue
        s = len(tags & {t.lower() for t in q["tags"]}) + (1 if q["area"] == p["area"] else 0)
        if s:
            scored.append((s, q))
    scored.sort(key=lambda x: (-x[0], x[1]["title"]))
    picks = [q for _, q in scored[:3]]
    if not picks:
        return ""
    lis = "".join(f'<li><a href="/{q["slug"]}/">{bars(q["status"])}<span>{esc(q["title"])}</span></a></li>' for q in picks)
    return f'<nav class="related" aria-label="Related projects"><h2>Related</h2><ul>{lis}</ul></nav>'


def build_project(site, p, projects):
    sub_nav = ""
    if p["subpages"]:
        sub_nav = ('<nav class="subpages" aria-label="Pages in this project"><h2>More on this project</h2><ul>'
                   + "".join(f'<li><a href="/{p["slug"]}/{s["slug"]}.html">{esc(s.get("title", s["slug"]))}</a>'
                             f'<span>{esc(s.get("summary", ""))}</span></li>' for s in p["subpages"])
                   + "</ul></nav>")
    body = f'''
<article class="project">
  <header class="project-head">
    <p class="crumbs"><a href="/projects/">Projects</a> / {esc(AREAS[p["area"]])}</p>
    <h1>{esc(p["title"])}</h1>
    <p class="lede">{esc(p.get("summary", ""))}</p>
    {tag_list(p["tags"])}
  </header>
  <div class="project-grid">
    <aside>{project_aside(p)}</aside>
    <div class="prose">
      {render_md(p["body"])}
      {sub_nav}
      {project_timeline(p)}
    </div>
  </div>
  {related(p, projects)}
</article>'''
    write(f"/{p['slug']}/", shell(site, title=p["title"], desc=p.get("summary"), body=body,
                                  path=f"/{p['slug']}/", body_class="project-page", og_type="article"))

    for s in p["subpages"]:
        sbody = f'''
<article class="project">
  <header class="project-head">
    <p class="crumbs"><a href="/projects/">Projects</a> / <a href="/{p["slug"]}/">{esc(p["title"])}</a></p>
    <h1>{esc(s.get("title", s["slug"]))}</h1>
    <p class="lede">{esc(s.get("summary", ""))}</p>
  </header>
  <div class="prose prose-solo">{render_md(s["body"])}</div>
</article>'''
        write(f"/{p['slug']}/{s['slug']}.html", shell(
            site, title=s.get("title", s["slug"]), desc=s.get("summary"), body=sbody,
            path=f"/{p['slug']}/{s['slug']}.html", body_class="project-page"))
    copy_images(p)


def copy_images(item):
    src = item["dir"] / "images"
    if src.exists():
        dest = OUT / item["slug"] / "images"
        shutil.copytree(src, dest, dirs_exist_ok=True)
    for f in item["dir"].iterdir():   # loose downloadable files (e.g. firmware/)
        if f.is_dir() and f.name not in ("images",):
            shutil.copytree(f, OUT / item["slug"] / f.name, dirs_exist_ok=True)


def build_page(site, pg):
    body = f'''
<article class="page">
  <header class="page-head"><h1>{esc(pg["title"])}</h1>
  {f'<p class="lede">{esc(pg["summary"])}</p>' if pg.get("summary") else ""}</header>
  <div class="prose prose-solo">{render_md(pg["body"])}</div>
</article>'''
    write(f"/{pg['slug']}/", shell(site, title=pg["title"], desc=pg.get("summary") or pg.get("description"),
                                   body=body, path=f"/{pg['slug']}/", body_class="plain-page"))
    copy_images(pg)


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
<div class="resume-tools">
  <fieldset class="focus-switch" data-focus-switch>
    <legend>Show first</legend>
    {radios}
  </fieldset>
  <p class="pdf-links">{pdf_links}</p>
</div>
<article class="resume" data-resume>
{resume_html(r)}
</article>'''
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
    body = '''<article class="page"><header class="page-head"><h1>Signal lost</h1>
<p class="lede">That page doesn't exist, or it moved when the site was rebuilt.
Try the <a href="/">timeline</a> or the <a href="/projects/">project list</a>.</p></header></article>'''
    (OUT / "404.html").write_text(shell(site, title="Page not found", desc="", body=body, path="/404.html"), "utf-8")


def build_sitemap(paths):
    urls = "".join(f"<url><loc>{SITE_URL}{p}</loc></url>" for p in paths)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        "utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", "utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit non-zero on content warnings")
    ap.add_argument("--no-pdf", action="store_true", help="skip resume PDFs")
    args = ap.parse_args()

    print(f"Building {CONTENT} -> {OUT}")
    site = yaml.safe_load(read(CONTENT / "site.yaml"))
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

    build_home(site, projects)
    build_projects_index(site, projects)
    for p in projects:
        build_project(site, p, projects)
    for pg in pages:
        build_page(site, pg)
    build_resume(site, resume, make_pdf=not args.no_pdf)
    build_404(site)
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
