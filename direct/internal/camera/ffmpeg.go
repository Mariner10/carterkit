package camera

import (
	"context"
	"errors"
	"fmt"
	"net"
	"os/exec"
	"strings"
	"time"

	"github.com/pion/rtp"
)

var encoderOrder = []string{"h264_v4l2m2m", "h264_videotoolbox", "h264_vaapi", "libx264"}

func findFFmpeg() string {
	p, err := exec.LookPath("ffmpeg")
	if err != nil {
		return ""
	}
	return p
}

// probeEncoder picks the first listed H.264 encoder that also encodes one frame.
func probeEncoder(ffmpeg string) (string, error) {
	out, err := exec.Command(ffmpeg, "-hide_banner", "-encoders").Output()
	if err != nil {
		return "", err
	}
	listed := string(out)
	for _, enc := range encoderOrder {
		if !strings.Contains(listed, " "+enc+" ") && !strings.Contains(listed, " "+enc+"\n") {
			continue
		}
		args := append([]string{"-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x240:r=1", "-frames:v", "1"},
			encArgs(enc, "baseline")...)
		args = append(args, "-f", "null", "-")
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		err := exec.CommandContext(ctx, ffmpeg, args...).Run()
		cancel()
		if err == nil {
			return enc, nil
		}
	}
	return "", errors.New("no usable H.264 encoder")
}

const fps = 15

func encArgs(enc, profile string) []string {
	a := []string{}
	if enc == "h264_vaapi" {
		a = append(a, "-vaapi_device", "/dev/dri/renderD128", "-vf", "format=nv12,hwupload")
	} else {
		a = append(a, "-pix_fmt", "yuv420p")
	}
	a = append(a, "-c:v", enc, "-g", fmt.Sprint(fps), "-bf", "0", "-profile:v", profileArg(enc, profile))
	if enc == "libx264" {
		a = append(a, "-preset", "veryfast", "-tune", "zerolatency", "-maxrate", "2M", "-bufsize", "4M")
	} else {
		a = append(a, "-b:v", "2M") // the hardware wrappers otherwise default to 200 kbit/s
	}
	return a
}

// profileArg is the -profile:v value enc accepts: libx264 takes names, the hardware
// wrappers take the AV_PROFILE_H264_* number (h264_v4l2m2m refuses "main" by name).
// "baseline" means constrained baseline, the track's profile-level-id 42e01f.
func profileArg(enc, profile string) string {
	if enc == "libx264" {
		return profile
	}
	if profile == "main" {
		return "77"
	}
	return "578"
}

func inputArgs(url string) []string {
	switch {
	case strings.HasPrefix(url, "file://"):
		return []string{"-re", "-stream_loop", "-1", "-i", strings.TrimPrefix(url, "file://")}
	case strings.HasPrefix(url, "/dev/video"):
		return []string{"-f", "v4l2", "-i", url}
	}
	return []string{"-i", url}
}

func (r *Registry) encoder(ffmpeg string) (string, error) {
	r.mu.Lock()
	enc, ok := r.enc[ffmpeg]
	r.mu.Unlock()
	if ok {
		return enc, nil
	}
	enc, err := probeEncoder(ffmpeg)
	if err != nil {
		return "", err
	}
	r.mu.Lock()
	r.enc[ffmpeg] = enc
	r.mu.Unlock()
	return enc, nil
}

// runFFmpeg encodes url to H.264 RTP on a loopback UDP port and feeds write.
func (r *Registry) runFFmpeg(run *running, url string, write func([]byte)) error {
	ffmpeg := findFFmpeg()
	if ffmpeg == "" {
		return ErrNeedsFFmpeg
	}
	enc, err := r.encoder(ffmpeg)
	if err != nil {
		return err
	}
	conn, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		return err
	}
	defer conn.Close()
	port := conn.LocalAddr().(*net.UDPAddr).Port

	go func() {
		buf := make([]byte, 2048)
		for {
			n, _, err := conn.ReadFrom(buf)
			if err != nil {
				return
			}
			var p rtp.Packet
			if p.Unmarshal(buf[:n]) == nil {
				write(append([]byte(nil), buf[:n]...))
			}
		}
	}()

	for _, profile := range []string{"baseline", "main"} {
		args := append([]string{"-hide_banner", "-loglevel", "error"}, inputArgs(url)...)
		args = append(args, "-an", "-r", fmt.Sprint(fps))
		args = append(args, encArgs(enc, profile)...)
		args = append(args, "-f", "rtp", "-payload_type", "96", fmt.Sprintf("rtp://127.0.0.1:%d?pkt_size=1200", port))
		name := ffmpeg
		if nice, e := exec.LookPath("nice"); e == nil {
			args = append([]string{"-n", "10", ffmpeg}, args...)
			name = nice
		}
		cmd := exec.CommandContext(run.ctx, name, args...)
		started := time.Now()
		if err := cmd.Start(); err != nil {
			return err
		}
		run.pid.Store(int64(cmd.Process.Pid))
		err := cmd.Wait()
		run.pid.Store(0)
		if run.ctx.Err() != nil {
			return nil
		}
		// An early exit may mean the profile was refused: retry once with main.
		if profile == "baseline" && time.Since(started) < 3*time.Second {
			continue
		}
		if err == nil {
			err = errors.New("ffmpeg ended")
		}
		return err
	}
	return errors.New("ffmpeg failed")
}
