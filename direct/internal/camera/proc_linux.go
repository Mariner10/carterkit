package camera

import (
	"os/exec"
	"syscall"
)

// dieWithParent has the kernel SIGKILL ffmpeg when the thread that started it ends.
func dieWithParent(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{Pdeathsig: syscall.SIGKILL}
}
