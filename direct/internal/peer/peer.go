// Package peer is the Pion WebRTC side of the direct link: it answers a phone's
// non-trickle offer and bridges the `rpc` data channel to the host.
package peer

import (
	"context"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"net/netip"
	"strings"
	"sync"
	"time"

	"github.com/pion/webrtc/v4"
)

// MaxMessage is the largest rpc data channel message accepted.
const MaxMessage = 262144

// Want says what the offerer asked for.
type Want struct {
	Video []string `json:"video"`
	Data  bool     `json:"data"`
}

// Config tunes the Manager.
type Config struct {
	ICEServers    []string      // STUN urls
	GatherTimeout time.Duration // cap on ICE gathering (default 1.5 s)
	MaxInflight   int           // per-session requests in flight (default 32)
}

type session struct {
	id       string
	peerID   string
	pc       *webrtc.PeerConnection
	mu       sync.Mutex
	dc       *webrtc.DataChannel
	inflight map[string]bool
	closed   bool
}

// Manager owns all peer sessions.
type Manager struct {
	mu       sync.Mutex
	cfg      Config
	sessions map[string]*session
	onRPC    func(session string, header map[string]any, body []byte)
	onState  func(session, state, path string)
}

// New returns a Manager with defaults applied.
func New(cfg Config) *Manager {
	if cfg.GatherTimeout <= 0 {
		cfg.GatherTimeout = 1500 * time.Millisecond
	}
	if cfg.MaxInflight <= 0 {
		cfg.MaxInflight = 32
	}
	return &Manager{cfg: cfg, sessions: map[string]*session{}}
}

// SetConfig replaces the config for future sessions.
func (m *Manager) SetConfig(cfg Config) {
	n := New(cfg)
	m.mu.Lock()
	m.cfg = n.cfg
	m.mu.Unlock()
}

// OnRPC registers the request handler.
func (m *Manager) OnRPC(f func(session string, header map[string]any, body []byte)) {
	m.mu.Lock()
	m.onRPC = f
	m.mu.Unlock()
}

// OnState registers the session state handler.
func (m *Manager) OnState(f func(session, state, path string)) {
	m.mu.Lock()
	m.onState = f
	m.mu.Unlock()
}

func (m *Manager) emit(id, state, path string) {
	m.mu.Lock()
	f := m.onState
	m.mu.Unlock()
	if f != nil {
		f(id, state, path)
	}
}

// Answer builds a peer for the offer and returns the answer SDP with ICE complete.
func (m *Manager) Answer(ctx context.Context, sid, peerID, offerSDP string, want Want) (string, error) {
	m.mu.Lock()
	cfg := m.cfg
	m.mu.Unlock()

	se := webrtc.SettingEngine{}
	se.SetSTUNGatherTimeout(cfg.GatherTimeout)
	api := webrtc.NewAPI(webrtc.WithSettingEngine(se))
	wcfg := webrtc.Configuration{}
	if len(cfg.ICEServers) > 0 {
		wcfg.ICEServers = []webrtc.ICEServer{{URLs: cfg.ICEServers}}
	}
	pc, err := api.NewPeerConnection(wcfg)
	if err != nil {
		return "", err
	}
	s := &session{id: sid, peerID: peerID, pc: pc, inflight: map[string]bool{}}

	m.mu.Lock()
	old := m.sessions[sid]
	m.sessions[sid] = s
	m.mu.Unlock()
	if old != nil {
		old.shutdown()
	}

	fail := func(err error) (string, error) {
		m.drop(s)
		return "", err
	}

	pc.OnDataChannel(func(dc *webrtc.DataChannel) {
		if dc.Label() != "rpc" {
			return
		}
		s.mu.Lock()
		s.dc = dc
		s.mu.Unlock()
		dc.OnMessage(func(msg webrtc.DataChannelMessage) { m.handle(s, msg.Data) })
	})
	pc.OnConnectionStateChange(func(st webrtc.PeerConnectionState) {
		switch st {
		case webrtc.PeerConnectionStateConnected:
			m.emit(sid, "connected", pathOf(pc))
		case webrtc.PeerConnectionStateFailed:
			m.emit(sid, "failed", "")
		case webrtc.PeerConnectionStateClosed:
			m.emit(sid, "closed", "")
		}
	})

	if err := pc.SetRemoteDescription(webrtc.SessionDescription{Type: webrtc.SDPTypeOffer, SDP: offerSDP}); err != nil {
		return fail(err)
	}
	ans, err := pc.CreateAnswer(nil)
	if err != nil {
		return fail(err)
	}
	gather := webrtc.GatheringCompletePromise(pc)
	if err := pc.SetLocalDescription(ans); err != nil {
		return fail(err)
	}
	timer := time.NewTimer(cfg.GatherTimeout)
	defer timer.Stop()
	select {
	case <-gather:
	case <-timer.C:
	case <-ctx.Done():
		return fail(ctx.Err())
	}
	ld := pc.LocalDescription()
	if ld == nil {
		return fail(errors.New("no local description"))
	}
	return endOfCandidates(ld.SDP), nil
}

// endOfCandidates makes sure every media section closes its candidate list.
func endOfCandidates(sdp string) string {
	parts := strings.Split(sdp, "\r\nm=")
	for i, p := range parts {
		if strings.Contains(p, "a=candidate") && !strings.Contains(p, "a=end-of-candidates") {
			p = strings.TrimRight(p, "\r\n") + "\r\na=end-of-candidates"
			if i == len(parts)-1 {
				p += "\r\n"
			}
			parts[i] = p
		}
	}
	return strings.Join(parts, "\r\nm=")
}

func pathOf(pc *webrtc.PeerConnection) string {
	sc := pc.SCTP()
	if sc == nil {
		return "internet"
	}
	pair, err := sc.Transport().ICETransport().GetSelectedCandidatePair()
	if err != nil || pair == nil || pair.Remote == nil {
		return "internet"
	}
	if pair.Remote.Typ == webrtc.ICECandidateTypeHost {
		if a, err := netip.ParseAddr(pair.Remote.Address); err == nil && (a.IsPrivate() || a.IsLoopback() || a.IsLinkLocalUnicast()) {
			return "lan"
		}
	}
	return "internet"
}

func (s *session) shutdown() {
	s.mu.Lock()
	s.closed = true
	s.mu.Unlock()
	_ = s.pc.Close()
}

func (m *Manager) drop(s *session) {
	m.mu.Lock()
	if m.sessions[s.id] == s {
		delete(m.sessions, s.id)
	}
	m.mu.Unlock()
	s.shutdown()
}

// Close ends a session.
func (m *Manager) Close(sid string) {
	m.mu.Lock()
	s := m.sessions[sid]
	delete(m.sessions, sid)
	m.mu.Unlock()
	if s != nil {
		s.shutdown()
	}
}

// CloseAll ends every session.
func (m *Manager) CloseAll() {
	m.mu.Lock()
	all := m.sessions
	m.sessions = map[string]*session{}
	m.mu.Unlock()
	for _, s := range all {
		s.shutdown()
	}
}

func decode(data []byte) (map[string]any, []byte, error) {
	if len(data) < 4 {
		return nil, nil, errors.New("short message")
	}
	h := binary.BigEndian.Uint32(data)
	if uint64(h) > uint64(len(data)-4) {
		return nil, nil, errors.New("bad header length")
	}
	hdr := map[string]any{}
	if err := json.Unmarshal(data[4:4+h], &hdr); err != nil {
		return nil, nil, err
	}
	return hdr, data[4+h:], nil
}

func encode(header map[string]any, body []byte) ([]byte, error) {
	hb, err := json.Marshal(header)
	if err != nil {
		return nil, err
	}
	out := make([]byte, 4, 4+len(hb)+len(body))
	binary.BigEndian.PutUint32(out, uint32(len(hb)))
	out = append(out, hb...)
	return append(out, body...), nil
}

func (m *Manager) handle(s *session, data []byte) {
	hdr, body, err := decode(data)
	if err != nil {
		return
	}
	id, _ := hdr["id"].(string)
	typ, _ := hdr["type"].(string)
	if id == "" {
		return
	}
	errReply := func(code string) {
		out, e := encode(map[string]any{"reply_to": id, "type": typ, "payload": map[string]any{"error": code}}, nil)
		if e == nil {
			s.mu.Lock()
			dc := s.dc
			s.mu.Unlock()
			if dc != nil {
				_ = dc.Send(out)
			}
		}
	}
	m.mu.Lock()
	h := m.onRPC
	max := m.cfg.MaxInflight
	m.mu.Unlock()
	s.mu.Lock()
	if s.inflight[id] || len(s.inflight) >= max {
		s.mu.Unlock()
		errReply("busy")
		return
	}
	s.inflight[id] = true
	s.mu.Unlock()
	if h == nil {
		s.mu.Lock()
		delete(s.inflight, id)
		s.mu.Unlock()
		errReply("unknown_type")
		return
	}
	// The sidecar binds the session to its peer; handlers never see a claimed identity.
	delete(hdr, "_from")
	delete(hdr, "_relayFrom")
	hdr["_peer"] = s.peerID
	go h(s.id, hdr, body)
}

// Reply sends a reply on the session's rpc channel.
func (m *Manager) Reply(sid string, header map[string]any, body []byte) error {
	m.mu.Lock()
	s := m.sessions[sid]
	m.mu.Unlock()
	if s == nil {
		return fmt.Errorf("unknown session %q", sid)
	}
	out, err := encode(header, body)
	if err != nil {
		return err
	}
	if len(out) > MaxMessage {
		return errors.New("reply too large")
	}
	s.mu.Lock()
	dc := s.dc
	if rt, ok := header["reply_to"].(string); ok {
		delete(s.inflight, rt)
	}
	closed := s.closed
	s.mu.Unlock()
	if dc == nil || closed {
		return errors.New("rpc channel not open")
	}
	return dc.Send(out)
}
