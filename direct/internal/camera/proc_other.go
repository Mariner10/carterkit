//go:build !linux

package camera

import "os/exec"

// dieWithParent is Linux-only; elsewhere the sidecar stops encoders before it exits.
func dieWithParent(*exec.Cmd) {}
