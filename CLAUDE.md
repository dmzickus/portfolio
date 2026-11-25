# Notes for Claude

This repo is Dylan's personal site. Read README.md for the content model.

## Adding or updating a project

- **Only add a project after Dylan approves it.** Not everything belongs on the site. Updating an existing page's status or timeline is fine whenever he mentions a change.
- Start from `content/_template/index.md` (include `icon` and three short `highlights`). Reuse existing tags; run `grep -h "^tags:" content/*/index.md` to see them.
- For an update, **append** a `timeline` entry (`date: YYYY-MM`, one sentence) and change `status` if it changed. Don't rewrite history.
- Write plainly, in first person, like the existing pages: what it is, how it works, what went wrong, what's next. Short paragraphs, no hype.
- Facts must come from Dylan or the work itself. Mark uncertain dates as year-only rather than guessing a month.
- If a project should be on the resume, add or adjust it in `content/resume.yaml` with the right `focus` tags. The PDF must stay one page; `--strict` fails otherwise.

## Never publish

- Internal IPs, hostnames, Tailscale/tunnel names, Cloudflare team names, ports, usernames, API keys, or anything from `.env`/secrets files
- Download sources: indexer or tracker names, cracks/repacks, VPN exit locations. Describe the media and game pipelines as library automation and untrusted-file handling.
- Roommates' or family members' names or private details

## Editing with Dylan

- Preview every visible change before pushing: `python tools/preview.py --compare <changed paths>` and send him the PNGs from `preview/`. Push only after he says to ship it (adding or updating a project page he already approved is fine to push directly).
- Photos he sends: strip EXIF/GPS, resize to about 1600px wide, save as `content/<slug>/images/cover.jpg` (or `.webp`). Never commit originals with location data.
- Keep design changes in `build/static/style.css` and the render functions in `build/build.py`; content stays in `content/`.

## Before pushing

```
python build/build.py --strict
```

Then commit and push to `master`; GitHub Actions deploys it. Look at the changed page locally if anything structural changed.
