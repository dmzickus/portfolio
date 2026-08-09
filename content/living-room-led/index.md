---
title: Living Room LED Strip
nav_label: LED Strip
icon: 💡
icon_color: green
badge: 3-stage iteration
order: 30
description: Desoldered the IR receiver off a salvaged LED strip and wired it to an ESP for full RGB MQTT control. Per-channel color correction to fix hardware imbalance.
tags:
- ESP8266
- PWM
- MQTT
- Color correction
---

# Living Room LED Strip — ESP8266 + MQTT + Home Assistant

## Overview

Ambient RGB LED accent lighting for the living room, controlled entirely through Home Assistant. The strip responds to on/off toggles, brightness sliders, and full RGB color picking — all from the HA dashboard or any automation. The project started as a simple hardware experiment and evolved into a fully integrated smart home device through several distinct iterations, each one teaching something new about embedded development, MQTT, and the realities of working with real hardware.

---

## Hardware

- **Microcontroller:** ESP8266 (NodeMCU)
- **LED strip:** Analog RGB strip, common anode (5V shared positive rail)
- **Wiring:** 4-pin direct connection — 5V to the strip's common anode, and each of the R, G, B pins tied directly to GPIO pins on the ESP (D7/GPIO15, D8/GPIO13, D6/GPIO12)
- **Power switch:** An inline switch on the 5V line, serving double duty: it lets you cut power to the strip cleanly, and — critically — it lets you drop the GPIO pins to a safe state before flashing new firmware, since the ESP8266 won't accept uploads if those pins are being driven

No transistors, MOSFETs, or driver boards. The ESP's GPIO pins drive the strip directly, which works for a low-current analog strip at this scale.

---

## Iteration History

### Stage 1 — Proof of Concept (`led_strip_basic_colors.ino`)

The very first firmware did one thing: cycle through red, green, and blue using PWM `analogWrite` calls in a loop. No networking, no control — just confirming that the hardware was wired correctly and the ESP could drive the strip at all.

```cpp
for (int i = 0; i <= 255; i++) {
  analogWrite(r, i);
  delay(20);
}
digitalWrite(r, HIGH); // FANCY PANTS
```

The `// FANCY PANTS` comment in the source says it all. This was the "does it work?" stage.

---

### Stage 2 — MQTT Control, No HA (`led_mqtt_works_no_ha_yet.ino`)

With basic hardware confirmed, the next step was adding WiFi and MQTT. The ESP connects to a local Mosquitto broker, subscribes to three command topics, and publishes retained state back on all three:

| Topic | Purpose |
|---|---|
| `home/lights/living_room/led/command` | ON / OFF |
| `home/lights/living_room/led/brightness/command` | 0–100 integer |
| `home/lights/living_room/led/rgb/command` | `R,G,B` comma-separated string |

Two hardware realities surfaced here that required firmware workarounds:

**Inverted PWM.** Because the strip is common anode, the logic is backwards from what you'd expect — pulling a pin LOW turns the channel *on*, not off. The fix is a one-liner inversion in the `ledWrite` helper:

```cpp
void ledWrite(int pin, int val) {
  int newVal = val * ((float) brightness / 100.0);
  newVal = 255 - newVal; // Invert: common anode wiring
  analogWrite(pin, newVal);
}
```

This wasn't anticipated upfront — the strip was wired, powered on, and immediately behaved backwards. The inversion was the diagnosis and fix.

**Retained state on reconnect.** If the ESP drops WiFi or the broker restarts, it re-publishes its last known state on reconnect so Home Assistant never gets out of sync:

```cpp
client.publish(state_topic, lightOn ? "ON" : "OFF", true);
client.publish(brightness_state_topic, String(brightness).c_str(), true);
client.publish(rgb_state_topic, rgb, true);
```

At this stage everything worked end-to-end over MQTT — controllable from any MQTT client — but Home Assistant wasn't in the picture yet.

---

### Stage 3 — Final Firmware + HA Integration (`led_living_room_final.ino`)

The final firmware added one more correction discovered during real-world use: the green and blue channels appeared significantly brighter than red at the same PWM value, making color mixing noticeably off. The fix was a channel-specific attenuation:

```cpp
void ledWrite(int pin, int val) {
  if (pin == gPin || pin == bPin) val /= 4; // Balance against red
  int newVal = val * ((float) brightness / 100.0);
  newVal = 255 - newVal;
  analogWrite(pin, newVal);
}
```

The `/4` factor was arrived at through trial and error — eyeballing colors until white looked actually white and reds didn't look pink. The trade-off is that the overall maximum brightness is lower than it would be without correction, since green and blue are now capped at 25% of their hardware maximum. Acceptable for accent lighting; worth noting for anyone reproducing this.

**Home Assistant integration** was done manually through the HA MQTT integration UI rather than MQTT discovery (which proved difficult to get working reliably). Each channel was configured by hand — telling HA which topics to publish commands to, which topics to read state from, and what payload conventions to expect. The result is a first-class HA light entity with full on/off, brightness, and RGB color support visible in the dashboard and available to any automation.

---

## Architecture Diagram

```
┌─────────────────────────────────┐
│        Home Assistant           │
│  (Light entity: Living Room LED)│
│  - Toggle on/off                │
│  - Brightness slider (0–100)    │
│  - RGB color picker             │
└────────────┬────────────────────┘
             │ MQTT publish/subscribe
             ▼
┌─────────────────────────────────┐
│     Mosquitto MQTT Broker       │
│     (running on local server)   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│         ESP8266 (NodeMCU)       │
│  - Subscribes to command topics │
│  - Publishes retained state     │
│  - PWM output with inversion    │
│    and per-channel correction   │
└────────────┬────────────────────┘
             │ GPIO PWM (D6, D7, D8)
             ▼
┌─────────────────────────────────┐
│      Analog RGB LED Strip       │
│      Common anode, 5V           │
└─────────────────────────────────┘
```

---

## What Works

- On/off, brightness, and full RGB color control from Home Assistant
- State persists across ESP reboots and broker reconnects via retained MQTT messages
- Stable WiFi reconnection loop — the device recovers on its own if the network drops
- Color balance correction produces believable whites and accurate-ish hues

## Known Limitations & Future Work

**Physical finishing.** The current build is bare wires plugged into a wall outlet. It works, but it gets unplugged accidentally more than it should. The real "done" state involves soldering the connections and putting the ESP into an enclosure.

**Color effects / scenes.** Simple color-cycling or fade effects were attempted but not implemented in firmware. The challenge was that smooth animation requires either non-blocking timing logic (using `millis()` instead of `delay()`) or interrupt-driven approaches — neither of which was in the toolkit at the time. The silver lining: Home Assistant's native scene and script system handles this on the HA side without any firmware changes, so the gap is less painful than it sounds.

**Brightness trade-off from color correction.** The `/4` attenuation on green and blue means the strip never hits its true maximum brightness. For living room accent lighting this is fine, but it's a pragmatic fix rather than a calibrated one. A proper solution would measure each channel with a light meter and apply gamma-corrected lookup tables.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | ESP8266 (NodeMCU) |
| Firmware | Arduino (C++) |
| Networking | ESP8266WiFi, PubSubClient |
| Messaging | MQTT (Mosquitto broker) |
| Smart home | Home Assistant, MQTT integration |
| Hardware | Analog RGB LED strip, common anode |
