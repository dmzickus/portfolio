---
title: CT Clamp Appliance Monitor
nav_label: CT Clamp
icon: ⚡
icon_color: yellow
badge: In progress
order: 70
description: Non-invasive current sensing for washer/dryer/dishwasher done notifications. Validated circuit on oscilloscope; blocked by ESP ADC noise — pivoting to Arduino ADC.
tags:
- CT clamp
- ADC
- Arduino
- Oscilloscope
---

# CT Clamp Appliance Monitor — Smart Home Notifications

## Overview

The goal of this project is to turn our "dumb" washer, dryer, and dishwasher into smart appliances. We have a tendency to leave clothes and dishes sitting in them long after the cycles finish, so the objective is to trigger automated notifications when they stop running. 

To achieve this safely and non-invasively, the project uses a CT (current transformer) clamp to measure the magnetic field around the appliance's power lead, allowing us to determine if electricity is flowing without splicing any high-voltage wires.

---

## Hardware

- **Sensing:** Non-invasive CT clamp 
- **Signal Conditioning Circuit:** Custom voltage divider and smoothing capacitor (breadboarded)
- **Microcontroller (Initial Testing):** ESP32 (Failed due to poor ADC quality)
- **Microcontroller (Planned):** Repurposed Arduino (for superior ADC resolution)
- **Testing Equipment:** Oscilloscope (borrowed from ECE roommate)

---

## Iteration History

### Stage 1 — Proof of Concept & Oscilloscope Validation

The first step was proving the sensor could detect a live load. We built a simple signal conditioning circuit using a voltage divider and a capacitor to bring the AC current waveform from the CT clamp into a measurable DC-biased range.

We hooked the output up to my ECE roommate's oscilloscope and clamped the sensor onto the power cable of a standard box fan. Having the oscilloscope was a huge win for debugging here—it showed a clear, measurable waveform when the fan was powered on. While a fan draws significantly less power than a washer or dryer, the proof of concept was a success.

### Stage 2 — Microcontroller Integration (The Blocker)

With the circuit working, the next logical step was connecting the conditioned analog output to a microcontroller to read the state. We specifically used an ESP32 for this stage in the hopes that it would have a better ADC.

Unfortunately, no luck. The onboard ADC (Analog-to-Digital Converter) GPIO pins on the ESP32 were of such low quality and high noise that we couldn't get any accurate or reliable readings out of them. The resolution was simply too poor to confidently distinguish between the baseline noise and the appliance's active current draw. Because we couldn't get past this detection phase, the project hasn't been integrated into Home Assistant yet.

### Stage 3 — The Arduino Pivot & Baseline Testing

Instead of buying more external parts (like a dedicated I2C ADC module), the plan is to repurpose an old Arduino. Arduinos are known for having vastly superior and stable ADCs compared to the ESP chips. 

To kick this off, I wrote a simple testing sketch (`ct_sensor_test.ino`) to dump the raw analog readings to the Serial monitor. This allows us to establish the baseline noise floor and figure out the exact threshold that indicates the appliance is actively drawing power.

```cpp
#define READ A0

void setup() {
  Serial.begin(115200);
}

void loop() {
  Serial.println(analogRead(READ));
  delay(500);
  Serial.println(analogRead(READ));
  delay(500);
}
```

---

## Architecture Diagram (Planned)

```
┌─────────────────────────────────┐
│       Appliance Power Cord      │
│  (Washer / Dryer / Dishwasher)  │
└────────────┬────────────────────┘
             │ Magnetic Field
             ▼
┌─────────────────────────────────┐
│            CT Clamp             │
│   (Non-invasive current sensor) │
└────────────┬────────────────────┘
             │ Raw AC Voltage
             ▼
┌─────────────────────────────────┐
│    Signal Conditioning Circuit  │
│ - Voltage Divider               │
│ - Smoothing Capacitor           │
└────────────┬────────────────────┘
             │ DC-Biased Analog Signal
             ▼
┌─────────────────────────────────┐
│        Repurposed Arduino       │
│  - High-quality ADC             │
│  - Signal threshold processing  │
└────────────┬────────────────────┘
             │ State (Serial/I2C)
             ▼
┌─────────────────────────────────┐
│        ESP Microcontroller      │
│  - MQTT Client (Planned)        │
│  - WiFi interface               │
└────────────┬────────────────────┘
             │ MQTT Topic
             ▼
┌─────────────────────────────────┐
│         Home Assistant          │
│  - Push notifications to phones │
└─────────────────────────────────┘
```

---

## Status & Next Steps

**What Works:**
- The CT clamp successfully registers load changes.
- The voltage divider and smoothing capacitor circuit is validated via oscilloscope.

**Known Limitations & Blockers:**
- ESP32 onboard ADC is too noisy/low-resolution for this specific analog circuit.

**Next Steps:**
- Wire the circuit output to the repurposed Arduino.
- Use the testing sketch to measure the analog threshold and determine the binary on/off state.
- Establish a communication link (Serial or I2C) between the Arduino and an ESP32.
- Write the MQTT integration on the ESP32 to push the state to Home Assistant.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller (ADC) | Arduino (C++) |
| Microcontroller (Net) | ESP32 (Planned) |
| Protocol (Planned) | MQTT |
| Smart Home | Home Assistant |
| Hardware | CT Clamp, Resistors, Capacitors, Breadboard |
