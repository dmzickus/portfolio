---
title: 3D-Printed Switch Mount
nav_label: Switch Mount
icon: 🔄
icon_color: ''
badge: 3-stage iteration
order: 50
description: Custom enclosure over the wall switch housing an ESP32 and rotary encoder. Sends relative commands to HA instead of tracking absolute state — key architectural lesson.
tags:
- ESP32
- Rotary encoder
- 3D print
- MQTT
---

# 3D-Printed Smart Switch Mount — ESP32 + MQTT + Rotary Encoder

## Overview

Smart bulbs introduce a frustrating physical limitation: the wall switch must remain permanently "on" to keep the bulbs powered. This forces you to rely entirely on an app or voice assistant to control the lights, which is highly inconvenient when walking into a pitch-black room. 

To solve this, my roommate and I designed a custom 3D-printed mount that fits directly over the existing light switch. Inside, an ESP32 paired with a rotary encoder and a DHT11 temperature/humidity sensor restores physical control over the smart bulbs without cutting their power, communicating directly with Home Assistant over MQTT.

---

## Hardware

- **Microcontroller:** ESP32
- **Input:** Rotary Encoder (CLK on GPIO 14, DT on GPIO 27, SW on GPIO 26)
- **Sensor:** DHT11 Temperature and Humidity Sensor (GPIO 4)
- **Enclosure:** Custom 3D-printed mount designed to cover a standard wall switch.

---

## Iteration History

### Stage 1 — Hardware Validation & LCD Debugging (`rotary_lcd_working.ino`)

The first challenge was reliably reading the rotary encoder without hardware interrupts and debouncing the built-in push button. Early iterations outputted the encoder position and button state to a 16x2 I2C LCD screen for immediate visual debugging before introducing any networking complexity.

### Stage 2 — Absolute State via MQTT (`rotary_light_works_mqtt.ino`)

Once the hardware inputs were reliable, I added WiFi and MQTT using `PubSubClient`. In this iteration, the ESP32 attempted to manage the state internally—storing an absolute brightness value (0–100) and tracking whether the light was "ON" or "OFF." 

```cpp
if (digitalRead(pinDT) != currentCLK) {
  brightness -= 10;
} else {
  brightness += 10;
}
if (brightness > 100) brightness = 100;
if (brightness < 0)   brightness = 0;

client.publish(brightness_state_topic, String(brightness).c_str(), true);
```
This created synchronization issues. If the lights were adjusted via the Home Assistant app, the ESP32's internal state became outdated, leading to jumping brightness levels on the next physical rotation.

### Stage 3 — Relative Commands & Sensor Integration (`rotary_light_toggle_temp_humidity.ino`)

To fix the state mismatch, the architecture was shifted. The ESP32 became a "dumb" input device that simply publishes relative action strings over MQTT, making Home Assistant the ultimate source of truth. A DHT11 sensor was also integrated into the loop, publishing environmental data every two seconds.

```cpp
// Publishing relative rotational commands
if (digitalRead(pinDT) != currentCLK) {
  client.publish(brightness_state_topic, "decrease", true);
} else {
  client.publish(brightness_state_topic, "increase", true);
}
```

The button logic was expanded to count loops while the switch was held down (20 loops at a 50ms delay = 1 second hold), allowing a single press to send a "toggle" payload and a long press to send a "reset" payload.

---

## Home Assistant Integration

With the ESP32 publishing simple string commands (`increase`, `decrease`, `toggle`, `reset`), Home Assistant automations take over the actual control of the smart bulbs (`light.dylan_s_lights_2`). 

**Brightness Adjustment (Step Percentage):**
```yaml
alias: Increase Dylan's Lights
trigger:
  - trigger: mqtt
    topic: home/lights/esp32/brightness/state
    payload: increase
action:
  - action: light.turn_on
    data:
      brightness_step_pct: 10
      transition: 0
    target:
      entity_id: light.dylan_s_lights_2
```
*(A mirrored automation handles the "decrease" payload using `brightness_step_pct: -10`)*

**Long-Press Reset (100% White):**
```yaml
alias: Reset Dylan's Lights
trigger:
  - trigger: mqtt
    topic: home/lights/esp32/state
    payload: reset
action:
  - action: light.turn_on
    data:
      brightness_pct: 100
      rgb_color: [255, 255, 255]
    target:
      entity_id: light.dylan_s_lights_2
```

---

## Architecture Diagram

```text
┌─────────────────────────────────┐
│     Custom 3D-Printed Mount     │
│  - Covers physical wall switch  │
│  - Rotary Encoder (Turn & Push) │
│  - DHT11 Temp/Humidity Sensor   │
└────────────┬────────────────────┘
             │ GPIO Inputs
             ▼
┌─────────────────────────────────┐
│              ESP32              │
│  - Debounces rotary & button    │
│  - Reads DHT11 sensor           │
│  - Translates to string payloads│
└────────────┬────────────────────┘
             │ MQTT Publish (WiFi)
             ▼
┌─────────────────────────────────┐
│      Mosquitto MQTT Broker      │
│  home/lights/esp32/state        │
│  home/lights/esp32/brightness   │
└────────────┬────────────────────┘
             │ MQTT Subscribe
             ▼
┌─────────────────────────────────┐
│         Home Assistant          │
│  - Automations interpret strings│
│  - Adjusts smart bulb entities  │
└─────────────────────────────────┘
```

---

## Status & Reflections

- **Functional but Flawed:** The system successfully maps rotation to 10% brightness steps, clicks to toggles, and holds to resets. However, the ESP32 suffers from intermittent WiFi connection drops, requiring periodic reboots. 
- **Architectural Lesson:** Moving state management off the edge device (the ESP32) and centralizing it in Home Assistant (using relative step commands) was a major turning point in building resilient smart home hardware. 
- **Current State:** Since integrating Alexa and mmWave presence sensors, the physical switch is rarely used. It remains on the wall mostly as an aesthetic piece and a functional fallback for guests.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | ESP32 |
| Inputs/Sensors | Rotary Encoder, DHT11 |
| Firmware | Arduino (C++) — WiFi, PubSubClient, DHT |
| Messaging | MQTT (Mosquitto broker) |
| Smart home | Home Assistant Automations |
| Fabrication | 3D Printing (CAD enclosure) |
