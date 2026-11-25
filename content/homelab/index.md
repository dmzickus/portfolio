---
title: Homelab
short_title: Homelab
summary: A Raspberry Pi NAS that grew into Proxmox VMs, an OPNsense firewall with five VLANs, and remote access through Tailscale and Cloudflare. Every other homelab project runs on this.
status: live
area: homelab
rank: 1
started: 2026-04
role: Design, build and day-to-day operation (the Proxmox host is shared with a roommate)
stack: [Proxmox, Debian, OpenMediaVault, Docker, OPNsense, Tailscale, Cloudflare Tunnel, mergerfs]
focus: [infra]
tags: [Linux, Docker, Proxmox, Networking, VLANs, OPNsense, Tailscale, Cloudflare, Raspberry Pi, Self-hosting]
timeline:
  - date: 2026-04
    text: First Raspberry Pi 5 arrives and becomes a NAS running OpenMediaVault and Samba, with Tailscale for remote access.
  - date: 2026-04
    text: Tried network-booting a small Pi cluster from one SSD. Shelved; the cluster idea is parked for now.
  - date: 2026-06
    text: Repurposed an HP Z240 workstation. It started as a CPU-only LLM box, then became a small hosting server.
  - date: 2026-06
    text: Planned a Pi-hole + Unbound DNS stack on a Pi 3B. Never deployed. The Pi's 100 Mbps NIC was a bottleneck, and OPNsense later made it unnecessary.
  - date: 2026-09
    text: Storage and services moved off the Pi into a Debian VM on a Proxmox host, with the Intel iGPU passed through and two 2 TB drives pooled with mergerfs.
  - date: 2026-10
    text: OPNsense VM takes over routing. Five VLANs through a managed switch; VMs can only reach each other through firewall rules.
  - date: 2026-10
    text: The old Pi 5 is retired from NAS duty and becomes a dedicated Tailscale exit node.
  - date: 2026-11
    text: Public apps move from Tailscale Funnel to Cloudflare Tunnel behind Cloudflare Access.
  - date: 2026-11
    text: Claude starts running the homelab's daily health check through a custom MCP server. See the [ops agent](/ops-agent/).
---

This is the platform everything else runs on: the [media server](/media-stack/), [music](/music-stack/), [photos](/immich/), the [couch game box](/couch-box/) and the [ops agent](/ops-agent/) that watches over all of it. It started as one Raspberry Pi in April 2026 and has been rebuilt twice since.

## What it looks like now

| Piece | Job |
|---|---|
| Proxmox host (Intel i5-8500, 48 GB) | Runs everything as VMs. It's my roommate's machine, so the rule is that VMs never talk to the hypervisor. |
| Media VM (Debian + OpenMediaVault) | Docker host for the media, music and photo stacks. Gets the CPU's Quick Sync iGPU through VFIO. |
| Storage | Two 2 TB drives pooled with mergerfs. Configs and databases sit on NVMe; caches and backups on a separate HDD. |
| OPNsense VM | Router and firewall. Its NIC is passed through, with one trunk to a managed switch. |
| Raspberry Pi 5 | Formerly the NAS, now a Tailscale exit node. |
| Home Assistant (Pi 5) | The [smart home](/home-assistant/), deliberately kept on its own box. |

## Network

The network is split into five VLANs: local devices, trusted machines, exposed services, management, and an isolated one for untrusted things like the [game pipeline](/couch-box/). VMs can't see each other directly. Everything goes through OPNsense rules, so a compromised container on the media VM can't reach the Proxmox management interface.

Remote access comes in two flavours. I use **Tailscale** for anything only I or my roommates should reach. A few apps are meant for friends and family, like media requests and photos. Those go through a **Cloudflare Tunnel** with **Cloudflare Access** in front, so nothing is port-forwarded on the home router.

## Why it got rebuilt

The original Pi 5 did everything: NAS, media server, about fifteen containers, Samba. It worked until it didn't. When I tried to add an NFS export for a transcoding node, the kernel couldn't even allocate memory for the NFS threads. The Pi had 486 MB free and was nearly 2 GB into swap. That was the push to move to real hardware.

The migration had a few hard requirements:

- **Hardlinks had to keep working.** The download and library folders are on one filesystem so imports are instant and don't double the space used. That meant one unified `/data` tree, mounted identically in every container.
- **Keep the history.** Watch history and stats, app databases, and requests all moved over; Jellyfin itself went from a native install to a container with its data carried along.
- **The drives moved, they weren't copied.** The same two disks were moved to the new host and pooled.

## How it's kept tidy

Every service stack lives in its own `/opt/<stack>` folder with a compose file. Every container gets a name and a healthcheck. Secrets live in one env file. Scheduled jobs log to one place. I wrote those rules down as a policy file when I set up the [ops agent](/ops-agent/). Writing them down turned out to be the most useful part of that project, because anything that follows the rules can be monitored and repaired automatically.

## What's next

- A small monitoring Pi so the health checks cover every machine, not just the media VM
- Locking the couch box onto its own VLAN with Tailscale ACLs instead of the default allow-all
- [Frigate](/frigate/) if outdoor cameras ever happen
