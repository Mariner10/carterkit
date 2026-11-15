#!/usr/bin/env bash
# Vet, test and build the direct sidecar. Uses `go` on PATH, else fetches the latest stable Go.
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v go >/dev/null 2>&1; then
  root="$HOME/.cache/carterkit-go"
  if [ ! -x "$root/go/bin/go" ]; then
    os=$(uname -s | tr A-Z a-z); arch=$(uname -m)
    case "$arch" in x86_64) arch=amd64;; aarch64|arm64) arch=arm64;; esac
    ver=$(curl -fsSL 'https://go.dev/VERSION?m=text' | head -1)
    mkdir -p "$root"
    curl -fsSL "https://go.dev/dl/${ver}.${os}-${arch}.tar.gz" | tar -xz -C "$root"
  fi
  export PATH="$root/go/bin:$PATH"
fi
go vet ./...
go test ./...
mkdir -p build
go build -o build/carter-direct ./cmd/carter-direct
