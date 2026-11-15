package camera

import (
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/Mariner10/carterkit/direct/internal/peer"
	"github.com/pion/rtp"
	"github.com/pion/webrtc/v4"
)

func fakeFFmpeg(t *testing.T) {
	t.Helper()
	dir := t.TempDir()
	script := "#!/bin/sh\ncase \"$*\" in *-encoders*) printf ' V....D libx264 x\\n V....D h264_v4l2m2m y\\n';; esac\nexit 0\n"
	if err := os.WriteFile(filepath.Join(dir, "ffmpeg"), []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", dir)
}

func TestProbeOrder(t *testing.T) {
	fakeFFmpeg(t)
	enc, err := probeEncoder(findFFmpeg())
	if err != nil || enc != "h264_v4l2m2m" {
		t.Fatalf("got %q, %v", enc, err)
	}
}

func TestNoFFmpegStatus(t *testing.T) {
	t.Setenv("PATH", "")
	r := NewRegistry()
	r.Add("cam", "http://127.0.0.1/stream", "Cam")
	if st := r.Status("cam"); st != StatusNeedsFFmpeg {
		t.Fatalf("status %q", st)
	}
	if _, _, err := r.Track("cam"); err == nil {
		t.Fatal("Track should fail without ffmpeg")
	}
}

func TestUnknownCameraAnswerError(t *testing.T) {
	m := peer.New(peer.Config{})
	defer m.CloseAll()
	m.SetCameras(NewRegistry())
	pc, _ := webrtc.NewPeerConnection(webrtc.Configuration{})
	defer pc.Close()
	if _, err := pc.AddTransceiverFromKind(webrtc.RTPCodecTypeVideo, webrtc.RTPTransceiverInit{Direction: webrtc.RTPTransceiverDirectionRecvonly}); err != nil {
		t.Fatal(err)
	}
	off, _ := pc.CreateOffer(nil)
	g := webrtc.GatheringCompletePromise(pc)
	_ = pc.SetLocalDescription(off)
	<-g
	_, err := m.Answer(context.Background(), "s", "p", pc.LocalDescription().SDP, peer.Want{Video: []string{"nope"}})
	if !errors.Is(err, peer.ErrUnknownCamera) || peer.ErrorCode(err) != "unknown_camera" {
		t.Fatalf("err %v", err)
	}
}

// viewer is a recvonly-video Pion offerer counting RTP packets.
type viewer struct {
	pc   *webrtc.PeerConnection
	pkts atomic.Int64
}

func newViewer(t *testing.T, m *peer.Manager, sid, cam string) *viewer {
	t.Helper()
	pc, err := webrtc.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { pc.Close() })
	v := &viewer{pc: pc}
	if _, err := pc.AddTransceiverFromKind(webrtc.RTPCodecTypeVideo, webrtc.RTPTransceiverInit{Direction: webrtc.RTPTransceiverDirectionRecvonly}); err != nil {
		t.Fatal(err)
	}
	pc.OnTrack(func(tr *webrtc.TrackRemote, _ *webrtc.RTPReceiver) {
		for {
			if _, _, err := tr.ReadRTP(); err != nil {
				return
			}
			v.pkts.Add(1)
		}
	})
	off, _ := pc.CreateOffer(nil)
	g := webrtc.GatheringCompletePromise(pc)
	_ = pc.SetLocalDescription(off)
	<-g
	ans, err := m.Answer(context.Background(), sid, "p", pc.LocalDescription().SDP, peer.Want{Video: []string{cam}})
	if err != nil {
		t.Fatal(err)
	}
	if err := pc.SetRemoteDescription(webrtc.SessionDescription{Type: webrtc.SDPTypeAnswer, SDP: ans}); err != nil {
		t.Fatal(err)
	}
	return v
}

func waitCount(t *testing.T, v *viewer, delta int64) {
	t.Helper()
	start := v.pkts.Load()
	deadline := time.Now().Add(15 * time.Second)
	for v.pkts.Load()-start < delta {
		if time.Now().After(deadline) {
			t.Fatalf("viewer got only %d packets", v.pkts.Load()-start)
		}
		time.Sleep(50 * time.Millisecond)
	}
}

func testClip(t *testing.T) string {
	t.Helper()
	if _, err := exec.LookPath("ffmpeg"); err != nil {
		t.Skip("no ffmpeg")
	}
	clip := filepath.Join(t.TempDir(), "clip.mp4")
	out, err := exec.Command("ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=s=320x240:r=15",
		"-t", "3", "-pix_fmt", "yuv420p", "-c:v", "libx264", clip).CombinedOutput()
	if err != nil {
		t.Skipf("cannot make clip: %v %s", err, out)
	}
	return "file://" + clip
}

func TestFanoutTwoViewers(t *testing.T) {
	url := testClip(t)
	r := NewRegistry()
	r.Add("c", url, "C")
	m := peer.New(peer.Config{})
	defer m.CloseAll()
	m.SetCameras(r)
	a := newViewer(t, m, "a", "c")
	b := newViewer(t, m, "b", "c")
	waitCount(t, a, 10)
	waitCount(t, b, 10)
	m.Close("a")
	waitCount(t, b, 10)
	if r.pid("c") == 0 {
		t.Fatal("encoder should still run")
	}
}

func TestEncoderStopsAfterLastViewer(t *testing.T) {
	url := testClip(t)
	r := NewRegistry()
	r.Add("c", url, "C")
	_, release, err := r.Track("c")
	if err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(10 * time.Second)
	for r.pid("c") == 0 && time.Now().Before(deadline) {
		time.Sleep(50 * time.Millisecond)
	}
	pid := r.pid("c")
	if pid == 0 {
		t.Fatal("ffmpeg did not start")
	}
	release()
	deadline = time.Now().Add(StopDelay + 2*time.Second)
	for time.Now().Before(deadline) {
		if syscall.Kill(pid, 0) != nil && r.Status("c") == StatusIdle {
			return
		}
		time.Sleep(100 * time.Millisecond)
	}
	t.Fatalf("ffmpeg %d still alive or status %q", pid, r.Status("c"))
}

type fakeCams struct{ tr *webrtc.TrackLocalStaticRTP }

func (f fakeCams) Track(string) (*webrtc.TrackLocalStaticRTP, func(), error) {
	return f.tr, func() {}, nil
}

// TestVideoTrackBindsToRecvonlyOffer needs no ffmpeg: it feeds synthetic RTP.
func TestVideoTrackBindsToRecvonlyOffer(t *testing.T) {
	tr, _ := webrtc.NewTrackLocalStaticRTP(h264Cap, "v", "s")
	m := peer.New(peer.Config{})
	defer m.CloseAll()
	m.SetCameras(fakeCams{tr})
	v := newViewer(t, m, "x", "c")
	stop := make(chan struct{})
	defer close(stop)
	go func() {
		for seq := uint16(0); ; seq++ {
			select {
			case <-stop:
				return
			case <-time.After(10 * time.Millisecond):
			}
			p := &rtp.Packet{Header: rtp.Header{Version: 2, SequenceNumber: seq, Timestamp: uint32(seq) * 6000, Marker: true},
				Payload: []byte{0x65, 1, 2, 3}}
			_ = tr.WriteRTP(p)
		}
	}()
	waitCount(t, v, 10)
}

// TestStopAllKillsEncoder needs no real ffmpeg: the fake one lists encoders, then
// sleeps in place of encoding. The sidecar calls StopAll before it exits.
func TestStopAllKillsEncoder(t *testing.T) {
	dir := t.TempDir()
	script := "#!/bin/sh\ncase \"$*\" in *-encoders*) printf ' V....D libx264 x\\n';; *rtp://*) exec /bin/sleep 60;; esac\nexit 0\n"
	if err := os.WriteFile(filepath.Join(dir, "ffmpeg"), []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", dir)
	r := NewRegistry()
	r.Add("c", "http://127.0.0.1:1/stream", "C")
	if _, _, err := r.Track("c"); err != nil {
		t.Fatal(err)
	}
	deadline := time.Now().Add(10 * time.Second)
	for r.pid("c") == 0 && time.Now().Before(deadline) {
		time.Sleep(20 * time.Millisecond)
	}
	pid := r.pid("c")
	if pid == 0 {
		t.Fatal("encoder did not start")
	}
	r.StopAll()
	deadline = time.Now().Add(3 * time.Second)
	for syscall.Kill(pid, 0) == nil {
		if time.Now().After(deadline) {
			t.Fatalf("encoder %d still running after StopAll", pid)
		}
		time.Sleep(20 * time.Millisecond)
	}
	if r.pid("c") != 0 {
		t.Fatal("registry still lists a source")
	}
}
