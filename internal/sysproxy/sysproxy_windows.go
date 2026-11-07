//go:build windows

package sysproxy

import (
	"fmt"
	"syscall"

	"golang.org/x/sys/windows/registry"
)

const (
	internetOptionSettingsChanged = 39
	internetOptionRefresh         = 37
)

var (
	modwininet            = syscall.NewLazyDLL("wininet.dll")
	procInternetSetOption = modwininet.NewProc("InternetSetOptionW")
)

// Restore reverts the system proxy to its previous state.
type Restore func() error

func refreshSettings() {
	_, _, _ = procInternetSetOption.Call(0, uintptr(internetOptionSettingsChanged), 0, 0)
	_, _, _ = procInternetSetOption.Call(0, uintptr(internetOptionRefresh), 0, 0)
}

// Enable points the Windows system proxy at host:socksPort (or host:httpPort if provided)
// by modifying the Current User Internet Settings in the Windows Registry.
func Enable(host string, socksPort, httpPort int) (Restore, error) {
	k, err := registry.OpenKey(registry.CURRENT_USER, `Software\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.QUERY_VALUE|registry.SET_VALUE)
	if err != nil {
		return nil, fmt.Errorf("open internet settings registry key: %w", err)
	}
	defer k.Close()

	prevEnable, _, err := k.GetIntegerValue("ProxyEnable")
	if err != nil {
		prevEnable = 0
	}
	prevServer, _, err := k.GetStringValue("ProxyServer")
	if err != nil {
		prevServer = ""
	}
	prevOverride, _, err := k.GetStringValue("ProxyOverride")
	if err != nil {
		prevOverride = ""
	}

	// Format proxy server string
	var proxyStr string
	if httpPort > 0 && socksPort > 0 {
		proxyStr = fmt.Sprintf("http=%s:%d;https=%s:%d;socks=%s:%d", host, httpPort, host, httpPort, host, socksPort)
	} else if socksPort > 0 {
		proxyStr = fmt.Sprintf("socks=%s:%d", host, socksPort)
	} else if httpPort > 0 {
		proxyStr = fmt.Sprintf("%s:%d", host, httpPort)
	} else {
		return nil, fmt.Errorf("no proxy port provided")
	}

	overrideStr := "<local>;<-loopback>"

	if err := k.SetDWordValue("ProxyEnable", 1); err != nil {
		return nil, fmt.Errorf("set ProxyEnable: %w", err)
	}
	if err := k.SetStringValue("ProxyServer", proxyStr); err != nil {
		return nil, fmt.Errorf("set ProxyServer: %w", err)
	}
	if err := k.SetStringValue("ProxyOverride", overrideStr); err != nil {
		return nil, fmt.Errorf("set ProxyOverride: %w", err)
	}

	refreshSettings()

	restore := func() error {
		rk, rerr := registry.OpenKey(registry.CURRENT_USER, `Software\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.SET_VALUE)
		if rerr != nil {
			return fmt.Errorf("reopen registry for restore: %w", rerr)
		}
		defer rk.Close()

		_ = rk.SetDWordValue("ProxyEnable", uint32(prevEnable))
		if prevServer != "" {
			_ = rk.SetStringValue("ProxyServer", prevServer)
		} else {
			_ = rk.DeleteValue("ProxyServer")
		}
		if prevOverride != "" {
			_ = rk.SetStringValue("ProxyOverride", prevOverride)
		}

		refreshSettings()
		return nil
	}

	return restore, nil
}

// DisableAll turns off the system proxy on Windows.
func DisableAll() error {
	k, err := registry.OpenKey(registry.CURRENT_USER, `Software\Microsoft\Windows\CurrentVersion\Internet Settings`, registry.SET_VALUE)
	if err != nil {
		return fmt.Errorf("open internet settings registry key: %w", err)
	}
	defer k.Close()

	if err := k.SetDWordValue("ProxyEnable", 0); err != nil {
		return fmt.Errorf("set ProxyEnable to 0: %w", err)
	}

	refreshSettings()
	return nil
}

