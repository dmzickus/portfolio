---
title: Infrastructure
icon: 🖥️
icon_color: ''
description: The Raspberry Pi 5 NAS running OpenMediaVault, remote access via Tailscale, and the full monitoring stack — Beszel, Jellystat, Homarr, Uptime-Kuma.
tags:
- Pi 5
- OpenMediaVault
- Tailscale
- Beszel
---

# Infrastructure

> The hardware and base OS layer that everything else runs on.

## The Hardware

### nas-pi — Raspberry Pi 5 (8GB)

The primary server for the entire media stack. The Pi 5 was a significant step up from older Pi hardware — enough RAM to run Docker Compose, Jellyfin, and several arr stack containers concurrently, with an actual PCIe bus for real NVMe storage.

**Why a Pi 5 specifically?**
- 8GB RAM — enough headroom to run a full arr stack, Jellyfin, and monitoring containers simultaneously
- Passive-coolable with a good case, silent 24/7 operation
- Low idle power draw — this machine runs constantly
- PCIe Gen 2 x1 interface for an NVMe HAT (real random I/O, not USB-attached storage)

**Limitations I've run into:**
- No hardware video encode — the Pi 5's VideoCore can decode but not encode in any useful way for transcoding. This is why the Tdarr transcoding node lives on a different machine entirely.
- RAM pressure is real when everything is running. The NFS server experiment (documented in the [Tdarr page](./tdarr.md)) failed entirely because the Pi ran out of memory trying to start `nfsd` while Jellyfin and the arr stack were up.

### z240 — HP Z240 Workstation

An older HP workstation repurposed as a secondary compute node. Runs the Tdarr transcoding worker using its integrated Intel HD P530 graphics for Quick Sync hardware encoding. Not always on — it spins up for transcoding work and hosts some other Docker services.

---

## Operating System: OpenMediaVault

The Pi 5 runs **OpenMediaVault (OMV)**, a Debian-based NAS OS. OMV handles:

- Storage management (disk setup, shared folder definitions, SMART monitoring)
- Samba/SMB share configuration — critically, OMV auto-generates `smb.conf`, which means you cannot edit it directly. Any change has to go through OMV's web UI or it'll be overwritten on the next OMV operation. This caused a debugging headache when the z240 couldn't write to the media share (documented in the Tdarr page).
- Docker integration via the `compose` plugin — all containerized services are defined in Docker Compose files managed through OMV's UI

Jellyfin runs **natively** (outside Docker) because of stability issues with the containerized version on ARM. Everything else runs in containers.

---

## Networking & Remote Access

Remote access is via **Tailscale**, a WireGuard-based mesh VPN. Every machine — nas-pi, z240, and any client I'm using — is on the same Tailscale network regardless of physical location.

This means:
- Jellyfin is accessible from the apartment without any port forwarding or dynamic DNS
- The z240 can mount nas-pi's media share over SMB-on-Tailscale for transcoding
- SSH into nas-pi from anywhere with no configuration changes

The connection between nas-pi and z240 is a direct Tailscale peer-to-peer link (not relayed), running at around 115–127 Mbit/s sustained — enough for the transcoding pipeline to work without the network being the bottleneck.

---

## Monitoring Stack

### Beszel

Lightweight system monitoring — CPU, RAM, disk, network. Replaced Netdata, which was removed from the stack because it was too resource-heavy for a Pi 5 running this many services concurrently. Beszel runs as a server + per-machine agent architecture and integrates with the Homarr dashboard.

### Jellystat

Jellyfin-specific statistics and usage tracking. Backed by a Postgres database container. Tracks what's been watched, playback history, and stream quality. Useful for auditing whether the transcoding work is actually paying off in direct-play rates.

### Uptime-Kuma

Service health monitoring with alerting. Watches all the key services (Jellyfin, Radarr, Sonarr, etc.) and alerts if anything goes down. Simple but effective.

### Homarr

The dashboard that ties everything together — a single browser tab showing the status of every service, quick links, and widgets from Beszel/Uptime-Kuma. Much easier than bookmarking individual service UIs.

---

## Lessons Learned

**OMV is opinionated and will fight you if you go around it.** Editing system files it manages directly always backfires. Work through the UI, or accept that your changes will be silently overwritten.

**RAM budgeting matters on a Pi.** Eight gigabytes sounds like plenty until you're running Jellyfin (with active streams), qBittorrent, six arr stack containers, three monitoring containers, and a Docker daemon — and then you try to start an NFS server. Profile memory usage before adding new services.

**Tailscale is genuinely magic for this use case.** Zero-configuration encrypted cross-network connectivity with direct peer-to-peer connections where possible. It's been the most "set it and forget it" piece of the entire stack.
