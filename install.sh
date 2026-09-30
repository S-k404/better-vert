#!/usr/bin/env bash
# Better VERT installer.
#
#   ./install.sh                 build, start, and offer to put `vert` on your PATH
#   ./install.sh --no-start      set up config only, don't build or start
#   ./install.sh --link          install the `vert` command without prompting
#   ./install.sh --no-link       skip the PATH step
#   ./install.sh --prefix <dir>  where to link `vert` (default: /usr/local/bin,
#                                falling back to ~/.local/bin)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  R=$'\033[0m'; B=$'\033[1m'; D=$'\033[2m'
  CY=$'\033[36m'; GR=$'\033[32m'; YL=$'\033[33m'; RD=$'\033[31m'; MG=$'\033[35m'
else
  R=''; B=''; D=''; CY=''; GR=''; YL=''; RD=''; MG=''
fi

step() { printf '\n%s==>%s %s%s%s\n' "$CY" "$R" "$B" "$*" "$R"; }
ok()   { printf '%s  ✓%s %s\n' "$GR" "$R" "$*"; }
warn() { printf '%s  !%s %s\n' "$YL" "$R" "$*"; }
die()  { printf '%s  ✗%s %s\n' "$RD" "$R" "$*" >&2; exit 1; }

DO_START=1
LINK_MODE="ask"     # ask | yes | no
PREFIX=""

while [ $# -gt 0 ]; do
  case "$1" in
    --no-start) DO_START=0; shift ;;
    --link)     LINK_MODE="yes"; shift ;;
    --no-link)  LINK_MODE="no"; shift ;;
    --prefix)   PREFIX="$2"; shift 2 ;;
    -h|--help)  sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)          die "unknown option: $1 (try --help)" ;;
  esac
done

printf '\n%s  Better VERT%s %s· installer%s\n' "$B$MG" "$R" "$D" "$R"

# --- 1. Prerequisites -------------------------------------------------------
step "Checking prerequisites"

command -v docker >/dev/null 2>&1 \
  || die "Docker is not installed. Get Docker Desktop: https://docs.docker.com/get-docker/"
ok "docker $(docker --version | awk '{print $3}' | tr -d ,)"

docker compose version >/dev/null 2>&1 \
  || die "'docker compose' is unavailable. Update Docker Desktop, or install the Compose v2 plugin."
ok "docker compose $(docker compose version --short 2>/dev/null || echo present)"

command -v curl >/dev/null 2>&1 || die "curl is required but not installed."
ok "curl"

for opt in unzip jq; do
  command -v "$opt" >/dev/null 2>&1 && ok "$opt ${D}(optional)${R}" \
    || warn "$opt not found — optional, improves 'vert md' and JSON output"
done

if [ "$DO_START" -eq 1 ] && ! docker info >/dev/null 2>&1; then
  die "The Docker daemon isn't running. Start Docker Desktop, then re-run ./install.sh"
fi

# --- 2. Configuration -------------------------------------------------------
step "Configuring"

if [ -f .env ]; then
  ok ".env already exists — leaving it untouched"
else
  cp .env.example .env
  ok "created .env from .env.example"
fi

# On Linux, bind-mount permissions are enforced literally, so the container user
# has to match the host user or it cannot write to ./output.
if [ "$(uname -s)" = "Linux" ]; then
  if ! grep -q '^VERT_UID=' .env 2>/dev/null; then
    printf '\nVERT_UID=%s\nVERT_GID=%s\n' "$(id -u)" "$(id -g)" >> .env
    ok "pinned VERT_UID/VERT_GID to $(id -u):$(id -g) for bind-mount writes"
  fi
else
  ok "$(uname -s) host — Docker Desktop maps bind-mount ownership for you"
fi

mkdir -p input output
chmod +x scripts/vert scripts/convert.sh scripts/mac-gpu-accelerator.sh convert.sh 2>/dev/null || true
ok "input/ and output/ ready, scripts marked executable"

PORT="$(grep -E '^PORT=' .env | tail -1 | cut -d= -f2- | tr -d '"'"'"' ' || true)"
PORT="${PORT:-8394}"

# --- 3. Build & start -------------------------------------------------------
if [ "$DO_START" -eq 1 ]; then
  step "Building the image ${D}(first run pulls ffmpeg, tesseract, poppler, pandoc — this takes a few minutes)${R}"
  docker compose build
  ok "image built"

  step "Starting the stack"
  docker compose up -d
  printf '%s  …%s waiting for the API on port %s' "$D" "$R" "$PORT"
  i=0
  until curl -fsS --max-time 3 "http://127.0.0.1:${PORT}/api/version" >/dev/null 2>&1; do
    i=$((i+1))
    [ "$i" -gt 90 ] && { printf '\n'; die "Timed out. Check logs with: docker compose logs better-vert"; }
    printf '.'
    sleep 1
  done
  printf '\n'
  ok "API is live at http://localhost:${PORT}"
else
  warn "skipping build/start (--no-start)"
fi

# --- 4. Install the `vert` command -----------------------------------------
step "Command line tool"

if [ "$LINK_MODE" = "ask" ]; then
  if [ -t 0 ]; then
    printf '  Install the %svert%s command on your PATH? [Y/n] ' "$B" "$R"
    read -r reply
    case "$reply" in [Nn]*) LINK_MODE="no" ;; *) LINK_MODE="yes" ;; esac
  else
    LINK_MODE="no"
  fi
fi

if [ "$LINK_MODE" = "yes" ]; then
  if [ -z "$PREFIX" ]; then
    if [ -w /usr/local/bin ] 2>/dev/null; then PREFIX=/usr/local/bin
    else PREFIX="$HOME/.local/bin"
    fi
  fi
  mkdir -p "$PREFIX"
  if ln -sf "$PROJECT_DIR/scripts/vert" "$PREFIX/vert" 2>/dev/null; then
    ok "linked $PREFIX/vert -> scripts/vert"
    case ":$PATH:" in
      *":$PREFIX:"*) : ;;
      *) warn "$PREFIX is not on your PATH. Add this to your shell profile:"
         printf '      %sexport PATH="%s:$PATH"%s\n' "$D" "$PREFIX" "$R" ;;
    esac
  else
    warn "could not write to $PREFIX. Either re-run with:"
    printf '      %ssudo ./install.sh --link --prefix /usr/local/bin%s\n' "$D" "$R"
    printf '   or use it in place: %s./scripts/vert%s\n' "$D" "$R"
  fi
else
  printf '  Skipped. Run it in place with %s./scripts/vert%s\n' "$D" "$R"
fi

# --- 5. Done ----------------------------------------------------------------
printf '\n%s  Ready.%s\n\n' "$B$GR" "$R"
printf '  %sWeb UI%s      http://localhost:%s\n' "$B" "$R" "$PORT"
printf '  %sInteractive%s vert\n' "$B" "$R"
printf '  %sConvert%s     vert convert clip.mov --to mp4 --crf 20\n' "$B" "$R"
printf '  %sMarkdown%s    vert md report.pdf -o ./notes\n' "$B" "$R"
printf '  %sAll commands%s vert help\n\n' "$B" "$R"
