# Architecture

## Components

```
Better-vertsh/
├── backend/
│   ├── app.py                   # FastAPI app: routes, CORS, upload limits, error handling
│   ├── markitdown_engine.py     # Microsoft MarkItDown + Tesseract OCR + Poppler fallbacks
│   ├── media_engine.py          # FFmpeg/ImageMagick conversion routes + format catalogue
│   └── requirements.txt
├── frontend/
│   ├── index.html / style.css / app.js   # Static single-page UI, served by the backend
├── scripts/
│   ├── vert                     # CLI client (see CLI_REFERENCE.md)
│   ├── convert.sh               # Batch converter used by `vert batch`
│   └── mac-gpu-accelerator.sh   # Host-side Apple VideoToolbox GPU encode helper
├── input/ output/                # Bind-mounted host folders for batch and converted files
├── install.sh                   # Prereq check, .env setup, build, start, PATH link
├── Dockerfile                   # python:3.12-slim + ffmpeg/tesseract/poppler/imagemagick/pandoc/potrace
└── docker-compose.yml            # Single-service compose stack, loopback-only port binding
```

One FastAPI process serves both the JSON API and the static frontend (mounted
at `/static`, with `/` serving `frontend/index.html`). The `vert` CLI and the
web UI are two clients of the same API — nothing the UI can do is unavailable
from the command line.

## Request flow

1. A file arrives via `multipart/form-data` at one of the `/api/convert-*` or
   `/api/pdf-*` routes, or `/api/convert-markdown*`.
2. `safe_filename()` reduces the client-supplied name to a safe basename
   before it ever touches disk (see [Security model](#security-model)).
3. The request is dispatched to `media_engine.convert_media` (FFmpeg/ImageMagick
   routes, keyed by `SUPPORTED_FORMATS`) or `markitdown_engine` (document →
   Markdown routes), which shells out to the relevant system binary.
4. The result is written to `OUTPUT_DIR` (bind-mounted to `./output` on the
   host) **and** streamed back in the HTTP response, so both the web UI
   download and the host filesystem copy come from one conversion.
5. Any failure is logged in full server-side and returned to the client as a
   generic `"<stage> failed. See server logs for details."` — see
   [Security model](#security-model).

## Batch path

`./convert.sh` (or `vert batch`) hits `POST /api/batch-convert`, which walks
`IN_DIR` (`./input`, bind-mounted) and converts every file it finds to
Markdown via the same `markitdown_engine` used by the interactive routes,
writing `{processed, failed}` manifests to the response.

## Hardware acceleration

- **Container (FFmpeg/ImageMagick)**: `-threads 0` lets FFmpeg use every core
  the container is given; on Apple Silicon this includes ARM NEON SIMD
  automatically via the ffmpeg build in `python:3.12-slim`'s apt packages.
- **Browser**: `Cross-Origin-Opener-Policy: same-origin` and
  `Cross-Origin-Embedder-Policy: credentialless` are set on every response so
  the frontend can use SharedArrayBuffer-dependent WebAssembly SIMD / WebGPU.
- **Host GPU bridge**: `scripts/mac-gpu-accelerator.sh` runs *outside* the
  container, directly on macOS, so it can reach Apple's VideoToolbox hardware
  encoders (`hevc_videotoolbox`, `h264_videotoolbox`, `prores_videotoolbox`),
  which aren't exposed inside Linux containers on Apple Silicon.
- `GET /api/system-info` reports what the container can actually observe
  (logical/physical core count, memory, architecture) rather than guessing a
  specific host chip — Docker Desktop virtualizes `/proc/cpuinfo`, so the API
  reports an architecture family, not a model name.

## Security model

The service has **no authentication** — it relies entirely on only being
reachable from the machine it runs on:

- `docker-compose.yml` publishes the port as `127.0.0.1:${PORT}:8000`, not
  `0.0.0.0`, so it's unreachable from the LAN even if your firewall is open.
- CORS (`ALLOWED_ORIGINS`) defaults to `localhost`/`127.0.0.1` on the common
  dev ports, with credentials disabled, so no page you have open elsewhere in
  your browser can call the API cross-origin.
- The container runs as a non-root user (`vert`, uid 10001 by default) with
  `no-new-privileges`, even though it routinely shells out to FFmpeg/
  ImageMagick/Tesseract/Poppler/Pandoc on files it didn't create.
- `safe_filename()` + `safe_output_path()` strip directory components and
  disallowed characters from every client-supplied filename and re-verify the
  resolved path stays under `OUTPUT_DIR` before any write — closing the usual
  `../../etc/passwd`-style path traversal via upload filenames.
- `MAX_UPLOAD_MB` (default 2048) is enforced by reading the upload into memory
  and checking its length before any processing starts.
- `conversion_error()` logs the real exception (which often contains absolute
  container paths or full command lines) server-side only, and returns a
  generic message to the client.

If you expose this beyond `localhost` — e.g. to reach it from another device
on your LAN — put an authenticating reverse proxy in front of it and update
`ALLOWED_ORIGINS` accordingly; the app itself has no login.
