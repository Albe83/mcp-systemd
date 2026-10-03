#!/bin/bash
#
# Run the locked checks under a Python version that is not installed on the
# host, using a throwaway container. The repository is mounted read-only and
# the virtualenv is created outside the tree, so the working copy is never
# modified.
#
# Usage:
#   Containerfiles/verify-python.sh [python-version]
#
# Environment:
#   PYTHON_VERSION    Python minor version to use (default: 3.10)
#   CONTAINER_ENGINE  container engine to invoke (default: docker)
#   TEST_CA_CERT      CA certificate trusted for PyPI access; when unset, the
#                     gewiss anchor is used if present, otherwise no CA is added
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_VERSION="${1:-${PYTHON_VERSION:-3.10}}"
CONTAINER_ENGINE="${CONTAINER_ENGINE:-docker}"
TEST_CA_CERT="${TEST_CA_CERT:-/etc/pki/ca-trust/source/anchors/gewiss.cer}"
IMAGE="ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim"

MOUNTS=(-v "$PWD:/workspace:ro")
CA_INSTALL=""
if [[ -f "$TEST_CA_CERT" ]]; then
	MOUNTS+=(-v "$TEST_CA_CERT:/tmp/uv-test-ca.crt:ro")
	CA_INSTALL="cp /tmp/uv-test-ca.crt /usr/local/share/ca-certificates/uv-test-ca.crt && update-ca-certificates >/dev/null 2>&1 &&"
fi

CHECKS="python --version && uv --version && uv sync --locked && uv run python -m unittest discover -s tests/unit && uv run python -m unittest discover -s tests/integration && uv run python evals/validate.py && uv lock --check"

"$CONTAINER_ENGINE" run --rm \
	--security-opt label=disable \
	"${MOUNTS[@]}" \
	-w /workspace \
	-e UV_NATIVE_TLS=1 \
	-e UV_PROJECT_ENVIRONMENT=/tmp/venv \
	-e UV_COMPILE_BYTECODE=0 \
	"$IMAGE" \
	bash -c "set -e; $CA_INSTALL $CHECKS"
