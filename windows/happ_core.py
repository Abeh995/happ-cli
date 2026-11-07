#!/usr/bin/env python3
"""
Happ Windows Terminal Application & Background Daemon (happ-cli)
Author: Abeh995
Provides terminal interactive TUI, persistent background daemon,
and direct CLI commands for managing Happ VPN on Windows.
Supports both TUN Mode (Wintun Layer 3) and System Proxy Mode.
"""

import sys
import os
import json
import socket
import subprocess
import time
import urllib.request
import urllib.parse
import base64
import winreg
import ctypes
import shutil
from typing import List, Dict, Optional, Tuple

# Enable Virtual Terminal Processing on Windows Console
def enable_vt_mode():
    try:
        kernel32 = ctypes.windll.kernel32
        h_conout = kernel32.CreateFileW("CONOUT$", 0xC0000000, 2, None, 3, 0, None)
        if h_conout != -1:
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_conout, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h_conout, mode.value | 0x0004) # ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.CloseHandle(h_conout)
        kernel32.SetConsoleOutputCP(65001) # UTF-8
    except Exception:
        pass

enable_vt_mode()

# Color definitions
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"
GRAY = "\033[90m"

# Paths
APP_DIR = os.path.expandvars(r"%LOCALAPPDATA%\happ-cli")
os.makedirs(APP_DIR, exist_ok=True)
DATA_FILE = os.path.join(APP_DIR, "data.json")
DAEMON_FILE = os.path.join(APP_DIR, "daemon.json")
RUNTIME_CFG = os.path.join(APP_DIR, "runtime_xray.json")
RUNTIME_SINGBOX_CFG = os.path.join(APP_DIR, "runtime_singbox.json")

HAPP_SYSTEM_DIR = r"C:\Program Files\FlyFrogLLC\Happ"
XRAY_BIN = os.path.join(HAPP_SYSTEM_DIR, "core", "xray.exe")
SINGBOX_BIN = os.path.join(HAPP_SYSTEM_DIR, "tun", "sing-box.exe")
TCPING_BIN = os.path.join(HAPP_SYSTEM_DIR, "happ-tcping.exe")
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
USER_AGENT = "INCY/2.4.1/macos CFNetwork/3860.600.21 Darwin/25.5.0"

# Copy wintun.dll to APP_DIR if missing to ensure sing-box loads it reliably
WINTUN_SRC = os.path.join(HAPP_SYSTEM_DIR, "core", "wintun.dll")
WINTUN_DST = os.path.join(APP_DIR, "wintun.dll")
if os.path.isfile(WINTUN_SRC) and not os.path.isfile(WINTUN_DST):
    try:
        shutil.copy2(WINTUN_SRC, WINTUN_DST)
    except Exception:
        pass

# --- Privileges & System Helpers ---

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# --- WinINet & Registry Functions ---

def refresh_wininet():
    try:
        wininet = ctypes.windll.wininet
        wininet.InternetSetOptionW(0, 39, 0, 0) # INTERNET_OPTION_SETTINGS_CHANGED
        wininet.InternetSetOptionW(0, 37, 0, 0) # INTERNET_OPTION_REFRESH
    except Exception:
        pass

def get_sys_proxy() -> Tuple[bool, str]:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as k:
            enable, _ = winreg.QueryValueEx(k, "ProxyEnable")
            server = ""
            try:
                server, _ = winreg.QueryValueEx(k, "ProxyServer")
            except FileNotFoundError:
                pass
            return bool(enable), server
    except Exception:
        return False, ""

def set_sys_proxy(enable: bool, server: str = "http=127.0.0.1:10809;https=127.0.0.1:10809;socks=127.0.0.1:10808"):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE) as k:
            winreg.SetValueEx(k, "ProxyEnable", 0, winreg.REG_DWORD, 1 if enable else 0)
            if enable:
                winreg.SetValueEx(k, "ProxyServer", 0, winreg.REG_SZ, server)
                winreg.SetValueEx(k, "ProxyOverride", 0, winreg.REG_SZ, "<local>;<-loopback>")
        refresh_wininet()
        return True
    except Exception:
        return False

# --- Data Store ---

def load_data() -> dict:
    if os.path.isfile(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "mode" not in d:
                    d["mode"] = "tun"
                return d
        except Exception:
            pass
    return {"subscriptions": [], "nodes": [], "selected_node_id": None, "mode": "tun"}

def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Daemon Process Management ---

def is_process_running(pid: int) -> bool:
    try:
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    except Exception:
        return False

def get_daemon_state() -> Optional[dict]:
    if os.path.isfile(DAEMON_FILE):
        try:
            with open(DAEMON_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            x_pid = d.get("xray_pid") or d.get("pid")
            if x_pid and is_process_running(x_pid):
                return d
            else:
                # Process is dead, clean up stale state
                if os.path.isfile(DAEMON_FILE):
                    os.remove(DAEMON_FILE)
        except Exception:
            pass
    return None

def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0

def tcp_ping(host: str, port: int) -> int:
    if os.path.isfile(TCPING_BIN):
        try:
            out = subprocess.check_output([TCPING_BIN, host, str(port)], text=True, timeout=2.5, stderr=subprocess.DEVNULL).strip()
            val = int(out)
            return val if val > 0 else -1
        except Exception:
            pass
    t0 = time.time()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((host, port))
            return int((time.time() - t0) * 1000)
    except Exception:
        return -1

# --- VLESS / VMess / Trojan Parsing & Config Builders ---

def parse_node_link(link: str) -> Optional[dict]:
    link = link.strip()
    if not link:
        return None

    if link.startswith("vless://"):
        try:
            u = urllib.parse.urlparse(link)
            q = urllib.parse.parse_qs(u.query)
            tag = urllib.parse.unquote(u.fragment) if u.fragment else f"{u.hostname}:{u.port}"
            return {
                "protocol": "vless",
                "tag": tag,
                "host": u.hostname,
                "port": u.port or 443,
                "uuid": u.username,
                "security": q.get("security", ["none"])[0],
                "net": q.get("type", ["tcp"])[0],
                "sni": q.get("sni", [u.hostname])[0],
                "flow": q.get("flow", [""])[0],
                "pbk": q.get("pbk", [""])[0],
                "sid": q.get("sid", [""])[0],
                "spx": q.get("spx", [""])[0],
                "path": q.get("path", ["/"])[0],
                "serviceName": q.get("serviceName", [""])[0],
                "raw": link
            }
        except Exception:
            return None

    elif link.startswith("vmess://"):
        try:
            raw_b64 = link[8:]
            pad = len(raw_b64) % 4
            if pad:
                raw_b64 += "=" * (4 - pad)
            payload = json.loads(base64.b64decode(raw_b64).decode("utf-8", errors="ignore"))
            tag = payload.get("ps") or f"{payload.get('add')}:{payload.get('port')}"
            return {
                "protocol": "vmess",
                "tag": tag,
                "host": payload.get("add"),
                "port": int(payload.get("port", 443)),
                "uuid": payload.get("id"),
                "aid": int(payload.get("aid", 0)),
                "security": payload.get("tls", "none"),
                "net": payload.get("net", "tcp"),
                "sni": payload.get("sni") or payload.get("host") or payload.get("add"),
                "path": payload.get("path", "/"),
                "raw": link
            }
        except Exception:
            return None

    elif link.startswith("trojan://"):
        try:
            u = urllib.parse.urlparse(link)
            q = urllib.parse.parse_qs(u.query)
            tag = urllib.parse.unquote(u.fragment) if u.fragment else f"{u.hostname}:{u.port}"
            return {
                "protocol": "trojan",
                "tag": tag,
                "host": u.hostname,
                "port": u.port or 443,
                "password": u.username,
                "security": q.get("security", ["tls"])[0],
                "net": q.get("type", ["tcp"])[0],
                "sni": q.get("sni", [u.hostname])[0],
                "raw": link
            }
        except Exception:
            return None

    return None

def build_xray_config(node: dict, socks_port: int = 10808, http_port: int = 10809) -> dict:
    """
    Builds robust Xray core configuration with:
    1. Remote DoH / Cloudflare / Google DNS to eliminate local Iranian ISP DNS poisoning.
    2. Active TLS/HTTP/QUIC sniffing on inbounds.
    3. IPIfNonMatch domain routing strategy.
    """
    cfg = {
        "log": {"loglevel": "warning"},
        "dns": {
            "servers": [
                "https+local://1.1.1.1/dns-query",
                "https+local://8.8.8.8/dns-query",
                "1.1.1.1",
                "8.8.8.8"
            ],
            "queryStrategy": "UseIPv4"
        },
        "inbounds": [
            {
                "port": socks_port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"udp": True, "auth": "noauth"},
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls", "quic"],
                    "metadataOnly": False,
                    "routeOnly": False
                },
                "tag": "socks-in"
            },
            {
                "port": http_port,
                "listen": "127.0.0.1",
                "protocol": "http",
                "settings": {"timeout": 300},
                "sniffing": {
                    "enabled": True,
                    "destOverride": ["http", "tls", "quic"],
                    "metadataOnly": False,
                    "routeOnly": False
                },
                "tag": "http-in"
            }
        ],
        "outbounds": [],
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "rules": [
                {
                    "type": "field",
                    "inboundTag": ["socks-in", "http-in"],
                    "outboundTag": "proxy"
                }
            ]
        }
    }

    proto = node.get("protocol")

    if proto == "vless":
        user_obj = {
            "id": node.get("uuid"),
            "encryption": "none"
        }
        if node.get("flow"):
            user_obj["flow"] = node.get("flow")

        stream_settings = {
            "network": node.get("net", "tcp"),
            "security": node.get("security", "none")
        }

        if node.get("security") == "tls":
            stream_settings["tlsSettings"] = {
                "serverName": node.get("sni") or node.get("host"),
                "allowInsecure": False
            }
        elif node.get("security") == "reality":
            stream_settings["realitySettings"] = {
                "show": False,
                "dest": f"{node.get('host')}:{node.get('port')}",
                "serverName": node.get("sni") or node.get("host"),
                "publicKey": node.get("pbk", ""),
                "shortId": node.get("sid", ""),
                "spiderX": node.get("spx", "")
            }

        if node.get("net") == "ws":
            stream_settings["wsSettings"] = {
                "path": node.get("path", "/"),
                "headers": {"Host": node.get("sni") or node.get("host")}
            }
        elif node.get("net") == "grpc":
            stream_settings["grpcSettings"] = {
                "serviceName": node.get("serviceName", "")
            }

        outbound = {
            "protocol": "vless",
            "tag": "proxy",
            "settings": {
                "vnext": [
                    {
                        "address": node.get("host"),
                        "port": node.get("port"),
                        "users": [user_obj]
                    }
                ]
            },
            "streamSettings": stream_settings
        }
        cfg["outbounds"].append(outbound)

    elif proto == "vmess":
        stream_settings = {
            "network": node.get("net", "tcp"),
            "security": node.get("security", "none")
        }
        if node.get("security") == "tls":
            stream_settings["tlsSettings"] = {
                "serverName": node.get("sni") or node.get("host"),
                "allowInsecure": False
            }
        if node.get("net") == "ws":
            stream_settings["wsSettings"] = {
                "path": node.get("path", "/"),
                "headers": {"Host": node.get("sni") or node.get("host")}
            }

        outbound = {
            "protocol": "vmess",
            "tag": "proxy",
            "settings": {
                "vnext": [
                    {
                        "address": node.get("host"),
                        "port": node.get("port"),
                        "users": [
                            {
                                "id": node.get("uuid"),
                                "alterId": node.get("aid", 0),
                                "security": "auto"
                            }
                        ]
                    }
                ]
            },
            "streamSettings": stream_settings
        }
        cfg["outbounds"].append(outbound)

    elif proto == "trojan":
        stream_settings = {
            "network": node.get("net", "tcp"),
            "security": "tls",
            "tlsSettings": {
                "serverName": node.get("sni") or node.get("host"),
                "allowInsecure": False
            }
        }
        outbound = {
            "protocol": "trojan",
            "tag": "proxy",
            "settings": {
                "servers": [
                    {
                        "address": node.get("host"),
                        "port": node.get("port"),
                        "password": node.get("password")
                    }
                ]
            },
            "streamSettings": stream_settings
        }
        cfg["outbounds"].append(outbound)

    cfg["outbounds"].append({"protocol": "freedom", "tag": "direct"})
    return cfg

def build_singbox_tun_config(socks_port: int = 10808) -> dict:
    """
    Builds Layer-3 Wintun TUN adapter configuration for sing-box.
    Hijacks all system DNS (UDP 53) and routes 100% of Windows network
    traffic through the local Xray SOCKS5 core.
    """
    return {
        "dns": {
            "servers": [
                {
                    "address": "8.8.8.8",
                    "detour": "direct",
                    "tag": "dns-proxy"
                }
            ]
        },
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun-in",
                "interface_name": "happ-cli-tun",
                "address": ["172.18.0.1/30"],
                "mtu": 1500,
                "auto_route": True,
                "strict_route": True,
                "stack": "mixed"
            }
        ],
        "log": {
            "level": "warn",
            "timestamp": True
        },
        "outbounds": [
            {
                "type": "socks",
                "tag": "proxy",
                "server": "127.0.0.1",
                "server_port": socks_port,
                "udp_fragment": True,
                "domain_resolver": {
                    "server": "dns-proxy",
                    "strategy": "prefer_ipv4"
                }
            },
            {
                "type": "direct",
                "tag": "direct",
                "domain_resolver": {
                    "server": "dns-proxy",
                    "strategy": "prefer_ipv4"
                }
            }
        ],
        "route": {
            "auto_detect_interface": True,
            "final": "proxy",
            "rules": [
                {
                    "process_name": [
                        "xray.exe",
                        "sing-box.exe",
                        "python.exe",
                        "happd.exe"
                    ],
                    "outbound": "direct"
                },
                {
                    "action": "sniff"
                },
                {
                    "protocol": "dns",
                    "action": "hijack-dns"
                }
            ]
        }
    }

# --- Subscription Fetcher ---

def fetch_subscription(sub_url: str) -> Tuple[List[dict], dict]:
    req = urllib.request.Request(sub_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=12) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        headers = dict(resp.headers)

    content = body.strip()
    if not content.startswith(("vless://", "vmess://", "trojan://", "ss://")):
        try:
            pad = len(content) % 4
            if pad:
                content += "=" * (4 - pad)
            decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
            if any(p in decoded for p in ["vless://", "vmess://", "trojan://", "ss://"]):
                content = decoded
        except Exception:
            pass

    nodes = []
    lines = content.splitlines()
    for line in lines:
        node = parse_node_link(line)
        if node and node.get("host"):
            nodes.append(node)

    return nodes, headers

# --- Core VPN Controller ---

def start_vpn(node: Optional[dict] = None) -> bool:
    data = load_data()
    mode = data.get("mode", "tun").lower()

    if not node:
        sel_id = data.get("selected_node_id")
        nodes = data.get("nodes", [])
        if sel_id:
            for n in nodes:
                if n.get("id") == sel_id:
                    node = n
                    break
        if not node and nodes:
            node = nodes[0]
            data["selected_node_id"] = node.get("id")
            save_data(data)

    if not node:
        print(f"{RED}Error: No server selected or available. Add a subscription first with 'happ sub add <url>'.{RESET}")
        return False

    if mode == "tun":
        if not is_admin():
            print(f"\n{RED}Error: TUN mode requires Administrator privileges to create the Wintun network adapter.{RESET}")
            print(f"{YELLOW}Suggestions:{RESET}")
            print(f"  1. Re-run your PowerShell/Terminal as {BOLD}Administrator{RESET}.")
            print(f"  2. Or switch to System Proxy mode: {CYAN}happ mode proxy{RESET}\n")
            return False

        if not os.path.isfile(SINGBOX_BIN):
            print(f"{RED}Error: sing-box core not found at '{SINGBOX_BIN}'. Ensure Happ Desktop is installed.{RESET}")
            return False

    if not os.path.isfile(XRAY_BIN):
        print(f"{RED}Error: Xray core not found at '{XRAY_BIN}'. Ensure Happ Desktop is installed.{RESET}")
        return False

    # Stop any running daemon first
    stop_vpn(silent=True)

    # 1. Build & save Xray configuration
    cfg = build_xray_config(node, socks_port=10808, http_port=10809)
    with open(RUNTIME_CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    # Common process flags for detached background execution
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    CREATE_NO_WINDOW = 0x08000000
    flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0 # SW_HIDE

    # 2. Launch Xray core
    try:
        p_xray = subprocess.Popen(
            [XRAY_BIN, "run", "-c", RUNTIME_CFG],
            cwd=APP_DIR,
            creationflags=flags,
            startupinfo=startupinfo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"{RED}Failed to launch Xray core: {e}{RESET}")
        return False

    time.sleep(1.0)
    if not is_process_running(p_xray.pid) or not is_port_listening(10808):
        print(f"{RED}Error: Xray core exited prematurely. Check server parameters.{RESET}")
        return False

    p_tun_pid = None

    # 3. Handle TUN mode or Proxy mode
    if mode == "tun":
        sb_cfg = build_singbox_tun_config(socks_port=10808)
        with open(RUNTIME_SINGBOX_CFG, "w", encoding="utf-8") as f:
            json.dump(sb_cfg, f, ensure_ascii=False, indent=2)

        try:
            p_tun = subprocess.Popen(
                [SINGBOX_BIN, "run", "-c", RUNTIME_SINGBOX_CFG],
                cwd=APP_DIR,
                creationflags=flags,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            p_tun_pid = p_tun.pid
        except Exception as e:
            print(f"{RED}Failed to launch sing-box TUN daemon: {e}{RESET}")
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p_xray.pid)], capture_output=True)
            except Exception:
                pass
            return False

        time.sleep(1.2)
        if not is_process_running(p_tun.pid):
            print(f"{RED}Error: sing-box TUN daemon failed to initialize Wintun adapter.{RESET}")
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p_xray.pid)], capture_output=True)
            except Exception:
                pass
            return False

        # In TUN mode, WinINet system proxy is not needed because Layer-3 routes all packets
        set_sys_proxy(False)

    else:
        # System Proxy mode: Enable Windows WinINet proxy with HTTP/HTTPS/SOCKS
        set_sys_proxy(True, "http=127.0.0.1:10809;https=127.0.0.1:10809;socks=127.0.0.1:10808")

    # Record active state in daemon.json
    daemon_info = {
        "xray_pid": p_xray.pid,
        "tun_pid": p_tun_pid,
        "pid": p_xray.pid, # backward compatibility
        "mode": mode,
        "node_id": node.get("id"),
        "node_tag": node.get("tag"),
        "host": node.get("host"),
        "port": node.get("port"),
        "protocol": node.get("protocol"),
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(DAEMON_FILE, "w", encoding="utf-8") as f:
        json.dump(daemon_info, f, indent=2)

    return True

def stop_vpn(silent: bool = False):
    d = get_daemon_state()
    if d:
        pids = []
        if d.get("tun_pid"):
            pids.append(d.get("tun_pid"))
        if d.get("xray_pid"):
            pids.append(d.get("xray_pid"))
        if d.get("pid") and d.get("pid") not in pids:
            pids.append(d.get("pid"))

        for pid in pids:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            except Exception:
                pass

        if os.path.isfile(DAEMON_FILE):
            try:
                os.remove(DAEMON_FILE)
            except Exception:
                pass

    # Revert System Proxy
    set_sys_proxy(False)

    if not silent:
        print(f"{GREEN}✓ VPN disconnected. Direct network restored.{RESET}")

def get_egress_ip() -> Optional[dict]:
    try:
        cmd = ["curl.exe", "-s", "--max-time", "3", "http://ip-api.com/json"]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except Exception:
        return None

# --- CLI Action Handlers ---

def cmd_status():
    d = get_daemon_state()
    proxy_on, proxy_srv = get_sys_proxy()
    port_open = is_port_listening(10808)
    data = load_data()
    mode = (d.get("mode") if d else data.get("mode", "tun")).upper()

    print(f"\n{BOLD}{CYAN}┌────────────────────────────────────────────────────────┐{RESET}")
    print(f"{BOLD}{CYAN}│                   HAPP VPN STATUS                      │{RESET}")
    print(f"{BOLD}{CYAN}├────────────────────────────────────────────────────────┤{RESET}")

    if d and port_open:
        print(f"│  {BOLD}Status:{RESET}       {GREEN}● Connected (Background Daemon active){RESET}    │")
        print(f"│  {BOLD}Mode:{RESET}         {CYAN}{mode:<43}{RESET}│")
        print(f"│  {BOLD}Active Node:{RESET}  {WHITE}{d.get('node_tag')[:38]:<38}{RESET} │")
        print(f"│  {BOLD}Protocol:{RESET}     {CYAN}{d.get('protocol', 'vless').upper():<43}{RESET}│")
        pids_str = f"Xray: {d.get('xray_pid') or d.get('pid')}"
        if d.get("tun_pid"):
            pids_str += f" | TUN: {d.get('tun_pid')}"
        print(f"│  {BOLD}Daemons:{RESET}      {GRAY}{pids_str:<43}{RESET}│")
    elif port_open:
        print(f"│  {BOLD}Status:{RESET}       {YELLOW}● Connected via external Happ instance{RESET}    │")
        print(f"│  {BOLD}Mode:{RESET}         {CYAN}{mode:<43}{RESET}│")
    else:
        print(f"│  {BOLD}Status:{RESET}       {RED}○ Disconnected (Direct Traffic){RESET}           │")
        print(f"│  {BOLD}Config Mode:{RESET}  {CYAN}{mode:<43}{RESET}│")

    p_str = f"{GREEN}Enabled ({proxy_srv[:28]}){RESET}" if proxy_on else f"{GRAY}Disabled (Direct){RESET}"
    print(f"│  {BOLD}System Proxy:{RESET} {p_str:<51}│")
    admin_str = f"{GREEN}Yes (Elevated){RESET}" if is_admin() else f"{YELLOW}No (Standard User){RESET}"
    print(f"│  {BOLD}Admin Privs:{RESET}  {admin_str:<51}│")
    print(f"{BOLD}{CYAN}├────────────────────────────────────────────────────────┤{RESET}")

    info = get_egress_ip()
    if info and info.get("status") == "success":
        ip = info.get("query")
        loc = f"{info.get('country')} ({info.get('countryCode')}) - {info.get('city')}"
        isp = f"{info.get('isp')}"
        print(f"│  {BOLD}Public IP:{RESET}    {CYAN}{ip:<43}{RESET}│")
        print(f"│  {BOLD}Location:{RESET}     {loc[:43]:<43}│")
        print(f"│  {BOLD}ISP:{RESET}          {isp[:43]:<43}│")
    else:
        print(f"│  {GRAY}Egress IP lookup timed out.                           {RESET}│")

    print(f"{BOLD}{CYAN}└────────────────────────────────────────────────────────┘{RESET}\n")

def cmd_mode(target_mode: Optional[str] = None):
    data = load_data()
    curr = data.get("mode", "tun").lower()
    if not target_mode:
        print(f"\n{BOLD}Current Connection Mode:{RESET} {CYAN}{curr.upper()}{RESET}")
        if curr == "tun":
            print(f"  {GREEN}● TUN Mode:{RESET} Full system virtual network adapter (happ-cli-tun).")
            print(f"    Routes all applications, browsers, Telegram, Discord, and terminal.")
        else:
            print(f"  {YELLOW}● System Proxy Mode:{RESET} Windows Internet Settings (WinINet).")
            print(f"    Routes browsers and proxy-aware apps via 127.0.0.1:10808 / 10809.")
        print(f"\n{DIM}To switch mode, run: happ mode tun  OR  happ mode proxy{RESET}\n")
        return

    target_mode = target_mode.lower().strip()
    if target_mode not in ["tun", "proxy"]:
        print(f"{RED}Invalid mode '{target_mode}'. Choose 'tun' or 'proxy'.{RESET}")
        return

    if target_mode == "tun" and not is_admin():
        print(f"{YELLOW}Warning: TUN mode requires Administrator privileges to create network adapter.{RESET}")
        print(f"Please ensure you run terminal as Administrator when connecting in TUN mode.")

    data["mode"] = target_mode
    save_data(data)
    print(f"{GREEN}✓ Default connection mode set to: {BOLD}{target_mode.upper()}{RESET}")
    if target_mode == "tun":
        print(f"  Mode: Virtual Network Adapter (happ-cli-tun) for 100% of system traffic.")
    else:
        print(f"  Mode: System Proxy (WinINet) for web browsers and proxy-aware applications.")

    # If VPN is currently running, restart it seamlessly with the new mode
    if get_daemon_state():
        print(f"\n{CYAN}VPN is currently running. Reconnecting seamlessly in {target_mode.upper()} mode...{RESET}")
        start_vpn()

def cmd_sub_add(url_arg: str, name_arg: str = "primary"):
    url_arg = url_arg.strip().strip("'\"")
    if not url_arg.startswith(("http://", "https://")):
        print(f"{RED}Error: Subscription URL must begin with http:// or https://{RESET}")
        return

    print(f"{CYAN}Fetching subscription from server...{RESET}")
    try:
        nodes, headers = fetch_subscription(url_arg)
    except Exception as e:
        print(f"{RED}Failed to fetch subscription: {e}{RESET}")
        return

    if not nodes:
        print(f"{RED}No valid proxy configurations (VLESS/VMess/Trojan) found in subscription.{RESET}")
        return

    data = load_data()
    data["subscriptions"] = [s for s in data.get("subscriptions", []) if s.get("name") != name_arg]

    sub_info = {
        "name": name_arg,
        "url": url_arg,
        "nodes_count": len(nodes),
        "user_info": headers.get("Subscription-Userinfo", ""),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    data["subscriptions"].append(sub_info)

    formatted_nodes = []
    for idx, n in enumerate(nodes, 1):
        n["id"] = idx
        formatted_nodes.append(n)

    data["nodes"] = formatted_nodes
    if formatted_nodes:
        data["selected_node_id"] = 1

    save_data(data)
    print(f"{GREEN}✓ Successfully added subscription '{name_arg}'!{RESET}")
    print(f"  Imported: {BOLD}{len(formatted_nodes)}{RESET} nodes.")
    if sub_info["user_info"]:
        print(f"  Account Info: {GRAY}{sub_info['user_info']}{RESET}")
    print(f"  Active Node: {CYAN}#{formatted_nodes[0]['id']} {formatted_nodes[0]['tag']}{RESET}")

def cmd_sub_update():
    data = load_data()
    subs = data.get("subscriptions", [])
    if not subs:
        print(f"{YELLOW}No subscriptions found. Add one with 'happ sub add <url>'.{RESET}")
        return

    total_imported = 0
    for sub in subs:
        print(f"{CYAN}Updating '{sub.get('name')}'...{RESET}")
        try:
            nodes, headers = fetch_subscription(sub.get("url"))
            if nodes:
                sub["nodes_count"] = len(nodes)
                sub["user_info"] = headers.get("Subscription-Userinfo", "")
                sub["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                formatted = []
                for idx, n in enumerate(nodes, 1):
                    n["id"] = idx
                    formatted.append(n)
                data["nodes"] = formatted
                total_imported += len(formatted)
                print(f"  {GREEN}✓ Updated: {len(formatted)} nodes imported.{RESET}")
        except Exception as e:
            print(f"  {RED}Failed: {e}{RESET}")

    save_data(data)
    print(f"{GREEN}✓ All subscriptions updated successfully.{RESET}")

def cmd_list(page: int = 1, page_size: int = 20):
    data = load_data()
    nodes = data.get("nodes", [])
    if not nodes:
        print(f"{YELLOW}No nodes available. Add a subscription first with 'happ sub add <url>'.{RESET}")
        return

    sel_id = data.get("selected_node_id", 1)
    total = len(nodes)
    total_pages = (total + page_size - 1) // page_size
    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    end = min(start + page_size, total)

    print(f"\n{BOLD}{CYAN}=== Available Servers ({start+1}-{end} of {total}) - Page {page}/{total_pages} ==={RESET}")
    print(f" {BOLD}{'ID':<4} {'PROTOCOL':<8} {'TAG / LOCATION':<36} {'HOST':<26} {'PORT'}{RESET}")
    print(f" {GRAY}{'-'*82}{RESET}")

    for n in nodes[start:end]:
        nid = n.get("id")
        marker = f"{GREEN}●{RESET}" if nid == sel_id else " "
        proto = n.get("protocol", "").upper()
        tag = n.get("tag", "")[:34]
        host = n.get("host", "")[:24]
        port = str(n.get("port", ""))
        print(f"{marker}{nid:<3} {proto:<8} {tag:<36} {host:<26} {port}")

    print(f" {GRAY}{'-'*82}{RESET}")
    print(f" {DIM}To select: happ select <ID> | To view next page: happ list <page>{RESET}\n")

def cmd_select(node_id_or_name: str):
    data = load_data()
    nodes = data.get("nodes", [])
    if not nodes:
        print(f"{RED}No nodes available. Add a subscription first.{RESET}")
        return

    target = None
    if node_id_or_name.isdigit():
        target_id = int(node_id_or_name)
        for n in nodes:
            if n.get("id") == target_id:
                target = n
                break
    else:
        query = node_id_or_name.lower()
        for n in nodes:
            if query in n.get("tag", "").lower() or query in n.get("host", "").lower():
                target = n
                break

    if not target:
        print(f"{RED}Error: Server matching '{node_id_or_name}' not found.{RESET}")
        return

    data["selected_node_id"] = target.get("id")
    save_data(data)
    print(f"{GREEN}✓ Selected server #{target.get('id')}: {BOLD}{target.get('tag')}{RESET} ({target.get('host')}:{target.get('port')})")

    # If VPN is currently connected, restart it with the new server seamlessly
    if get_daemon_state():
        print(f"{CYAN}Switching active VPN connection to {target.get('tag')}...{RESET}")
        if start_vpn(target):
            print(f"{GREEN}✓ Switched seamlessly to new server!{RESET}")

def cmd_connect(node_id_or_name: Optional[str] = None):
    if node_id_or_name:
        cmd_select(node_id_or_name)

    data = load_data()
    sel_id = data.get("selected_node_id")
    target = None
    for n in data.get("nodes", []):
        if n.get("id") == sel_id:
            target = n
            break

    if not target:
        if data.get("nodes"):
            target = data["nodes"][0]
        else:
            print(f"{RED}Error: No servers available. Run 'happ sub add <url>' first.{RESET}")
            return

    mode = data.get("mode", "tun").upper()
    print(f"{CYAN}Connecting to #{target.get('id')} {target.get('tag')} in [{mode} Mode]...{RESET}")
    if start_vpn(target):
        print(f"{GREEN}✓ Connected successfully in {mode} Mode!{RESET}")
        print(f"  {BOLD}Server:{RESET}      {target.get('tag')}")
        if mode == "TUN":
            print(f"  {BOLD}Virtual TUN:{RESET} happ-cli-tun (All System Traffic & DNS Routed)")
            print(f"  {BOLD}Local Core:{RESET}  127.0.0.1:10808 (Xray)")
        else:
            print(f"  {BOLD}Local Proxy:{RESET} 127.0.0.1:10808 (SOCKS5), 10809 (HTTP/HTTPS)")
            print(f"  {BOLD}Sys Proxy:{RESET}   Enabled (WinINet)")

        info = get_egress_ip()
        if info and info.get("status") == "success":
            print(f"  {BOLD}Public IP:{RESET}   {CYAN}{info.get('query')}{RESET} ({info.get('country')})")
        print(f"\n{DIM}Note: The VPN is running as a detached background daemon. Closing terminal will NOT disconnect.{RESET}")

def cmd_ping_all():
    data = load_data()
    nodes = data.get("nodes", [])
    if not nodes:
        print(f"{RED}No nodes available.{RESET}")
        return

    print(f"\n{BOLD}Pinging all {len(nodes)} servers via TCP...{RESET}")
    print(f"{GRAY}{'-'*60}{RESET}")
    alive = 0
    for n in nodes[:25]:
        host = n.get("host")
        port = n.get("port")
        ms = tcp_ping(host, port)
        n["ping"] = ms
        if ms > 0:
            alive += 1
            color = GREEN if ms < 100 else (YELLOW if ms < 250 else RED)
            print(f"  #{n.get('id'):<3} {n.get('tag')[:30]:<30} {color}{ms} ms{RESET}")
        else:
            print(f"  #{n.get('id'):<3} {n.get('tag')[:30]:<30} {RED}Timeout{RESET}")

    save_data(data)
    print(f"{GRAY}{'-'*60}{RESET}")
    print(f"Done. {alive} servers responsive.\n")

# --- Interactive Terminal App (TUI) ---

def run_interactive_app():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        d = get_daemon_state()
        data = load_data()
        nodes = data.get("nodes", [])
        sel_id = data.get("selected_node_id")
        mode = data.get("mode", "tun").upper()

        active_tag = "None"
        for n in nodes:
            if n.get("id") == sel_id:
                active_tag = f"#{n.get('id')} {n.get('tag')}"
                break

        print(f"{BOLD}{CYAN}┌──────────────────────────────────────────────────────────────┐{RESET}")
        print(f"{BOLD}{CYAN}│                  HAPP VPN TERMINAL DASHBOARD                 │{RESET}")
        print(f"{BOLD}{CYAN}├──────────────────────────────────────────────────────────────┤{RESET}")

        if d:
            active_m = (d.get("mode") or mode).upper()
            print(f"│  {BOLD}Status:{RESET}       {GREEN}● CONNECTED (Background Daemon Running){RESET}      │")
            sub_title = "(Virtual Adapter: happ-cli-tun)" if active_m == "TUN" else "(WinINet System Proxy)"
            print(f"│  {BOLD}Connection:{RESET}   {CYAN}{active_m} Mode{RESET} {sub_title:<39}│")
            print(f"│  {BOLD}Active Server:{RESET}{WHITE}{active_tag[:43]:<43}{RESET}│")
            pids = f"Xray: {d.get('xray_pid') or d.get('pid')}"
            if d.get("tun_pid"):
                pids += f" | TUN: {d.get('tun_pid')}"
            print(f"│  {BOLD}Daemon PIDs:{RESET}  {GRAY}{pids:<43}{RESET}│")
        else:
            print(f"│  {BOLD}Status:{RESET}       {RED}○ DISCONNECTED (Traffic Direct){RESET}              │")
            sub_title = "(Virtual Adapter - All Apps)" if mode == "TUN" else "(WinINet - Browsers Only)"
            print(f"│  {BOLD}Default Mode:{RESET} {CYAN}{mode} Mode{RESET} {sub_title:<37}│")
            print(f"│  {BOLD}Selected:{RESET}     {active_tag[:43]:<43}│")

        proxy_on, _ = get_sys_proxy()
        p_mode = f"{GREEN}Enabled{RESET}" if proxy_on else f"{GRAY}Disabled (Direct){RESET}"
        print(f"│  {BOLD}System Proxy:{RESET} {p_mode:<52}│")
        admin_str = f"{GREEN}Yes (Elevated){RESET}" if is_admin() else f"{YELLOW}No (Standard User){RESET}"
        print(f"│  {BOLD}Admin Privs:{RESET}  {admin_str:<51}│")
        print(f"│  {BOLD}Total Nodes:{RESET}  {len(nodes):<43}│")
        print(f"{BOLD}{CYAN}├──────────────────────────────────────────────────────────────┤{RESET}")
        print(f"│  {GREEN}[1]{RESET} ⚡ Connect (Start Background VPN)                         │")
        print(f"│  {RED}[2]{RESET} 🛑 Disconnect (Stop VPN & Revert Direct)                 │")
        print(f"│  {CYAN}[3]{RESET} 🌐 Select Server (Browse {len(nodes)} servers)                     │")
        print(f"│  {YELLOW}[4]{RESET} 🔄 Update Subscription (Refresh Servers)                 │")
        print(f"│  {BLUE}[5]{RESET} ➕ Add New Subscription Link                             │")
        print(f"│  {MAGENTA}[6]{RESET} 📶 Ping Servers (Latency Test)                           │")
        print(f"│  {CYAN}[7]{RESET} 🔀 Switch Mode (Current: {BOLD}{mode}{RESET})                        │")
        print(f"│  {WHITE}[8]{RESET} 📋 View Detailed Status & Public IP                      │")
        print(f"│  {GRAY}[0]{RESET} 🚪 Exit Terminal App {DIM}(VPN stays connected!){RESET}             │")
        print(f"{BOLD}{CYAN}└──────────────────────────────────────────────────────────────┘{RESET}")

        choice = input(f"{BOLD}Choose option [0-8]: {RESET}").strip()

        if choice == "1":
            print()
            cmd_connect()
            input(f"\n{GRAY}Press Enter to return to menu...{RESET}")
        elif choice == "2":
            print()
            stop_vpn()
            input(f"\n{GRAY}Press Enter to return to menu...{RESET}")
        elif choice == "3":
            page = 1
            while True:
                cmd_list(page=page, page_size=15)
                sub_ch = input(f"{BOLD}Enter Server ID to select, 'n' (next page), 'p' (prev), or 'b' (back): {RESET}").strip()
                if sub_ch.isdigit():
                    cmd_select(sub_ch)
                    time.sleep(1)
                    break
                elif sub_ch.lower() == "n":
                    page += 1
                elif sub_ch.lower() == "p":
                    page = max(1, page - 1)
                elif sub_ch.lower() == "b" or sub_ch == "":
                    break
        elif choice == "4":
            print()
            cmd_sub_update()
            input(f"\n{GRAY}Press Enter to return to menu...{RESET}")
        elif choice == "5":
            print()
            new_url = input(f"{BOLD}Paste Subscription URL: {RESET}").strip()
            if new_url:
                new_name = input(f"{BOLD}Enter subscription name [primary]: {RESET}").strip() or "primary"
                cmd_sub_add(new_url, new_name)
            input(f"\n{GRAY}Press Enter to return to menu...{RESET}")
        elif choice == "6":
            cmd_ping_all()
            input(f"\n{GRAY}Press Enter to return to menu...{RESET}")
        elif choice == "7":
            print()
            new_m = "proxy" if mode.lower() == "tun" else "tun"
            cmd_mode(new_m)
            input(f"\n{GRAY}Press Enter to return to menu...{RESET}")
        elif choice == "8":
            cmd_status()
            input(f"\n{GRAY}Press Enter to return to menu...{RESET}")
        elif choice in ["0", "q", "exit"]:
            print(f"\n{GREEN}Exiting Happ Terminal App.{RESET}")
            if d:
                print(f"{CYAN}✓ The VPN connection remains running in background.{RESET}")
                print(f"Run {BOLD}'happ disconnect'{RESET} anytime to turn off.")
            break

# --- Main Entry Point ---

def main():
    args = sys.argv[1:]

    # If no arguments provided, launch the Interactive Terminal Dashboard!
    if not args:
        run_interactive_app()
        return

    cmd = args[0].lower()

    if cmd in ["app", "ui", "menu"]:
        run_interactive_app()
    elif cmd in ["status", "-s", "--status"]:
        cmd_status()
    elif cmd in ["mode", "--mode"]:
        m = args[1] if len(args) > 1 else None
        cmd_mode(m)
    elif cmd in ["connect", "on", "up", "start"]:
        target = None
        for a in args[1:]:
            if a in ["--tun", "-tun"]:
                cmd_mode("tun")
            elif a in ["--proxy", "-proxy"]:
                cmd_mode("proxy")
            elif not a.startswith("-"):
                target = a
        cmd_connect(target)
    elif cmd in ["disconnect", "off", "down", "stop"]:
        stop_vpn()
    elif cmd in ["list", "ls"]:
        page = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
        cmd_list(page=page)
    elif cmd in ["select", "use", "switch"]:
        if len(args) > 1:
            cmd_select(args[1])
        else:
            print(f"{YELLOW}Usage: happ select <node_id | name>{RESET}")
    elif cmd in ["sub", "subscription"]:
        if len(args) > 1:
            sub_action = args[1].lower()
            if sub_action == "add":
                url_val = ""
                name_val = "primary"
                remaining = args[2:]
                i = 0
                while i < len(remaining):
                    token = remaining[i]
                    if token in ["--url", "-u"] and i + 1 < len(remaining):
                        url_val = remaining[i+1]
                        i += 2
                    elif token in ["--name", "-n"] and i + 1 < len(remaining):
                        name_val = remaining[i+1]
                        i += 2
                    elif not token.startswith("-") and not url_val:
                        if token.startswith("http"):
                            url_val = token
                        else:
                            name_val = token
                        i += 1
                    elif not token.startswith("-") and url_val and not name_val:
                        name_val = token
                        i += 1
                    else:
                        i += 1
                if url_val:
                    cmd_sub_add(url_val, name_val)
                else:
                    print(f"{YELLOW}Usage: happ sub add <url> [name] or happ sub add --url <url> --name <name>{RESET}")
            elif sub_action in ["update", "refresh"]:
                cmd_sub_update()
            elif sub_action in ["list", "ls"]:
                data = load_data()
                print(f"\n{BOLD}Configured Subscriptions:{RESET}")
                for s in data.get("subscriptions", []):
                    print(f"  - {CYAN}{s.get('name')}{RESET}: {s.get('nodes_count')} nodes (Updated: {s.get('updated_at')})")
                print()
            else:
                print(f"{RED}Unknown sub command: {sub_action}. Available: add, update, list{RESET}")
        else:
            print(f"{YELLOW}Usage: happ sub [add|update|list]{RESET}")
    elif cmd in ["ping"]:
        if len(args) > 1 and args[1] == "all":
            cmd_ping_all()
        else:
            host = args[1] if len(args) > 1 else "8.8.8.8"
            port = int(args[2]) if len(args) > 2 else 53
            ms = tcp_ping(host, port)
            if ms > 0:
                print(f"TCP Ping to {host}:{port} -> {GREEN}{ms} ms{RESET}")
            else:
                print(f"TCP Ping to {host}:{port} -> {RED}Timeout{RESET}")
    elif cmd in ["help", "-h", "--help"]:
        print(f"""
{BOLD}Happ Windows Command-Line Interface & Terminal App{RESET} (happ-cli)

{CYAN}Interactive App:{RESET}
  happ                    Open interactive Terminal Dashboard (Menu & Node Browser)

{CYAN}One-Line CLI Commands:{RESET}
  happ connect [id/name]  Start VPN background daemon and connect to server
  happ connect --tun      Connect explicitly using TUN Mode (Virtual Adapter)
  happ connect --proxy    Connect explicitly using System Proxy Mode
  happ disconnect         Stop VPN daemon and restore direct connection
  happ mode [tun|proxy]   View or set default connection mode (TUN or Proxy)
  happ status             Show active connection status, IP, and location
  happ list [page]        List servers with IDs, country flags, and ports
  happ select <id/name>   Switch active server
  happ sub add <url>      Add a new subscription link
  happ sub update         Update servers from active subscription
  happ sub list           List saved subscriptions
  happ ping [host] [port] Test latency to host
  happ ping all           Ping all saved servers
""")
    else:
        print(f"{RED}Unknown command: {cmd}. Type 'happ help' for usage.{RESET}")

if __name__ == "__main__":
    main()
