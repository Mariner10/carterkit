package peer

import (
	"bytes"
	"context"
	"strings"
	"testing"
	"time"

	"github.com/pion/webrtc/v4"
)

type offerer struct {
	pc  *webrtc.PeerConnection
	dc  *webrtc.DataChannel
	sdp string
	msg chan []byte
	up  chan struct{}
}

func newOfferer(t *testing.T) *offerer {
	t.Helper()
	pc, err := webrtc.NewPeerConnection(webrtc.Configuration{})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { pc.Close() })
	o := &offerer{pc: pc, msg: make(chan []byte, 64), up: make(chan struct{})}
	o.dc, _ = pc.CreateDataChannel("rpc", nil)
	o.dc.OnOpen(func() { close(o.up) })
	o.dc.OnMessage(func(m webrtc.DataChannelMessage) { o.msg <- m.Data })
	off, err := pc.CreateOffer(nil)
	if err != nil {
		t.Fatal(err)
	}
	g := webrtc.GatheringCompletePromise(pc)
	pc.SetLocalDescription(off)
	<-g
	o.sdp = pc.LocalDescription().SDP
	return o
}

func (o *offerer) accept(t *testing.T, sdp string) {
	t.Helper()
	if err := o.pc.SetRemoteDescription(webrtc.SessionDescription{Type: webrtc.SDPTypeAnswer, SDP: sdp}); err != nil {
		t.Fatal(err)
	}
	select {
	case <-o.up:
	case <-time.After(10 * time.Second):
		t.Fatal("data channel did not open")
	}
}

func (o *offerer) send(t *testing.T, h map[string]any, body []byte) {
	t.Helper()
	b, _ := encode(h, body)
	if err := o.dc.Send(b); err != nil {
		t.Fatal(err)
	}
}

func connect(t *testing.T, m *Manager, sid string) *offerer {
	o := newOfferer(t)
	ans, err := m.Answer(context.Background(), sid, "peer1", o.sdp, Want{Data: true})
	if err != nil {
		t.Fatal(err)
	}
	o.accept(t, ans)
	return o
}

func TestAnswerIsNonTrickle(t *testing.T) {
	m := New(Config{ICEServers: []string{"stun:127.0.0.1:1"}})
	defer m.CloseAll()
	o := newOfferer(t)
	start := time.Now()
	ans, err := m.Answer(context.Background(), "s1", "p", o.sdp, Want{Data: true})
	if err != nil {
		t.Fatal(err)
	}
	if d := time.Since(start); d > 1700*time.Millisecond {
		t.Fatalf("answer took %v", d)
	}
	if !strings.Contains(ans, "a=candidate") || !strings.Contains(ans, "a=end-of-candidates") {
		t.Fatalf("answer not complete:\n%s", ans)
	}
}

func TestRPCLoopback(t *testing.T) {
	m := New(Config{})
	defer m.CloseAll()
	got := make(chan map[string]any, 1)
	m.OnRPC(func(sid string, h map[string]any, body []byte) {
		got <- h
		big := bytes.Repeat([]byte{9}, 131072)
		if err := m.Reply(sid, map[string]any{"reply_to": h["id"], "type": "echo", "payload": map[string]any{}, "body": "data"}, big); err != nil {
			t.Error(err)
		}
	})
	o := connect(t, m, "s1")
	o.send(t, map[string]any{"id": "r1", "type": "echo", "payload": map[string]any{}}, nil)
	select {
	case h := <-got:
		if h["id"] != "r1" || h["type"] != "echo" {
			t.Fatalf("bad header %v", h)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("no rpc request")
	}
	select {
	case d := <-o.msg:
		h, body, err := decode(d)
		if err != nil || h["reply_to"] != "r1" || h["body"] != "data" || len(body) != 131072 {
			t.Fatalf("bad reply %v %d %v", h, len(body), err)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("no reply")
	}
}

func TestInflightCap(t *testing.T) {
	m := New(Config{})
	defer m.CloseAll()
	m.OnRPC(func(string, map[string]any, []byte) {}) // never answers
	o := connect(t, m, "s1")
	for i := 0; i < 33; i++ {
		o.send(t, map[string]any{"id": string(rune('a' + i)), "type": "x", "payload": map[string]any{}}, nil)
	}
	select {
	case d := <-o.msg:
		h, _, _ := decode(d)
		p, _ := h["payload"].(map[string]any)
		if p["error"] != "busy" || h["reply_to"] != string(rune('a'+32)) {
			t.Fatalf("unexpected %v", h)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("no busy reply")
	}
}

func TestUnknownSessionReplyIsDropped(t *testing.T) {
	m := New(Config{})
	if err := m.Reply("gone", map[string]any{"reply_to": "x"}, nil); err == nil {
		t.Fatal("expected error")
	}
	o := connect(t, m, "s1")
	_ = o
	m.Close("s1")
	if err := m.Reply("s1", map[string]any{"reply_to": "x"}, nil); err == nil {
		t.Fatal("expected error after close")
	}
}
