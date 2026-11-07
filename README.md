# Happ CLI (Windows, Linux, macOS) — Headless Terminal VPN Client & TUI ⚡

<div align="center">

[![GitHub Release](https://img.shields.io/github/v/release/Abeh995/happ-cli?style=for-the-badge&color=blue)](https://github.com/Abeh995/happ-cli/releases)
[![License: GPL-3.0](https://img.shields.io/github/license/Abeh995/happ-cli?style=for-the-badge&color=green)](LICENSE)
[![Platforms](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=for-the-badge)](#)
[![Go Version](https://img.shields.io/badge/Go-1.24%2B-00ADD8?style=for-the-badge&logo=go)](https://golang.org)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![Build Status](https://img.shields.io/github/actions/workflow/status/Abeh995/happ-cli/build-release.yml?branch=main&style=for-the-badge)](https://github.com/Abeh995/happ-cli/actions)

**Happ CLI (happ-windows-cli)** is a high-performance, headless VPN client and interactive terminal application (TUI) for the **Happ** and **Xray-core** proxy ecosystem on **Windows**, **Linux**, and **macOS**.  
Equipped with an interactive console TUI dashboard, native Windows Layer-3 Wintun TUN virtual adapter (`happ-cli-tun`), WinINet System Proxy switching, zero-leak DoH DNS subsystem, and persistent background daemon execution.

[فارسی (Persian Guide)](README.fa.md) • [Русская документация](README.ru.md) • [Report Bug](https://github.com/Abeh995/happ-cli/issues) • [Releases](https://github.com/Abeh995/happ-cli/releases)

</div>

---

## 📖 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [5-Second Windows Installation](#-5-second-windows-installation)
- [Interactive Terminal App (TUI Dashboard)](#-interactive-terminal-app-tui-dashboard)
- [Connection Modes: TUN vs System Proxy](#-connection-modes-tun-vs-system-proxy)
- [One-Line CLI Commands](#-one-line-cli-commands)
- [Architecture & Network Internals](#-architecture--network-internals)
- [Linux & macOS Installation](#-linux--macos-installation)
- [Building from Source](#-building-from-source)
- [Frequently Asked Questions (FAQ)](#-frequently-asked-questions-faq)
- [Contributing & License](#-contributing--license)

---

## 💡 Overview

Developers, sysadmins, and power users often need a dependable, zero-lag VPN connection on headless servers, developer workstations, and development environments without dealing with bloated graphical interfaces.

**Happ CLI** bridges the gap by wrapping embedded **Xray-core** and **sing-box** engines into a lightweight, scriptable command-line interface:
- **Persistent Background Daemon:** Running `happ connect` spawns an independent background daemon. Closing the terminal or shell **never** drops the VPN connection.
- **Layer-3 Wintun TUN Routing:** Creates a virtual network adapter (`happ-cli-tun`) that transparently tunnels 100% of Windows network traffic (browsers, Telegram, Discord, terminal commands, games) without requiring per-app proxy configuration.
- **Anti-DNS Poisoning & Sniffing:** Completely eliminates local ISP DNS manipulation by intercepting UDP 53 (`hijack-dns`), sniffing TLS/HTTP/QUIC headers, and resolving through encrypted Cloudflare and Google DoH endpoints.

---

## ✨ Key Features

- ⚡ **Ultra-Fast 1-Line Setup:** Complete Windows installation in 5 seconds via automated PowerShell script.
- 🎛️ **Interactive Console Dashboard (TUI):** Sleek, keyboard-driven terminal dashboard for server browsing, mode toggling, and ping benchmarks.
- 🛡️ **Layer-3 TUN & Proxy Modes:** Instant switching between Wintun virtual adapter mode (full system) and WinINet System Proxy mode (browsers only).
- 🔒 **Zero DNS Leaks:** Built-in DNS hijacking on port 53 and encrypted remote DNS resolvers (`https+local://1.1.1.1/dns-query`, `8.8.8.8`).
- 🔄 **Detached Daemon Supervisor:** VPN stays running across multiple terminal sessions until explicitly disconnected.
- 🌐 **Modern Protocol Support:** Full support for VLESS (Reality, WebSocket, gRPC), VMess, Trojan, and Shadowsocks links.
- 📊 **Subscription Telemetry:** Displays data quota consumed, remaining bandwidth, and account expiration dates.
- 📶 **Live Latency Benchmarking:** Fast TCPing latency measurements for individual servers or entire clusters.

---

## ⚡ 5-Second Windows Installation

Open **PowerShell** (preferably **Run as Administrator** to allow virtual adapter creation) and run:

```powershell
powershell -c "irm https://raw.githubusercontent.com/Abeh995/happ-cli/main/windows/install.ps1 | iex"
```

The installer verifies prerequisites, installs the `happ` binary globally into your system `PATH`, and synchronizes the Wintun driver.

---

## 🖥️ Interactive Terminal App (TUI Dashboard)

Launch the interactive dashboard anywhere in your terminal:

```powershell
happ
```

### Dashboard Preview:
```text
┌──────────────────────────────────────────────────────────────┐
│                  HAPP VPN TERMINAL DASHBOARD                 │
├──────────────────────────────────────────────────────────────┤
│  Status:       ● CONNECTED (Background Daemon Running)       │
│  Connection:   TUN Mode (Virtual Adapter: happ-cli-tun)      │
│  Active Server:#2 🇩🇪 Frankfurt                               │
│  Daemon PIDs:  Xray: 14220 | TUN: 15304                      │
│  System Proxy: Disabled (Direct - Not needed in TUN)         │
│  Admin Privs:  Yes (Elevated)                                │
│  Total Nodes:  118                                           │
├──────────────────────────────────────────────────────────────┤
│  [1] ⚡ Connect (Start Background VPN)                         │
│  [2] 🛑 Disconnect (Stop VPN & Revert Direct)                 │
│  [3] 🌐 Select Server (Browse 118 servers)                   │
│  [4] 🔄 Update Subscription (Refresh Servers)                 │
│  [5] ➕ Add New Subscription Link                             │
│  [6] 📶 Ping Servers (Latency Test)                           │
│  [7] 🔀 Switch Mode (Current: TUN)                           │
│  [8] 📋 View Detailed Status & Public IP                      │
│  [0] 🚪 Exit Terminal App (VPN stays connected!)             │
└──────────────────────────────────────────────────────────────┘
Choose option [0-8]: 
```

---

## 🔌 Connection Modes: TUN vs System Proxy

Happ CLI supports two distinct routing architectures:

| Dimension | **TUN Mode** (Recommended) | **System Proxy Mode** |
| :--- | :--- | :--- |
| **Traffic Scope** | 100% of all applications (Browsers, Telegram, Discord, CLI, Games) | Browsers and apps respecting Windows WinINet proxy |
| **Network Layer** | Layer 3 IP Packet Tunnel (`happ-cli-tun` via Wintun driver) | Layer 7 Application Proxy (`WinINet Internet Settings`) |
| **DNS Resolution** | Intercepts UDP 53 (`hijack-dns`) — zero DNS leaks | Encrypted DoH through local Xray core |
| **Privileges** | Requires Administrator terminal | Standard User (No admin required) |

```powershell
# View current active mode:
happ mode

# Set default mode to TUN (Full system):
happ mode tun

# Set default mode to System Proxy (Browsers only):
happ mode proxy
```

---

## ⌨️ One-Line CLI Commands

For automated scripts, CI/CD, or users who prefer direct command-line execution:

| Command | Action Description |
| :--- | :--- |
| `happ` | Open interactive terminal dashboard (TUI) |
| `happ connect` | Connect to preferred node as a detached background daemon |
| `happ connect --tun` | Connect explicitly using Layer-3 TUN Mode |
| `happ connect --proxy` | Connect explicitly using System Proxy Mode |
| `happ connect <ID>` | Connect directly to node by index (e.g., `happ connect 3`) |
| `happ disconnect` | Terminate VPN background daemons and restore direct traffic |
| `happ status` | Display connection status, daemon PIDs, and public egress IP |
| `happ mode [tun/proxy]` | View or set default connection mode |
| `happ list [page]` | Browse proxy nodes with paginated view |
| `happ select <ID/query>` | Select active server by numeric ID or country/city name |
| `happ sub add <URL>` | Import new subscription link (VLESS/VMess/Trojan) |
| `happ sub update` | Refresh all subscription nodes from provider |
| `happ sub list` | View saved subscriptions and quota telemetry |
| `happ ping all` | Benchmark live TCP latency across all nodes |
| `happ help` | Print command-line usage reference |

---

## 🏗️ Architecture & Network Internals

```
+-----------------------------------------------------------------------+
|                    Terminal (PowerShell / CMD / Bash)                 |
|            Commands: happ, happ connect, happ mode, happ list         |
+-----------------------------------+-----------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
[Mode 1: TUN Mode (Default)]                [Mode 2: System Proxy Mode]
Layer-3 Virtual Network Adapter             Windows Internet Settings (WinINet)
Wintun Driver (`happ-cli-tun`)              Configures HTTP/HTTPS/SOCKS registry
Hijacks 100% of System Traffic & DNS        Routes browsers & proxy-aware apps
Requires Administrator terminal             Standard User (No Admin required)
          |                                                   |
          +-------------------------+-------------------------+
                                    |
+-----------------------------------+-----------------------------------+
|               Local Core Engine (127.0.0.1:10808 / 10809)            |
|  - Embedded Xray-core 26.9.9 (VLESS Reality / VMess / Trojan)        |
|  - Active Sniffing for TLS, HTTP, and QUIC (IPIfNonMatch strategy)    |
|  - Encrypted Remote DoH Resolvers (Cloudflare 1.1.1.1 / Google 8.8.8.8)|
+-----------------------------------------------------------------------+
```

---

## 🐧 Linux & macOS Installation

Pre-compiled standalone Go binaries for Linux and macOS are available on the [Releases](https://github.com/Abeh995/happ-cli/releases) page:

```bash
# Download latest Linux amd64 binary:
curl -Lo happ.tar.gz https://github.com/Abeh995/happ-cli/releases/latest/download/happ-linux-amd64.tar.gz
tar -xzf happ.tar.gz
sudo mv happ /usr/local/bin/

# Verify installation:
happ --help
```

### Nix / NixOS Module
Happ CLI exports a full Nix flake module with systemd service integration (`nix/module.nix`).

```nix
# flake.nix inputs
inputs.happ-cli.url = "github:Abeh995/happ-cli";

# Configuration
services.happ-cli.enable = true;
services.happ-cli.mode = "tun";
services.happ-cli.autoUpdate = true;
```

---

## 🛠️ Building from Source

### Go Core Engine
```bash
git clone https://github.com/Abeh995/happ-cli.git
cd happ-cli

# Run unit tests
go test ./...

# Build binary
CGO_ENABLED=0 go build -trimpath -o bin/happ ./cmd/happ
```

### Windows Suite
The Windows headless suite is located in `windows/` and runs on Python 3.8+:
```powershell
python -m py_compile windows/happ_core.py
```

---

## ❓ Frequently Asked Questions (FAQ)

### What is Happ Windows CLI?
**Happ Windows CLI** is the lightweight command-line and headless terminal edition of the Happ proxy client. While Happ Desktop provides a standard GUI, Happ CLI allows power users, developers, and sysadmins to run, automate, and monitor Xray-based VPN connections directly from PowerShell, Windows Terminal, CMD, or scripts without any graphical overhead.

### How do I install Happ CLI on Windows?
Run this single line in **PowerShell (Run as Administrator)**:
```powershell
powershell -c "irm https://raw.githubusercontent.com/Abeh995/happ-cli/main/windows/install.ps1 | iex"
```
This globally registers the `happ` command in your system `PATH` and synchronizes the Wintun Layer-3 driver automatically.

### Why choose Happ CLI over Happ Desktop GUI?
- **Zero GUI Overhead:** Minimal RAM and CPU consumption, ideal for developer workstations and remote servers.
- **Interactive Console Dashboard (TUI):** Sleek, keyboard-driven menu (`happ`) with real-time status and live TCP ping tests.
- **Persistent Daemon:** The VPN connection survives closing your terminal or logging out.
- **Instant TUN / Proxy Toggle:** Switch between 100% full-system routing (`happ mode tun`) and browser-only proxy (`happ mode proxy`) in 1 second.
- **Zero DNS Leaks:** Integrated DoH remote resolvers and UDP port 53 hijacking eliminate ISP DNS spoofing and manipulation.

### Which proxy protocols does Happ CLI support?
Happ CLI parses and connects to **VLESS** (Reality, WebSocket, gRPC), **VMess**, **Trojan**, and **Shadowsocks** links and subscription feeds.

---

## 🤝 Contributing & License

Contributions, issues, and feature requests are very welcome! Please read the [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

This project is licensed under the **[GNU General Public License v3.0 (GPL-3.0)](LICENSE)**.

---

<div align="center">
Crafted with precision by <a href="https://github.com/Abeh995">Abeh995</a>
</div>
