---
title: Couch Game Box and Untrusted-File Pipeline
short_title: Couch game box
summary: A small PC under the TV that boots straight into a controller-driven game menu, fed by a pipeline that
  treats every downloaded file as hostile. Quarantine, hashing, multi-engine scanning, an approval step, and offline
  installs on an isolated machine.
icon: 🎮
highlights:
- Boots straight to a controller menu
- Library mounted read-only over NFS
- Every download treated as hostile
status: building
area: homelab
rank: 6
started: 2026-10
role: Solo (the PC is a roommate's)
stack:
- Bazzite Linux
- RetroDECK / ES-DE
- Wine / umu
- NFS
- Samba
- VirusTotal API
- Windows Defender
- systemd timers
- Tailscale ACLs
focus:
- infra
tags:
- Linux
- Security
- Networking
- VLANs
- Automation
- Bash
- Python
- Self-hosting
timeline:
- date: 2026-10
  text: A Dell OptiPlex mini PC becomes the couch box. Bazzite boots straight into a controller-driven menu; the
    library is a read-only NFS mount from the NAS.
- date: 2026-10
  text: First intake pipeline. Downloads land in a drop folder, get hashed and checked against VirusTotal, then
    a Defender scan runs.
- date: 2026-10
  text: Redesigned as "assume infected." Detection is a filter, not a guarantee, so containment does the real work.
- date: 2026-11
  text: A fake installer tried to download extra files. New Windows installs now need my approval and run offline.
- date: 2026-11
  text: Library shares locked down; game folders read-only, with a separate drop share for adding new ones.
- date: 2026-11
  text: The couch box joins the ops agent's daily check, including items held for review or quarantined.
- date: 2026-12
  text: Move the box onto the isolated VLAN and replace the default allow-all Tailscale policy with ACLs.
---
The apartment wanted one box under the TV for retro games and party games that anyone could use with a controller. It shouldn't need a keyboard or someone technical. The interesting part turned out to be getting games *onto* it safely.

## The box

A roommate's Dell OptiPlex runs **Bazzite** and auto-boots into **ES-DE** through RetroDECK. The game library lives on the NAS and is mounted **read-only over NFS**, so the box can't change or delete the library. It mixes Xbox, 8BitDo and Switch Pro controllers. Alexa can switch the TV to it ("Game Box"), and I maintain it over Tailscale. PC games run through Wine/umu from a small per-game launch file. A local copy is never deleted automatically when a game leaves the NAS.

## The untrusted-file pipeline

Anything downloaded is treated as hostile until proven otherwise, and I assume the scanners will miss things. The steps:

1. **Quarantine.** Downloads land in an inbox the box can't read. Archives and install images are unpacked so their executables can be inspected.
2. **Hash and look up.** Every file is SHA-256 hashed and checked against VirusTotal. Three or more engine detections is a reject. One or two is common for harmless crash reporters, so that's a flag for review.
3. **Local scan.** A scheduled Windows Defender scan of the "safe" folder runs nightly as a SYSTEM task and moves flagged items aside. If it can't run for 48 hours, items go through with only the online checks, and that's noted in the report.
4. **Approval.** Installers need my explicit approval before they reach the box. I added this after a fake installer passed the scans and then tried to download extra files.
5. **Contained install.** Installers run on the box with networking off. Only games that need internet (like phone-controller party games) get it afterwards.

## What I'd tell someone building this

Detection-based security gives you a false sense of safety. Making the pipeline *assume* compromise changed the design questions. The question stopped being "did the scanner catch it?" and became "what can this file reach if it's bad?" The answer should be: a disposable box on its own VLAN with no write access to anything that matters.

## Next

- Isolated VLAN and Tailscale ACLs for the box
- Automatic art and metadata for games with no store match
- Streaming heavier games from the Proxmox host
