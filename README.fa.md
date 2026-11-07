# کلاینت ترمینال ویندوز و لینوکس هپ (Happ CLI & Happ Windows CLI) ⚡

<div align="center">

[![Release](https://img.shields.io/github/v/release/Abeh995/happ-cli?style=for-the-badge&color=blue)](https://github.com/Abeh995/happ-cli/releases)
[![License](https://img.shields.io/github/license/Abeh995/happ-cli?style=for-the-badge&color=green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=for-the-badge)](#)
[![Go Version](https://img.shields.io/badge/Go-1.24%2B-00ADD8?style=for-the-badge&logo=go)](https://golang.org)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python)](https://python.org)

**Happ CLI (happ-windows-cli)** کلاینت قدرتمند، سبک و کامندلاین (Headless) اکوسیستم **Happ** و **Xray-core** برای سیستم‌عامل‌های **ویندوز (Windows)**، **لینوکس (Linux)** و **مک (macOS)** است.  
مجهز به داشبورد تعاملی کنسول (TUI)، کارت شبکه مجازی لایه ۳ Wintun TUN (`happ-cli-tun`) در ویندوز، تغییر آنی پروکسی سیستم (WinINet)، سیستم ضد نشت و ضد مسمومیت DNS و اجرای دائمی در پس‌زمینه (Background Daemon).

[English Documentation](README.md) • [Русская документация](README.ru.md) • [گزارش باگ](https://github.com/Abeh995/happ-cli/issues) • [دانلود آخرین نسخه](https://github.com/Abeh995/happ-cli/releases)

</div>

---

## 📖 فهرست مطالب
- [چرا Happ CLI؟](#-چرا-happ-cli)
- [ویژگی‌های کلیدی](#-ویژگیهای-کلیدی)
- [نصب سریع در ۵ ثانیه (ویندوز)](#-نصب-سریع-در-۵-ثانیه-ویندوز)
- [داشبورد تعاملی ترمینال (TUI)](#-داشبورد-تعاملی-ترمینال-tui)
- [حالت‌های اتصال (TUN در برابر Proxy)](#-حالت‌های-اتصال-tun-در-برابر-proxy)
- [جدول دستورات تک‌خطی (CLI)](#-جدول-دستورات-تک‌خطی-cli)
- [معماری سیستم](#-معماری-سیستم)
- [نصب در لینوکس و مک](#-نصب-در-لینوکس-و-مک)
- [سوالات متداول (FAQ)](#-سوالات-متداول-faq)
- [مشارکت و لایسنس](#-مشارکت-و-لایسنس)

---

## 💡 چرا Happ CLI؟

بسیاری از کاربران و توسعه‌دهندگان در سرورها، سیستم‌های توسعه، WSL یا محیط‌های کاری به یک ابزار پایدار، بدون لگ و مبتنی بر ترمینال نیاز دارند تا بدون درگیر شدن با رابط گرافیکی حجیم، اتصال امن به اینترنت آزاد را مدیریت کنند.

**Happ CLI** به عنوان یک پروژه مستقل، هسته‌های پرقدرت **Xray-core** و **sing-box** را در قالب یک ابزار سبک ترکیب کرده تا:
1. مشکل **مسمومیت DNS در ایران (DNS Poisoning)** را با مکانیزم استراق بسته (Sniffing) و DNS رمزنگاری‌شده (DoH) به طور ۱۰۰٪ ریشه‌کن کند.
2. با ایجاد کارت شبکه مجازی لایه ۳ (`happ-cli-tun`)، تمام نرم‌افزارها، مرورگرها، دانلود منیجرها و ترمینال‌ها را بدون نیاز به تنظیم پروکسی از تونل عبور دهد.
3. با بستن پنجره ترمینال، اتصال قطع نشود و به عنوان یک دیمن پس‌زمینه مستقل به فعالیت خود ادامه دهد.

---

## ✨ ویژگی‌های کلیدی

- 🚀 **نصب فوق‌سریع:** نصب در ۵ ثانیه با یک خط دستور پاورشل بدون نیاز به هیچ پیش‌نیاز پیچیده.
- 🎛️ **داشبورد گرافیکی کنسول (TUI):** محیط جذاب متنی برای مشاهده وضعیت لحظه‌ای، انتخاب سرورها با صفحه‌بندی، تست پینگ و تعویض مود.
- ⚡ **حالت TUN Mode (لایه ۳):** پشتیبانی از درایور استاندارد Wintun برای مسیریابی کامل ترافیک سیستم (TCP و UDP).
- 🛡️ **سیستم ضد نشت DNS:** مجهز به ریموت DoH با سرورهای کلودفلر و گوگل (`https+local://1.1.1.1/dns-query`) به همراه ربودن کوئری‌های پورت ۵۳ (`hijack-dns`).
- 🔄 **اتصال دائمی (Background Daemon):** خروج از ترمینال، اتصال VPN را قطع نمی‌کند!
- 🌐 **پشتیبانی از پروتکل‌های ضد فیلترینگ:** VLESS Reality, VMess, Trojan, Shadowsocks.
- 📊 **بررسی وضعیت اکانت:** نمایش حجم مصرف‌شده، حجم کل و تاریخ انقضای لینک سابسکرایب.
- 📶 **تست پینگ زنده:** بررسی تاخیر سرورها به صورت گروهی یا تکی بر پایه TCPing.

---

## ⚡ نصب سریع در ۵ ثانیه (ویندوز)

کافیست در پنجره **PowerShell** (ترجیحاً Run as Administrator) دستور زیر را وارد کنید:

```powershell
powershell -c "irm https://raw.githubusercontent.com/Abeh995/happ-cli/main/windows/install.ps1 | iex"
```

این اسکریپت به صورت خودکار دستور سراسری `happ` را در سیستم شما فعال می‌کند!

---

## 🖥️ داشبورد تعاملی ترمینال (TUI)

برای باز کردن داشبورد گرافیکی کنسول، کافیست در هر کجای خط فرمان تایپ کنید:

```powershell
happ
```

پیش‌نمایش محیط ترمینال:
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

## 🔌 حالت‌های اتصال (TUN در برابر Proxy)

Happ CLI از دو نوع معماری اتصال مستقل پشتیبانی می‌کند:

| معیار | **حالت TUN Mode** (پیش‌فرض پیشنهادی) | **حالت System Proxy Mode** |
| :--- | :--- | :--- |
| **دامنه پوشش** | ۱۰۰٪ ترافیک کل سیستم (همه نرم‌افزارها، مرورگرها، تلگرام، بازی‌ها، CLI) | مرورگرها و نرم‌افزارهای سازگار با پروکسی سیستم |
| **لایه شبکه** | لایه ۳ پکت (`happ-cli-tun` مبتنی بر Wintun) | لایه ۷ اپلیکیشن (`WinINet Internet Settings`) |
| **امنیت DNS** | ربودن کامل پکت‌های ۵۳ و رفع ۱۰۰٪ مسمومیت DNS | ریموت DoH از طریق هسته Xray |
| **سطح دسترسی** | نیازمند باز کردن ترمینال به صورت ادمین (Run as Admin) | کاربر استاندارد و عادی |

```powershell
# مشاهده حالت فعلی:
happ mode

# تنظیم حالت پیش‌فرض روی TUN:
happ mode tun

# تنظیم حالت پیش‌فرض روی Proxy:
happ mode proxy
```

---

## ⌨️ جدول دستورات تک‌خطی (CLI)

برای کاربرانی که ترجیح می‌دهند بدون باز کردن منو کار کنند:

| دستور | شرح عملکرد |
| :--- | :--- |
| `happ` | باز کردن داشبورد تعاملی منومحور (TUI) |
| `happ connect` | اتصال به سرور پیش‌فرض در پس‌زمینه |
| `happ connect --tun` | اتصال صریح در حالت کارت شبکه مجازی لایه ۳ |
| `happ connect --proxy` | اتصال صریح در حالت پروکسی سیستم |
| `happ connect <ID>` | اتصال مستقیم به سرور با شماره مشخص (مثلاً `happ connect 3`) |
| `happ disconnect` | قطع اتصال و بازگرداندن اینترنت به حالت مستقیم |
| `happ status` | مشاهده وضعیت اتصال، پروسه‌ها، کارت شبکه و آی‌پی عمومی |
| `happ mode` | مشاهده یا تغییر مود اتصال (`happ mode [tun/proxy]`) |
| `happ list [صفحه]` | مشاهده لیست سرورها به صورت صفحه‌بندی‌شده |
| `happ select <ID/نام>` | انتخاب سرور فعال با شماره یا نام شهر/کشور |
| `happ sub add <URL>` | اضافه کردن لینک سابسکرایب جدید |
| `happ sub update` | به‌روزرسانی لیست سرورها از سرور ارائه‌دهنده |
| `happ sub list` | مشاهده لیست سابسکرایب‌های ذخیره‌شده |
| `happ ping all` | تست پینگ زنده تمامی سرورها با فرمت میلی‌ثانیه |
| `happ help` | نمایش راهنمای خط فرمان |

---

## 🏗️ معماری سیستم

```
+-----------------------------------------------------------------------+
|                    Terminal (PowerShell / CMD / Bash)                 |
|             دستورات: happ, happ connect, happ mode, happ list         |
+-----------------------------------+-----------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
[حالت ۱: TUN Mode (پیش‌فرض)]                 [حالت ۲: System Proxy Mode]
آداپتور مجازی لایه ۳ (wintun.sys)            تنظیمات رجیستری ویندوز (WinINet)
پوشش کامل ترافیک سیستم و DNS                 هدایت مرورگرها و نرم‌افزارهای سازگار
نیازمند دسترسی Administrator                 بدون نیاز به دسترسی ادمین
          |                                                   |
          +-------------------------+-------------------------+
                                    |
+-----------------------------------+-----------------------------------+
|               Local Core Engine (127.0.0.1:10808 / 10809)            |
|  - هسته Xray-core (VLESS Reality / VMess / Trojan)                    |
|  - استراق بسته هوشمند (Active Sniffing: TLS, HTTP, QUIC)             |
|  - ریموت DNS امن (DoH Cloudflare 1.1.1.1 / Google 8.8.8.8)           |
+-----------------------------------------------------------------------+
```

---

## 🐧 نصب در لینوکس و مک

باینری‌های مستقل هسته Go برای توزیع‌های مختلف لینوکس و سیستم‌عامل مک در صفحه [GitHub Releases](https://github.com/Abeh995/happ-cli/releases) به صورت فشرده ارائه شده‌اند:

```bash
# دانلود آخرین نسخه لینوکس:
curl -Lo happ.tar.gz https://github.com/Abeh995/happ-cli/releases/latest/download/happ-linux-amd64.tar.gz
tar -xzf happ.tar.gz
sudo mv happ /usr/local/bin/

# تست اجرا:
happ --help
```

همچنین پکیج NixOS و سرویس آماده systemd در پوشه `nix/` در دسترس است.

---

## ❓ سوالات متداول (FAQ)

### هپ CLI ویندوز (Happ Windows CLI) چیست و چه تفاوتی با نسخه Happ Desktop دارد؟
**Happ Windows CLI** نسخه خط فرمانی و بدون نیاز به محیط گرافیکی (Headless) کلاینت محبوب هپ است. در حالی که Happ Desktop از رابط گرافیکی سنگین استفاده می‌کند، Happ CLI با مصرف رم و پردازنده فوق‌العاده ناچیز، به توسعه‌دهندگان، ادمین‌های سرور و کاربران ویندوز اجازه می‌دهد ارتباط VPN مبتنی بر Xray را در محیط‌های PowerShell، ترمینال ویندوز و خط فرمان مدیریت کنند.

### چگونه می‌توان Happ CLI را در ویندوز نصب کرد؟
کافیست در پنجره **PowerShell** (به صورت Run as Administrator) دستور زیر را اجرا کنید:
```powershell
powershell -c "irm https://raw.githubusercontent.com/Abeh995/happ-cli/main/windows/install.ps1 | iex"
```
این دستور فایل‌های اجرایی را در `PATH` سیستم قرار داده و درایور کارت شبکه مجازی Wintun را برای لایه ۳ آماده می‌کند.

### حالت کارت شبکه مجازی (TUN Mode) در ویندوز چگونه کار می‌کند؟
با فعال‌سازی حالت TUN (`happ mode tun`)، یک کارت شبکه مجازی پرسرعت به نام `happ-cli-tun` مبتنی بر درایور Wintun روی ویندوز ایجاد می‌شود. تمام ترافیک TCP و UDP سیستم (مرورگرها، تلگرام، دیسکورد، ترمینال، گیت و بازی‌ها) به همراه بسته‌های DNS پورت ۵۳ به صورت خودکار از تونل رمزنگاری‌شده رد می‌شوند و هیچ نشتی یا مسمومیت DNS رخ نمی‌دهد.

### چه پروتکل‌هایی توسط هپ پشتیبانی می‌شوند؟
کلاینت هپ به صورت پیش‌فرض از پروتکل‌های **VLESS** (با Reality، WebSocket، gRPC)، **VMess**، **Trojan** و **Shadowsocks** پشتیبانی کامل دارد.

---

## 🤝 مشارکت و لایسنس

مشارکت‌ها، پیشنهادات و گزارش باگ‌ها به شدت استقبال می‌شوند! لطفاً قبل از ارسال کدها، [راهنمای مشارکت (CONTRIBUTING.md)](CONTRIBUTING.md) را مطالعه فرمایید.

این پروژه تحت مجوز **[GNU General Public License v3.0 (GPL-3.0)](LICENSE)** به صورت آزاد و متن‌باز منتشر شده است.

---

<div align="center">
توسعه داده شده با ❤️ توسط <a href="https://github.com/Abeh995">Abeh995</a>
</div>

