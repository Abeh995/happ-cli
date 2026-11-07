//go:build windows

package store

import (
	"os"
	"path/filepath"

	"golang.org/x/sys/windows"
)

// Reload under the lock so an update timer cannot overwrite a concurrent selection.
func (s *Store) mutate(change func() error) error {
	if err := os.MkdirAll(s.dir, 0o700); err != nil {
		return err
	}
	f, err := os.OpenFile(filepath.Join(s.dir, "state.lock"), os.O_CREATE|os.O_RDWR, 0o600)
	if err != nil {
		return err
	}
	defer f.Close()

	var overlapped windows.Overlapped
	h := windows.Handle(f.Fd())
	if err := windows.LockFileEx(h, windows.LOCKFILE_EXCLUSIVE_LOCK, 0, 1, 0, &overlapped); err != nil {
		return err
	}
	defer windows.UnlockFileEx(h, 0, 1, 0, &overlapped)

	fresh, err := Open(s.dir)
	if err != nil {
		return err
	}
	s.state = fresh.state
	if err := change(); err != nil {
		return err
	}
	return s.save()
}

