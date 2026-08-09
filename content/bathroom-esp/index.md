---
title: Bathroom Automation Controller
nav_label: Bathroom ESP
icon: 🚿
icon_color: ''
badge: 5-stage iteration
order: 20
description: ESP8266 handling a 3-state occupancy machine from a reed switch and DHT11 — door-triggered lighting plus shower detection driving a servo fan via Home Assistant.
tags:
- ESP8266
- Reed switch
- DHT11
- State machine
---

# Bathroom ESP8266 Controller — DHT11 + Reed Switch + MQTT + Home Assistant

## Overview

An ESP8266 in the bathroom handles two independent sensor streams: a magnetic reed switch on the door and a DHT11 temperature/humidity sensor. Together they feed a three-state occupancy machine running entirely in Home Assistant, which uses the result to control the bathroom light automatically. The door determines whether the room is empty or occupied; the humidity sensor detects shower activity and promotes the state accordingly. Five automations cover every transition, and manual light changes are implicitly handled — the sensor events are always the source of truth, so the state self-corrects on the next trigger regardless of what happened to the light in the interim.

A servo-driven exhaust fan is hardware-complete and pending firmware. A VOC sensor and automated air freshener are planned additions.

---

## Hardware

- **Microcontroller:** ESP8266 (D1 Mini or similar NodeMCU variant)
- **Humidity/Temperature sensor:** DHT11 on `D4` (GPIO2)
- **Door sensor:** Magnetic reed switch on `D3` (GPIO0), wired to GND with `INPUT_PULLUP`
- **Light control:** Physical smart flipper on the wall switch — actuates multiple bulbs via Home Assistant
- **Fan control (hardware-ready):** Servo motor in a custom 3D-printed wall switch cover — CAD complete, firmware pending
- **MQTT broker:** Mosquitto on `192.168.1.144:1883`

### Wiring

```
DHT11
  VCC  ── 3.3V
  DATA ── D4 (GPIO2)
  GND  ── GND

Reed Switch
  Pin A ── D3 (GPIO0)
  Pin B ── GND
  INPUT_PULLUP enabled — LOW = door closed, HIGH = door open
```

> **Boot pin note:** GPIO0 (D3) is the ESP8266 boot mode pin. The reed switch being closed (pulling GPIO0 LOW) can prevent the chip from entering flash mode. Disconnect the reed switch before re-flashing if you run into upload failures.

---

## Iteration History

Development ran through five distinct files, each one adding a layer. The interesting evolution is in how door state gets handled.

### Stage 1 — Proof of Concept (`simple_temp_humidity.ino`)

Bare DHT11 sketch. Reads humidity and temperature every 2 seconds and prints to Serial at 9600 baud. No networking, no door sensor — just confirming the DHT11 was wired correctly and returning sane values before building anything on top of it.

---

### Stage 2 — Door Added (`bathroom_humidity_and_door_sensor.ino`)

Adds the reed switch on GPIO0 with `INPUT_PULLUP`. Door state is read each loop cycle and printed alongside temp/humidity. Still serial only — the complete hardware verification stage before introducing WiFi or MQTT.

---

### Stage 3 — MQTT Stub (`led_strip_mqtt_almost.ino`)

Adds WiFi and MQTT boilerplate — WiFi connect, broker connect, reconnect loop — but `postState()` never actually calls `client.publish()`. The publish calls are absent, hence the name. Worth noting: the filename is a misnaming artifact; this file has nothing to do with LED strips and was used as the MQTT scaffolding starting point for the bathroom project.

---

### Stage 4 — First Working MQTT Build (`bathroom_mqtt.ino`)

First fully working version. Temp and humidity publish on a 2-second timer. Door state publishes every loop cycle regardless of whether it changed:

```cpp
void updateDoor() {
  bool isOpen = digitalRead(DOORPIN);
  const char* state = isOpen ? "open" : "closed";
  Serial.print("Door is ");
  Serial.println(state);
  client.publish(door_state_topic, state, true);  // every loop — chatty
}
```

This worked end-to-end and was usable for testing, but flooding the broker with repeated identical retained messages added unnecessary noise and slightly slowed HA automation response.

---

### Stage 5 — Final Deployed Firmware (`bathroom_mqtt_quicker_door.ino`)

Adds a `door_open` bool initialized at startup from the actual pin state, and only publishes when the value changes:

```cpp
void updateDoor() {
  bool isOpen = digitalRead(DOORPIN);
  if (isOpen != door_open) {         // only publish on change
    door_open = isOpen;
    const char* state = isOpen ? "open" : "closed";
    Serial.print("Door is ");
    Serial.println(state);
    client.publish(door_state_topic, state, true);
  }
}
```

The initialization matters — without it, `door_open` defaults to `false` and the ESP fires a spurious publish on the first loop if the door happens to be open at boot. Seeding it from `digitalRead(DOORPIN)` in `setup()` prevents that.

The DHT read guards against `NaN` before publishing, which prevents bad sensor readings from polluting retained state:

```cpp
void postDHT() {
  float humidity = dht.readHumidity();
  float temperatureF = dht.readTemperature(true);
  if (isnan(humidity) || isnan(temperatureF)) {
    Serial.println("Failed to read from DHT11 sensor!");
    return;
  }
  client.publish(temp_state_topic, String(temperatureF).c_str(), true);
  client.publish(humidity_state_topic, String(humidity).c_str(), true);
}
```

---

## MQTT Topics

| Topic | Direction | Payload | Notes |
|---|---|---|---|
| `home/sensors/bathroom/door/state` | ESP → HA | `open` / `closed` | Retained. Published on change only. |
| `home/sensors/bathroom/temp/state` | ESP → HA | Float °F | Retained. Published every 2 seconds. |
| `home/sensors/bathroom/humidity/state` | ESP → HA | Float %RH | Retained. Published every 2 seconds. |

All topics configured manually in the HA MQTT integration UI — no MQTT discovery. Client ID is `bathroom-esp`.

---

## State Machine

The bathroom is always in one of three states, tracked in Home Assistant via `input_text.bathroom_state`. Sensors trigger transitions; automations act on the result.

```
   ┌─────────────────────────────────────────────────────────┐
   │                                                         │
   ▼    door opens (state = Empty)                           │
┌──────┐ ─────────────────────────► ┌──────┐                │
│Empty │                            │ Full │                │
│      │ ◄───────────────────────── │      │                │
└──────┘  door opens (state ≠ Empty) └──────┘                │
                                       │  ▲                  │
                         humidity >50% │  │ humidity <50%    │
                                       ▼  │                  │
                                    ┌────────┐               │
                                    │ Shower │               │
                                    └────────┘               │
                                         │  door opens       │
                                         └───────────────────┘
```

**Empty** — bathroom unoccupied, light off. The only way to enter this state is via a door open event (from Full or Shower) or the Sleep automation timeout.

**Full** — someone is in the bathroom, light on. Entered when the door opens from Empty. Humidity rising above 50% promotes to Shower; dropping back below 50% returns to Full.

**Shower** — active shower detected. The 1-hour light timeout (Sleep automation) does not fire in this state. Opening the door while in Shower jumps directly to Empty and turns the light off — consistent with the Exit automation's "state ≠ Empty" condition, which catches both Full and Shower.

### Dual-trigger door pattern

Both the Enter and Exit automations trigger on the same event — `binary_sensor` transitioning to `on` (door opening). The distinction is entirely in the condition:

- **Enter:** only runs when state is `Empty` → turns light on, sets state to `Full`
- **Exit:** only runs when state is not `Empty` → turns light off, sets state to `Empty`

When the door opens, Home Assistant evaluates both automations. Only one condition can be true at a time, so exactly one fires. This is more direct than using separate `on`/`off` triggers for open and close.

---

## Home Assistant Integration

### Entities

| Entity | Type | Role |
|---|---|---|
| `binary_sensor.bathroom_esp_thermo_door_sensor_bathroom` | Binary Sensor | Door — triggers Enter and Exit |
| `sensor.bathroom_esp_thermo_humidity_sensor_bathroom` | Sensor | Humidity — triggers Shower and Unshower |
| `input_text.bathroom_state` | Input Text | State register — `Empty`, `Full`, `Shower` |
| `light.bathroom_light` | Light | Used to turn the light **on** |
| `switch.bathroom_light_switch` | Switch | Used to turn the light **off** and in the Sleep trigger |

`light.bathroom_light` and `switch.bathroom_light_switch` are two separate HA entities that map to the same physical wall switch and smart flipper. The reason for the split is unclear, but both work reliably in their respective automations.

### Automations

**Bathroom Enter** — fires on door open when state is `Empty`. Turns on `light.bathroom_light`, sets state to `Full`.

**Bathroom Exit** — fires on door open when state is not `Empty` (catches both `Full` and `Shower`). Sets state to `Empty`, turns off `light.bathroom_light`.

**Bathroom Shower** — fires when humidity crosses above 50%. No condition. Sets state to `Shower`. This can happen from either `Full` or `Empty` — if someone turns on a hot shower before stepping in, the state will update regardless.

**Bathroom Unshower** — fires when humidity drops back below 50%. No condition. Sets state to `Full`. Does not touch the light — the assumption is someone is still in the bathroom post-shower.

**Bathroom Sleep** — fires when `switch.bathroom_light_switch` has been on continuously for 1 hour, provided state is not `Shower`. Turns off the switch and resets state to `Empty`. Covers the case where someone slipped out without the door sensor catching it, or left the light on manually. Intentionally suppressed during Shower state to avoid cutting the light mid-shower regardless of duration.

### Manual Override

Manual changes to the light don't require explicit handling. The door and humidity events are the source of truth — whatever state the light is in, the next sensor event will correct it. For example: if someone turns the light off manually and then opens the door to leave, the Exit automation sets state to `Empty` and tries to turn the light off, which is already off — no issue. If they turn it back on after leaving and then close the door, Sleep will eventually clean it up after an hour.

---

## Known Limitations

**Door-closed assumption.** The Enter automation only fires when state is `Empty`. If someone leaves the bathroom without closing the door, the state stays `Full` indefinitely — the next door open will trigger Exit (since state ≠ Empty) rather than Enter, turning the light off as if they're leaving. This is usually the right behavior but can produce unexpected results if the bathroom is left with the door open for extended periods.

---

## Future Work

**Exhaust fan automation (hardware-ready).** A servo motor is mounted in a custom 3D-printed wall switch cover that replaces the existing fan light switch plate. The CAD is complete and the hardware is physically installed. Firmware is not yet written — the servo will actuate the fan based on humidity, reusing the DHT11 readings already publishing from the ESP. The existing Shower state is the natural trigger.

**VOC sensor.** A volatile organic compound sensor would enable odor detection independent of humidity — a separate trigger for the fan that doesn't require a shower to be running.

**Automated air freshener.** Paired with the VOC sensor, a small actuator or relay would trigger an air freshener spray. Likely driven from the same ESP or a small satellite microcontroller, publishing to a new MQTT topic and handled by a dedicated HA automation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | ESP8266 |
| Firmware | Arduino (C++) |
| Sensors | DHT11, magnetic reed switch |
| Networking | ESP8266WiFi, PubSubClient |
| Messaging | MQTT (Mosquitto broker) |
| Smart home | Home Assistant, MQTT integration (manual) |
| Light control | Smart flipper on physical wall switch |
