---
title: Tdarr Pipeline
icon: 🎬
icon_color: ''
description: Automated transcoding to normalize 117 files to H.264 for direct play. Cross-network QSV encoding, a custom Docker image to get VA-API working, the NFS failure, and the OMV/Samba debugging rabbit hole.
tags:
- Tdarr
- Intel QSV
- H.264
- FFmpeg
---

# Tdarr Transcoding Pipeline

> Automated library normalization: every file gets converted to H.264 + AC3 so every client can direct-play without the server breaking a sweat.

## The Problem

A media library accumulated over time from different sources ends up with a chaotic codec mix. An audit of the full library (352 files, ~740GB) revealed:

| Codec | Files | Size |
|-------|-------|------|
| H.264 (already good) | 233 | 506.5 GB |
| HEVC (H.265) | 96 | — |
| AV1 | 21 | — |
| **Needs conversion** | **117** | **~233.5 GB** |

The HEVC files were mostly *House of the Dragon* (S01, S03). The AV1 files were S02 of the same show plus *Cyberpunk: Edgerunners*. Neither codec direct-plays on all clients — older TVs, game consoles, and some browser implementations fall back to software transcoding or refuse to play entirely.

The goal: get every file to **H.264 video, AC3/AAC audio, SRT subtitles** — a combination that direct-plays on essentially everything.

---

## Architecture

The Pi 5 (`nas-pi`) has no usable hardware video encoder. Running software transcoding on it for 117 files would take days and put sustained 100% CPU load on the machine that also runs the arr stack and Jellyfin.

The solution: **distributed Tdarr** with the encode work offloaded to a separate machine.

```
nas-pi                          z240 (HP Workstation)
─────────────────────           ──────────────────────────────
Tdarr Server                    Tdarr Node (Docker/Podman)
  - manages the queue     ←──→    - pulls jobs from server
  - no local workers              - Intel QSV hardware encode
  - internalNode=false            - reads/writes via SMB mount
                                  - 1 GPU worker (network cap)
```

The z240 has an Intel HD P530 integrated GPU with Quick Sync Video (QSV) — Intel's fixed-function hardware encoder. QSV can encode H.264 at 10–20x real-time speed while barely touching CPU, and the power draw is a fraction of software encoding.

Files travel between machines over **SMB mounted on Tailscale** — the z240 mounts nas-pi's media share, reads the source file, encodes it locally in a temp directory, and writes the output back. The Tailscale link sustains ~115–127 Mbit/s between the two machines, enough that network I/O isn't the bottleneck.

---

## Getting QSV Working: The Docker Image Problem

The standard `tdarr_node` Docker image doesn't include the Intel VA-API drivers needed for QSV. The first attempt to use hardware encoding silently fell back to software — Tdarr's generic "Set Encoder" node is known to do this without any warning.

Two fixes:

**1. Use an explicit FFmpeg Command node instead of Set Encoder.**
The FFmpeg Command node in the Tdarr Flow editor lets you specify the exact encoder (`h264_qsv`) rather than relying on Tdarr's abstraction layer to pick it. No silent fallback.

**2. Build a custom Docker image with the VA-API driver.**
```dockerfile
FROM ghcr.io/haveagitgat/tdarr_node:latest
RUN apt-get update && apt-get install -y \
    intel-media-va-driver-non-free \
    && rm -rf /var/lib/apt/lists/*
```

After building and starting this image, `vainfo` inside the container confirmed:
- `iHD` driver loaded (Intel's modern VA-API implementation)
- `H264 VAEntrypointEncSliceLP` available — that's the Quick Sync low-power encode entry point

QSV was working. The encode target:

```
h264_qsv
  global_quality: 20
  scale cap: 1920px width
  audio: add AC3 5.1 640k track if missing; convert lossless (DTS-HD MA, TrueHD) to AC3
  subtitles: OCR PGS → SRT (despite quality tradeoff, SRT direct-plays everywhere)
```

---

## The NFS Rabbit Hole

Getting files from nas-pi to z240 should have been simple. The first approach: NFS share from nas-pi, mounted on z240.

It wasn't simple.

**Attempt 1: NFS**

`nfs-server.service` on nas-pi failed to start with a `nfsdctl lockd configuration failure / exit code 1`. After digging into the journal:

```
writing to /proc/fs/nfsd/threads failed: Cannot allocate memory
```

The Pi 5 was out of RAM. At the time of the NFS attempt, nas-pi was running Jellyfin, the full arr stack, Docker, and OMV — sitting at 486MB free RAM with 1.7GB of its 2GB swap in use. Starting an NFS server on top of that was never going to work.

Root cause: the NFS kernel server allocates memory at startup based on the number of threads requested. With essentially no free RAM, the kernel rejected the allocation.

**Attempt 2: Samba/SMB**

Switched to SMB (already in use on nas-pi for other purposes). Faster to set up, no kernel memory requirements.

Hit a second wall: the z240 could mount the share but couldn't write to it. The SMB mount succeeded, files were readable, but every write attempt returned "permission denied."

Debugging layers:
1. Checked filesystem permissions on nas-pi — looked fine
2. Checked Samba share config — found `read list = z240`, an explicit read-only override
3. Tried editing `smb.conf` directly — changes were overwritten within seconds

Root cause: **OMV manages `smb.conf` automatically**. Any direct edit is silently overwritten whenever OMV makes a change. The correct fix: go into OMV's web UI → Shared Folder → Privileges/ACL for the media folder → remove `z240` from the read-only list.

After that fix and an `smbd` restart, write access worked. The full debugging path took longer than it should have because the "smb.conf is managed" behavior isn't well-documented in OMV's UI.

---

## Audio & Subtitle Strategy

**Audio:**
- If a file already has both stereo and 5.1 tracks: leave them both as-is
- If a file has only 5.1 lossless (DTS-HD MA, TrueHD): convert to AC3 5.1 (lossy but direct-playable)
- If a file has only stereo: leave it — Tdarr cannot fabricate real surround from a stereo mix
- Do not upmix stereo to fake 5.1

The "no upmix" decision is about honesty. Upmixed surround sounds worse than the original stereo mix and wastes space. If real 5.1 audio matters for a specific title, Radarr's quality profiles will find a 5.1 source (see the [arr stack page](./arr-stack.md)).

**Subtitles:**
- PGS (image-based) subtitles: OCR-convert to SRT
- SRT/ASS text subtitles: pass through unchanged
- The OCR conversion loses some formatting and occasionally mistranscribes text, but SRT subtitles direct-render on every client. PGS requires server-side rendering (transcoding), which defeats the whole point.

---

## Lessons Learned

**Silent fallback is the enemy of hardware encoding pipelines.** Tdarr's Set Encoder node falling back to software without logging it was hours of "why is this so slow" before I found the explicit FFmpeg Command node approach. Always verify hardware encoding is actually happening — check `vainfo`, check the Tdarr worker logs for the encoder string being used.

**NFS on a memory-constrained machine is a non-starter.** The Pi 5 at 8GB has enough RAM for its normal workload, but that workload leaves little headroom. NFS's kernel-space memory requirements pushed it over the edge. SMB/Samba is userspace and much lighter.

**OMV is the source of truth for Samba config, not `smb.conf`.** Any time something seems wrong with a share on an OMV machine, check the OMV UI first. Direct config edits are a trap.

**One GPU worker is the right call at this network throughput.** At ~115 Mbit/s sustained, the network link can handle about one 1080p H.264 encode stream worth of I/O at a time. Running two workers would have them competing for the same pipe. Cap it at one and let it run.
