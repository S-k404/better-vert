#!/usr/bin/env bash
# Apple Silicon M5 Max VideoToolbox GPU Acceleration Bridge
# Leverages macOS native VideoToolbox hardware encoders for zero-overhead GPU video export.
#
# Usage:
#   ./scripts/mac-gpu-accelerator.sh input.mov [output.mp4] [hevc|h264|prores]

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <input_file> [output_file] [codec: hevc|h264|prores]"
  exit 1
fi

INPUT="$1"
STEM="$(basename "${INPUT%.*}")"
CODEC="${3:-hevc}"

if [ $# -ge 2 ]; then
  OUTPUT="$2"
else
  OUTPUT="./output/${STEM}-gpu.mp4"
fi

FFMPEG_BIN="/opt/homebrew/bin/ffmpeg"
if [ ! -x "$FFMPEG_BIN" ]; then
  FFMPEG_BIN="$(which ffmpeg || true)"
fi

if [ -z "$FFMPEG_BIN" ] || [ ! -x "$FFMPEG_BIN" ]; then
  echo "Error: FFmpeg not found on macOS host."
  echo "Install via Homebrew: brew install ffmpeg"
  exit 1
fi

# Select hardware encoder
case "$CODEC" in
  h264)
    VCODEC="h264_videotoolbox"
    EXTRA_ARGS="-b:v 8M"
    ;;
  prores)
    VCODEC="prores_videotoolbox"
    EXTRA_ARGS="-profile:v 3"
    ;;
  hevc|*)
    VCODEC="hevc_videotoolbox"
    EXTRA_ARGS="-b:v 6M -tag:v hvc1"
    ;;
esac

echo "========================================================"
echo "⚡ Apple M5 Max VideoToolbox GPU Encoding"
echo "  Input:   $INPUT"
echo "  Output:  $OUTPUT"
echo "  Encoder: $VCODEC (Apple Metal Hardware)"
echo "========================================================"

mkdir -p "$(dirname "$OUTPUT")"

"$FFMPEG_BIN" -y -hide_banner \
  -hwaccel videotoolbox \
  -i "$INPUT" \
  -c:v "$VCODEC" \
  $EXTRA_ARGS \
  -c:a aac -b:a 192k \
  "$OUTPUT"

echo "✅ Hardware GPU conversion complete: $OUTPUT"
