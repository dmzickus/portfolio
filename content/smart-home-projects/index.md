---
title: Smart Home Overview
nav_label: Smart Home
icon: 🏠
icon_color: green
badge: 15+ projects
order: 10
description: The full ecosystem — Zigbee bulbs, MQTT broker, mmWave presence sensors, Alexa, and every ESP device in the apartment. Start here for the complete picture.
tags:
- Home Assistant
- Zigbee
- MQTT
- Presence sensors
---

# Smart Home & Hardware Projects

A collection of physical projects built around Home Assistant, ESP microcontrollers, and custom hardware — spanning my dorm room and apartment.

---

## Infrastructure

**Zigbee + MQTT Smart Home Ecosystem**
Deployed a full smart home stack across the apartment: smart bulbs in every room (bedroom, living room, kitchen, bathroom, hallway), smart outlets for energy monitoring and device control, and Alexa/Google Home integration via Nabu Casa. Chose Zigbee as the primary protocol to minimize WiFi congestion. Ran a Mosquitto MQTT broker through Home Assistant to connect all ESP devices after evaluating and ruling out ESPHome (too restrictive, YAML-only). Also runs a Matter server for a roommate's devices, though Matter proved unreliable in practice.

**Presence Sensors**
Installed mmWave presence sensors throughout the apartment, which detect occupancy even when people are stationary (via heartbeat and breathing detection), unlike standard PIR motion sensors. Used these to drive automatic lighting behavior — dimmed lights when someone enters the living room at night, room state awareness for sleep vs. active modes. Required careful calibration to get reliable results from consumer-grade hardware.

---

## Bathroom Automation

**ESP8266 Bathroom Controller**
One of the more complete systems I've built. An ESP8266 in the bathroom handles two independent automations:

- **Door-triggered lighting** — A magnetic reed sensor on the door drives a state machine: open → lights on, close → lights stay on, open again → lights off, close → idle. Requires the door to be closed when the bathroom is empty, which is a known limitation.
- **Shower fan automation** — A combined temperature/humidity sensor detects shower activity (both rise, but temperature climbs faster) and actuates the bathroom exhaust fan via a servo mounted in a custom 3D-printed light switch cover. The fan turns off automatically once temperature and humidity return to baseline. Currently disassembled, pending reinstallation.

**Planned addition:** A VOC sensor to detect odors and trigger both the fan and an automated air freshener spray.

---

## Living Room LED Strip

**Direct ESP Control of Salvaged LED Strip**
The previous tenants left behind a low-quality LED strip with a missing IR remote. Rather than setting up an IR blaster and dealing with line-of-sight constraints, I desoldered the original microcontroller and IR receiver directly from the strip and wired it to an ESP. This gave full RGB control over WiFi — no line-of-sight required, no remote needed, and integrated cleanly into Home Assistant. Also compensated in software for the hardware imbalance where the red channel ran weaker than the others.

---

## Light Switch Enclosures

**3D-Printed Smart Switch Mounts (Rotary Encoder + MQTT)**
Smart bulbs require the physical switch to stay on at all times, which makes manual control awkward. To solve this, my roommate and I designed 3D-printed mounts that fit over existing light switches and house an ESP with a rotary encoder and temperature sensor. After significant iteration on both the MQTT integration and rotary encoder handling, the final implementation maps:

- Rotation → brightness adjustment in 10% increments (0–100%)
- Single press → toggle on/off
- Long press → reset to 100% white

Currently has intermittent connection issues and has largely been superseded by Alexa voice control, but remains functional.

---

## Alarm & Security System

**ESP-Based Alarm with Home Assistant Integration**
Built a home security prototype using an ESP, magnetic door sensors, indicator LEDs, a buzzer, and a numpad for PIN entry. Arm/disarm was available both physically and through Home Assistant, with push notifications on trigger.

The more interesting sub-problem was pin reduction: the numpad normally requires 7–8 GPIO pins, which was impractical. Using a resistor ladder, I redesigned the circuit to produce a unique voltage per button, reducing the interface to 2 analog pins. Works correctly for individual keypresses; simultaneous inputs produce undefined behavior (known limitation).

**Home Assistant response sequence on alarm trigger:**
- Smart lights flash red and blue
- Alexa plays a custom alert sound
- Smart TV powers on, opens YouTube, and navigates to a custom-uploaded deterrent video — fully automated

The system was never permanently installed, and the breadboard circuit came apart without soldering.

---

## Automated Blinds (In Progress)

Motor and rope mechanism for automating window blinds is partially complete — motor selected, rope rigged to the blind cord, and motor control code written. Not yet installed; still needs a mounting bracket and housing to be designed and printed.

---

## Appliance Monitoring (In Progress)

**CT Clamp Laundry & Dishwasher Notifier**
To get notifications when the washer, dryer, or dishwasher finishes, I explored non-invasive current sensing using a CT clamp. Built a test circuit with a voltage divider and smoothing capacitor, validated the output on an oscilloscope with a fan as a load — proof of concept was successful. The blocker is ADC quality on the ESP: the onboard analog pins don't have the resolution to reliably distinguish current levels. Plan is to route the CT clamp output to an Arduino instead, which has a higher-quality ADC.

---

## Lizard Watering System

**Voice-Activated Water Pump ("Water Spotty")**
Built a pump-based automated watering system for a roommate's lizard. An ESP controls a small water pump on a reservoir, with the nozzle positioned over the lizard's water bowl. Integrated with Alexa so that saying "water Spotty" activates the pump for 30 seconds then shuts it off automatically — significantly easier than manually accessing the enclosure.

---

## Tablet Smart Home Dashboard

**Repurposed Tablet as Wall Controller**
Converted an old tablet into a dedicated Home Assistant control panel for the apartment. The tablet was too old to run the official HA app or access the web UI, so we sourced a third-party home automation app with a simplified interface and got it working. Plans to wall-mount it and power it directly (bypassing the battery) were shelved after Alexa made it redundant.

---

## Roku Integration & Custom Remote

**Unified TV Control via Home Assistant**
Integrated the apartment's smart TVs through Roku into Home Assistant and built custom virtual remotes. Unlike the official Roku app — which requires opening, loading, network scanning, and device selection before use — the custom remote connects directly to a specific TV and is immediately responsive.

---

## Egg Timer with HA Integration

**OLED Countdown Timer + Home Assistant UI**
Built a standalone egg timer using an OLED display, rotary encoder, and buzzer, with a full Home Assistant companion interface that let you select which household members' phones received the completion notification. Hardware and software were both functional. The enclosure (CAD'd egg shape) was never finished, and the problem it solved became moot after we got Alexa.

---

## Milk Weight Sensor (Proof of Concept)

**Fridge Milk Level Monitor**
A lighthearted project to track how much milk was left in the fridge, motivated by a roommate's habit of declaring the household "dangerously low on milk." Designed a 3D-printed base with load cells to weigh milk jugs and report remaining volume via an ESP. Validated the hypothesis that the fridge acts as a Faraday cage — WiFi signal from inside the fridge was completely blocked, confirming the ESP would need to live outside with a wired sensor run in. Load cell calibration was never resolved, so the project stalled there.

---

## Dorm Room Projects

**Desk Occupancy Lighting (Pressure Sensor)**
In my dorm, I wired a pressure sensor under my desk chair to a repurposed door sensor that toggled an LED strip above the desk. Included a turn-off delay to avoid the lights cutting out during brief moments of standing up.

**Bedtime Detection & Goodnight Routine**
A smart switch monitored for phone-charging behavior after sunset while I wasn't at my desk, using this as a proxy for going to sleep. On detection, it sent a goodnight notification and turned off all the lights automatically.

---

## Standalone Hardware

**Overengineered 7-Segment Clock**
My most ambitious standalone hardware project at the time. Built on an Arduino Mega with a DS3231 RTC module, a 20×4 seven-segment display, physical mode buttons, and photoresistors for adaptive brightness. Three display modes, each with randomly generated greetings and Easter eggs:

1. Current time
2. Elapsed time since a set date
3. Countdown to the next occurrence of a set calendar date

Handled month-length variation, leap years, and daylight saving time in C — written before taking a formal C course, so the implementation is brute-force (full recalculation every second) but correct. The RTC was chosen specifically for its accuracy (~1–2 minutes/year vs. several minutes/month for the Arduino's internal oscillator) and battery-backed timekeeping through power loss.

The enclosure was fully self-designed in CAD — my first CAD project. Multiple print iterations were needed to get screw hole placement right, which was an expensive lesson in designing for assembly.
