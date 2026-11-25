---
title: School Email Digest
short_title: Email digest
summary: A daily summary of my WPI inbox that puts internship postings, professors and deadlines first. Gemini does
  the daily pass and a Python script handles the backlog.
icon: 📬
highlights:
- Daily digest of the school inbox
- Internships and deadlines first
- Gemini daily, Python for the backlog
status: dormant
area: software
rank: 20
started: 2026-10
role: Solo
stack:
- Python
- IMAP / mbox
- Claude API
- Gemini scheduled actions
- Gmail filters
focus:
- fullstack
tags:
- Python
- Automation
- AI agents
timeline:
- date: 2026-10
  text: WPI mail forwarded into Gmail and labelled automatically. A Gemini scheduled action writes the daily digest.
- date: 2026-10
  text: Python script for the one-time backlog run and a weekly check that the digest didn't miss anything, keeping
    API costs low.
- date: 2026-11
  text: Not in use anymore. It probably still works.
---
The school inbox gets a lot of mail, and the emails I actually needed were internship postings, professors, classmates, and anything with a deadline. This project sorted those to the top.

- **Daily:** WPI mail auto-forwards into Gmail under a label. A Gemini scheduled action reads the day's mail and writes a digest in a fixed format, ranked by what needs a reply.
- **Backlog and safety net:** a Python script parses an mbox export, trims it, and runs it through the Claude API in batches for the one-time backlog. The same script runs weekly as a check that the digest didn't skip anything.

I've since stopped using it. It's marked dormant because I'm not sure it still runs cleanly.
