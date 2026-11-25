---
title: Apartment Smart Home
short_title: Smart home
summary: Home Assistant for a four-person apartment, built around voice and physical buttons rather than an app.
  Zigbee, MQTT and custom ESP devices, plus a light-effects engine that hands rooms back exactly as it found them.
icon: 🏠
highlights:
- Built for voice and buttons, not the app
- Zigbee + MQTT + mmWave presence
- Light effects that restore every room
status: live
area: embedded
rank: 1
started: 2024-08
role: Built and maintained by me; roommates have their own dashboards
stack:
- Home Assistant OS
- Raspberry Pi 5
- Zigbee (ZHA)
- Mosquitto MQTT
- Alexa (Nabu Casa)
- Matter
- mmWave presence sensors
focus:
- embedded
tags:
- Home Assistant
- MQTT
- Zigbee
- Voice
- Automation
- Raspberry Pi
- YAML
- Self-hosting
timeline:
- date: 2024-08
  text: First Home Assistant setup in my dorm. A chair pressure sensor drives the desk lights, and a phone-charging
    "bedtime" routine turns everything off.
- date: 2025
  text: Moved to the apartment. Zigbee bulbs in every room, a Mosquitto broker for ESP devices, and Alexa through
    Nabu Casa.
- date: 2025
  text: mmWave presence sensors pick up people sitting still, so lights stop turning off on someone reading.
- date: 2026-10
  text: The SD card corrupted. Rebuilt from backups on wired ethernet with a static IP; nightly backups now go to
    the cloud too.
- date: 2026-11
  text: Cleanup around how the household actually uses it. A curated Alexa device list, physical buttons, and dashboards
    only for what voice can't do.
- date: 2026-11
  text: Built a light-effects engine. Rainbow, spooky and holiday modes per room, with snapshot and restore so lights
    go back to how they were.
- date: 2026-11
  text: Music Assistant and a custom Alexa skill bring the music library and TV control to voice. See [Music + voice](/music-stack/).
---
Four people live in the apartment and almost nobody opens the Home Assistant app. So the system is built around how people actually control things: **Alexa**, a few **physical buttons**, and automations that guess right. Dashboards are for the stuff voice can't do.

## Hardware

- **Home Assistant OS** on a Raspberry Pi 5, wired, with its own static IP. It's kept separate from the [homelab](/homelab/) so the lights don't depend on the media server.
- **Zigbee (ZHA)** for bulbs, plugs and buttons.
- **MQTT (Mosquitto)** for my own [ESP builds](/esp-builds/). They run hand-written Arduino C++ firmware rather than ESPHome.
- **mmWave presence sensors**, which detect breathing rather than motion, so the living room lights come on when it's dark and turn off only when the room is actually empty.

## Voice first

Alexa only sees a curated list: room light groups, the Christmas tree, the humidifier, temperatures, and a few scripts. Auto-exposing new devices is off, because every ghost entity makes voice control worse. One living room button covers the rest: single press toggles the lights, double press toggles the Christmas lights, hold runs "lights out" for the whole apartment.

## The light-effects engine

The goal was for "Alexa, turn on spooky kitchen" to work, and for "Alexa, turn off the kitchen lights" to actually stop the effect and keep the lights off. Then everything should go back to normal afterwards. The engine has four parts:

- **Snapshot and ownership.** Starting an effect snapshots the bulbs it takes over and registers which effect owns them. If a room effect starts while the apartment-wide effect is running, the room takes its bulbs and the apartment effect keeps going everywhere else. The last claim wins.
- **Watchers restore state.** When an effect stops, the lights go back to exactly what they were. Lights with no snapshot fall back to a sensible default.
- **Voice shortcuts.** Alexa can't drive dropdowns, so each room and effect pair gets a scene-style script. Dashboards use one selector per room.
- **Integration with everything else.** "Lights out" releases its lights from effects first. Presence lighting backs off while an effect is running. The Halloween and Christmas sound scripts run only while a matching effect is on.

A few things I learned the hard way. Snapshots live in memory, so they're lost on restart, and a startup automation re-applies selectors. Home Assistant stores script variables alphabetically, so dependent variables have to be separate steps. Cheap Tuya LED strips lock up if you send them commands too quickly.

## Next

Rewrite the custom devices on a shared ESP-NOW gateway with OTA updates. See [ESP builds](/esp-builds/).
