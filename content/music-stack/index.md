---
title: Self-Hosted Music and Voice Control
short_title: Music + voice
summary: A self-hosted Spotify replacement for the apartment. Navidrome with per-person accounts, automatic library growth and cleanup, AI-assisted playlists, and a custom Alexa skill to play it on any Echo.
status: live
area: homelab
rank: 4
started: 2026-11
role: Solo; used by me and two roommates
stack: [Navidrome, Lidarr, beets, ffmpeg (Opus), AudioMuse-AI, ListenBrainz, Music Assistant, Home Assistant, Alexa Skills Kit]
focus: [infra, embedded]
tags: [Docker, Self-hosting, Automation, Home Assistant, Voice, Bash, Python]
timeline:
  - date: 2026-11
    text: Navidrome added to the media VM with separate accounts, smart playlists and a music library next to movies and TV.
  - date: 2026-11
    text: Lidarr grabs albums; lossless files are converted to Opus 160k on import to save space. beets adds synced lyrics, ReplayGain and cover art nightly.
  - date: 2026-11
    text: AudioMuse-AI analyses the library for "more like this" radio and similar-track playlists.
  - date: 2026-11
    text: Years of Spotify listening history imported into ListenBrainz to seed weekly discovery.
  - date: 2026-11
    text: Music Assistant in Home Assistant plays the library on the apartment's Echo speakers.
  - date: 2026-11-18
    text: Custom Alexa skill "spotty" handles music requests and switches the TV between Jellyfin and the game box.
  - date: 2026-12
    text: Weekly discovery playlist (Explo) that rotates out each week; starring a track adds the album to the library.
---

The goal was a Spotify replacement the apartment would actually use. That meant separate accounts, playlists and likes, search, shuffle, and working on lots of devices at once, on the LAN and away from home. It also had to cost less disk space than a lossless hoard.

## How it fits together

- **Navidrome** serves the music. Each person has their own account, so likes and history stay separate. Smart playlists (recently added, random mix, by decade) are files in the library, so they're versioned with everything else.
- **Lidarr** fills the library. It prefers lossless sources, and an import hook converts them to **Opus at 160 kbps**, which sounds the same on the apartment's speakers and takes a fraction of the space.
- **beets** runs nightly in place. It adds synced lyrics, ReplayGain and embedded cover art, and swaps "instrumental-padded" album editions for the normal ones.
- **AudioMuse-AI** analyses the audio for similarity, which drives "radio" and similar-track features inside Navidrome.
- **ListenBrainz** holds the listening history, including the Spotify history I exported, for recommendations.

## Voice

Hardly anyone in the apartment opens an app, so voice had to work. **Music Assistant** in [Home Assistant](/home-assistant/) treats the Echo speakers as players with Navidrome as the source. A **custom Alexa skill** ("Alexa, ask spotty to…") handles music requests and also switches the living room TV between Jellyfin and the [game box](/couch-box/).

## Keeping it hands-off

A nightly script force-imports stuck downloads, drops singles that already exist on an album, and cleans up music downloads once they're converted, since nothing needs to be kept around for seeding. Its log is part of the [ops agent](/ops-agent/)'s morning check.

## Next

- Explo: a weekly discovery playlist built from ListenBrainz recommendations, rotated out each week
- Starring a discovery track adds its album to the library and follows the artist for new releases only
