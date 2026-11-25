---
title: Claude Ops Agent for the Homelab
short_title: Homelab ops agent
summary: A custom MCP server that lets Claude check on the homelab every morning, fix routine problems itself within
  set limits, and email me a report of anything that needs a decision.
icon: 🤖
highlights:
- Custom Python MCP server, no root shell for the AI
- Typed actions run by a separate root runner
- Fixes routine issues, emails a 7 AM report
status: live
area: homelab
rank: 2
started: 2026-11
role: Solo; designed the server, the permission model and the policy it enforces
stack:
- Python
- MCP
- Docker socket proxy
- systemd
- Cloudflare Tunnel
- Cloudflare Access
- Gmail
focus:
- infra
- fullstack
tags:
- Python
- MCP
- AI agents
- Docker
- Linux
- systemd
- Cloudflare
- Security
- Self-hosting
timeline:
- date: 2026-11-17
  text: First version goes live, report-only, behind Cloudflare Access with OAuth.
- date: 2026-11-17
  text: Added a root runner that executes only fixed, typed actions, so Claude never gets a shell. Daily 7 AM report
    scheduled.
- date: 2026-11-18
  text: Widened the autonomy tier. Small config fixes and broken cron jobs get repaired first, and the report lists
    only what's left.
- date: 2026-11-18
  text: API access to every app in the media stack, with keys pulled from one secrets file.
- date: 2026-11-20
  text: OMV share management (changes need my approval). The couch game box joins the daily scan.
- date: 2026-11-25
  text: The game pipeline's held and quarantined items are now part of the daily check.
---
I wanted the homelab to tell me when something was wrong instead of me finding out when a roommate says the TV app is broken. I also didn't want to hand an AI a root shell. This project is the middle ground: Claude gets a purpose-built set of tools, and the server decides what those tools are allowed to do.

## How it works

The server is a small Python [MCP](https://modelcontextprotocol.io) server running in its own Docker stack on the media VM. Claude reaches it through a Cloudflare Tunnel, and Cloudflare Access with OAuth sits in front, so the endpoint isn't open to the internet.

It's split into three parts that don't trust each other:

1. **A read-only view.** The MCP server runs as a non-root user with the host's root filesystem mounted read-only. Secret files are denied, and secret values are redacted from anything it returns. Docker access goes through a socket proxy that allows listing, logs, and restarts, and nothing else.
2. **A collector.** A root cron job writes a host-state snapshot every 15 minutes (disk, memory, services, failed units). The MCP server only reads the file.
3. **A root runner.** Anything that changes the system is a typed action: restart this allowlisted unit, edit this file (with a `.bak`), move this folder to the HDD, run this named job. Claude can only *queue* an action. A systemd path unit wakes the runner, which validates the action against a fixed schema and runs it. There is no "run this command" action.

## Autonomy tiers

The policy file on the server spells out what can happen without me:

| Tier | Examples |
|---|---|
| Automatic | Restart an unhealthy app container (Jellyfin only if nobody is watching), clear known caches, repair a broken cron line, silence a known-noisy error |
| Maintenance window | Full system upgrades and reboot, Sundays at 5 AM |
| Needs my OK | Share or permission changes, anything touching the VPN container, databases, the tunnel, or the ops stack itself |

The morning report is written "fix first, report what's left." It lists what happened overnight, what it repaired, and the decisions it's waiting on.

## What I learned

- **The policy mattered more than the code.** Writing down where every stack lives, how containers are named, and where logs go made the whole homelab easier to reason about, for me as much as for the agent.
- **Typed actions beat clever sandboxes.** A short list of verbs with validated arguments is easy to audit. Each new ability is a deliberate code change, not a prompt.
- **Session length is a real problem.** The connector kept dropping because Access sessions and OAuth grants expired after 24 hours. I raised both through the Cloudflare API so the scheduled run doesn't silently fail.

## Next

A dedicated monitoring Pi, so the same checks cover the Proxmox host, OPNsense, Home Assistant and the exit node, with a dead man's switch in case the agent itself stops reporting.
