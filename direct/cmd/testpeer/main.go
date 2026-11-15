// testpeer is a Pion offerer for tests: it writes its complete offer, waits for
// the answer, opens `rpc`, sends one request and prints the reply header and body length.
package main

import (
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/pion/webrtc/v4"
)

func main() {
	sdpOut := flag.String("sdp-out", "", "file to write the offer SDP to (default stdout)")
	answerIn := flag.String("answer-in", "", "file to read the answer SDP from (waits for it)")
	typ := flag.String("type", "echo", "request msg_type")
	timeout := flag.Duration("timeout", 20*time.Second, "overall timeout")
	flag.Parse()

	pc, err := webrtc.NewPeerConnection(webrtc.Configuration{})
	must(err)
	dc, err := pc.CreateDataChannel("rpc", nil)
	must(err)
	done := make(chan struct{})
	dc.OnOpen(func() {
		h, _ := json.Marshal(map[string]any{"id": "t1", "type": *typ, "payload": map[string]any{}})
		msg := binary.BigEndian.AppendUint32(nil, uint32(len(h)))
		must(dc.Send(append(msg, h...)))
	})
	dc.OnMessage(func(m webrtc.DataChannelMessage) {
		n := binary.BigEndian.Uint32(m.Data)
		fmt.Printf("%s\nbody=%d\n", m.Data[4:4+n], len(m.Data)-4-int(n))
		close(done)
	})
	off, err := pc.CreateOffer(nil)
	must(err)
	g := webrtc.GatheringCompletePromise(pc)
	must(pc.SetLocalDescription(off))
	<-g
	sdp := pc.LocalDescription().SDP
	if *sdpOut == "" {
		fmt.Println(sdp)
	} else {
		must(os.WriteFile(*sdpOut, []byte(sdp), 0o600))
	}
	deadline := time.Now().Add(*timeout)
	for *answerIn != "" {
		if b, err := os.ReadFile(*answerIn); err == nil && len(b) > 0 {
			must(pc.SetRemoteDescription(webrtc.SessionDescription{Type: webrtc.SDPTypeAnswer, SDP: string(b)}))
			break
		}
		if time.Now().After(deadline) {
			fail("timed out waiting for answer")
		}
		time.Sleep(100 * time.Millisecond)
	}
	select {
	case <-done:
	case <-time.After(time.Until(deadline)):
		fail("timed out waiting for reply")
	}
	pc.Close()
}

func must(err error) {
	if err != nil {
		fail(err.Error())
	}
}

func fail(s string) {
	fmt.Fprintln(os.Stderr, "testpeer:", s)
	os.Exit(1)
}
