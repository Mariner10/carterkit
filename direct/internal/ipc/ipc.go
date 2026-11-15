// Package ipc implements the sidecar's stdio framing:
// u32 BE frame length N, u32 BE header length H, header JSON, body (N-4-H bytes).
package ipc

import (
	"encoding/binary"
	"encoding/json"
	"errors"
	"io"
)

// MaxFrame bounds a single frame (header + body).
const MaxFrame = 8 << 20

// ReadFrame reads one frame.
func ReadFrame(r io.Reader) (map[string]any, []byte, error) {
	var lb [4]byte
	if _, err := io.ReadFull(r, lb[:]); err != nil {
		return nil, nil, err
	}
	n := binary.BigEndian.Uint32(lb[:])
	if n < 4 || n > MaxFrame {
		return nil, nil, errors.New("ipc: bad frame length")
	}
	buf := make([]byte, n)
	if _, err := io.ReadFull(r, buf); err != nil {
		return nil, nil, err
	}
	h := binary.BigEndian.Uint32(buf[:4])
	if h > n-4 {
		return nil, nil, errors.New("ipc: bad header length")
	}
	hdr := map[string]any{}
	if err := json.Unmarshal(buf[4:4+h], &hdr); err != nil {
		return nil, nil, err
	}
	return hdr, buf[4+h:], nil
}

// WriteFrame writes one frame in a single Write call.
func WriteFrame(w io.Writer, header any, body []byte) error {
	hb, err := json.Marshal(header)
	if err != nil {
		return err
	}
	n := 4 + len(hb) + len(body)
	if n > MaxFrame {
		return errors.New("ipc: frame too large")
	}
	out := make([]byte, 8, 8+len(hb)+len(body))
	binary.BigEndian.PutUint32(out[0:], uint32(n))
	binary.BigEndian.PutUint32(out[4:], uint32(len(hb)))
	out = append(out, hb...)
	out = append(out, body...)
	_, err = w.Write(out)
	return err
}
