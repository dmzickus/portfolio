---
title: Alarm System Keypad
short_title: Alarm keypad
status: retired
area: embedded
summary: A 7-pin matrix keypad rewired into one analog input with a resistor ladder, so every key reads as its own
  voltage. PIN arm/disarm through Home Assistant.
tags:
- ESP8266
- Resistor ladder
- ADC
- Home Assistant
- Arduino C++
started: '2025'
focus:
- embedded
stack:
- ESP8266
- Arduino C++
- MQTT
- Home Assistant
rank: 20
timeline:
- date: '2025'
  text: Matrix keypad version works, but eats seven GPIO pins.
- date: '2025'
  text: Resistor ladder collapses the keypad onto a single ADC pin; arm/disarm via PIN and Home Assistant.
- date: '2026'
  text: Breadboard came apart; never permanently installed. Parts reused for the ESP-NOW revamp.
---
# Alarm System Keypad — Educational Project

## Overview

This project was an educational exercise in electronics and microcontroller programming, resulting in an alarm system featuring a keypad, indicator LEDs, a buzzer, and a magnetic door sensor. Though the system worked effectively—including virtual arming/disarming and alerts via Home Assistant—it was never permanently installed. The breadboard circuit eventually came apart, and planned features, such as a deadbolt motor, were ultimately not realized.

---

## Hardware

- **Microcontroller:** ESP8266 / ESP32
- **Keypad:** Transitioned from a 7-pin digital matrix to a 1-pin analog resistor ladder
- **Sensors:** Magnetic door reed switch using internal pull-up
- **Indicators:** Green, Red, and Yellow LEDs
- **Audio:** Passive Buzzer

The hardware evolved significantly to accommodate microcontroller limitations. Initially relying on 7 distinct GPIO pins for a standard matrix keypad, the system was redesigned to utilize resistor math, allowing the entire keypad to be read through a single analog pin.

---

## Iteration History

### Stage 1 — Digital Matrix Keypad (`simple_alarm.ino`)

The initial prototype used a standard digital scanning method to read the keypad. The firmware utilized the standard `Keypad.h` library to map a 4-row by 3-column matrix layout. 

```cpp
const byte ROWS = 4;
const byte COLS = 3;
byte rowPins[ROWS] = {5, 4, 0, 2};
byte colPins[COLS] = {14, 12, 13};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);
```

This matrix required a total of 7 GPIO pins mapped to the microcontroller. Because the standard method sequentially pulses input lanes and listens on output lanes, it consumed too many pins and severely limited the small microcontroller.

---

### Stage 2 — Analog Resistor Keypad (`alarm_panel.ino`)

To conserve GPIO pins, the keypad was redesigned using resistor math to output a specific analog voltage for each button press, condensed down to a single analog input on pin 13. 

**Analog Threshold Mapping.** The microcontroller read the analog voltage and mapped it against an array of 16 descending threshold values. These values started from 4097 down to 220.

```cpp
int value = analogRead(keypad_pin);
if (value != 0) {
  for (int i = 15; i >= 0; i--) {
    if (value < values[i]) {
      readSymbol(symbols[i]);
      value = 5000; // Break out
    }
  }
}
```

While this method worked perfectly for individual presses mapping exact symbols, the physical nature of the resistor logic caused unexpected behavior when multiple keys were pressed simultaneously.

---

### Stage 3 — Sensor Diagnostics (`basic_reed_sensor.ino`)

During development, a simple diagnostic script was used to verify sensor behavior.
*   The script monitored a sensor connected to pin 13 configured with an internal pull-up resistor (`INPUT_PULLUP`).
*   It tracked the digital state of the sensor and printed the result to the serial monitor at continuous 100-millisecond intervals.

---

## Architecture Diagram

```text
┌─────────────────────────────────┐
│         Resistor Keypad         │
│  16 buttons mapped to voltages  │
└────────────┬────────────────────┘
             │ Analog Input (Pin 13)
             ▼
┌─────────────────────────────────┐
│         Microcontroller         │
│  - Threshold parsing  │
│  - State management (Armed)     │
└────────────┬────────────────────┘
             │ Digital Outputs
             ▼
┌─────────────────────────────────┐
│         Status & Audio          │
│  Green/Red/Yellow LEDs│
│  Passive Buzzer       │
└─────────────────────────────────┘
```

---

## What Works

- Analog threshold mapping successfully detects all 16 unique individual button presses.
- Virtual arming, disarming, and alert notifications through Home Assistant integrations.

## Known Limitations & Future Work

**Stacked Voltages.** Combinations of multiple buttons pressed simultaneously trigger unexpected behavior due to stacked voltages in the resistor ladder.
**Physical finishing.** The circuit was purely a breadboard prototype. It was never permanently installed or soldered, and eventually fell apart. Planned features, like a motorized deadbolt lock, were never built.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | ESP8266 / ESP32 |
| Firmware | Arduino (C++) — Keypad.h |
| Inputs | Matrix Keypad, Magnetic Reed Switch |
| Outputs | Green, Red, Yellow LEDs, Passive Buzzer |