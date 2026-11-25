# dylanzickus.com

Personal site for Dylan Zickus, branded **Spotty Connection**. Markdown in, static HTML out, deployed to GitHub Pages on every push to `master`.

```
content/                 <- everything you edit
  site.yaml                name, homepage intro, links, "Start here" projects
  resume.yaml              resume (web page + PDFs)
  <slug>/index.md          a project (frontmatter + Markdown)
  <slug>/<page>.md         optional extra pages for a project
  <slug>/images/           images for that project
  about/, privacy/, terms/ plain pages (`type: page`; privacy/terms are hidden)
  _template/               copy this to start a new project (never built)
build/
  build.py                 the generator
  templates/base.html      page shell
  static/                  CSS, JS, fonts, logos (copied to /assets/)
  resume-print.css         PDF styling
tools/make_logos.py        regenerates the logo set (rarely needed)
website/                   build output, git-ignored; CI builds it
```

## Build and preview

```
python -m pip install -r build/requirements.txt
python build/build.py                 # add --no-pdf to skip resume PDFs
python -m http.server 8000 --directory website
```

### Screenshot previews (no deploy needed)

```
pip install playwright pillow        # plus: python -m playwright install chromium, if no Chrome
python tools/preview.py / /ops-agent/            # desktop + mobile shots of the local build
python tools/preview.py --compare /projects/     # live site vs local build, side by side
```

PNGs land in `preview/` (git-ignored).

CI runs `python build/build.py --strict`, which fails on content warnings (bad status, missing summary, broken featured slug, a resume PDF longer than one page).

## Add a project

1. `cp -r content/_template content/my-project` and fill in the frontmatter and body.
2. `status` is one of `live`, `building`, `dormant`, `retired`, `planned`. It drives the signal bars.
3. `area` is `homelab`, `embedded`, `software` or `other`.
4. Every `timeline` entry appears on the homepage timeline. Add an entry when the project changes rather than rewriting the old ones.
5. Build, check it, commit, and push to `master`.

To feature a project on the homepage, add its folder name to `featured` in `content/site.yaml`.

## Statuses

| Status | Bars | Meaning |
|---|---|---|
| live | 4 | Running and in use |
| building | 3 | Actively being built |
| dormant | 2 | Works, but not in use |
| retired | 1 | Taken down or replaced |
| planned | outline | An idea, not built yet |

## Photos

Drop `content/<slug>/images/cover.jpg` (or `.png`/`.webp`, roughly 16:10) and it replaces the
placeholder on the homepage carousel, the timeline and the project page.

## robots.txt and the honeypot

`robots.txt` disallows `/signal-lost/`. Every page has an invisible link there, so only crawlers that
ignore robots.txt follow it, into a maze of 48 noindex nonsense pages that only link to each other.
GitHub Pages can't block anyone; banning visitors who hit the trap would need a Cloudflare Worker.

## Hidden pages

`hidden: true` builds a page without listing it anywhere. `/privacy/` and `/terms/` exist for the rclone Google OAuth app and must keep working.

## Deploy

`.github/workflows/deploy.yml` has two jobs: a build job uploads `website/` with `upload-pages-artifact@v4`, and a deploy job runs after it with `deploy-pages@v4`. The custom domain comes from `build/static/CNAME`, and DNS is on Cloudflare.
