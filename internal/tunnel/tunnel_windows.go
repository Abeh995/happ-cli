//go:build windows

package tunnel

import (
	"fmt"

	"github.com/xjasonlyu/tun2socks/v2/engine"
)

// Tunnel represents a running TUN tunnel on Windows.
type Tunnel struct {
	teardown []func()
}

// Start creates the Wintun adapter and routes traffic into the SOCKS proxy.
func Start(opts Options) (*Tunnel, error) {
	opts.withDefaults()

	if len(opts.ServerIPs) == 0 {
		return nil, fmt.Errorf("TUN mode requires the resolved server IP(s) to pin around the tunnel")
	}

	key := &engine.Key{
		Device:   fmt.Sprintf("wintun://%s", opts.TunName),
		Proxy:    fmt.Sprintf("socks5://%s", opts.SocksAddr),
		LogLevel: opts.LogLevel,
		MTU:      opts.MTU,
	}

	engine.Insert(key)
	engine.Start()

	tun := &Tunnel{
		teardown: []func(){
			func() {
				engine.Stop()
			},
		},
	}

	return tun, nil
}

// Close terminates the tunnel and tears down installed adapters.
func (t *Tunnel) Close() error {
	for i := len(t.teardown) - 1; i >= 0; i-- {
		t.teardown[i]()
	}
	return nil
}
