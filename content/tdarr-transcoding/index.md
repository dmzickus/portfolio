---
title: Remote Transcoding Pipeline
short_title: Tdarr pipeline
summary: A Tdarr transcoding node on a second machine, connected over Tailscale and using Intel Quick Sync, to normalize
  the media library for direct play. Retired once quality rules at download time made it unnecessary.
icon: 🎞️
highlights:
- Quick Sync node two networks away
- Debugged NFS, VA-API and OMV Samba
- 'Retired: fixed at download time instead'
status: retired
area: homelab
rank: 20
started: 2026-07
ended: 2026-11
role: Solo
stack:
- Tdarr
- Docker
- ffmpeg
- Intel Quick Sync (VA-API)
- Tailscale
- Samba
- OpenMediaVault
focus:
- infra
tags:
- Docker
- ffmpeg
- Linux
- Networking
- Tailscale
- Hardware debugging
- Self-hosting
timeline:
- date: 2026-07
  text: Library audit shows 119 of 352 files (234 GB) in codecs that force the Pi to transcode.
- date: 2026-07
  text: Tdarr server on the Pi; a node on an HP Z240 two networks away, connected over a direct Tailscale link (~15
    MB/s).
- date: 2026-07
  text: NFS export fails. Root cause is the Pi being out of memory, not the config.
- date: 2026-07
  text: Built a custom node image with the Intel media driver; Quick Sync verified working inside the container.
- date: 2026-07
  text: Tracked the Samba write failure to an OMV-generated read-only override on the share.
- date: 2026-11
  text: Retired. Quality rules at download time do the same job, and the new server transcodes in hardware.
---
The original media server was a Raspberry Pi 5, which can decode video but has no usable hardware encoder. Any file a client couldn't play directly meant the Pi transcoding in software, badly. The plan was to convert the library ahead of time into formats every client could play, using a machine that *could* encode in hardware.

## Setup

- **Tdarr server** on the Pi, holding the queue and the library.
- **Tdarr node** on an HP Z240, which isn't on the same LAN. It's connected over Tailscale; I verified with `iperf3` that the link was direct rather than relayed (~49 ms, ~120 Mbit/s). It used the Xeon's integrated GPU for Quick Sync encoding.
- **One GPU worker only**, because the network link was the bottleneck, not the encoder.
- **An explicit FFmpeg command node** instead of Tdarr's generic encoder node, because the generic node silently falls back to CPU encoding when QSV isn't configured exactly right.

## Debugging it

Most of the time went into layers that had nothing to do with video:

1. **Bind mounts:** `statfs: no such file or directory`. The host folders the compose file mounted didn't exist yet.
2. **NFS:** `nfs-server` wouldn't start. Writing to `/proc/fs/nfsd/threads` returned *Cannot allocate memory*. The Pi was down to 486 MB free and nearly out of swap. I dropped NFS and used the existing SMB share.
3. **No VA-API driver** in the stock node image. I built a thin wrapper image (`FROM` the official image plus `intel-media-va-driver-non-free`) instead of patching a running container. `vainfo` then showed the H.264 low-power encode entrypoint.
4. **SMB was read-only for the node.** Two separate causes: the node's user wasn't in the group that owned the media folders, and OpenMediaVault had generated a `read list` override for that user on the share. Editing `smb.conf` directly doesn't stick because OMV regenerates it, so the fix had to go through OMV's share privileges.

## Why it's retired

Two things made it pointless. The [media server](/media-stack/) moved to a machine with Quick Sync, so transcoding on the fly is cheap. And the quality rules now pick releases that are already the right codec and size when they're downloaded. Converting after the fact was solving the problem at the wrong end.
