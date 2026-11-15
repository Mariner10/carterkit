package ipc

import (
	"bytes"
	"testing"
)

func TestFrameRoundTrip(t *testing.T) {
	for _, size := range []int{0, 1, 200 << 10} {
		body := bytes.Repeat([]byte{7}, size)
		var buf bytes.Buffer
		if err := WriteFrame(&buf, map[string]any{"op": "x", "n": size}, body); err != nil {
			t.Fatal(err)
		}
		h, b, err := ReadFrame(&buf)
		if err != nil {
			t.Fatal(err)
		}
		if h["op"] != "x" || int(h["n"].(float64)) != size || !bytes.Equal(b, body) {
			t.Fatalf("mismatch at size %d", size)
		}
	}
}
