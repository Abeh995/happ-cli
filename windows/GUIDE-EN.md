# HAPP-CLI: Complete 0 to 100 User Manual & Command Reference

**Happ CLI** is a headless command-line interface and interactive terminal application for the Happ VPN / Proxy ecosystem on Windows. It enables full terminal control over your proxy profiles, subscriptions, connections, routing, and system network tunnel without needing to open a graphical user interface (GUI).

---

## Table of Contents
1. [Architecture Overview & Connection Modes](#1-architecture-overview--connection-modes)
2. [Interactive Terminal App (TUI Dashboard)](#2-interactive-terminal-app-tui-dashboard)
3. [One-Line CLI Commands](#3-one-line-cli-commands)
4. [Connection Modes: TUN vs System Proxy](#4-connection-modes-tun-vs-system-proxy)
5. [Subscription Management (VLESS, VMess, Trojan)](#5-subscription-management)
6. [Latency Probing (TCP Ping)](#6-latency-probing-tcp-ping)
7. [Daemon Process & Background Architecture](#7-daemon-process--background-architecture)
8. [Command Cheat Sheet](#8-command-cheat-sheet)

---

## 1. Architecture Overview & Connection Modes

Happ CLI operates as a detached background daemon suite:

```
+-----------------------------------------------------------------------+
|                    Terminal (PowerShell / CMD)                        |
|           Commands: happ, happ connect, happ mode, happ list          |
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
|  - Xray Core 26.9.9 (VLESS Reality / VMess / Trojan)                  |
|  - Active Sniffing for TLS, HTTP, and QUIC                            |
|  - Remote DNS Resolvers (DoH 1.1.1.1 / 8.8.8.8)                       |
+-----------------------------------------------------------------------+
```

---

## 2. Interactive Terminal App (TUI Dashboard)

Opening a PowerShell or CMD window and typing `happ` without parameters launches the interactive terminal dashboard:

```powershell
happ
```

### Dashboard Interface:
```text
┌──────────────────────────────────────────────────────────────┐
│                  HAPP VPN TERMINAL DASHBOARD                 │
├──────────────────────────────────────────────────────────────┤
│  Status:       ● CONNECTED (Background Daemon Running)       │
│  Connection:   TUN Mode (Virtual Adapter: happ-cli-tun)      │
│  Active Server:#1 Germany - Ultra 01                         │
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

* **Option [7] (Switch Mode):** Instantly toggle between **TUN Mode** and **System Proxy Mode**.
* **Option [0] (Exit):** Closes the terminal dashboard, but the **VPN daemon keeps running in the background**.

---

## 3. One-Line CLI Commands

You can run any command directly from PowerShell or Command Prompt:

### 3.1 Connection Mode Management
```powershell
# View active connection mode:
happ mode

# Switch default mode to TUN (Full system routing):
happ mode tun

# Switch default mode to System Proxy (Web browsers):
happ mode proxy
```

### 3.2 Connecting & Disconnecting
```powershell
# Connect to currently selected server:
happ connect

# Connect explicitly using TUN mode:
happ connect --tun

# Connect explicitly using System Proxy mode:
happ connect --proxy

# Connect directly to server ID 5:
happ connect 5

# Disconnect and restore direct network:
happ disconnect
```

### 3.3 Server Selection & Listing
```powershell
# List first page of servers (with ID, protocol, tag, and host):
happ list

# List page 2:
happ list 2

# Select server by numeric ID:
happ select 3

# Select server by name/country search query:
happ select "Germany"
happ select "Frankfurt"
```

### 3.4 Status & Egress IP
```powershell
happ status
```
Outputs live daemon state, active node, connection mode, WinINet proxy status, elevated privilege check, and public egress IP with geolocation.

---

## 4. Connection Modes: TUN vs System Proxy

| Dimension | **TUN Mode** (Recommended) | **System Proxy Mode** |
| :--- | :--- | :--- |
| **Traffic Scope** | 100% of system traffic (Browsers, Telegram, Discord, CLI, Games) | Browsers and apps respecting WinINet proxy |
| **Network Layer** | Layer 3 IP Packet Tunnel (`wintun.sys` via `sing-box.exe`) | Layer 7 Application Proxy (`WinINet Internet Settings`) |
| **DNS Handling** | Full DNS hijacking on port 53 (Zero ISP DNS leaks) | Remote DoH through Xray core + active sniffing |
| **Privileges** | Requires Administrator terminal | Standard User |
| **Adapter Name** | `happ-cli-tun` | N/A |

---

## 5. Subscription Management

### Adding a Subscription
```powershell
happ sub add "https://dash.cyberpower.space/guards/173d5ef57198aa54e09acc39d32bef57#8556_abeh"
```
Imports and parses VLESS (Reality/WS/gRPC), VMess, and Trojan links, assigning sequential IDs.

### Updating Subscriptions
```powershell
happ sub update
```
Refreshes all proxy nodes and updates account usage info from the server.

### Listing Subscriptions
```powershell
happ sub list
```

---

## 6. Latency Probing (TCP Ping)

```powershell
# Ping default target (8.8.8.8:53):
happ ping

# Ping all saved servers in batch:
happ ping all

# Ping custom host and port:
happ ping 1.1.1.1 53
```

---

## 7. Daemon Process & Background Architecture

When `happ connect` executes:
1. Two background processes are launched detached from the terminal:
   - `xray.exe`: The cryptographic proxy core (handling VLESS Reality).
   - `sing-box.exe`: The Layer-3 Wintun TUN adapter engine (in TUN mode).
2. The processes run with `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_NO_WINDOW`.
3. Closing the terminal or shell does NOT kill the VPN.
4. Running `happ disconnect` safely terminates both child processes via their tracked PIDs in `%LOCALAPPDATA%\happ-cli\daemon.json` and restores default routing.

---

## 8. Command Cheat Sheet

| Command | Action |
| :--- | :--- |
| `happ` | Open interactive terminal dashboard (TUI) |
| `happ mode` | Check current connection mode |
| `happ mode tun` | Set default mode to TUN (Virtual Adapter) |
| `happ mode proxy` | Set default mode to System Proxy |
| `happ connect` | Start VPN in background |
| `happ connect --tun` | Connect using TUN mode |
| `happ connect --proxy` | Connect using Proxy mode |
| `happ connect <id>` | Connect directly to node ID |
| `happ disconnect` | Stop VPN and restore direct network |
| `happ status` | Show status, IP, country, and daemon PIDs |
| `happ list [page]` | View available proxy nodes |
| `happ select <id>` | Select server ID |
| `happ sub add <url>` | Add subscription URL |
| `happ sub update` | Refresh all subscription nodes |
| `happ ping all` | Test latency across servers |
| `happ help` | Print command line help |

---
*Maintained for Happ CLI | GitHub: [github.com/Abeh995/happ-cli](https://github.com/Abeh995/happ-cli)*
