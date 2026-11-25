---
# Copy this folder to content/<project-slug>/ (lowercase-with-dashes) and fill it in.
# Folders starting with "_" are never built.
title: Full Project Title                 # page heading
short_title: Short title                  # optional; used on the timeline and "Start here"
summary: One or two plain sentences. Shown under the title, in the project list and in search results.
icon: 🔧            # emoji on the placeholder image until there's a photo
highlights:         # three short lines shown as cards on the project page
  - First thing worth knowing
  - Second
  - Third
status: live        # live | building | dormant | retired | planned
area: homelab       # homelab | embedded | software | other  (homelab and embedded are the focus)
rank: 50            # optional; lower = higher in its area on /projects/
started: 2026-11    # YYYY-MM (or YYYY if unsure)
# ended: 2026-12    # only for finished/retired projects
role: Solo          # optional; "Team lead (5 people)", "With a roommate", ...
stack: [Docker, Python]                   # shown in the sidebar
focus: [infra]      # optional; resume focus this supports: infra | embedded | fullstack
tags: [Docker, Python, Self-hosting]      # filter/search tags; reuse existing tags where possible
links:                                    # optional
  - { label: Repository, url: "https://github.com/dmzickus/..." }
timeline:           # each entry shows on the homepage timeline and on the project page
  - date: 2026-11
    text: What happened, in one sentence. Markdown links are fine.
---

Opening paragraph: what this is and why it exists, in plain words.

## How it works

The pieces and how they fit together. A table is fine if it helps.

## What went wrong / what I learned

The debugging story is usually the most interesting part. Keep it concrete.

## Next

- What's planned, if anything

<!--
Images: put them in content/<slug>/images/ and use ![alt text](images/photo.jpg).
images/cover.jpg (or .png/.webp) replaces the placeholder everywhere: carousel, timeline, page header.
Keep public pages free of internal IPs, hostnames, tunnel/team names, secrets,
and specifics about download sources.
-->
