---
title: VPN & Downloading
icon: 🔐
icon_color: yellow
description: How Gluetun creates a container-level WireGuard tunnel that the entire download stack shares. AirVPN, port forwarding, kill switch behavior, and Docker network namespaces.
tags:
- Gluetun
- WireGuard
- AirVPN
- Docker
---

# VPN & Downloading

> All download traffic routes through an encrypted VPN tunnel. Here's how that works and why it's set up the way it is.

## Why Route Downloads Through a VPN?

Running a download pipeline without a VPN exposes your IP address to every torrent swarm you connect to. That's a privacy concern and, depending on what's being downloaded, a legal one. A VPN ensures that the IP address visible to peers and to your ISP is the VPN provider's, not yours.

The implementation has to be done carefully though. A naive setup — "just run a VPN on the host" — creates several problems:

- If the VPN drops, traffic falls back to your real IP (a "kill switch" is needed to prevent this)
- Multiple services sharing one system-level VPN can interfere with each other
- Port forwarding for qBittorrent (needed for good peer connectivity) has to be managed at the VPN provider level

The solution used here is **Gluetun** — a container-based VPN client that acts as a network gateway for other containers.

---

## Gluetun: Container-Based VPN Gateway

Gluetun is a Docker container that establishes and maintains a WireGuard (or OpenVPN) tunnel and exposes it as a network namespace that other containers can join. Instead of every container managing its own VPN connection, they all share Gluetun's tunnel.

The key Docker Compose configuration:

```yaml
# Gluetun establishes the tunnel
gluetun:
  image: qmcgaw/gluetun
  cap_add:
    - NET_ADMIN
  devices:
    - /dev/net/tun:/dev/net/tun
  environment:
    - VPN_SERVICE_PROVIDER=airvpn
    - VPN_TYPE=wireguard
    - SERVER_CITIES=Alblasserdam
    # ... AirVPN credentials and WireGuard keys

# Other containers join Gluetun's network namespace
qbittorrent:
  network_mode: "service:gluetun"
  # This container has NO direct network access — only through Gluetun

radarr:
  network_mode: "service:gluetun"

sonarr:
  network_mode: "service:gluetun"

lidarr:
  network_mode: "service:gluetun"

bazarr:
  network_mode: "service:gluetun"
```

`network_mode: "service:gluetun"` means the container shares Gluetun's network namespace entirely — it has the same IP, the same interfaces, and the same routing. If Gluetun's tunnel drops, those containers lose network access completely. There's no fallback to the host network. That's the kill switch.

**Prowlarr and Flaresolverr** are excluded from the VPN tunnel — they need to reach indexer websites and work better with a direct connection for that purpose. Only traffic from the actual download client (qBittorrent) strictly needs VPN protection; the indexing layer is less sensitive.

---

## AirVPN & WireGuard

**AirVPN** is the VPN provider. Reasons for choosing it over alternatives:

- **Port forwarding support** — critical for qBittorrent (see below). Many VPN providers have dropped port forwarding support. AirVPN still offers it.
- **WireGuard support** — WireGuard is significantly faster and more reliable than OpenVPN, with a simpler codebase and better cryptography
- **Static forwarded port** — AirVPN assigns a fixed forwarded port that doesn't change, which means the qBittorrent port configuration is set once and stays correct
- **No logging** policy

The WireGuard configuration is locked to **Alblasserdam** (Netherlands) with a static tunnel IP of `10.162.38.114`. Pinning to a specific city ensures the forwarded port assignment stays valid — forwarded ports are tied to specific servers, and if the VPN connection roams to a different city the port assignment breaks.

---

## Port Forwarding for qBittorrent

BitTorrent peer connectivity works best when you have an **open inbound port**. Without one, you're in "passive" mode — you can connect to peers who are listening, but peers can't connect to you. This cuts you off from a large portion of the swarm and hurts both download speeds and upload ratios.

AirVPN assigns a forwarded port (`24618` in this setup) that maps inbound connections on that port at the VPN server to the tunnel IP. Gluetun is configured to expose this port, and qBittorrent is configured to listen on it. The result: peers can reach qBittorrent through the VPN, as if it had a public IP.

```
Peer → AirVPN server:24618 → WireGuard tunnel → Gluetun → qBittorrent
```

Without this, qBittorrent would still work, but speeds and connectivity would be noticeably worse.

---

## Network Topology Inside Docker

Because multiple containers share Gluetun's network namespace, they all appear on the same "virtual host" from Docker's perspective. This has an important implication: **containers in the VPN group communicate with each other via `localhost`**, not via Docker's internal DNS (container names).

For example, Radarr reaching qBittorrent uses `localhost:8080`, not `qbittorrent:8080`. This tripped me up initially — the standard Docker networking advice (use container names as hostnames) doesn't apply inside a shared network namespace.

Services that need to be reachable from *outside* the VPN group (like Jellyfin accessing the arr stack's APIs) use Gluetun's port mapping to expose specific ports on the host.

---

## Lessons Learned

**`network_mode: service:gluetun` is elegant but has sharp edges.** The shared namespace is a clean solution until you hit the "use localhost not container names" issue or need to debug why a service can't reach the network. `docker exec` into a container and `curl ifconfig.me` to confirm traffic is going through the tunnel — that single check saves a lot of confusion.

**Pin your VPN city if you're using forwarded ports.** AirVPN's port forwarding is server-specific. Letting the VPN client pick any server means the forwarded port will stop working whenever it connects to a different city. Lock it down.

**WireGuard over OpenVPN if you have the choice.** WireGuard reconnects after network disruptions almost instantly (sub-second in practice). OpenVPN can take 30–60 seconds to re-establish. On a machine that occasionally loses connectivity, this matters — the arr stack can't do anything while the tunnel is down.
