---
title: The arr Stack
icon: ⚙️
icon_color: ''
description: Radarr, Sonarr, Lidarr, Bazarr, and Prowlarr automating the full library lifecycle. Hardlink setup, custom format scoring, and a security incident with malware-disguised torrents.
tags:
- Radarr
- Sonarr
- Prowlarr
- Hardlinks
---

# The arr Stack

> Automated library management: find it, download it, organize it, and keep it up to date.

## Overview

The "arr stack" is a collection of open-source tools that automate the entire lifecycle of a media library. You tell Radarr you want a movie, and it finds a release, hands it to qBittorrent to download, waits for it to finish, moves it into your library in the right place with the right name, and notifies Jellyfin to scan the new file. No manual searching, no manual renaming, no manual moving.

The full stack:

| Tool | Role |
|------|------|
| **Radarr** | Movies — monitors for new releases, manages quality upgrades |
| **Sonarr** | TV shows — tracks episodes, seasons, ongoing series |
| **Lidarr** | Music — album and artist tracking |
| **Bazarr** | Subtitles — automatically fetches subtitles for everything |
| **Prowlarr** | Indexer proxy — manages torrent indexers in one place and syncs them to Radarr/Sonarr/Lidarr |
| **qBittorrent** | Download client |

All of these run as Docker containers on nas-pi, with download traffic routed through a VPN tunnel — see the [VPN & Downloading page](./vpn-routing.md) for how that works.

---

## Hardlinks: Why They Matter

One of the first things to get right in an arr stack is **hardlinks**. Without them, importing a completed download into the library means copying the file — temporarily doubling your storage use and taking time proportional to file size. With hardlinks, the "copy" is instantaneous and uses no additional space: both the download path and the library path point to the same underlying data on disk.

For hardlinks to work, the download directory and library directory **must be on the same filesystem**. The standard pattern is a unified `/data` tree:

```
/data/
  downloads/
    movies/
    tv/
  media/
    movies/
    tv/
    music/
```

Every container that needs to touch files — qBittorrent, Radarr, Sonarr, Jellyfin — mounts `/data` at the same path. This took some iteration to get right, particularly making sure Jellyfin's library root aligned with the same mount structure the arr containers use.

---

## Quality Profiles and Custom Formats

Radarr and Sonarr have a sophisticated quality system that goes well beyond "grab the highest bitrate release." **Custom formats** let you score releases based on codec, audio track, resolution, source, and more — and set a minimum score a release must meet before it's grabbed, and a target score that triggers automatic upgrades.

The current scoring setup, developed specifically around what the Tdarr pipeline can and can't do:

| Custom Format | Score |
|---------------|-------|
| 5.1 Surround Audio | +100 |
| x264 (H.264 video) | +50 |
| AAC Audio | +10 |
| Stereo Only | 0 |
| Avoid HEVC | 0 |
| Avoid AV1 | 0 |

**Why 5.1 ranks highest:** Tdarr can transcode any video codec to H.264, but it cannot fabricate surround sound from a stereo-only source. A stereo-only release is a permanent downgrade in audio quality. So the priority is: get a release with real 5.1 audio first, then worry about video codec.

**Why x264 ranks second:** A native H.264 release means no transcoding needed at all. HEVC and AV1 need to go through Tdarr before they direct-play everywhere, so there's a real operational cost to grabbing them — they're not avoided, just deprioritized.

The minimum custom format score is set to 100, meaning Radarr won't grab anything without verified surround audio. Max quality is capped at Bluray-1080p (not Remux) to keep file sizes manageable — Remux files can be 40–60GB each, which is untenable at nas-pi's upload speed ceiling.

---

## The Security Incident

In Q2 2026, qBittorrent downloaded a batch of torrent files that contained `.exe` and `.scr` executables disguised as TV episodes. The files showed up in Sonarr as completed downloads but obviously weren't playable video.

**What happened:** A torrent indexer (since removed) was either compromised or simply hosted malicious content. The files made it all the way through the pipeline — downloaded, extracted, and sitting in the downloads directory — before being flagged.

**The risk:** `.scr` files are Windows screensavers — executable by double-click. On a Linux server, they're inert. But the incident raised a real question: had anything actually run? The answer was almost certainly no (qBittorrent runs as a non-privileged user, and nothing in the pipeline executes downloaded files), but "almost certainly" isn't "definitely."

**What changed:**
- Removed the indexer that served the malicious content
- Audited all remaining indexers and set per-indexer minimum seeder counts in Prowlarr (low-seeder releases are statistically higher risk)
- Added Uptime-Kuma alerting so unusual activity is more visible
- Accepted that this is an inherent risk of the download pipeline and the mitigation is defense-in-depth (non-privileged users, container isolation, regular audits), not elimination

The episode was a good reminder that running a download pipeline isn't a set-and-forget operation. Indexer quality matters.

---

## Indexers (via Prowlarr)

Current active indexers, synced automatically to Radarr and Sonarr:

- 1337x
- The Pirate Bay
- Knaben
- YTS (movies)
- LimeTorrents (TV)
- EZTV (TV)

TorrentGalaxy was removed after persistent redirect and connection errors. Indexer reliability matters — a slow or flaky indexer degrades the whole pipeline's responsiveness.

---

## Lessons Learned

**Get the `/data` mount structure right first, before adding content.** Retroactively fixing hardlinks in an existing library is painful. Plan the filesystem layout before you import anything.

**Quality profiles are genuinely powerful but need domain knowledge.** The custom format scoring system only makes sense once you understand what Tdarr can and can't do, what your clients can direct-play, and what your storage constraints are. It took a few iterations to get to a setup that makes the right tradeoffs automatically.

**Indexer hygiene matters for both reliability and security.** Remove indexers that misbehave. Set minimum seeder counts. Don't treat the indexer list as "more is better."
