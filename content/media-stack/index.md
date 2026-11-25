---
title: Self-Hosted Media Server
short_title: Media server
summary: Jellyfin for the apartment and family, with request-driven library automation, a 2 TB size budget, hardware
  transcoding, and a nightly "preshow" of vintage trailers before movies.
icon: 🎬
highlights:
- Request → library automation → Jellyfin
- 2 TB budget enforced by cleanup rules
- Nightly vintage 'preshow' before movies
status: live
area: homelab
rank: 3
started: 2026-04
role: Solo; used daily by roommates, friends and family
stack:
- Jellyfin
- Docker
- Sonarr
- Radarr
- Seerr
- Maintainerr
- WireGuard (Gluetun)
- Intel Quick Sync
- ffmpeg
focus:
- infra
tags:
- Docker
- Linux
- Jellyfin
- ffmpeg
- WireGuard
- Networking
- Self-hosting
- Automation
- Bash
timeline:
- date: 2026-04
  text: Jellyfin installed natively on a Raspberry Pi 5 next to OpenMediaVault.
- date: 2026-05
  text: Request-driven library management with Seerr, Sonarr and Radarr. Download clients isolated inside a WireGuard
    container's network namespace.
- date: 2026-07
  text: Codec audit of 352 files (740 GB). Remote transcoding node built over Tailscale. See [Tdarr pipeline](/tdarr-transcoding/).
- date: 2026-07
  text: Upload-speed analysis from 580 daily speed tests sets an 8 Mbps per-stream cap, enough for three remote
    streams without transcoding.
- date: 2026-09
  text: Migrated to a Proxmox VM. Jellyfin containerized with Quick Sync passthrough; watch history and app data
    carried over.
- date: 2026-11
  text: Quality rules switched to HEVC with 5.1 audio now that the server can transcode in hardware. Space became
    the constraint.
- date: 2026-11
  text: A 2 TB budget, enforced by Maintainerr cleanup rules with a grace period. Anything someone watched, requested
    or favorited is kept.
- date: 2026-11
  text: Nightly generated "preshows" for Jellyfin cinema mode, with local trailers and vintage theater bumpers.
---
The media server replaced streaming subscriptions for the apartment and a few family members. People request a movie or show from a web page, it shows up in Jellyfin a while later, and it plays on the living room Roku, phones, or laptops anywhere.

## The pieces

- **Jellyfin** serves the library. It's containerized on the [homelab](/homelab/)'s media VM, with Intel Quick Sync passed through for hardware transcoding.
- **Seerr** is the front door: anyone with an account can request something.
- **Sonarr and Radarr** manage the library. They pick a release that matches the quality rules, rename and file it, and keep the library tidy. Downloads and imports use hardlinks on one filesystem, so a finished download doesn't take up space twice.
- **The download clients run inside a WireGuard container's network namespace.** They have no network path except the tunnel, so if the tunnel drops, they lose connectivity instead of leaking onto the home connection.
- **Maintainerr** enforces the size budget (below).
- **Jellystat** keeps watch history and statistics, which feed the cleanup rules.

## Rules instead of babysitting

Most of the work on this project has been turning "I'll keep an eye on it" into rules:

- **Quality profiles decide what gets downloaded.** Custom-format scores prefer 5.1 audio and efficient codecs and cap size at 1080p Blu-ray, so files arrive already playable and the right size. This is what made the [transcoding pipeline](/tdarr-transcoding/) unnecessary.
- **A 2 TB budget for movies and TV.** Cleanup rules flag titles nobody has watched, requested, or favorited. They show up in a "leaving soon" list with a grace period before anything is deleted. A short list of staples is always kept. Deletions also unmonitor the title and clear the request, so nothing is downloaded again by accident.
- **Nightly jobs** import stuck downloads, clear orphaned partial downloads, and keep subtitles and metadata in order. They log to one folder that the [ops agent](/ops-agent/) reads every morning.

## The preshow

The Roku app plays only the first cinema-mode intro before a movie, so the normal "a few trailers, then the movie" setup didn't work. A nightly job instead builds ten merged preshow clips. Each one has an upcoming-release trailer, a trailer for something already in the library, and a vintage theater bumper, with rating cards in between. There are seasonal variants, and the Christmas one runs longer than it should. New bumpers only go into rotation after I approve them.

## Numbers

| | |
|---|---|
| Accounts | 6 (roommates, friends, family) |
| Library budget | 2 TB movies + TV |
| Remote stream cap | 8 Mbps each, based on measured upload (median 40 Mbps) |
| Transcoding | Intel UHD 630 (Quick Sync), H.264 / HEVC / VP9 |

## Earlier versions

The first version ran on the Pi 5 with Jellyfin installed natively. It worked, but the Pi has no usable hardware encoder and was out of memory. The [Tdarr pipeline](/tdarr-transcoding/) was the workaround, and the [homelab](/homelab/) migration was the real fix.
