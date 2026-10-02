# Format reference

Source of truth: `backend/media_engine.py` (`SUPPORTED_FORMATS`) and `backend/markitdown_engine.py`.
`vert formats [category]` prints this same catalogue live from the running API
(`GET /api/formats-catalog`), with a static fallback baked into `scripts/vert`
for when the container is down.

## Universal converter (`vert convert` / `POST /api/convert-universal`)

Multi-threaded FFmpeg for video/audio, ImageMagick for images, Pandoc/Poppler
for the document formats below.

| Category | Formats |
|---|---|
| **video** | mp4, mkv, webm, mov, avi, gif, av1, wmv, flv, m4v, ts, mts, m2ts, vob, ogv, 3gp, asf |
| **audio** | mp3, wav, aac, flac, m4a, m4b, ogg, opus, wma, aiff, alac, ac3, caf, mp2, aif |
| **image** | png, jpg, jpeg, webp, avif, gif, tiff, bmp, ico, svg |
| **document** | pdf, docx, md, html, epub, txt, rtf, odt |
| **data** | json, csv, yaml, yml, xml, tsv, xlsx |

Every video target in the table above has a tuned FFmpeg encoder preset in
`VIDEO_ENCODER_MAP` (codec, CRF, pixel format, audio codec/bitrate) — for
example `mp4`/`mov`/`m4v` use `libx264 -preset fast -crf 22` with `+faststart`,
`webm` uses `libvpx-vp9`, and `av1` uses `libsvtav1`. Pass `--codec`, `--crf`,
`--resolution`, `--fps`, `--audio-bitrate`, `--loudnorm`, `--trim-start` /
`--trim-duration`, or `--speed` on `vert convert` to override the defaults for
a given run (see [CLI_REFERENCE.md](CLI_REFERENCE.md)).

## Cross-medium routes (`POST /api/convert-universal` with a `cross` target)

These aren't simple re-encodes — each is its own pipeline:

| Route id | Badge | Description |
|---|---|---|
| `pdf_storyboard` | Video → PDF | Multi-page PDF storyboard with video telemetry and adaptive keyframes |
| `waveform_video` | Audio → Video | Peak-to-peak neon waveform visualizer, 1280×720 @ 30fps, web-faststart MP4 |
| `transcript_md` | Audio → Markdown | Speech-to-text transcript plus audio telemetry |
| `images_zip` | Doc/MD → Images ZIP | 200 DPI page rasterization and embedded figure extraction, zipped |
| `svg` | Image → SVG | Potrace vectorization (luminance bezier path tracing) |
| `gif` | Video → GIF | Two-pass palette-optimized Lanczos/Bayer-dither GIF |
| `xlsx` | Data → XLSX | Structured multi-column spreadsheet workbook |

## Anything → Markdown (`vert md` / `POST /api/convert-markdown-zip`)

Powered by Microsoft MarkItDown, with Tesseract OCR and Poppler as fallbacks
for scanned/image-only PDFs:

- **Office**: DOCX, PPTX, XLSX, XLS
- **Documents**: PDF (text + table layer extraction, OCR fallback), EPUB, RTF, ODT
- **Web & data**: HTML, CSV, TSV, JSON, XML
- **Images & audio**: photos (EXIF extraction + OCR), audio (speech transcription + metadata)
- **Archives**: ZIP (recurses into nested files and converts each one)

Output is one `.md` per input file plus an `images/` folder for any extracted
figures, bundled into a zip by the API and unpacked automatically by
`vert md`.

## PDF utilities

- `POST /api/pdf-merge` — merge 2+ uploaded PDFs into one.
- `POST /api/pdf-split` — split a PDF or extract a page range.
- `POST /api/inspect-media` (`vert inspect`) — ffprobe-backed stream/codec/metadata
  telemetry for any video, audio, image, or document file.

## System packages behind all of this

Installed in the Docker image (see `Dockerfile`): `ffmpeg`, `tesseract-ocr`
(+ `tesseract-ocr-eng`), `poppler-utils`, `imagemagick`, `pandoc`, `potrace`,
`libmagic1`. If you ever run the backend outside Docker, all of these need to
be on `PATH`.
