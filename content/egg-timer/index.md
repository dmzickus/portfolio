---
title: OLED Egg Timer + HA Companion
nav_label: Egg Timer
icon: ⏱️
icon_color: ''
badge: 2-phase build
order: 60
description: Standalone timer with animated egg character on SSD1306 OLED. Full HA dashboard with per-roommate notification routing. Hardware and firmware done; never merged or shipped.
tags:
- ESP8266
- SSD1306
- Animations
- HA dashboard
---

# Egg Timer — ESP8266 + OLED + MQTT + Home Assistant

## Overview

A standalone kitchen timer built around an OLED display, rotary encoder, and buzzer — with a full Home Assistant companion dashboard and per-roommate push notification support. The problem it solved was simple: microwave timers would go off while everyone had retreated to their rooms, and nobody would hear it. Before Alexa arrived, this was the solution.

The hardware came together in two distinct phases: an initial LCD-based prototype to nail the timer logic and UX, then a second pass with an SSD1306 OLED and animated egg character. Both phases worked independently. They were never merged into a single firmware, and the CAD egg enclosure was never finished. The problem became moot when Alexa made the whole thing redundant.

---

## Hardware

- **Microcontroller:** ESP8266
- **Display:** SSD1306 128×64 OLED (I2C, 0x3C), Adafruit_SSD1306
- **Input:** Rotary encoder (CLK/DT/SW pins)
- **Output:** Passive buzzer — distinct tones for increment, decrement, start, stop, reset, and finish
- **Enclosure:** Planned as a 3D-printed egg shape — CAD was started, never finished

---

## Firmware — What Existed

### Phase 1 — LCD Timer (`egg_timer_proto.ino`)

The first firmware ran on a 16×2 I2C LCD and established all the core timer behavior:

- Rotary encoder adjusts time in **30-second increments**
- **Press** to start or stop the countdown
- **Hold** to reset to zero
- Display shows `HH:MM:SS` with leading-zero padding, collapsing hours when zero
- Distinct buzzer tones for each action (inc, dec, start, stop, reset, finish)
- Timer decrements via `millis()` — no blocking delays in the main loop

```cpp
void ledWrite / printTime() logic — manual cursor placement to avoid full lcd.clear()
on every tick, with digit-count tracking to know when a clear is actually needed.
```

The `printTime()` implementation is careful about partial redraws: it tracks digit counts for minutes and hours separately so it only calls `lcd.clear()` when the number of digits actually changes (e.g. 10:00 → 9:59), avoiding flicker on every second tick.

### Phase 2 — OLED + Animations (`oled_egg_animation.ino`)

A separate sketch built out the OLED visuals:

**Startup — `eggDanceWithSound()`:** An egg character bounces side to side (±4px), alternating arm and leg poses on each frame, with clicky buzzer tones synced to the step. Runs for a configurable duration.

```cpp
void drawEgg(int x, int y, bool step) {
  display.fillEllipse(x, y, 14, 18, SSD1306_WHITE); // body
  // Eyes, smile, alternating arms and legs based on `step`
}
```

**Finish — `eggCrackAnimation()`:** A 7-stage crack sequence: the egg shell splits apart progressively, falls off screen, then plays a three-note finish jingle.

```cpp
for (int stage = 0; stage < 7; stage++) {
  drawCrackedEgg(64, 32, stage);
  // Crack sounds: descending pitch early, deeper thud late
}
```

### What Was Never Done

The two sketches were never merged. A complete firmware would have:
- Replaced the LCD with the OLED
- Shown the dancing egg while the timer counts down
- Triggered the crack animation on finish
- Added WiFi + MQTT to sync state with Home Assistant

---

## Home Assistant Integration

### Dashboard

A custom Lovelace card with full timer control:

- **Time Remaining** — live countdown display
- **Progress gauge** — arc showing % elapsed
- **Timer State** — `RUNNING` / `STOPPED` / `RESET`
- **Start / Stop / Reset** buttons
- **+30s / −30s** buttons
- **Per-roommate notification toggles** — Dylan, Cole, Gabe; tap to opt in before starting

### Underlying Entities

| Entity | Purpose |
|---|---|
| `input_number.timer_remaining` | Seconds remaining, decremented every second by automation |
| `input_number.timer_total` | Original duration (for progress %) |
| `input_text.timer_state` | `RUNNING` / `STOPPED` / `RESET` |
| `input_boolean.timer_dylan/cole/gabe` | Notification opt-in per roommate |
| `input_button.timer_start/stop/reset/add_30s/sub_30s` | Dashboard button triggers |

### Automations

Every action has two paths — one triggered by the dashboard button, one by MQTT from the physical device — so both stay in sync:

| Automation | Trigger | Action |
|---|---|---|
| Timer Start | Button or `egg_timer/state: START` | Set state → RUNNING |
| Timer Stop | Button or `egg_timer/state: STOP` | Set state → STOPPED |
| Timer Reset | Button or `egg_timer/state: RESET` | Set state → RESET, zero both numbers |
| Add 30s | Button or `egg_timer/state: ADD30` | Increment remaining + total; if RESET → STOPPED |
| Sub 30s | Button or `egg_timer/state: SUB30` | Decrement remaining + total (guarded: remaining > 29) |
| Timer Decrease | `time_pattern` every second | Decrement `timer_remaining` while RUNNING |
| Timer Finished | `timer_remaining` drops below 1 | Zero both, stop, fire notification script, reset booleans |

### MQTT Topics

```
egg_timer/command    ← HA → device  (START, STOP, RESET, ADD30, SUB30)
egg_timer/state      ← device → HA  (same payload set)
egg_timer/notification ← device → HA (Dylan / Cole / Gabe — toggles opt-in boolean)
```

The physical device was meant to publish its own encoder/button actions to `egg_timer/state` so HA mirrors the local state in real time. This was never wired up.

---

## Architecture

```
┌─────────────────────────────────┐
│        Home Assistant           │
│  Lovelace dashboard:            │
│  countdown, gauge, state label  │
│  start/stop/reset, ±30s,        │
│  per-roommate notification opt-in│
└────────────┬────────────────────┘
             │ MQTT publish / subscribe
             ▼
┌─────────────────────────────────┐
│     Mosquitto MQTT Broker       │
│  egg_timer/command              │
│  egg_timer/state                │
│  egg_timer/notification         │
└────────────┬────────────────────┘
             │ (never connected)
             ▼
┌─────────────────────────────────┐
│         ESP8266                 │
│  Rotary encoder → 30s steps     │
│  Press → start/stop             │
│  Hold → reset                   │
│  Buzzer tones per action        │
└────────────┬────────────────────┘
             │ I2C
             ▼
┌─────────────────────────────────┐
│   SSD1306 128×64 OLED           │
│  Dancing egg → countdown        │
│  Crack animation → finish       │
│  (animation never merged)       │
└─────────────────────────────────┘
```

---

## What Works

- LCD prototype timer: full countdown logic, encoder input, buzzer tones, hold-to-reset
- OLED animations: dancing egg startup, crack finish sequence, synced buzzer sounds
- Home Assistant dashboard: all controls, progress gauge, per-roommate notification toggles
- HA automation set: complete bidirectional MQTT + button trigger coverage

## What Was Never Finished

- **Firmware merge** — OLED + animations + timer logic + MQTT never combined into one sketch
- **MQTT bridge** — ESP never connected to HA; the two sides never talked
- **Enclosure** — egg-shaped CAD was planned, never modeled or printed
- **Project relevance** — Alexa solved the same problem before any of this shipped

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | ESP8266 |
| Firmware | Arduino (C++) — Adafruit_SSD1306, Adafruit_GFX |
| Display | SSD1306 128×64 OLED (I2C) |
| Messaging | MQTT (Mosquitto broker) — planned, not connected |
| Smart home | Home Assistant — input helpers, Lovelace, automations |
| Notifications | HA mobile push, per-roommate opt-in via input_boolean |
