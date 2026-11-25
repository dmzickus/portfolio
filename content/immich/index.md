---
title: Photo Library and Backups
short_title: Photos + backups
summary: Immich as a private Google Photos for family and friends, and an encrypted 3-2-1 backup with restic to a local disk and Google Drive, using two keys.
status: building
area: homelab
rank: 5
started: 2026-10
role: Solo
stack: [Immich, Docker, PostgreSQL, restic, rclone, Google Drive API (OAuth), cron]
focus: [infra]
tags: [Docker, Self-hosting, Backups, Security, Linux, Bash]
links:
  - { label: "Privacy policy for the backup app", url: /privacy/ }
timeline:
  - date: 2026-10
    text: Fresh Immich install on the media VM, one account per person. Originals on the pooled drives, thumbnails on the HDD.
  - date: 2026-10
    text: Machine learning (faces, search, duplicates) turned back on after the Proxmox host's RAM upgrade.
  - date: 2026-11
    text: Backup design settled. restic to a local repository plus an encrypted copy in Google Drive, through my own OAuth app.
  - date: 2026-11
    text: Two keys. A daily key in password managers, and a handwritten break-glass key on paper.
  - date: 2026-12
    text: Make sure every phone is auto-uploading, then switch the nightly backup on and add it to the morning report.
---

Immich gives the household a Google Photos-style app (phone auto-upload, faces, search) without handing the photos to anyone. It's the one service where losing data would actually hurt, so most of this project is about backups.

## Layout

Originals go to the pooled 4 TB drives in the same `/data/media` tree as everything else. Thumbnails, previews and the database live on separate disks, so a full media pool can't take down the app. Machine learning runs on CPU and was re-enabled once the [homelab](/homelab/) host had RAM to spare.

## Backups: 3-2-1 with restic

- **Copy 1:** the live library.
- **Copy 2:** a restic repository on a separate local disk.
- **Copy 3:** an encrypted restic repository in Google Drive, reached through rclone.

Data is encrypted before it leaves the server, so Google only ever sees encrypted chunks. The Drive connection uses my own Google OAuth app with the narrow `drive.file` scope, which can only see files it created. That app is why this site has a [privacy policy](/privacy/) and [terms](/terms/) page.

**Two keys.** The daily key is in two password managers so the nightly job can run. A separate break-glass key is written on paper and kept somewhere else. Neither key is stored on the Pis or the VM beyond what the job needs to run.

## Status

The install and the backup design are done. Before turning the nightly 2:30 AM job on, I'm checking that everyone's phones are actually auto-uploading. The job will then report into the [ops agent](/ops-agent/)'s morning email.
