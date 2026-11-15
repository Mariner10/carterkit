package camera

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"

	"github.com/bluenviron/gortsplib/v5"
	"github.com/bluenviron/gortsplib/v5/pkg/base"
	"github.com/bluenviron/gortsplib/v5/pkg/format"
	"github.com/pion/rtp"
)

// running is one live source.
type running struct {
	ctx    context.Context
	cancel context.CancelFunc
	done   chan struct{}
	pid    atomic.Int64
	cache  *gopCache
}

func newRunning() *running {
	ctx, cancel := context.WithCancel(context.Background())
	return &running{ctx: ctx, cancel: cancel, done: make(chan struct{}), cache: &gopCache{}}
}

func (r *running) stop() {
	r.cancel()
	<-r.done
}

// gopCache keeps the RTP packets since the last key frame (marshalled), so a late
// consumer of an already-running source can start on a picture.
type gopCache struct {
	mu      sync.Mutex
	pkts    [][]byte
	prevKey bool
}

// isKey reports whether an RTP payload starts an IDR picture or carries SPS/PPS.
func isKey(payload []byte) bool {
	if len(payload) < 2 {
		return false
	}
	t := payload[0] & 0x1f
	switch t {
	case 5, 7, 8:
		return true
	case 24: // STAP-A: key if it holds SPS/PPS/IDR
		return len(payload) > 3 && (payload[3]&0x1f == 7 || payload[3]&0x1f == 5)
	case 28: // FU-A start of IDR
		return payload[1]&0x80 != 0 && payload[1]&0x1f == 5
	}
	return false
}

func (g *gopCache) add(b []byte) {
	var p rtp.Packet
	if p.Unmarshal(b) != nil {
		return
	}
	g.mu.Lock()
	defer g.mu.Unlock()
	k := isKey(p.Payload)
	if k && !g.prevKey {
		g.pkts = g.pkts[:0] // a new GOP starts
	}
	g.prevKey = k
	g.pkts = append(g.pkts, append([]byte(nil), b...))
	if len(g.pkts) > 4096 {
		g.pkts = g.pkts[len(g.pkts)-4096:]
	}
}

// snapshot returns a copy of the cached packets.
func (g *gopCache) snapshot() [][]byte {
	g.mu.Lock()
	defer g.mu.Unlock()
	return append([][]byte(nil), g.pkts...)
}

// runRTSP passes an RTSP camera's H.264 RTP through untouched until ctx ends.
func runRTSP(ctx context.Context, rawURL string, write func([]byte)) error {
	u, err := base.ParseURL(rawURL)
	if err != nil {
		return err
	}
	c := gortsplib.Client{Scheme: u.Scheme, Host: u.Host}
	if err := c.Start(); err != nil {
		return err
	}
	defer c.Close()
	desc, _, err := c.Describe(u)
	if err != nil {
		return err
	}
	var forma *format.H264
	medi := desc.FindFormat(&forma)
	if medi == nil {
		return errors.New("no H.264 stream")
	}
	if _, err := c.Setup(desc.BaseURL, medi, 0, 0); err != nil {
		return err
	}
	c.OnPacketRTP(medi, forma, func(pkt *rtp.Packet) {
		if b, err := pkt.Marshal(); err == nil {
			write(b)
		}
	})
	if _, err := c.Play(nil); err != nil {
		return err
	}
	waitErr := make(chan error, 1)
	go func() { waitErr <- c.Wait() }()
	select {
	case <-ctx.Done():
		return nil
	case err := <-waitErr:
		return err
	}
}
