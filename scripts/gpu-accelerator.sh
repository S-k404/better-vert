#!/usr/bin/env bash
# Host-side hardware-accelerated video encode.
#
# Docker cannot reach the host GPU on macOS or Windows, so for large 4K/8K jobs
# this runs ffmpeg directly on the host and uses whichever hardware encoder it
# can actually drive:
#
#   macOS            VideoToolbox   (Apple Silicon and Intel Macs)
#   NVIDIA GPU       NVENC          (Linux, Windows, WSL2 with CUDA)
#   Intel GPU        QSV            (Linux, Windows)
#   AMD / Intel GPU  VAAPI          (Linux)
#   AMD GPU          AMF            (Windows)
#
# Every candidate is test-encoded before it is used, because an encoder being
# compiled into ffmpeg says nothing about a working driver. If none works it
# falls back to software x264/x265 so the job still finishes.
#
# Usage:
#   ./scripts/gpu-accelerator.sh <input> [output] [hevc|h264|prores]
#
# Environment:
#   VERT_HWACCEL       auto (default) | videotoolbox | nvenc | qsv | vaapi | amf | software
#   VERT_FFMPEG        path to the ffmpeg binary to use
#   VERT_VAAPI_DEVICE  VAAPI render node (default: first /dev/dri/renderD*)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/platform.sh
. "$SCRIPT_DIR/lib/platform.sh"

usage() {
  sed -n '2,/^set -euo/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'
}

case "${1:-}" in
  ""|-h|--help) usage; [ -n "${1:-}" ] && exit 0 || exit 1 ;;
esac

INPUT="$1"
CODEC="${3:-hevc}"
case "$CODEC" in hevc|h264|prores) ;; *) echo "Error: unknown codec '$CODEC' (use hevc, h264 or prores)" >&2; exit 1 ;; esac
[ -f "$INPUT" ] || { echo "Error: no such file: $INPUT" >&2; exit 1; }

STEM="$(basename "${INPUT%.*}")"
if [ $# -ge 2 ] && [ -n "$2" ]; then
  OUTPUT="$2"
else
  # ProRes cannot live in an mp4 container.
  if [ "$CODEC" = "prores" ]; then EXT=mov; else EXT=mp4; fi
  OUTPUT="./output/${STEM}-gpu.${EXT}"
fi

# --- locate ffmpeg ----------------------------------------------------------
find_ffmpeg() {
  local c
  if [ -n "${VERT_FFMPEG:-}" ]; then
    [ -x "$VERT_FFMPEG" ] && { echo "$VERT_FFMPEG"; return 0; }
    return 1
  fi
  command -v ffmpeg 2>/dev/null && return 0
  command -v ffmpeg.exe 2>/dev/null && return 0
  # GUI-launched shells on macOS often lack Homebrew on PATH.
  for c in /opt/homebrew/bin/ffmpeg /usr/local/bin/ffmpeg; do
    [ -x "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

FFMPEG_BIN="$(find_ffmpeg || true)"
if [ -z "$FFMPEG_BIN" ]; then
  HOST_OS="$(host_os)"
  echo "Error: ffmpeg not found on this machine." >&2
  case "$HOST_OS" in
    macos)   echo "Install it with Homebrew:  brew install ffmpeg" >&2 ;;
    windows) echo "Install it with:           winget install Gyan.FFmpeg" >&2 ;;
    *)       echo "Install it with your package manager, e.g.  sudo apt install ffmpeg  /  sudo dnf install ffmpeg" >&2 ;;
  esac
  exit 1
fi

# --- encoder selection ------------------------------------------------------
# encoder_for <backend> <codec> -> ffmpeg encoder name, empty if unsupported
encoder_for() {
  case "$1:$2" in
    videotoolbox:hevc|videotoolbox:h264|videotoolbox:prores) echo "$2_videotoolbox" ;;
    nvenc:hevc|nvenc:h264|qsv:hevc|qsv:h264|vaapi:hevc|vaapi:h264|amf:hevc|amf:h264) echo "$2_$1" ;;
    software:hevc)   echo libx265 ;;
    software:h264)   echo libx264 ;;
    software:prores) echo prores_ks ;;
    *) echo "" ;;
  esac
}

has_encoder() {
  "$FFMPEG_BIN" -hide_banner -encoders 2>/dev/null \
    | grep -Eq "^[[:space:]]*[VAS][.A-Z]{5}[[:space:]]+$1([[:space:]]|$)"
}

find_vaapi_device() {
  local d
  if [ -n "${VERT_VAAPI_DEVICE:-}" ]; then echo "$VERT_VAAPI_DEVICE"; return 0; fi
  for d in /dev/dri/renderD*; do
    [ -e "$d" ] && { echo "$d"; return 0; }
  done
  return 1
}

# build_args <backend> <codec>
# Fills IN_ARGS (placed before the real input), PROBE_IN (the same, minus any
# hardware *decode* flags, for the synthetic test input) and OUT_ARGS (placed
# after the input). All hold at least one element so they are safe to expand
# under `set -u` on bash 3.2.
IN_ARGS=(); PROBE_IN=(); OUT_ARGS=()
build_args() {
  local be="$1" codec="$2" enc dev
  enc="$(encoder_for "$be" "$codec")"
  IN_ARGS=(-hide_banner)
  PROBE_IN=(-hide_banner)
  OUT_ARGS=(-c:v "$enc")

  case "$be" in
    videotoolbox)
      IN_ARGS=(-hide_banner -hwaccel videotoolbox)
      case "$codec" in
        hevc)   OUT_ARGS=(-c:v "$enc" -b:v 6M -tag:v hvc1) ;;
        h264)   OUT_ARGS=(-c:v "$enc" -b:v 8M) ;;
        prores) OUT_ARGS=(-c:v "$enc" -profile:v 3) ;;
      esac ;;
    nvenc|qsv|amf)
      case "$codec" in
        hevc) OUT_ARGS=(-c:v "$enc" -b:v 6M -tag:v hvc1) ;;
        h264) OUT_ARGS=(-c:v "$enc" -b:v 8M -pix_fmt yuv420p) ;;
      esac ;;
    vaapi)
      dev="$(find_vaapi_device)" || return 1
      IN_ARGS=(-hide_banner -vaapi_device "$dev")
      PROBE_IN=(-hide_banner -vaapi_device "$dev")
      case "$codec" in
        hevc) OUT_ARGS=(-vf "format=nv12,hwupload" -c:v "$enc" -b:v 6M -tag:v hvc1) ;;
        h264) OUT_ARGS=(-vf "format=nv12,hwupload" -c:v "$enc" -b:v 8M) ;;
      esac ;;
    software)
      case "$codec" in
        hevc)   OUT_ARGS=(-c:v "$enc" -crf 23 -preset medium -tag:v hvc1) ;;
        h264)   OUT_ARGS=(-c:v "$enc" -crf 20 -preset medium -pix_fmt yuv420p) ;;
        prores) OUT_ARGS=(-c:v "$enc" -profile:v 3) ;;
      esac ;;
  esac
}

# works <backend> <codec>: can this machine really encode with it? One frame of
# synthetic video through the real argument set is the only reliable test.
works() {
  local be="$1" codec="$2" enc
  enc="$(encoder_for "$be" "$codec")"
  [ -n "$enc" ] || return 1
  has_encoder "$enc" || return 1
  build_args "$be" "$codec" || return 1
  "$FFMPEG_BIN" -loglevel error "${PROBE_IN[@]}" \
    -f lavfi -i "color=c=black:s=320x240:r=5:d=1" -frames:v 1 \
    "${OUT_ARGS[@]}" -f null - >/dev/null 2>&1
}

WANT="${VERT_HWACCEL:-auto}"
case "$(host_os)" in
  macos)   CANDIDATES="videotoolbox" ;;
  windows) CANDIDATES="nvenc qsv amf" ;;
  *)       CANDIDATES="nvenc qsv vaapi" ;;
esac

BACKEND=""
case "$WANT" in
  auto)
    # ProRes has a hardware encoder on macOS only; elsewhere it is software.
    for be in $CANDIDATES; do
      if works "$be" "$CODEC"; then BACKEND="$be"; break; fi
    done
    [ -n "$BACKEND" ] || BACKEND="software" ;;
  videotoolbox|nvenc|qsv|vaapi|amf)
    works "$WANT" "$CODEC" \
      || { echo "Error: VERT_HWACCEL=$WANT was requested but $(encoder_for "$WANT" "$CODEC" || true) is unavailable or failed a test encode on this machine." >&2; exit 1; }
    BACKEND="$WANT" ;;
  software) BACKEND="software" ;;
  *) echo "Error: VERT_HWACCEL must be auto, videotoolbox, nvenc, qsv, vaapi, amf or software (got '$WANT')" >&2; exit 1 ;;
esac

build_args "$BACKEND" "$CODEC"
ENCODER="$(encoder_for "$BACKEND" "$CODEC")"

if [ "$BACKEND" = "software" ] && [ "$WANT" = "software" ]; then
  LABEL="CPU (software), as requested"
elif [ "$BACKEND" = "software" ]; then
  LABEL="CPU (software) - no usable GPU encoder was found"
else
  LABEL="GPU hardware via $BACKEND"
fi

echo "========================================================"
echo "Better VERT host video encode"
echo "  Input:   $INPUT"
echo "  Output:  $OUTPUT"
echo "  Encoder: $ENCODER ($LABEL)"
echo "========================================================"

mkdir -p "$(dirname "$OUTPUT")"

"$FFMPEG_BIN" -y "${IN_ARGS[@]}" \
  -i "$INPUT" \
  "${OUT_ARGS[@]}" \
  -c:a aac -b:a 192k \
  "$OUTPUT"

echo "Conversion complete: $OUTPUT"
