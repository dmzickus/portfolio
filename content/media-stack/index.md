---
title: Self-Hosted Media Stack
nav_label: Media Stack
icon: 🖥️
icon_color: ''
badge: ''
order: 80
description: A full homelab media pipeline on a Raspberry Pi 5 — Jellyfin, automated library management via the arr stack, VPN-tunneled downloads, and cross-network hardware transcoding with Intel Quick Sync.
tags:
- Jellyfin
- Docker
- WireGuard
- Raspberry Pi
- Tdarr
pills:
- Raspberry Pi 5
- Docker
- Jellyfin
- WireGuard / AirVPN
- Intel QSV
- Tailscale
- OpenMediaVault
---

# Self-Hosted Home Media Stack

> A fully self-hosted media server, automated library management pipeline, and transcoding infrastructure — built on a Raspberry Pi 5, an old workstation, and a lot of troubleshooting.

## What is this?

This is a writeup of a project I've been building and iterating on throughout 2026: a home media stack that replaces streaming services with a fully self-hosted setup. No subscriptions, no content disappearing, no algorithmic recommendations — just a local library I control, available on any device anywhere.

The stack handles everything from **finding and downloading media**, to **organizing and cataloging it**, to **streaming it to any device** with near-zero transcoding. There's also an automated transcoding pipeline that normalizes the library's codec mix for maximum compatibility.

It's the kind of project that started simple and kept growing. What began as "just run Jellyfin on a Pi" turned into a multi-machine system with VPN-tunneled downloads, cross-network hardware transcoding, and more `docker-compose` files than I'd like to admit.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                   nas-pi (Pi 5)                  │
│                                                  │
│  Jellyfin (native)   ←── media library           │
│  Radarr / Sonarr / Lidarr / Bazarr              │
│  Prowlarr (indexer proxy)                        │
│  qBittorrent ──────────── Gluetun (AirVPN)      │
│  Tdarr Server (no local workers)                 │
│  Homarr · Jellystat · Beszel · Uptime-Kuma      │
└──────────────┬──────────────────────────────────┘
               │ Tailscale (Samba/SMB)
               │
┌──────────────▼──────────────────────────────────┐
│                  z240 (HP Workstation)            │
│                                                  │
│  Tdarr Node (Docker/Podman)                      │
│  Intel QSV hardware encode (HD P530)             │
└─────────────────────────────────────────────────┘
```

All download traffic routes through a WireGuard VPN tunnel (AirVPN via Gluetun). The arr stack containers share the VPN container's network namespace, so nothing leaks if the tunnel drops. Jellyfin streams directly to clients on the local network or via Tailscale from anywhere.

The transcoding node runs on a separate machine connected over Tailscale, using Intel Quick Sync for hardware-accelerated H.264 encoding. Files travel over SMB-on-Tailscale between machines.

---

## The Stack at a Glance

| Component | Role | Page |
|-----------|------|------|
| nas-pi (Pi 5 + OMV) | NAS, host for everything | [Infrastructure](./infrastructure.md) |
| Jellyfin | Media server, streaming | [Jellyfin](./jellyfin.md) |
| Radarr / Sonarr / Lidarr / Bazarr | Automated library management | [The arr Stack](./arr-stack.md) |
| Prowlarr + qBittorrent + Gluetun | Indexing, downloading, VPN routing | [VPN & Downloading](./vpn-routing.md) |
| Tdarr + z240 QSV node | Automated transcoding pipeline | [Tdarr Pipeline](./tdarr.md) |
| Homarr, Beszel, Jellystat, Uptime-Kuma | Dashboard & monitoring | [Infrastructure](./infrastructure.md) |

---

## Timeline

### Q1 2026 — Foundation
Set up the Raspberry Pi 5 as a NAS running OpenMediaVault. Got Jellyfin running natively (not containerized — more on why). Figured out storage layout, permissions, and remote access via Tailscale. This phase was mostly infrastructure groundwork: getting a stable, remotely accessible machine that could serve media reliably.

### Q2 2026 — Automation
Deployed the full arr stack: Radarr, Sonarr, Lidarr, Bazarr, Prowlarr, and qBittorrent — all containerized and routed through a Gluetun VPN tunnel. Spent significant time on hardlink configuration (critical for keeping a clean library without duplicating storage), quality profiles, and custom format scoring in Radarr/Sonarr. Also dealt with a security incident involving disguised malware in torrent files — documented in the arr stack page.

### Summer 2026 — Transcoding & Monitoring
Built the Tdarr transcoding pipeline to normalize the library to H.264 for direct play everywhere. This turned into a deep rabbit hole: NFS failures on a memory-constrained Pi, a custom Docker image to get Intel QSV working, cross-network SMB mounts over Tailscale, and a lot of `vainfo` output. Also set up the full monitoring stack (Beszel, Jellystat, Uptime-Kuma) and a Homarr dashboard to tie everything together.

---

## Why Self-Host?

Honestly, a mix of practical and philosophical reasons:

- **Control** — content I've downloaded doesn't disappear when a licensing deal expires
- **Compatibility** — Jellyfin runs on everything: browsers, phones, TVs, game consoles
- **Cost** — after the initial hardware, it's effectively free
- **Learning** — this project has touched Linux administration, Docker networking, VPN configuration, codec pipelines, and cross-machine file sharing. It's been one of the best practical learning experiences I've had

The tradeoff is real though: you become your own ops team. When something breaks at 11pm, that's on you to fix.

---

## Pages in This Section

- [Infrastructure](./infrastructure.md) — nas-pi, OpenMediaVault, hardware, and monitoring
- [Jellyfin](./jellyfin.md) — media server setup, native install, and stability debugging
- [The arr Stack](./arr-stack.md) — automated library management and quality control
- [VPN & Downloading](./vpn-routing.md) — Gluetun, AirVPN, WireGuard, and download routing
- [Tdarr Pipeline](./tdarr.md) — automated transcoding to H.264 with Intel Quick Sync
