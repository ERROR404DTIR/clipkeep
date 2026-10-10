#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/dist"

mkdir -p "${OUTPUT_DIR}"

echo "[1/2] Building .deb package..."
dpkg-deb --build "${SCRIPT_DIR}/deb-build" "${OUTPUT_DIR}/clipkeep_0.1.0_amd64.deb"

echo ""
echo "[2/2] Done! Output: ${OUTPUT_DIR}/clipkeep_0.1.0_amd64.deb"
ls -lh "${OUTPUT_DIR}/clipkeep_0.1.0_amd64.deb"
