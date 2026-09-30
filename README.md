# Better VERT · Apple M5 Max Studio Edition

A customized, privacy-focused, high-performance universal conversion suite built specifically for **Apple Silicon M-Series (Apple M5 Max with 18 CPU Cores)**.

It merges the universal format capabilities of [VERT](https://github.com/VERT-sh/VERT) with the document-parsing intelligence of [Microsoft MarkItDown](https://github.com/microsoft/markitdown) (with Tesseract OCR, Poppler PDF text/table extraction, and batch automation).

Everything runs **100% locally** in Docker on your Mac — no files ever leave your machine.

---

## ⚡ What Makes It "Better VERT" for M5 Max Mac?

| Feature | Upstream VERT | File Converter | **Better VERT (M5 Max Edition)** |
|---|---|---|---|
| **Video Conversion** | Offloaded to external cloud (`vertd.vert.sh`) or separate Rust daemon | Not supported | **Local multi-threaded FFmpeg** (18-core M5 Max auto-threaded) |
| **Anything &rarr; Markdown** | Limited (pandoc wasm) | Yes (`markitdown`) | **Fully integrated** (MarkItDown + Tesseract OCR + Poppler + live preview) |
| **Hardware Acceleration** | None by default | CPU only | **ARM NEON SIMD + 18-core threads + Browser Metal GPU + Host VideoToolbox Bridge** |
| **Upload Limits** | 10MB limit in Nginx | Unlimited | **2 GB per file by default** (`MAX_UPLOAD_MB`, raise as needed) |
| **Batch Processing** | Manual one-by-one | `./convert.sh` | **Both Web UI Batch Monitor & `./convert.sh` CLI** |
| **Docker Stack** | Complex multi-repo setup | Single container | **Single-command Compose stack tuned for M5 Max** (`8394:8000`) |

---

## 🚀 Quick Start

### Option A — one-line install (recommended)

```bash
git clone https://github.com/S-k404/better-vert.git
cd better-vert
./install.sh
```

The installer checks your prerequisites, writes a `.env`, builds the image,
waits for the API to come up, and offers to put the `vert` command on your PATH.

```
./install.sh --no-start      # set up config only
./install.sh --link          # install `vert` without prompting
./install.sh --prefix ~/bin  # choose where `vert` is linked
```

Then open **[http://localhost:8394](http://localhost:8394)**.

### Option B — plain Docker Compose

```bash
cp .env.example .env   # optional: change the host port
docker compose up -d --build
```

To stop: `docker compose down` (or `vert down`).

---

## 💻 Command Line Tool

`vert` drives the whole stack from your terminal. Run it with no arguments for an
interactive picker with arrow-key navigation, the same format categories as the
web UI, and a live progress bar:

```bash
vert
```

```
  Better VERT · local universal conversion
  http://127.0.0.1:8394

What would you like to do?  (↑/↓ move · enter select · q cancel)
  ❯ Convert a file to another format
    Convert files to Markdown
    Inspect a file
    Batch-convert ./input
    Show system status

Target category  (↑/↓ move · enter select · q cancel)
    🎬 Video
  ❯ 🎧 Audio
    🖼  Image
    📄 Document
    📊 Data
    ✨ Cross-medium

  ████████████████████░░░░░░░░░░░░░░  60%  podcast.wav → flac  6s
```

Or use it non-interactively:

```bash
vert up --build                 # start the stack and wait until it answers
vert convert clip.mov --to mp4 --crf 20 --resolution 1920x1080
vert md report.pdf slides.pptx -o ./notes
vert inspect movie.mkv          # codec / stream / metadata telemetry
vert batch                      # convert everything in ./input
vert formats video              # what you can convert to
vert status                     # health + hardware acceleration telemetry
vert open                       # open the web UI
vert down
```

| Command | What it does |
|---|---|
| `vert` | Interactive picker (arrow keys + progress bar) |
| `vert up` / `down` / `logs` | Container lifecycle |
| `vert convert <file> --to <fmt>` | Universal conversion with encoding flags |
| `vert md <file...>` | Anything → Markdown, with OCR and figure extraction |
| `vert inspect <file>` | Stream, codec and metadata telemetry |
| `vert batch` | Convert everything in `./input` → `./output` |
| `vert formats [category]` | Supported formats per category |
| `vert ls` | What's currently in `./input` and `./output` |
| `vert status` | Health check and host telemetry |

Conversion flags: `--crf`, `--resolution`, `--codec`, `--audio-bitrate`, `--fps`,
`--quality`, `--trim-start`, `--trim-duration`, `--speed`, `--dpi`, `--loudnorm`.
Run `vert help` for the full list.

`VERT_PORT` overrides the API port; `NO_COLOR` disables coloured output.

---

## 🛠 Features & Workflows

### 1. Universal 250+ Format Converter
Convert between video, audio, image, and document formats:
- **Video**: MP4, MKV, WEBM, MOV, AVI, GIF, WMV, FLV, TS, etc. (uses all 18 CPU cores with `-threads 0` and ARM NEON SIMD).
- **Audio**: MP3, WAV, AAC, FLAC, M4A, OGG, OPUS.
- **Images**: PNG, JPG, WEBP, AVIF, GIF, TIFF, BMP, SVG (via ImageMagick).
- **Documents**: PDF, DOCX, HTML, EPUB, TXT, RTF.

### 2. Anything &rarr; Markdown Studio (Incorporating File Converter)
Drag & drop any file to convert into structured Markdown:
- **Office**: Word (DOCX), PowerPoint (PPTX), Excel (XLSX, XLS).
- **Documents**: PDF (with text & table layer extraction via Poppler and OCR fallbacks), EPUB, RTF, ODT.
- **Web & Data**: HTML, CSV, TSV, JSON, XML.
- **Images & Audio**: Photos with EXIF extraction & Tesseract OCR; Audio with speech transcription & metadata.
- **Archives**: ZIP (converts nested files inside).
- **Rich Preview**: Live rendered Markdown modal (toggle between formatted HTML view and raw markdown), instant copy button, individual `.md` downloads, or **"Convert & Download .ZIP"**.
- Converted `.md` files are also saved directly to your Mac in `./output/`.

### 3. Batch Folder Automation (CLI & UI)
Drop any files into `./input/` on your Mac, then run:

```bash
./convert.sh
```

Or pass any folder path to convert it automatically:

```bash
./convert.sh ~/Desktop/research-papers
```

Converted files immediately land in `./output/`.

### 4. Native macOS VideoToolbox GPU Acceleration
For massive 4K/8K video conversions where you want dedicated Apple VideoToolbox GPU hardware encoders:

```bash
./scripts/mac-gpu-accelerator.sh input.mov output.mp4 hevc
```

Supports `hevc` (`hevc_videotoolbox`), `h264` (`h264_videotoolbox`), and `prores` (`prores_videotoolbox`).

---

## 🔐 Security Notes

This stack processes untrusted files (anything you drop on it) through FFmpeg,
ImageMagick, Tesseract, Poppler and Pandoc, so it is set up to stay local:

| Control | Default |
|---|---|
| **Network exposure** | Published on `127.0.0.1` only — not reachable from your LAN |
| **CORS** | Restricted to local origins via `ALLOWED_ORIGINS`; credentials disabled |
| **Container user** | Runs as non-root `vert` (uid 10001) with `no-new-privileges` |
| **Upload size** | Capped at `MAX_UPLOAD_MB` (2 GB default) per file |
| **Filenames** | Every client-supplied filename is reduced to a safe basename before it touches disk |
| **Error responses** | Conversion failures log full detail server-side and return a generic message |

There is **no authentication** — the loopback binding is what keeps it private.
If you expose this beyond `localhost`, put an authenticating reverse proxy in
front of it and set `ALLOWED_ORIGINS` accordingly.

`./output/` and `./input/` are git-ignored, since they hold your actual documents.

---

## 📂 Project Structure

```
Better-vertsh/
├── backend/
│   ├── app.py                   # FastAPI application with CORS, COOP/COEP, and telemetry
│   ├── markitdown_engine.py     # Microsoft MarkItDown + Tesseract OCR + Poppler fallbacks
│   ├── media_engine.py          # FFmpeg & ImageMagick converter tuned for 18-core M5 Max
│   └── requirements.txt         # Pinned dependencies
├── frontend/
│   ├── index.html               # Modern Apple Studio dark mode UI
│   ├── style.css                # Glassmorphism, CSS grid, micro-animations
│   └── app.js                   # Universal & Markdown controller with marked.js
├── input/                       # Drop files here for batch conversion
├── output/                      # Converted files land here directly on your Mac
├── scripts/
│   ├── vert                     # Command line client (interactive + scriptable)
│   ├── convert.sh               # CLI batch converter
│   └── mac-gpu-accelerator.sh   # Host Apple VideoToolbox GPU encoding helper
├── install.sh                   # Prerequisite check, build, start, PATH setup
├── convert.sh                   # Root shortcut for scripts/convert.sh
├── .env.example                 # Copy to .env to override port / upload limit
├── Dockerfile                   # Multi-stage ARM64 build (Python 3.12, FFmpeg, Tesseract, Poppler)
├── docker-compose.yml           # Compose configuration tuned for Apple Silicon
└── README.md
```
