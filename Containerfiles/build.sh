#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker build \
	--ignorefile Containerfiles/.dockerignore \
	--file Containerfiles/Containerfile \
	--tag localhost/mcp-systemd:latest \
	.
