---
title: Ambilight for Jellyfin
short_title: Ambilight
summary: An idea to sync the living room lights to whatever's playing on Jellyfin. Average the frame colour with ffmpeg and push it to Hyperion and the Zigbee bulbs.
status: planned
area: embedded
rank: 60
started: 2026-07
tags: [Python, ffmpeg, Home Assistant, Jellyfin]
stack: [Python, Jellyfin API, ffmpeg, Hyperion (JSON-RPC), Home Assistant, Zigbee]
timeline:
  - date: 2026-07
    text: Designed, not built.
---

The plan:

1. A small Python service polls Jellyfin's sessions API for what's playing on the living room TV and the current position.
2. ffmpeg grabs frames from the same file at that timestamp and computes the average colour, or a few edge colours.
3. The colour goes to **Hyperion** over its JSON-RPC API for the LED strip behind the TV.
4. The Zigbee bulbs follow at a slower rate through Home Assistant, since they can't handle fast updates.

Reading from the file instead of capturing the screen means no HDMI capture hardware is needed. The main risk is keeping the timing in sync when someone seeks or pauses.
