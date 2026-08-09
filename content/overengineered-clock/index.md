---
title: Overengineered RTC Clock
nav_label: Clock
icon: 🕐
icon_color: green
badge: 4-stage build
order: 90
description: Arduino Mega + DS3231 RTC in a custom 3D-printed purple enclosure. Brute-force calendar math including DST. Featured a scrapped side-scrolling game ("Spike and Dude").
tags:
- Arduino Mega
- DS3231
- 20×4 LCD
- 3D print
---

# Overengineered RTC Clock — Arduino Mega + Custom Hardware

## Overview

A standalone, feature-rich digital clock built from the ground up using an Arduino Mega and a DS3231 Real-Time Clock (RTC) module. The system was designed to display current time, calculate the exact time elapsed since a specific past date, and count down to future recurring anniversaries. 

What makes it worth documenting is the evolution. The project started as a software exercise in brute-forcing complex calendar math without external libraries, morphed into a battle against strict hardware memory limits, and ended as a hands-on lesson in 3D fabrication and physical assembly.

---

## Hardware

- **Microcontroller:** Arduino Mega
- **Timekeeping:** DS3231 RTC module (I2C) — chosen for its extreme accuracy (~1-2 minutes drift per year) and battery backup.
- **Display:** 20x4 Character LCD (I2C)
- **Inputs:** Physical push buttons for mode toggling and a photoresistor (LDR) for adaptive brightness.
- **Enclosure:** A custom 3D-printed purple trapezoidal cylinder, designed in two interlocking pieces (top and base).
- **Wiring:** No PCBs or perfboards. All components were point-to-point soldered and heavily superglued into a permanent, chaotic web to prevent shorting inside the tight case.

---

## Iteration History

### Stage 1 — Brute-Force Calendar Math (`rtcTest.ino` / `rtcTimeSince.ino`)

The initial firmware was developed before taking any formal C programming classes. Instead of relying on standard Unix epoch libraries, all time-delta calculations were written from scratch. The system had to manually account for varying month lengths, leap years, and Daylight Saving Time (DST) every single second.

```cpp
bool isStartDST (DateTime dt) {
  return !dst &&                                 // dst didn't start yet
          dt.dayOfTheWeek() == 0 &&              // it is a sunday
          dt.day() >= 8 && dt.day() <= 14 &&     // second sunday of the month
          dt.month() == 3 &&                     // it is march
          dt.hour() == 2 &&                      // 2 am
          dt.minute() == 0 && dt.second() == 0;  // on the dot
}
```

This brute-force approach was highly educational but computationally repetitive. To ensure the time didn't drift despite the heavy math, the DS3231 RTC was integrated to anchor the logic.

---

### Stage 2 — Feature Creep & The Memory Wall (`rtcDiffScreens.ino`)

With the math working, the project expanded to include randomized, highly personalized greetings combining arrays of prefixes and nicknames.

Two realities of embedded hardware surfaced immediately:

**SRAM Fragmentation.** On an 8-bit AVR microcontroller, large arrays of string literals rapidly devour dynamic memory. The system quickly hit 60% memory capacity, risking heap fragmentation and silent crashes.

**Custom Array Sizing.** To squeeze the messaging system in without crashing, standard library functions were abandoned. The fix was writing custom indexing loops to manually calculate array lengths on the fly:

```cpp
int calc_prefixes_len (char last[5]) {
  int i = 0;
  for (; prefixes[i] != last; i++) {}
  return i + 1;
}
```

---

### Stage 3 — The Ambition of "Spike and Dude" (`spike_and_dude.ino`)

Wanting to push the 20x4 LCD to its limits, a Chrome-dinosaur-style side-scrolling obstacle game was developed as an alternative clock mode. It featured real-time jump physics, custom byte-array character sprites, tick-rate acceleration, and EEPROM-backed high scores.

```cpp
// Custom byte-array character sprites
uint8_t spike_bits[] = {0x00, 0x00, 0x04, 0x04, 0x04, 0x0e, 0x0e, 0x1f};
uint8_t dude_bits[]  = {0x0e, 0x0e, 0x04, 0x0e, 0x15, 0x04, 0x0a, 0x11};
```

**The Reality Check:** While the game was successfully built and tested as a standalone script, the memory footprint of the brute-force calendar math and the personalized string arrays left absolutely no room for the game loop. "Spike and Dude" had to be cut from the final firmware to ensure the clock remained stable.

---

### Stage 4 — Physical Fabrication (The Purple Enclosure)

The final stage was moving from a breadboard to a permanent physical artifact. This was a first attempt at 3D CAD design. Translating digital dimensions to a physical purple trapezoidal enclosure required accounting for tolerances, mounting points, and wire routing.

It took multiple expensive, time-consuming print iterations just to align the bottom screw holes correctly — a harsh initiation into designing for assembly. Internally, the lack of a custom PCB meant relying on a soldered, superglued rat's nest of wires, permanently sealing the project in its final state.

---

## Architecture Diagram

```text
┌─────────────────────────────────┐
│          Arduino Mega           │
│  - Brute-force calendar logic   │
│  - Custom array memory management│
└────────────┬────────────┬───────┘
             │ I2C        │ GPIO / Analog
             ▼            ▼
┌──────────────────┐  ┌──────────────────┐
│  DS3231 RTC Mod  │  │  Physical UI     │
│  (Timekeeping)   │  │  - Push Buttons  │
└──────────────────┘  │  - Photoresistor │
                      └──────────────────┘
             │ I2C
             ▼
┌─────────────────────────────────┐
│      20x4 Character LCD         │
│      (Adaptive Backlight)       │
└─────────────────────────────────┘
```

---

## Status & Next Steps

- **Working:** Accurate timekeeping across power loss thanks to the battery-backed RTC.
- **Working:** Complex, brute-forced calendar math calculates elapsed and future time perfectly.
- **Trade-off:** "Spike and Dude" game was cut. The Mega's SRAM simply couldn't hold the calendar math, the massive string arrays, and the game loop simultaneously.
- **Lesson learned:** 3D printing tolerances are unforgiving. Misaligned screw holes cost time and filament, fundamentally changing how I approach CAD for physical electronics.
- **Physical finishing:** The exterior looks fantastic (purple trapezoid), but the interior is a permanent, superglued rat's nest. A custom PCB would be the next logical step for a V2.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | Arduino Mega |
| Firmware | C++ (Arduino Framework) — `Wire.h`, `LiquidCrystal_I2C.h`, `RTClib.h` |
| Hardware | DS3231 RTC, 20x4 I2C LCD, Push Buttons, LDR |
| Fabrication | Custom CAD, 3D Printed (Purple PLA/PETG) |
