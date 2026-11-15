// Package camera ingests camera sources once and fans the H.264 RTP out to many viewers.
package camera

import (
	"errors"
	"strings"
	"sync"
	"time"

	"github.com/Mariner10/carterkit/direct/internal/peer"
	"github.com/pion/webrtc/v4"
)

// StopDelay is how long a source keeps running after its last viewer leaves.
var StopDelay = 10 * time.Second

// Errors returned by Track.
var (
	ErrUnknown     = peer.ErrUnknownCamera
	ErrNeedsFFmpeg = errors.New("needs_ffmpeg")
)

// Status values.
const (
	StatusOK          = "ok"
	StatusIdle        = "idle"
	StatusStarting    = "starting"
	StatusNeedsFFmpeg = "needs_ffmpeg"
	StatusUnreachable = "unreachable"
)

var h264Cap = webrtc.RTPCodecCapability{
	MimeType:    webrtc.MimeTypeH264,
	ClockRate:   90000,
	SDPFmtpLine: "level-asymmetry-allowed=1;packetization-mode=1;profile-level-id=42e01f",
}

type cam struct {
	id, url, name string
	track         *webrtc.TrackLocalStaticRTP
	refs          int
	state         string // starting|ok|unreachable ("" = idle)
	src           *running
	stop          *time.Timer
}

// Registry owns the configured cameras and their running sources.
type Registry struct {
	mu       sync.Mutex
	cams     map[string]*cam
	onStatus func(id, status string)
	enc      map[string]string // ffmpeg path -> probed encoder
}

// NewRegistry returns an empty Registry.
func NewRegistry() *Registry {
	return &Registry{cams: map[string]*cam{}, enc: map[string]string{}}
}

// OnStatus registers the status change callback.
func (r *Registry) OnStatus(f func(id, status string)) {
	r.mu.Lock()
	r.onStatus = f
	r.mu.Unlock()
}

// Add registers (or replaces) a camera.
func (r *Registry) Add(id, url, name string) {
	r.Remove(id)
	t, _ := webrtc.NewTrackLocalStaticRTP(h264Cap, "video-"+id, "carter-"+id)
	r.mu.Lock()
	r.cams[id] = &cam{id: id, url: url, name: name, track: t}
	r.mu.Unlock()
}

// Remove forgets a camera and stops its source.
func (r *Registry) Remove(id string) {
	r.mu.Lock()
	c := r.cams[id]
	delete(r.cams, id)
	var src *running
	if c != nil {
		if c.stop != nil {
			c.stop.Stop()
		}
		src, c.src = c.src, nil
	}
	r.mu.Unlock()
	if src != nil {
		src.stop()
	}
}

// Info is one camera as advertised.
type Info struct{ ID, Name, Status string }

// List returns the cameras in no particular order.
func (r *Registry) List() []Info {
	r.mu.Lock()
	ids := make([]string, 0, len(r.cams))
	for id := range r.cams {
		ids = append(ids, id)
	}
	r.mu.Unlock()
	out := make([]Info, 0, len(ids))
	for _, id := range ids {
		r.mu.Lock()
		c := r.cams[id]
		r.mu.Unlock()
		if c != nil {
			out = append(out, Info{id, c.name, r.Status(id)})
		}
	}
	return out
}

func usesFFmpeg(url string) bool {
	return strings.HasPrefix(url, "http://") || strings.HasPrefix(url, "https://") ||
		strings.HasPrefix(url, "/dev/video") || strings.HasPrefix(url, "file://")
}

// Status reports a camera's status ("" when unknown).
func (r *Registry) Status(id string) string {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.statusLocked(r.cams[id])
}

func (r *Registry) statusLocked(c *cam) string {
	switch {
	case c == nil:
		return ""
	case usesFFmpeg(c.url) && findFFmpeg() == "":
		return StatusNeedsFFmpeg
	case c.state == "":
		return StatusIdle
	}
	return c.state
}

func (r *Registry) setState(c *cam, st string) {
	r.mu.Lock()
	if r.cams[c.id] != c || c.state == st {
		r.mu.Unlock()
		return
	}
	c.state = st
	f := r.onStatus
	s := r.statusLocked(c)
	r.mu.Unlock()
	if f != nil {
		f(c.id, s)
	}
}

// Track returns the camera's shared track, starting the source on first use.
// release must be called when the viewer is gone.
func (r *Registry) Track(id string) (*webrtc.TrackLocalStaticRTP, func(), error) {
	r.mu.Lock()
	c := r.cams[id]
	if c == nil {
		r.mu.Unlock()
		return nil, nil, ErrUnknown
	}
	if usesFFmpeg(c.url) && findFFmpeg() == "" {
		r.mu.Unlock()
		return nil, nil, ErrNeedsFFmpeg
	}
	c.refs++
	if c.stop != nil {
		c.stop.Stop()
		c.stop = nil
	}
	start := c.src == nil
	if start {
		c.state = StatusStarting
		c.src = r.launch(c)
	}
	r.mu.Unlock()
	if start {
		r.notify(c)
	}
	var once sync.Once
	release := func() { once.Do(func() { r.release(c) }) }
	return c.track, release, nil
}

func (r *Registry) notify(c *cam) {
	r.mu.Lock()
	f := r.onStatus
	s := r.statusLocked(c)
	r.mu.Unlock()
	if f != nil {
		f(c.id, s)
	}
}

func (r *Registry) release(c *cam) {
	r.mu.Lock()
	if c.refs > 0 {
		c.refs--
	}
	if c.refs > 0 || c.src == nil || r.cams[c.id] != c {
		r.mu.Unlock()
		return
	}
	src := c.src
	c.stop = time.AfterFunc(StopDelay, func() {
		r.mu.Lock()
		if c.refs > 0 || c.src != src {
			r.mu.Unlock()
			return
		}
		c.src, c.stop, c.state = nil, nil, ""
		r.mu.Unlock()
		src.stop()
		r.notify(c)
	})
	r.mu.Unlock()
}

// launch starts the source goroutine for c; r.mu must be held.
func (r *Registry) launch(c *cam) *running {
	run := newRunning()
	write := func(p []byte) {
		r.setState(c, StatusOK)
		run.cache.add(p)
		_, _ = c.track.Write(p)
	}
	go func() {
		defer close(run.done)
		var err error
		if strings.HasPrefix(c.url, "rtsp://") {
			err = runRTSP(run.ctx, c.url, write)
		} else {
			err = r.runFFmpeg(run, c.url, write)
		}
		if run.ctx.Err() != nil {
			return
		}
		_ = err
		r.mu.Lock()
		if c.src == run {
			c.src = nil
		}
		r.mu.Unlock()
		r.setState(c, StatusUnreachable)
	}()
	return run
}

// pid returns the running ffmpeg PID for tests (0 if none).
func (r *Registry) pid(id string) int {
	r.mu.Lock()
	c := r.cams[id]
	r.mu.Unlock()
	if c == nil || c.src == nil {
		return 0
	}
	return int(c.src.pid.Load())
}
