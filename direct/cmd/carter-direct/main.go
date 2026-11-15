// carter-direct is the Pion sidecar: it speaks framed IPC on stdin/stdout.
// stdout carries frames only; all logging goes out as `log` frames.
package main

import (
	"context"
	"encoding/json"
	"io"
	"os"
	"sync"
	"time"

	"github.com/Mariner10/carterkit/direct/internal/camera"
	"github.com/Mariner10/carterkit/direct/internal/ipc"
	"github.com/Mariner10/carterkit/direct/internal/peer"
)

const version = "1"

var (
	wmu sync.Mutex
	out io.Writer = os.Stdout
)

func send(h map[string]any, body []byte) {
	wmu.Lock()
	defer wmu.Unlock()
	_ = ipc.WriteFrame(out, h, body)
}

func logf(level, msg string) { send(map[string]any{"op": "log", "level": level, "msg": msg}, nil) }

func str(h map[string]any, k string) string { s, _ := h[k].(string); return s }

func main() {
	mgr := peer.New(peer.Config{})
	cams := camera.NewRegistry()
	mgr.SetCameras(cams)
	cams.OnStatus(func(id, st string) {
		send(map[string]any{"op": "camera_status", "id": id, "status": st}, nil)
	})
	mgr.OnRPC(func(s string, h map[string]any, b []byte) {
		send(map[string]any{"op": "rpc_request", "session": s, "header": h}, b)
	})
	mgr.OnState(func(s, st, path string) {
		send(map[string]any{"op": "session", "session": s, "state": st, "path": path}, nil)
	})
	send(map[string]any{"op": "ready", "version": version}, nil)

	for {
		h, body, err := ipc.ReadFrame(os.Stdin)
		if err != nil {
			mgr.CloseAll()
			return
		}
		switch str(h, "op") {
		case "config":
			var cfg peer.Config
			if arr, ok := h["ice_servers"].([]any); ok {
				for _, e := range arr {
					if m, ok := e.(map[string]any); ok {
						switch u := m["urls"].(type) {
						case string:
							cfg.ICEServers = append(cfg.ICEServers, u)
						case []any:
							for _, x := range u {
								if s, ok := x.(string); ok {
									cfg.ICEServers = append(cfg.ICEServers, s)
								}
							}
						}
					}
				}
			}
			if v, ok := h["gather_timeout_ms"].(float64); ok {
				cfg.GatherTimeout = time.Duration(v) * time.Millisecond
			}
			if v, ok := h["max_inflight"].(float64); ok {
				cfg.MaxInflight = int(v)
			}
			mgr.SetConfig(cfg)
			if arr, ok := h["cameras"].([]any); ok {
				for _, e := range arr {
					if m, ok := e.(map[string]any); ok {
						cams.Add(str(m, "id"), str(m, "url"), str(m, "name"))
					}
				}
			}
		case "offer":
			go func(h map[string]any) {
				sid := str(h, "session")
				var want peer.Want
				if raw, err := json.Marshal(h["want"]); err == nil {
					_ = json.Unmarshal(raw, &want)
				}
				ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
				defer cancel()
				sdp, err := mgr.Answer(ctx, sid, str(h, "peer"), str(h, "sdp"), want)
				if err != nil {
					logf("warn", "answer failed: "+err.Error())
					send(map[string]any{"op": "error", "session": sid, "code": peer.ErrorCode(err)}, nil)
					return
				}
				send(map[string]any{"op": "answer", "session": sid, "sdp": sdp}, nil)
			}(h)
		case "close":
			mgr.Close(str(h, "session"))
		case "rpc_reply":
			rh, _ := h["header"].(map[string]any)
			if err := mgr.Reply(str(h, "session"), rh, body); err != nil {
				logf("debug", "reply dropped: "+err.Error())
			}
		case "camera_add", "camera_remove":
			if str(h, "op") == "camera_add" {
				cams.Add(str(h, "id"), str(h, "url"), str(h, "name"))
			} else {
				cams.Remove(str(h, "id"))
			}
		}
	}
}
