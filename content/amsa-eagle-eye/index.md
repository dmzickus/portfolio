---
title: Eagle Eye RFID Attendance
short_title: Eagle Eye attendance
summary: A high school team project that tracked class attendance with RFID cards. Arduino readers, a PHP and MySQL back end on AWS, and a Swift app.
status: retired
area: software
rank: 10
started: 2023-08
ended: 2024-05
role: Full-stack developer on a team of eight
stack: [Arduino C, PHP, MySQL, AWS, Webhooks, Swift]
focus: [fullstack, embedded]
tags: [PHP, SQL, AWS, Arduino C++, Swift, Team project]
timeline:
  - date: 2023-08
    text: Team of eight starts the attendance system at Advanced Math and Science Academy.
  - date: 2024-05
    text: Working end to end. Card tap, reader, webhook, database, and the app.
---

At Advanced Math and Science Academy, eight of us built a system that logged students into class when they tapped an RFID card. It was my first project that went from hardware all the way to an app.

- **Readers:** Arduino firmware in C that reads cards and sends each tap to the back end.
- **Back end:** PHP with a MySQL database, hosted on AWS, receiving taps over webhooks.
- **App:** a Swift mobile app for viewing attendance.

I worked on the back end and the reader firmware.
