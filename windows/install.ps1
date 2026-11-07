# ==============================================================================
# Happ CLI - Automated Windows Installer
# Author: Abeh995
# Repository: https://github.com/Abeh995/happ-cli
# Usage:
#   powershell -c "irm https://raw.githubusercontent.com/Abeh995/happ-cli/main/windows/install.ps1 | iex"
# ==============================================================================

$ErrorActionPreference = "Stop"

function Write-Color([string]$text, [string]$color = "Cyan") {
    Write-Host $text -ForegroundColor $color
}

function Show-Banner {
    Write-Host ""
    Write-Color "  ██╗  ██╗ █████╗ ██████╗ ██████╗       ██████╗██╗     ██╗" "Cyan"
    Write-Color "  ██║  ██║██╔══██╗██╔══██╗██╔══██╗     ██╔════╝██║     ██║" "Cyan"
    Write-Color "  ███████║███████║██████╔╝██████╔╝     ██║     ██║     ██║" "Cyan"
    Write-Color "  ██╔══██║██╔══██║██╔═══╝ ██╔═══╝      ██║     ██║     ██║" "Cyan"
    Write-Color "  ██║  ██║██║  ██║██║     ██║     ██╗  ╚██████╗███████╗██║" "Cyan"
    Write-Color "  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝   ╚═════╝╚══════╝╚═╝" "Cyan"
    Write-Color "         Headless VPN Client & Interactive TUI for Windows" "DarkGray"
    Write-Color "                 Developed by Abeh995 (v0.2.0)" "DarkCyan"
    Write-Host ""
}

Show-Banner

# 1. Target Directories
$installDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
$dataDir = "$env:LOCALAPPDATA\happ-cli"

if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
}

# 2. Check Python prerequisite
Write-Color "-> Checking prerequisites..." "Yellow"
$pythonCmd = Get-Command "python" -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command "python3" -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Color "[-] Python 3 was not found in your system PATH." "Red"
    Write-Color "    Happ CLI requires Python 3.8+ on Windows." "Yellow"
    Write-Color "    You can install it quickly using Winget:" "Cyan"
    Write-Color "    winget install Python.Python.3.12" "White"
    Write-Host ""
    $installNow = Read-Host "Would you like to install Python now using Winget? (y/N)"
    if ($installNow -eq "y" -or $installNow -eq "Y") {
        winget install --id Python.Python.3.12 -e --source winget
        Write-Color "[+] Please restart your PowerShell and run this installer again." "Green"
        exit
    } else {
        exit 1
    }
} else {
    Write-Color "    [+] Python detected: $($pythonCmd.Source)" "Green"
}

# 3. Download or Copy Happ CLI Suite
$baseUrl = "https://raw.githubusercontent.com/Abeh995/happ-cli/main/windows"
$localScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$coreDest = Join-Path $installDir "happ_core.py"
$cmdDest = Join-Path $installDir "happ.cmd"

Write-Color "-> Installing Happ CLI to $installDir..." "Yellow"

if ($localScriptDir -and (Test-Path (Join-Path $localScriptDir "happ_core.py"))) {
    Copy-Item (Join-Path $localScriptDir "happ_core.py") $coreDest -Force
    Copy-Item (Join-Path $localScriptDir "happ.cmd") $cmdDest -Force
} else {
    Invoke-WebRequest -Uri "$baseUrl/happ_core.py" -OutFile $coreDest -UseBasicParsing
    Invoke-WebRequest -Uri "$baseUrl/happ.cmd" -OutFile $cmdDest -UseBasicParsing
}

Write-Color "    [+] Installed happ.cmd" "Green"
Write-Color "    [+] Installed happ_core.py" "Green"

# 4. Check for Happ Desktop binaries & Wintun driver
$happSysDir = "C:\Program Files\FlyFrogLLC\Happ"
$wintunSrc = Join-Path $happSysDir "core\wintun.dll"
$wintunDst = Join-Path $dataDir "wintun.dll"

if (Test-Path $wintunSrc) {
    Copy-Item $wintunSrc $wintunDst -Force
    Write-Color "    [+] Synced Wintun driver from Happ installation." "Green"
}

# 5. Success Summary
Write-Host ""
Write-Color "==================================================================" "Cyan"
Write-Color "  Happ CLI installed successfully! Available globally in PATH.   " "Green"
Write-Color "==================================================================" "Cyan"
Write-Host ""
Write-Color "Quick Start:" "Yellow"
Write-Color "  happ                    # Launch interactive terminal dashboard (TUI)" "White"
Write-Color "  happ connect            # Start background VPN daemon" "White"
Write-Color "  happ disconnect         # Stop VPN daemon and restore direct traffic" "White"
Write-Color "  happ mode [tun|proxy]   # Switch between TUN and System Proxy modes" "White"
Write-Color "  happ sub add <url>      # Add proxy subscription link" "White"
Write-Color "  happ status             # Check live connection status and public IP" "White"
Write-Host ""
Write-Color "For full documentation: https://github.com/Abeh995/happ-cli" "DarkGray"
Write-Host ""
