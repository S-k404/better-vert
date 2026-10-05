#!/usr/bin/env bash
# Kept so existing commands and docs keep working. The accelerator is no longer
# macOS-only; see gpu-accelerator.sh (picks VideoToolbox on a Mac, NVENC/QSV/
# VAAPI/AMF elsewhere, software otherwise).
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gpu-accelerator.sh" "$@"
