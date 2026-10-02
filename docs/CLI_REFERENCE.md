# `vert` CLI reference

`scripts/vert` is a single bash script (bash 3.2 compatible, so it runs
unmodified on macOS's stock shell) that drives the API over `curl`. It is
installed on your `PATH` by `./install.sh`, or run in place as `./scripts/vert`.

## Stack lifecycle

| Command | What it does |
|---|---|
| `vert up [--build]` | Start the container (`docker compose up -d`) and poll `/api/version` until it answers, up to 90s |
| `vert down` | `docker compose down` |
| `vert logs [-f]` | Tail container logs (default: last 100 lines) |
| `vert status` / `vert health` | Health check plus `/api/system-info` host/acceleration telemetry |
| `vert open` | Open the web UI in your default browser (`open` / `xdg-open`) |

## Conversion

```
vert convert <file> --to <format> [options]
```

| Flag | Maps to | Example |
|---|---|---|
| `-o, --out-dir <dir>` | — (client-side) | `-o ./out` |
| `--crf <n>` | `crf` | `--crf 20` (lower = higher quality) |
| `--resolution <WxH>` | `resolution` | `--resolution 1920x1080` |
| `--codec <name>` | `video_codec` | `--codec libx265` |
| `--audio-bitrate <br>` | `audio_bitrate` | `--audio-bitrate 192k` |
| `--fps <n>` | `fps` | `--fps 30` |
| `--quality <n>` | `quality` | `--quality 90` (images, 1-100) |
| `--trim-start <ts>` | `trim_start` | `--trim-start 00:00:05` |
| `--trim-duration <ts>` | `trim_duration` | `--trim-duration 00:00:30` |
| `--speed <x>` | `playback_speed` | `--speed 1.5` |
| `--dpi <n>` | `dpi` | `--dpi 300` (document rasterization) |
| `--loudnorm` | `loudnorm=true` | normalize audio loudness |

Other conversion-adjacent commands:

| Command | What it does |
|---|---|
| `vert md <file...> [-o <dir>]` | Anything → Markdown, with OCR and figure extraction; unzips the result into `<dir>` |
| `vert batch` | Convert everything in `./input` → `./output` (same as `./convert.sh`) |
| `vert inspect <file>` | Stream/codec/metadata telemetry via ffprobe |
| `vert formats [category]` | List supported formats; reads the live catalogue when the API is up, else a static fallback |
| `vert ls` | What's currently in `./input` and `./output` |

See [FORMATS.md](FORMATS.md) for the full format tables these commands operate on.

## Interactive mode

Running `vert` with no arguments (or `vert i` / `vert interactive`) opens an
arrow-key picker: action → file path → category → target format, with a live
progress bar during the conversion. It falls back to a numbered prompt when
stdin isn't a TTY.

## Environment variables

| Variable | Effect |
|---|---|
| `VERT_PORT` | Overrides the API port the CLI talks to (default: `PORT` in `.env`, else `8394`) |
| `NO_COLOR` | Disables ANSI colour in CLI output |

## Exit behavior

Every subcommand that talks to the API first checks `require_up` and fails
fast with `Better VERT is not responding on <url>. Start it with: vert up` if
the container isn't reachable. Conversion failures print a one-line error and
point you at `vert logs` for the detailed server-side traceback (the HTTP
response itself never includes internal paths or stack traces — see
[ARCHITECTURE.md](ARCHITECTURE.md#security-model)).
