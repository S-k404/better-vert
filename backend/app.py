"""
Better VERT (Universal Studio Edition) - Unified API Backend.
Integrates Microsoft MarkItDown, Universal Multi-Threaded Converter, and System Telemetry.
"""

import io
import json
import logging
import os
import platform
import re
import shutil
import urllib.parse
import zipfile
from pathlib import Path
from typing import List, Optional

import psutil
from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import math
import tempfile
from datetime import datetime
from markitdown_engine import (
    avoid_reserved_name,
    convert_bytes_to_markdown,
    convert_bytes_to_markdown_with_assets,
    safe_stem,
    unique_name,
)
from media_engine import (
    SUPPORTED_FORMATS,
    convert_media,
    inspect_file_metadata,
    merge_pdfs,
    split_pdf,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("better-vert")

app = FastAPI(
    title="Better VERT · Universal Studio Edition",
    description="Universal 250+ format conversion & Microsoft MarkItDown engine running locally.",
    version="2.0.0",
)

# CORS setup.
# This service runs locally and has no authentication, so it must not be callable
# from arbitrary websites the user happens to have open. Allow only local origins
# by default; override with ALLOWED_ORIGINS (comma-separated) if you front it with
# a reverse proxy on another hostname.
_default_origins = [
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in ("8394", "8000", "3000", "5173")
]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", ",".join(_default_origins)).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_hardware_and_coop_headers(request: Request, call_next):
    """
    Enables Cross-Origin Isolation for Browser-side WebAssembly SIMD and WebGPU compute,
    while removing standard upload limitations.
    """
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Embedder-Policy"] = "credentialless"
    response.headers["X-Hardware-Acceleration"] = platform.machine()
    return response


IN_DIR = Path(os.environ.get("INPUT_DIR", "/data/input"))
OUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/data/output"))
IN_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "2048"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


def safe_filename(name: Optional[str], fallback: str = "upload.dat") -> str:
    """Reduces a client-supplied filename to a bare, filesystem-safe basename.

    Browsers and API clients can send anything here, including '../../etc/passwd'
    or an absolute path. Path(...).name drops every directory component, then the
    remaining characters are restricted so the result can only ever name a single
    file inside the directory it is joined to.
    """
    candidate = Path(name or "").name
    candidate = re.sub(r"[^\w\-. ]+", "_", candidate).strip(" .")
    return avoid_reserved_name(candidate[:180] or fallback)


def safe_output_path(base: Path, name: str, fallback: str = "converted.dat") -> Path:
    """Resolves name under base, refusing anything that escapes base."""
    target = (base / safe_filename(name, fallback)).resolve()
    if base.resolve() not in target.parents:
        raise HTTPException(status_code=400, detail="Invalid output filename.")
    return target


async def read_upload(upload: UploadFile) -> bytes:
    """Reads an upload into memory, enforcing the configured size ceiling."""
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {MAX_UPLOAD_MB} MB upload limit.",
        )
    return data


def conversion_error(stage: str, exc: Exception) -> HTTPException:
    """Logs the full exception server-side and returns a non-leaking client error.

    Raw exception text from FFmpeg/MarkItDown routinely contains absolute container
    paths and command lines, so it stays in the logs rather than the HTTP response.
    """
    logger.exception("%s failed: %s", stage, type(exc).__name__)
    return HTTPException(status_code=500, detail=f"{stage} failed. See server logs for details.")


def _detect_host_label(arch: str, system_os: str) -> str:
    """Best-effort host description from what the container can actually observe.

    The container never has access to the real host model name (Docker Desktop
    virtualizes /proc/cpuinfo) and cannot tell macOS, Windows and Linux hosts apart,
    since it is always a Linux container. So this reports only the CPU architecture
    family; the web UI adds the OS it can see from the browser.
    """
    family = "ARM64" if arch in ("arm64", "aarch64") else arch
    return f"{family} host ({system_os} container)"


def _x86_cpu_flags() -> set:
    """CPU feature flags from /proc/cpuinfo (Linux containers only), else empty."""
    try:
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("flags"):
                    return set(line.split(":", 1)[1].split())
    except OSError:
        pass
    return set()


def _detect_simd(arch: str) -> Optional[str]:
    """Names the widest SIMD instruction set the container's CPU exposes, if known.

    FFmpeg and ImageMagick pick the right kernels at runtime, so this is telemetry
    only. It is architecture-aware: reporting NEON on an Intel/AMD host is wrong.
    """
    arch = arch.lower()
    if arch in ("arm64", "aarch64"):
        return "NEON"  # mandatory in the AArch64 baseline
    if arch in ("x86_64", "amd64"):
        flags = _x86_cpu_flags()
        for flag, label in (("avx512f", "AVX-512"), ("avx2", "AVX2"), ("avx", "AVX"), ("sse4_2", "SSE4.2")):
            if flag in flags:
                return label
        return "SSE2"  # mandatory in the x86-64 baseline
    return None


@app.get("/api/system-info")
def get_system_info():
    """Returns real-time host and hardware acceleration telemetry."""
    cpu_count = psutil.cpu_count(logical=True) or os.cpu_count() or 1
    physical_cores = psutil.cpu_count(logical=False) or cpu_count
    mem = psutil.virtual_memory()
    arch = platform.machine()
    system_os = platform.system()
    simd = _detect_simd(arch)

    return {
        "host": _detect_host_label(arch, system_os),
        "architecture": arch,
        "os": system_os,
        "cores_logical": cpu_count,
        "cores_physical": physical_cores,
        "memory_total_gb": round(mem.total / (1024**3), 2),
        "memory_available_gb": round(mem.available / (1024**3), 2),
        "acceleration": {
            "simd": simd,
            "container_neon_simd": simd == "NEON",
            "container_threads": cpu_count,
            "browser_webgpu_ready": True,
            "videotoolbox_bridge_supported": True,
            "host_gpu_script": "scripts/gpu-accelerator.sh",
        },
        "supported_formats": SUPPORTED_FORMATS,
    }


@app.post("/api/inspect-media")
async def api_inspect_media(file: UploadFile = File(...)):
    """Deeply inspects any video, audio, image, PDF, or document file and returns stream telemetry."""
    filename = safe_filename(file.filename, "file.dat")
    data = await read_upload(file)
    tmp_dir = Path(tempfile.mkdtemp(prefix="vert_insp_"))
    try:
        tmp_path = tmp_dir / filename
        tmp_path.write_bytes(data)
        telemetry = await inspect_file_metadata(tmp_path, filename)
        return JSONResponse(telemetry)
    except HTTPException:
        raise
    except Exception as e:
        raise conversion_error("Media inspection", e)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/api/pdf-merge")
async def api_pdf_merge(files: List[UploadFile] = File(...)):
    """Merges multiple uploaded PDF files into a single unified PDF."""
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files are required for merging.")
    tmp_dir = Path(tempfile.mkdtemp(prefix="vert_merge_"))
    logs: List[str] = []
    try:
        pdf_paths = []
        for idx, f in enumerate(files):
            fname = safe_filename(f.filename, f"doc_{idx}.pdf")
            p = tmp_dir / f"{idx:03d}_{fname}"
            p.write_bytes(await read_upload(f))
            pdf_paths.append(p)

        out_path = tmp_dir / "merged_document.pdf"
        await merge_pdfs(pdf_paths, out_path, logs)
        out_bytes = out_path.read_bytes()
        (OUT_DIR / "merged_document.pdf").write_bytes(out_bytes)

        return Response(
            content=out_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="merged_document.pdf"',
                "X-Converted-File": "merged_document.pdf",
                "X-Converted-Size": str(len(out_bytes)),
                "Access-Control-Expose-Headers": "Content-Disposition, X-Converted-File, X-Converted-Size",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise conversion_error("PDF merge", e)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/api/pdf-split")
async def api_pdf_split(
    file: UploadFile = File(...),
    page_range: str = Form("all")
):
    """Splits a PDF or extracts specific page ranges."""
    filename = safe_filename(file.filename, "document.pdf")
    data = await read_upload(file)
    tmp_dir = Path(tempfile.mkdtemp(prefix="vert_split_"))
    logs: List[str] = []
    try:
        in_path = tmp_dir / filename
        in_path.write_bytes(data)
        out_file, out_name, route = await split_pdf(in_path, page_range, tmp_dir, logs)
        out_bytes = out_file.read_bytes()
        out_name = safe_filename(out_name, "document_split.pdf")
        safe_output_path(OUT_DIR, out_name).write_bytes(out_bytes)

        media_type = "application/zip" if out_name.endswith(".zip") else "application/pdf"
        return Response(
            content=out_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{out_name}"',
                "X-Converted-File": out_name,
                "X-Converted-Size": str(len(out_bytes)),
                "Access-Control-Expose-Headers": "Content-Disposition, X-Converted-File, X-Converted-Size",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise conversion_error("PDF split", e)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/api/convert-markdown")
async def api_convert_markdown(
    files: List[UploadFile] = File(...),
    add_frontmatter: bool = Form(False),
):
    """
    Anything -> Markdown (incorporates Microsoft MarkItDown + Tesseract OCR + Image Extraction).
    Saves converted files and extracted images to output directory on host.
    """
    results = []
    taken: set[str] = set()

    for f in files:
        filename = safe_filename(f.filename, "document.txt")
        data = await read_upload(f)
        try:
            md, assets = convert_bytes_to_markdown_with_assets(data, filename)
            stem = Path(filename).stem
            words = md.split()
            word_count = len(words)
            est_reading_time = f"{max(1, math.ceil(word_count / 200))} min read" if word_count else "1 min read"

            if add_frontmatter:
                now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
                fm = f"""---
title: "{stem}"
date: "{now_iso}"
words: {word_count}
characters: {len(md)}
reading_time: "{est_reading_time}"
figures_extracted: {len(assets)}
engine: "Better VERT Universal Engine"
---

"""
                md = fm + md

            out_name = unique_name(filename, taken, "md")
            (OUT_DIR / out_name).write_text(md, encoding="utf-8")

            if assets:
                img_dir = OUT_DIR / "images"
                img_dir.mkdir(parents=True, exist_ok=True)
                for asset_name, asset_bytes in assets:
                    safe_output_path(img_dir, asset_name, "figure.png").write_bytes(asset_bytes)

            results.append(
                {
                    "name": filename,
                    "out": out_name,
                    "ok": True,
                    "chars": len(md),
                    "words": word_count,
                    "reading_time": est_reading_time,
                    "markdown": md,
                    "images_count": len(assets),
                }
            )
        except Exception as e:
            logger.exception(f"Error converting {filename} to markdown")
            results.append(
                {
                    "name": filename,
                    "ok": False,
                    "error": f"{type(e).__name__}: {e}",
                }
            )

    return JSONResponse({"results": results})


@app.post("/api/convert-markdown-zip")
async def api_convert_markdown_zip(files: List[UploadFile] = File(...)):
    """Converts uploaded files to Markdown and bundles them with all extracted images into a zip archive."""
    buf = io.BytesIO()
    taken: set[str] = set()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            filename = safe_filename(f.filename, "file.txt")
            data = await read_upload(f)
            try:
                md, assets = convert_bytes_to_markdown_with_assets(data, filename)
                out_name = unique_name(filename, taken, "md")
                z.writestr(out_name, md)
                for asset_name, asset_bytes in assets:
                    z.writestr(f"images/{safe_filename(asset_name, 'figure.png')}", asset_bytes)
            except Exception as e:
                md = f"<!-- Conversion failed: {type(e).__name__}: {e} -->\n"
                z.writestr(unique_name(filename, taken, "md"), md)

    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="better_vert_markdown.zip"'},
    )


@app.get("/api/formats-catalog")
def get_formats_catalog():
    """Returns comprehensive format catalogue with categories and cross-medium routes."""
    return {
        "categories": SUPPORTED_FORMATS,
        "cross_routes": [
            {
                "id": "pdf_storyboard",
                "label": "PDF Storyboard",
                "badge": "Video ➔ PDF",
                "from_cat": "video",
                "to_cat": "document",
                "description": "TrueType styled multi-page PDF storyboard with video telemetry and adaptive keyframes"
            },
            {
                "id": "waveform_video",
                "label": "Waveform Video (MP4)",
                "badge": "Audio ➔ Video",
                "from_cat": "audio",
                "to_cat": "video",
                "description": "Peak-to-peak neon audio waveform visualizer video (1280x720 30fps with Web FastStart)"
            },
            {
                "id": "transcript_md",
                "label": "Speech Transcript (MD)",
                "badge": "Audio ➔ Markdown",
                "from_cat": "audio",
                "to_cat": "document",
                "description": "Automatic speech recognition and deep audio telemetry transcript"
            },
            {
                "id": "images_zip",
                "label": "Extracted Images & Pages (.ZIP)",
                "badge": "Doc/MD ➔ Images ZIP",
                "from_cat": "document",
                "to_cat": "image",
                "description": "200 DPI vector clarity page rasterization and full embedded figure extraction"
            },
            {
                "id": "svg",
                "label": "Vector Graphic (SVG)",
                "badge": "Image ➔ SVG",
                "from_cat": "image",
                "to_cat": "image",
                "description": "Potrace vectorization and luminance bezier path tracing"
            },
            {
                "id": "gif",
                "label": "High-FPS GIF",
                "badge": "Video ➔ GIF",
                "from_cat": "video",
                "to_cat": "image",
                "description": "2-pass palette-optimized Lanczos Bayer dither animation"
            },
            {
                "id": "xlsx",
                "label": "Excel Workbook (XLSX)",
                "badge": "Data ➔ XLSX",
                "from_cat": "data",
                "to_cat": "data",
                "description": "Structured multi-column spreadsheet workbook"
            }
        ]
    }


@app.post("/api/convert-universal")
async def api_convert_universal(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    crf: Optional[int] = Form(None),
    resolution: Optional[str] = Form(None),
    video_codec: Optional[str] = Form(None),
    audio_bitrate: Optional[str] = Form(None),
    fps: Optional[str] = Form(None),
    quality: Optional[int] = Form(None),
    trim_start: Optional[str] = Form(None),
    trim_duration: Optional[str] = Form(None),
    loudnorm: bool = Form(False),
    audio_channels: Optional[str] = Form(None),
    playback_speed: Optional[str] = Form(None),
    color_filter: Optional[str] = Form(None),
    dpi: Optional[int] = Form(200),
):
    """
    Universal 250+ format conversion (video, audio, image, document, data, cross-medium).
    Multi-threaded FFmpeg/ImageMagick with advanced encoding controls.
    """
    filename = safe_filename(file.filename, "file.dat")
    data = await read_upload(file)
    try:
        converted_bytes, out_name, route, logs = await convert_media(
            input_bytes=data,
            input_filename=filename,
            target_format=target_format,
            crf=crf,
            resolution=resolution,
            video_codec=video_codec,
            audio_bitrate=audio_bitrate,
            fps=fps,
            quality=quality,
            trim_start=trim_start,
            trim_duration=trim_duration,
            loudnorm=loudnorm,
            audio_channels=audio_channels,
            playback_speed=playback_speed,
            color_filter=color_filter,
            dpi=dpi,
        )
        out_name = safe_filename(out_name, "converted.dat")
        safe_output_path(OUT_DIR, out_name).write_bytes(converted_bytes)

        return Response(
            content=converted_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{out_name}"',
                "X-Converted-File": out_name,
                "X-Converted-Size": str(len(converted_bytes)),
                "X-Conversion-Route": urllib.parse.quote(route),
                "X-Conversion-Logs": urllib.parse.quote(json.dumps(logs)),
                "Access-Control-Expose-Headers": "Content-Disposition, X-Converted-File, X-Converted-Size, X-Conversion-Route, X-Conversion-Logs",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise conversion_error("Universal conversion", e)


@app.post("/api/convert-universal-batch")
async def api_convert_universal_batch(
    files: List[UploadFile] = File(...),
    target_format: str = Form(...),
    crf: Optional[int] = Form(None),
    resolution: Optional[str] = Form(None),
    video_codec: Optional[str] = Form(None),
    audio_bitrate: Optional[str] = Form(None),
    fps: Optional[str] = Form(None),
    quality: Optional[int] = Form(None),
    trim_start: Optional[str] = Form(None),
    trim_duration: Optional[str] = Form(None),
    loudnorm: bool = Form(False),
    audio_channels: Optional[str] = Form(None),
    playback_speed: Optional[str] = Form(None),
    color_filter: Optional[str] = Form(None),
    dpi: Optional[int] = Form(200),
):
    """
    Multi-file batch conversion.
    Converts all uploaded files to target_format, saves to /data/output,
    and returns a downloadable .ZIP archive with all converted files and a manifest.
    """
    buf = io.BytesIO()
    manifest = []

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            fname = safe_filename(f.filename, "file.dat")
            data = await read_upload(f)
            try:
                converted_bytes, out_name, route, logs = await convert_media(
                    input_bytes=data,
                    input_filename=fname,
                    target_format=target_format,
                    crf=crf,
                    resolution=resolution,
                    video_codec=video_codec,
                    audio_bitrate=audio_bitrate,
                    fps=fps,
                    quality=quality,
                )
                out_name = safe_filename(out_name, "converted.dat")
                safe_output_path(OUT_DIR, out_name).write_bytes(converted_bytes)
                z.writestr(out_name, converted_bytes)
                manifest.append({
                    "original": fname,
                    "converted": out_name,
                    "size_bytes": len(converted_bytes),
                    "route": route,
                    "status": "success",
                })
            except Exception as e:
                logger.exception(f"Batch conversion failed for {fname}")
                manifest.append({
                    "original": fname,
                    "error": str(e),
                    "status": "failed",
                })

        z.writestr("conversion_manifest.json", json.dumps(manifest, indent=2))

    buf.seek(0)
    zip_filename = f"better_vert_batch_{target_format}.zip"
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "X-Converted-File": zip_filename,
            "Access-Control-Expose-Headers": "Content-Disposition, X-Converted-File",
        },
    )


@app.post("/api/batch-convert")
async def api_batch_convert():
    """
    Batch-converts everything currently in /data/input into /data/output as Markdown.
    Matches convert.sh behavior.
    """
    processed = []
    failed = []
    taken: set[str] = set()

    for item in IN_DIR.rglob("*"):
        if not item.is_file() or item.name.startswith("."):
            continue
        try:
            data = item.read_bytes()
            md = convert_bytes_to_markdown(data, item.name)
            out_name = unique_name(item.name, taken, "md")
            (OUT_DIR / out_name).write_text(md, encoding="utf-8")
            processed.append({"input": item.name, "output": out_name, "chars": len(md)})
        except Exception as e:
            failed.append({"input": item.name, "error": str(e)})

    return JSONResponse({
        "status": "completed",
        "processed_count": len(processed),
        "failed_count": len(failed),
        "processed": processed,
        "failed": failed,
    })


@app.get("/api/batch-status")
def api_batch_status():
    """Lists files currently in input and output directories."""
    input_files = [f.name for f in IN_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    output_files = [
        {"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime}
        for f in OUT_DIR.iterdir()
        if f.is_file() and not f.name.startswith(".")
    ]
    return {
        "input_count": len(input_files),
        "input_files": input_files,
        "output_count": len(output_files),
        "output_files": sorted(output_files, key=lambda x: x["modified"], reverse=True),
    }


@app.get("/api/version")
def api_version():
    return {"version": "2.0.0", "name": "Better VERT"}


# Mount static frontend files
FRONTEND_DIR = Path("/app/frontend")
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.api_route("/", methods=["GET", "HEAD"])
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse("<h1>Better VERT Backend is Running</h1>")
