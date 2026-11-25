---
title: ESP Builds
short_title: ESP builds
summary: Every custom microcontroller device I've built for the dorm and the apartment, what each one taught me, and the planned ESP-NOW rewrite that brings them back.
status: dormant
area: embedded
rank: 2
started: 2024-09
role: Solo, some builds with a roommate
stack: [ESP8266, ESP32, Arduino C++, MQTT, Home Assistant, KiCad, FDM 3D printing]
focus: [embedded]
tags: [ESP8266, ESP32, Arduino C++, MQTT, Home Assistant, 3D printing, Hardware debugging]
timeline:
  - date: 2024-09
    text: Dorm builds. A chair pressure sensor runs the desk lights, and an overengineered RTC clock.
  - date: 2025
    text: Apartment builds on MQTT, including the bathroom controller, LED strip, alarm keypad, switch knob, egg timer and appliance monitor.
  - date: 2025
    text: Smaller builds. Spotty the lizard's Alexa-triggered water pump, motorized blinds, and a fridge milk scale.
  - date: 2026-08
    text: Scoped a common pattern for push-button appliances (window ACs, an air purifier, a desk lamp). An ESP32 and relays "press" the buttons and track state.
  - date: 2026-11
    text: Most of the fleet is offline. The light knob is getting MQTT OTA updates as the template for the rewrite.
  - date: 2027
    text: ESP-NOW rewrite. Devices talk to one gateway instead of Wi-Fi, with OTA updates and shared firmware.
---

These are the custom devices around the apartment. Most of them are **offline right now**. Breadboards came apart, people moved rooms, and Alexa made a couple of them redundant. The write-ups stay up because each one taught me something I still use.

## The builds

| Build | Status | What it taught me |
|---|---|---|
| [Light switch knob](/smart-switch-mount/) | Live | Send relative commands, never absolute state, or the device and Home Assistant will fight |
| [Living room LED strip](/living-room-led/) | Live | Salvaging hardware, inverted PWM, correcting color in software |
| [Bathroom controller](/bathroom-esp/) | Retired | Designing a state machine so the sensors are always the source of truth |
| [Alarm keypad](/alarm-system-keypad/) | Retired | A resistor ladder fits seven keys onto one ADC pin |
| [Appliance monitor](/ct-clamp-project/) | Dormant | Debugging with an oscilloscope; the ESP8266 ADC is noisy |
| [Egg timer](/egg-timer/) | Dormant | Scope creep: two good prototypes, never merged |
| [RTC clock](/overengineered-clock/) | Retired | Memory limits on an Arduino Mega |

## Smaller ones

- **Spotty's water system:** "Alexa, water Spotty" runs a relay-driven pump over the lizard's bowl for 30 seconds, then shuts off. Retired.
- **Motorized blinds:** motor and firmware done, rope rigged, never mounted. Planned.
- **Fridge milk scale:** load cells in a printed base. It proved the fridge is a Faraday cage and stalled on calibration. Retired.
- **Dorm desk lighting:** a chair pressure sensor through a repurposed door sensor, with a turn-off delay so standing up doesn't kill the lights. Retired.

## Scoped but not built

- **Button-press appliances.** Window ACs, a Levoit air purifier and a Lepro desk lamp only have buttons or touch pads, and lose state when unplugged. The plan is the same for all of them: an ESP32 with relays wired across the button pads, state tracked on the ESP, and everything published to MQTT.
- **Roomba override.** Normal autonomous cleaning, plus a web page with gamepad support to drive it from anywhere.
- **Ambilight:** see [its page](/ambilight/).

## The rewrite

The fleet's real problem is Wi-Fi. A dozen ESPs on a crowded network drop off, reconnect slowly, and need a USB cable for every firmware change. The plan is to rebuild around **ESP-NOW**: devices talk to one gateway, the gateway bridges to MQTT, and every device gets OTA updates and shared firmware. A roommate is building a similar gateway, and the light knob is the first device getting MQTT-based OTA as a test.
