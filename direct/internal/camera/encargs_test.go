package camera

import (
	"strings"
	"testing"
)

func argAfter(a []string, flag string) string {
	for i := 0; i+1 < len(a); i++ {
		if a[i] == flag {
			return a[i+1]
		}
	}
	return ""
}

func TestEncArgsProfilePerEncoder(t *testing.T) {
	cases := []struct{ enc, profile, want string }{
		{"h264_v4l2m2m", "baseline", "578"}, // Pi ffmpeg 7.1 refuses "main" by name
		{"h264_v4l2m2m", "main", "77"},
		{"h264_vaapi", "baseline", "578"},
		{"h264_videotoolbox", "main", "77"},
		{"libx264", "baseline", "baseline"},
		{"libx264", "main", "main"},
	}
	for _, c := range cases {
		if got := argAfter(encArgs(c.enc, c.profile), "-profile:v"); got != c.want {
			t.Errorf("%s %s: -profile:v %q, want %q", c.enc, c.profile, got, c.want)
		}
	}
}

func TestEncArgsBitrate(t *testing.T) {
	for _, enc := range []string{"h264_v4l2m2m", "h264_videotoolbox", "h264_vaapi"} {
		if got := argAfter(encArgs(enc, "baseline"), "-b:v"); got != "2M" {
			t.Errorf("%s: -b:v %q, want 2M", enc, got)
		}
	}
	x := encArgs("libx264", "baseline")
	if argAfter(x, "-maxrate") != "2M" || argAfter(x, "-b:v") != "" {
		t.Errorf("libx264 args %s: want -maxrate 2M and no -b:v", strings.Join(x, " "))
	}
}
