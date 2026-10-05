#!/usr/bin/env bash
# Host-platform helpers shared by install.sh, scripts/vert and scripts/convert.sh.
# Sourced, never executed. Bash 3.2 compatible (the version macOS ships).

# host_os: macos | linux | wsl | windows (Git Bash / MSYS2 / Cygwin) | other
host_os() {
  case "$(uname -s 2>/dev/null)" in
    Darwin)               echo macos ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then echo wsl; else echo linux; fi ;;
    MINGW*|MSYS*|CYGWIN*) echo windows ;;
    *)                    echo other ;;
  esac
}

# compose <args...>
# Uses the Compose v2 plugin (`docker compose`) and falls back to the standalone
# v1 binary (`docker-compose`) that older Linux distro packages still ship.
compose_available() {
  docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1
}

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

# open_url <url>: open the default browser; returns non-zero if nothing could.
open_url() {
  local url="$1"
  case "$(host_os)" in
    macos)
      open "$url" ;;
    windows)
      # explorer.exe exits 1 even when it succeeds, so its status is ignored.
      if command -v cygstart >/dev/null 2>&1; then cygstart "$url"
      elif command -v explorer.exe >/dev/null 2>&1; then explorer.exe "$url" || true
      else return 1
      fi ;;
    wsl)
      if   command -v wslview      >/dev/null 2>&1; then wslview "$url"
      elif command -v explorer.exe >/dev/null 2>&1; then explorer.exe "$url" || true
      elif command -v xdg-open     >/dev/null 2>&1; then xdg-open "$url"
      else return 1
      fi ;;
    *)
      # Not `open`: on Debian/Ubuntu that name is an alias for `openvt`.
      if command -v xdg-open >/dev/null 2>&1; then xdg-open "$url"
      else return 1
      fi ;;
  esac
}
