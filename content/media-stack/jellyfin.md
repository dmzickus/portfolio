---
title: Jellyfin
icon: 📺
icon_color: green
description: Open-source media server handling library cataloging, metadata, and streaming. Why it runs natively instead of containerized, and the crash-debugging saga.
tags:
- Jellyfin
- Direct play
- Streaming
---

# Jellyfin

> Open-source media server. Streams the library to browsers, phones, TVs, and anything else with a network connection.

## What Jellyfin Does

Jellyfin is the frontend of the whole stack — it's what you actually interact with when you want to watch something. It handles:

- **Cataloging** the media library with metadata, artwork, and descriptions pulled from online databases (TMDB, MusicBrainz, etc.)
- **Streaming** to clients: browser, iOS/Android app, TV apps, game consoles
- **Transcoding** on-the-fly when a client can't play a file natively — converting it to something compatible in real time
- **User management** — multiple users with separate watch histories and preferences

The goal is to get as close to **direct play** as possible: the server sends the file as-is and the client decodes it locally. Transcoding is expensive (CPU-heavy, increases latency, and can degrade quality), so the [Tdarr pipeline](./tdarr.md) exists specifically to normalize the library to a codec and container that every client can direct-play.

---

## Why Native, Not Containerized

Almost everything in this stack runs in Docker containers. Jellyfin is the exception — it runs as a native `systemd` service on the Pi 5.

The containerized Jellyfin image on ARM had recurring stability issues that were difficult to diagnose and harder to fix inside a container (library paths, hardware device access, etc.). Running it natively gives direct access to the filesystem and system logs, makes `systemctl` management straightforward, and sidesteps a class of container networking issues around media library paths.

The tradeoff: updates require a manual `apt upgrade` rather than a `docker compose pull`. Worth it for the stability.

---

## Configuration Highlights

**Library paths** are shared with the arr stack containers via a unified `/data` directory structure. This is important for hardlinks to work — Radarr needs to be able to move a completed download into the library using a hardlink (not a copy), which only works if both the download directory and the library directory are on the same filesystem. Jellyfin's library root matches this layout.

**User preferences** handle audio and subtitle defaults — default English audio track, no default subtitles — rather than encoding these preferences into the files themselves. This keeps the pipeline simpler (Tdarr doesn't need to set default stream flags) and lets different users configure their own preferences independently.

**Hardware transcoding** is intentionally left mostly unused. The Pi 5 doesn't have useful hardware encode capability, and software transcoding at 1080p is CPU-intensive enough to cause problems if multiple streams need it simultaneously. The answer is to avoid transcoding in the first place — hence the Tdarr pipeline.

---

## Stability Issues

Jellyfin on the Pi 5 has had two distinct crash incidents:

### Crash 1: Permission Reset Loop

The `/var/log/jellyfin` directory kept having its permissions reset, causing Jellyfin to crash when it couldn't write logs. The root cause was a combination of how the native package sets up permissions on startup and an interaction with OMV's filesystem management. Fixed by locking down the directory ownership and ensuring the `jellyfin` user owned it persistently.

### Crash 2: Missing Log Directory

A later crash (signal `ABRT`) was traced to `/var/log/jellyfin` not existing at all — the directory had been removed, possibly during an OS-level cleanup or a manual tidy that went too far. Jellyfin couldn't start because it had nowhere to write logs. Fixed by recreating the directory with correct ownership, then confirmed with `systemctl status jellyfin` that it came back clean.

Both crashes were annoying to diagnose remotely (SSH into the Pi from the apartment, read journals, chase file permissions), but ultimately straightforward fixes once the root cause was clear.

---

## What Good Looks Like

With the Tdarr pipeline completing its initial library pass, the steady-state goal is:

- **100% direct play** for 1080p H.264 content on all clients
- Zero transcoding during normal playback
- Jellystat confirming direct-play rates over time

Jellyfin's own dashboard shows per-stream play method (Direct Play / Direct Stream / Transcode) — watching that metric improve as the library gets normalized is a good feedback loop.
