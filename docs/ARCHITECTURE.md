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
│   ├── gpu-accelerator.sh       # Host-side GPU encode helper (VideoToolbox/NVENC/QSV/VAAPI/AMF)
│   ├── mac-gpu-accelerator.sh   # Back-compat shim that calls gpu-accelerator.sh
│   └── lib/platform.sh          # Sourced by the scripts: OS detection, compose v1/v2, browser opener
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
  the container is given. SIMD kernels are chosen at runtime by the ffmpeg build
  in `python:3.12-slim`'s apt packages: NEON on ARM64, SSE/AVX on x86-64.
- **Browser**: `Cross-Origin-Opener-Policy: same-origin` and
  `Cross-Origin-Embedder-Policy: credentialless` are set on every response so
  the frontend can use SharedArrayBuffer-dependent WebAssembly SIMD / WebGPU.
- **Host GPU bridge**: `scripts/gpu-accelerator.sh` runs *outside* the
  container, directly on the host, because Docker Desktop doesn't expose the GPU
  to Linux containers on macOS or Windows. It chooses VideoToolbox on macOS,
  else NVENC, Quick Sync, VAAPI (Linux) or AMF (Windows), test-encoding each
  candidate first and falling back to software x264/x265. Override with
  `VERT_HWACCEL`.
- `GET /api/system-info` reports what the container can actually observe
  (logical/physical core count, memory, architecture, and the widest SIMD set
  its CPU exposes) rather than guessing a specific host chip — Docker Desktop
  virtualizes `/proc/cpuinfo`, so the API reports an architecture family, not a
  model name. The container is always Linux, so it cannot tell macOS, Windows
  and Linux hosts apart; the web UI reads the browser's OS (the same machine,
  since the port is loopback-only) to label the host and show the right GPU tip.

## Cross-platform notes

- **Output filenames** are written to a bind mount, so they must be valid on the
  *host* filesystem, not just in the Linux container. `safe_filename()` and
  `safe_stem()` prefix Windows device names (`con`, `nul`, `com1`, ...) with `_`,
  and `unique_name()` compares names case-insensitively so `Report.md` and
  `report.md` never overwrite each other on macOS or Windows.
- **Bind-mount ownership**: Docker Desktop (macOS/Windows) maps it for you. On
  Linux the container user must match the host user (`VERT_UID`/`VERT_GID`,
  set by `install.sh`), except for a root host, where `./input` and `./output`
  are handed to the container user instead (the image cannot create a second
  UID 0). On SELinux hosts `VERT_MOUNT_OPTS=:z` relabels the mounts.
- **Line endings**: `.gitattributes` pins shell scripts to LF so a Windows
  `core.autocrlf=true` checkout can't turn them into CRLF files bash rejects.

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
