# dylanzickus.com — content workflow

The site is generated from Markdown. Edit files under `content/`, run the build
script, and the static HTML in `website/` is regenerated — that's the whole
deploy story, no CI needed.

```
content/            <- edit this
  home.yaml           hero text, "other builds", "core stack" (homepage only)
  bathroom-esp/
    index.md           page content (frontmatter + markdown)
    images/             drop images here, reference as images/foo.png
  media-stack/          a "section" with multiple pages
    index.md            section landing page
    jellyfin.md          \_ subpages, listed automatically on the landing page
    arr-stack.md         /
    images/              shared by every page in this section

build/               <- the generator, you shouldn't need to touch this
  build.py
  page_template.html
  home_template.html
  style.css

website/             <- generated output, don't hand-edit, gets overwritten
```

## One-time setup

```
python -m pip install markdown pyyaml
```

## Regenerating the site

```
python build/build.py
```

Run this after any edit to `content/`. It rewrites everything in `website/`
from scratch (safe — `website/` has no content of its own).

To preview locally:

```
python -m http.server 8000 --directory website
```

then open `http://localhost:8000`.

## Editing an existing page

Open `content/<project>/index.md`. The top is a frontmatter block:

```yaml
---
title: Bathroom Automation Controller
nav_label: Bathroom ESP      # short label used in the top nav
icon: 🚿
icon_color: ''                # '', green, or yellow — accent color for the icon chip
badge: 5-stage iteration      # small pill shown on the homepage card
order: 20                     # controls ordering in the nav and on the homepage
description: One or two sentences — used as both the page subtitle and the homepage card blurb.
tags:
  - ESP8266
  - Reed switch
---
```

Everything below the `---` is plain Markdown (headings, lists, code blocks,
tables, blockquotes) and becomes the page body. Edit it like a normal `.md`
file, then re-run the build.

## Adding an image

Drop the file in that project's `images/` folder and reference it with a
relative path:

```markdown
![Wiring diagram](images/wiring.png)
```

## Adding a brand new project page

1. `mkdir content/my-new-project` (and `content/my-new-project/images` if it has pictures)
2. Create `content/my-new-project/index.md` with a frontmatter block (copy one
   from an existing project) plus your Markdown content
3. Pick a unique `order` number to control where it lands in the nav/homepage
4. Run the build — it's picked up automatically, no other file needs editing

## Adding a page to the Media Stack section (or any multi-page section)

Add a new `.md` file next to that section's `index.md`, e.g.
`content/media-stack/backups.md`, with its own frontmatter (`title`,
`description`, `icon`, `tags`). It's automatically linked from the section's
landing page and added to the nav-adjacent breadcrumb — no manual wiring.

## Editing the homepage

The hero text, the "Other builds" cards, and the "Core stack" grid all live
in `content/home.yaml` — edit the YAML directly. The main "Project pages"
grid is generated from every section's frontmatter, so it doesn't need
separate editing.

## Notes

- `content/living-room-led/firmware/` and `content/smart-switch-mount/firmware/`
  hold two `.ino` sketches that were sitting in the old project folders. They
  aren't currently linked from any page — add a link/mention in the relevant
  `index.md` if you want them surfaced on the site.
