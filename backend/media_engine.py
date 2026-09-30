"""
High-Performance Universal & Cross-Medium Media Engine.
Optimized for Studio-Grade Professional Architecture & Terminal Console Output.

Handles:
- Video -> Video (H.264, HEVC, VP9, Lanczos 2-Pass GIF)
- Audio -> Audio (MP3, WAV, AAC, FLAC, Opus, Ogg, M4A)
- Video -> Audio (Direct multi-threaded stream extraction)
- Video -> PDF Storyboard (FFmpeg keyframe sampling + Pillow grid assembler)
- Audio -> Waveform Video (FFmpeg showwaves visualizer MP4/WebM)
- PDF -> Images (PNG/JPG/WebP/ZIP multi-page extraction via pdftoppm)
- Images -> PDF (Multi-page document canvas)
- Image -> Vector SVG (ImageMagick vectorization)
- Data Cross-Conversion (JSON <-> CSV <-> YAML <-> XML <-> TSV <-> Markdown Table)
- Code / Text -> PDF / HTML / Markdown
- Media -> Speech Transcript & Audio Telemetry Markdown
"""

import asyncio
import base64
import csv
import io
import json
import logging
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("better-vert.media_engine")

SUPPORTED_FORMATS: Dict[str, List[str]] = {
    "video": [
        "mp4", "mkv", "webm", "mov", "avi", "gif", "av1", "wmv", "flv", "m4v",
        "ts", "mts", "m2ts", "vob", "ogv", "3gp", "asf"
    ],
    "audio": [
        "mp3", "wav", "aac", "flac", "m4a", "m4b", "ogg", "opus", "wma", "aiff",
        "alac", "ac3", "caf", "mp2", "aif"
    ],
    "image": [
        "png", "jpg", "jpeg", "webp", "avif", "gif", "tiff", "bmp", "ico", "svg"
    ],
    "document": [
        "pdf", "docx", "md", "html", "epub", "txt", "rtf", "odt"
    ],
    "data": [
        "json", "csv", "yaml", "yml", "xml", "tsv", "xlsx"
    ],
    "cross": [
        "pdf_storyboard", "waveform_video", "images_zip", "transcript_md"
    ]
}

VIDEO_ENCODER_MAP = {
    "mp4": ["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k"],
    "mkv": ["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"],
    "webm": ["-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0", "-row-mt", "1", "-deadline", "good", "-cpu-used", "2", "-c:a", "libopus", "-b:a", "128k"],
    "mov": ["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k"],
    "avi": ["-c:v", "mpeg4", "-qscale:v", "3", "-c:a", "mp3", "-b:a", "192k"],
    "av1": ["-c:v", "libsvtav1", "-preset", "8", "-crf", "30", "-pix_fmt", "yuv420p", "-c:a", "libopus", "-b:a", "128k", "-f", "mp4"],
    "m4v": ["-c:v", "libx264", "-preset", "fast", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k"],
    "wmv": ["-c:v", "wmv2", "-b:v", "2000k", "-c:a", "wmav2", "-b:a", "160k"],
    "flv": ["-c:v", "flv1", "-qscale:v", "3", "-c:a", "mp3", "-b:a", "128k", "-ar", "44100"],
    "3gp": ["-s", "352x288", "-c:v", "h263", "-r", "15", "-c:a", "aac", "-b:a", "64k", "-ar", "32000"],
    "ts": ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "192k"],
    "mts": ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "192k"],
    "m2ts": ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "192k"],
    "vob": ["-c:v", "mpeg2video", "-qscale:v", "2", "-c:a", "mp2", "-b:a", "192k"],
    "asf": ["-c:v", "wmv2", "-b:v", "2000k", "-c:a", "wmav2", "-b:a", "160k"],
    "ogv": ["-c:v", "libtheora", "-qscale:v", "6", "-c:a", "libvorbis", "-qscale:a", "4"],
}

AUDIO_ENCODER_MAP = {
    "mp3": ["-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100"],
    "wav": ["-c:a", "pcm_s16le", "-ar", "44100"],
    "aac": ["-c:a", "aac", "-b:a", "192k", "-ar", "44100"],
    "flac": ["-c:a", "flac", "-compression_level", "5"],
    "m4a": ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-ar", "44100"],
    "m4b": ["-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-ar", "44100"],
    "ogg": ["-c:a", "libvorbis", "-q:a", "4"],
    "opus": ["-c:a", "libopus", "-b:a", "128k", "-vbr", "on"],
    "aiff": ["-c:a", "pcm_s16be"],
    "aif": ["-c:a", "pcm_s16be"],
    "wma": ["-c:a", "wmav2", "-b:a", "160k"],
    "ac3": ["-c:a", "ac3", "-b:a", "384k", "-ar", "48000"],
    "alac": ["-c:a", "alac", "-f", "ipod"],
    "caf": ["-c:a", "alac"],
    "mp2": ["-c:a", "mp2", "-b:a", "192k", "-ar", "44100"],
}

CODE_EXTENSIONS = {
    "py", "js", "ts", "jsx", "tsx", "html", "css", "json", "yaml", "yml",
    "xml", "sql", "sh", "bash", "zsh", "c", "cpp", "h", "hpp", "rs", "go",
    "java", "kt", "swift", "rb", "php", "r", "lua", "dockerfile", "toml"
}


def log_entry(logs: List[str], token: str, message: str) -> None:
    """Formats a log entry with standard ISO millisecond timestamp and token."""
    now_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    logs.append(f"[{now_str}] [{token.upper()}] {message}")


def get_category(ext: str) -> str:
    ext = ext.lstrip(".").lower()
    if ext in ["pdf_storyboard", "waveform_video", "images_zip", "transcript_md"]:
        return "cross"
    for cat, formats in SUPPORTED_FORMATS.items():
        if ext in formats:
            return cat
    if ext in CODE_EXTENSIONS or ext in ["txt", "log"]:
        return "document"
    return "other"


def format_duration(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


async def probe_media_metadata(file_path: Path) -> Dict[str, Any]:
    """Uses ffprobe to extract rich media stream telemetry."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_streams", "-show_format",
        "-of", "json",
        str(file_path)
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    info: Dict[str, Any] = {
        "duration": 0.0,
        "width": 0,
        "height": 0,
        "video_codec": "",
        "fps": 0.0,
        "audio_codec": "",
        "sample_rate": 0,
        "channels": 0,
        "bit_rate": 0,
    }
    try:
        data = json.loads(stdout.decode())
        fmt = data.get("format", {})
        if "duration" in fmt:
            info["duration"] = float(fmt["duration"])
        if "bit_rate" in fmt:
            info["bit_rate"] = int(fmt["bit_rate"])

        for s in data.get("streams", []):
            stype = s.get("codec_type")
            disp = s.get("disposition", {})
            is_pic = disp.get("attached_pic") == 1 or disp.get("timed_thumbnails") == 1
            if stype == "video" and not is_pic and not info["video_codec"]:
                info["video_codec"] = s.get("codec_name", "")
                info["width"] = int(s.get("width", 0))
                info["height"] = int(s.get("height", 0))
                rf = s.get("r_frame_rate", "0/1")
                if "/" in rf:
                    num, den = rf.split("/")
                    info["fps"] = round(float(num) / float(den), 2) if float(den) != 0 else 0.0
            elif stype == "audio" and not info["audio_codec"]:
                info["audio_codec"] = s.get("codec_name", "")
                info["sample_rate"] = int(s.get("sample_rate", 0))
                info["channels"] = int(s.get("channels", 0))
    except Exception as e:
        logger.debug(f"ffprobe parse error: {e}")
    return info


async def get_media_duration(file_path: Path) -> float:
    meta = await probe_media_metadata(file_path)
    return meta.get("duration", 0.0)


async def has_audio_stream(file_path: Path) -> bool:
    meta = await probe_media_metadata(file_path)
    return bool(meta.get("audio_codec"))


async def has_moving_video_stream(file_path: Path) -> bool:
    """Returns True if the file contains a genuine moving video track (not just attached_pic / album cover art)."""
    meta = await probe_media_metadata(file_path)
    return bool(meta.get("video_codec"))


async def inspect_file_metadata(file_path: Path, filename: str) -> Dict[str, Any]:
    """
    Comprehensive media, document, and image inspector.
    Combines ffprobe, poppler pdfinfo, Pillow, and document structure analysis.
    """
    stat = file_path.stat()
    ext = file_path.suffix.lstrip(".").lower()
    cat = get_category(ext)
    size_bytes = stat.st_size

    if size_bytes > 1024 * 1024 * 1024:
        size_fmt = f"{size_bytes / (1024**3):.2f} GB"
    elif size_bytes > 1024 * 1024:
        size_fmt = f"{size_bytes / (1024**2):.2f} MB"
    elif size_bytes > 1024:
        size_fmt = f"{size_bytes / 1024:.1f} KB"
    else:
        size_fmt = f"{size_bytes} B"

    telemetry: Dict[str, Any] = {
        "filename": filename,
        "size_bytes": size_bytes,
        "size_formatted": size_fmt,
        "category": cat,
        "extension": ext,
        "general": {},
        "video_streams": [],
        "audio_streams": [],
        "subtitle_streams": [],
        "pdf_info": {},
        "image_info": {},
        "document_stats": {},
    }

    # 1. FFprobe for Video & Audio
    if cat in ["video", "audio"] or ext in ["mp4", "mkv", "mov", "webm", "avi", "flv", "wmv", "mp3", "wav", "m4a", "flac", "ogg", "opus", "m4b", "aac"]:
        try:
            cmd = ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(file_path)]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                data = json.loads(stdout.decode(errors="ignore"))
                fmt = data.get("format", {})
                telemetry["general"] = {
                    "format_name": fmt.get("format_long_name", fmt.get("format_name", "")),
                    "duration": round(float(fmt.get("duration", 0)), 2),
                    "duration_formatted": format_duration(float(fmt.get("duration", 0))),
                    "bit_rate": int(fmt.get("bit_rate", 0)),
                    "bit_rate_formatted": f"{int(fmt.get('bit_rate', 0)) // 1000} kbps" if fmt.get("bit_rate") else "N/A",
                    "stream_count": int(fmt.get("nb_streams", 0)),
                }
                for s in data.get("streams", []):
                    stype = s.get("codec_type")
                    disp = s.get("disposition", {})
                    is_pic = disp.get("attached_pic") == 1 or disp.get("timed_thumbnails") == 1
                    if stype == "video" and not is_pic:
                        rf = s.get("r_frame_rate", "0/1")
                        fps_val = 0.0
                        if "/" in rf:
                            n, d = rf.split("/")
                            fps_val = round(float(n) / float(d), 2) if float(d) != 0 else 0.0
                        telemetry["video_streams"].append({
                            "index": s.get("index"),
                            "codec": s.get("codec_name", "").upper(),
                            "codec_long": s.get("codec_long_name", ""),
                            "profile": s.get("profile", ""),
                            "resolution": f"{s.get('width', 0)}x{s.get('height', 0)}",
                            "width": s.get("width", 0),
                            "height": s.get("height", 0),
                            "fps": fps_val,
                            "pixel_format": s.get("pix_fmt", ""),
                            "aspect_ratio": s.get("display_aspect_ratio", s.get("sample_aspect_ratio", "")),
                            "bit_rate": int(s.get("bit_rate", 0)) if s.get("bit_rate") else None,
                        })
                    elif stype == "audio":
                        telemetry["audio_streams"].append({
                            "index": s.get("index"),
                            "codec": s.get("codec_name", "").upper(),
                            "codec_long": s.get("codec_long_name", ""),
                            "sample_rate": int(s.get("sample_rate", 0)),
                            "sample_rate_formatted": f"{int(s.get('sample_rate', 0)):,} Hz",
                            "channels": int(s.get("channels", 0)),
                            "channel_layout": s.get("channel_layout", "stereo" if s.get("channels") == 2 else "mono"),
                            "bit_rate": int(s.get("bit_rate", 0)) if s.get("bit_rate") else None,
                        })
                    elif stype == "subtitle":
                        telemetry["subtitle_streams"].append({
                            "index": s.get("index"),
                            "codec": s.get("codec_name", "").upper(),
                            "language": s.get("tags", {}).get("language", "und"),
                            "title": s.get("tags", {}).get("title", ""),
                        })
        except Exception as e:
            logger.debug(f"ffprobe telemetry error: {e}")

    # 2. PDF Inspector
    if ext == "pdf" and shutil.which("pdfinfo"):
        try:
            cmd = ["pdfinfo", str(file_path)]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                pdict = {}
                for line in stdout.decode(errors="ignore").splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        pdict[k.strip().lower().replace(" ", "_")] = v.strip()
                telemetry["pdf_info"] = {
                    "title": pdict.get("title", "Untitled"),
                    "author": pdict.get("author", "Unknown"),
                    "pages": int(pdict.get("pages", 1)) if pdict.get("pages", "").isdigit() else 1,
                    "page_size": pdict.get("page_size", "Letter"),
                    "encrypted": pdict.get("encrypted", "no"),
                    "producer": pdict.get("producer", ""),
                    "creator": pdict.get("creator", ""),
                    "pdf_version": pdict.get("pdf_version", "1.4"),
                }
        except Exception as e:
            logger.debug(f"pdfinfo error: {e}")

    # 3. Image Inspector
    if cat == "image" or ext in ["png", "jpg", "jpeg", "webp", "avif", "gif", "tiff", "bmp", "svg", "ico"]:
        try:
            with Image.open(file_path) as im:
                telemetry["image_info"] = {
                    "format": (im.format or ext).upper(),
                    "dimensions": f"{im.width} × {im.height} px",
                    "width": im.width,
                    "height": im.height,
                    "aspect_ratio": f"{im.width / max(1, im.height):.2f}:1",
                    "color_mode": im.mode,
                    "is_animated": getattr(im, "is_animated", False),
                    "frame_count": getattr(im, "n_frames", 1),
                    "dpi": im.info.get("dpi", (72, 72)),
                }
        except Exception as e:
            logger.debug(f"Pillow image inspect error: {e}")

    # 4. Document / Code Inspector
    if cat in ["document", "data"] or ext in ["md", "markdown", "txt", "py", "js", "ts", "json", "csv", "xml", "yaml", "yml", "html", "css"]:
        try:
            txt = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = txt.splitlines()
            words = txt.split()
            telemetry["document_stats"] = {
                "lines": len(lines),
                "words": len(words),
                "characters": len(txt),
                "reading_time_mins": round(len(words) / 200, 1) if words else 0.1,
            }
        except Exception as e:
            logger.debug(f"Document stats error: {e}")

    # Top-level convenience keys for instant frontend consumption
    telemetry["format"] = telemetry["general"].get("format_name") or telemetry["image_info"].get("format") or ext.upper()
    telemetry["duration"] = telemetry["general"].get("duration")
    telemetry["pages"] = telemetry["pdf_info"].get("pages")
    telemetry["words"] = telemetry["document_stats"].get("words")
    combined_streams = []
    for s in telemetry["video_streams"]:
        combined_streams.append({"type": "video", **s})
    for s in telemetry["audio_streams"]:
        combined_streams.append({"type": "audio", **s})
    for s in telemetry["subtitle_streams"]:
        combined_streams.append({"type": "subtitle", **s})
    telemetry["streams"] = combined_streams

    return telemetry


# ---------------------------------------------------------------------------
# Cross-Medium Handlers
# ---------------------------------------------------------------------------

def get_storyboard_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidate_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


async def handle_video_to_storyboard_pdf(
    in_path: Path,
    out_path: Path,
    in_stem: str,
    logs: List[str]
) -> str:
    route = "Video (FFmpeg Keyframe Sampler) ➔ TrueType Canvas Compositor ➔ PDF Storyboard"
    log_entry(logs, "ROUTE", route)
    log_entry(logs, "INFO", "Probing video stream duration, dimensions, and codec telemetry...")

    meta = await probe_media_metadata(in_path)
    duration = meta.get("duration", 0.0)
    if duration <= 0:
        duration = 10.0
    width = meta.get("width", 0)
    height = meta.get("height", 0)
    fps = meta.get("fps", 0.0)
    vcodec = meta.get("video_codec", "video").upper()
    acodec = meta.get("audio_codec", "none").upper()

    log_entry(logs, "INFO", f"Stream Telemetry: {width}x{height} @ {fps:.1f} FPS, Codecs: {vcodec}/{acodec}, Duration: {format_duration(duration)}")

    num_frames = 12 if duration >= 12 else max(4, int(duration))
    frames_dir = in_path.parent / "storyboard_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Adaptive distribution: sample from 5% to 95% of duration to bypass dark intro/outro clips
    start_sec = duration * 0.05
    end_sec = duration * 0.95
    step = (end_sec - start_sec) / max(1, num_frames - 1) if num_frames > 1 else 0

    log_entry(logs, "EXEC", f"Extracting {num_frames} balanced keyframes across {start_sec:.1f}s - {end_sec:.1f}s timeline...")
    frame_files: List[Tuple[float, Path]] = []

    for i in range(num_frames):
        ts = start_sec + (i * step)
        frame_file = frames_dir / f"frame_{i:03d}.jpg"
        cmd = [
            "ffmpeg", "-y", "-ss", f"{ts:.2f}",
            "-i", str(in_path),
            "-frames:v", "1",
            "-q:v", "2",
            "-vf", "scale=720:-1",
            str(frame_file)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if frame_file.exists() and frame_file.stat().st_size > 0:
            frame_files.append((ts, frame_file))

    if not frame_files:
        raise RuntimeError("Failed to extract any valid video keyframes for storyboard.")

    log_entry(logs, "INFO", f"Sampled {len(frame_files)} high-clarity keyframes. Rendering A4 dark-studio sheets...")

    PAGE_W, PAGE_H = 1240, 1754
    BG_COLOR = (11, 15, 25)
    HEADER_BG = (15, 23, 42)
    ACCENT_COLOR = (99, 102, 241)
    CARD_BG = (22, 28, 45)
    BORDER_COLOR = (45, 55, 78)
    TEXT_MAIN = (241, 245, 249)
    TEXT_MUTED = (148, 163, 184)
    TEXT_ACCENT = (129, 140, 248)

    font_title = get_storyboard_font(22, bold=True)
    font_badge = get_storyboard_font(12, bold=True)
    font_meta = get_storyboard_font(13, bold=False)
    font_card = get_storyboard_font(13, bold=True)

    pages: List[Image.Image] = []
    frames_per_page = 6
    cols, rows = 2, 3
    margin_x, margin_y = 60, 130
    gap_x, gap_y = 36, 46

    card_w = (PAGE_W - 2 * margin_x - (cols - 1) * gap_x) // cols
    card_h = (PAGE_H - margin_y - 120 - (rows - 1) * gap_y) // rows
    total_pages = math.ceil(len(frame_files) / frames_per_page)

    for page_idx in range(total_pages):
        page_img = Image.new("RGB", (PAGE_W, PAGE_H), BG_COLOR)
        draw = ImageDraw.Draw(page_img)

        # Header bar
        draw.rectangle([(0, 0), (PAGE_W, 84)], fill=HEADER_BG)
        draw.rectangle([(0, 82), (PAGE_W, 84)], fill=ACCENT_COLOR)

        title_text = f"VIDEO STORYBOARD · {in_stem.upper()}"
        draw.text((margin_x, 20), title_text, fill=TEXT_MAIN, font=font_title)

        telemetry_str = f"{width}x{height} · {fps:.1f} FPS · {vcodec} · {acodec} · {format_duration(duration)} · Page {page_idx + 1}/{total_pages}"
        draw.text((margin_x, 52), telemetry_str, fill=TEXT_ACCENT, font=font_meta)

        batch_frames = frame_files[page_idx * frames_per_page : (page_idx + 1) * frames_per_page]

        for idx, (ts, fpath) in enumerate(batch_frames):
            col = idx % cols
            row = idx // cols
            x = margin_x + col * (card_w + gap_x)
            y = margin_y + row * (card_h + gap_y)

            # Card background and border
            draw.rectangle([(x, y), (x + card_w, y + card_h)], fill=CARD_BG, outline=BORDER_COLOR, width=1)

            # Draw keyframe image
            try:
                with Image.open(fpath) as raw_frame:
                    thumb = raw_frame.convert("RGB")
                    thumb.thumbnail((card_w - 18, card_h - 48), Image.Resampling.LANCZOS)
                    paste_x = x + (card_w - thumb.width) // 2
                    paste_y = y + 10
                    page_img.paste(thumb, (paste_x, paste_y))
            except Exception as e:
                logger.warning(f"Error drawing frame thumbnail: {e}")

            # Bottom timecode bar
            frame_num = page_idx * frames_per_page + idx + 1
            ts_badge = f"Frame {frame_num:02d} · {format_duration(ts)}"
            draw.rectangle([(x + 12, y + card_h - 30), (x + card_w - 12, y + card_h - 10)], fill=(15, 23, 42))
            draw.text((x + 20, y + card_h - 28), ts_badge, fill=TEXT_MUTED, font=font_card)

        # Footer
        footer_text = f"Better VERT Universal Engine · TrueType Vector PDF · Page {page_idx + 1} of {total_pages}"
        draw.text((margin_x, PAGE_H - 45), footer_text, fill=(71, 85, 105), font=font_badge)

        pages.append(page_img)

    pages[0].save(str(out_path), "PDF", resolution=150.0, save_all=True, append_images=pages[1:])
    log_entry(logs, "DONE", f"Storyboard PDF compiled: {out_path.name} ({out_path.stat().st_size:,} bytes, {total_pages} pages).")
    return route


async def handle_video_to_gif(
    in_path: Path,
    out_path: Path,
    fps_val: Optional[str],
    resolution_val: Optional[str],
    logs: List[str],
    trim_start: Optional[str] = None,
    trim_duration: Optional[str] = None,
) -> str:
    route = "Video ➔ Lanczos Downsampler ➔ 2-Pass PaletteGen & Bayer Dither ➔ High-Fidelity GIF"
    log_entry(logs, "ROUTE", route)

    target_fps = int(fps_val) if fps_val and str(fps_val).isdigit() else 12
    scale_expr = "scale=480:-1:flags=lanczos"
    if resolution_val and resolution_val.lower() not in ["original", "none", ""]:
        res_map = {
            "4k": "scale=1920:-1:flags=lanczos",
            "1080p": "scale=1080:-1:flags=lanczos",
            "720p": "scale=720:-1:flags=lanczos",
            "480p": "scale=480:-1:flags=lanczos",
            "360p": "scale=360:-1:flags=lanczos",
        }
        scale_expr = res_map.get(resolution_val.lower(), f"scale={resolution_val}:flags=lanczos")

    log_entry(logs, "EXEC", f"Synthesizing 2-pass palette-optimized GIF at {target_fps} FPS ({scale_expr})...")

    filter_graph = f"[0:v] fps={target_fps},{scale_expr},split [a][b]; [a] palettegen=stats_mode=diff [p]; [b][p] paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle"

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-threads", "0"
    ]
    if trim_start and str(trim_start).strip():
        cmd.extend(["-ss", str(trim_start).strip()])
    cmd.extend(["-i", str(in_path)])
    if trim_duration and str(trim_duration).strip():
        cmd.extend(["-t", str(trim_duration).strip()])
    cmd.extend([
        "-filter_complex", filter_graph,
        "-loop", "0",
        str(out_path)
    ])

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode(errors="replace")
        log_entry(logs, "ERROR", f"FFmpeg GIF generation failed: {err_msg[:200]}")
        raise RuntimeError(f"GIF generation failed: {err_msg[:300]}")

    log_entry(logs, "DONE", f"High-fidelity GIF compiled: {out_path.name} ({out_path.stat().st_size:,} bytes).")
    return route


async def handle_audio_to_waveform_video(
    in_path: Path,
    out_path: Path,
    logs: List[str]
) -> str:
    route = "Audio ➔ FFmpeg Peak-to-Peak Waveform (1280x720 30fps) ➔ H.264 FastStart Video (MP4)"
    log_entry(logs, "ROUTE", route)
    log_entry(logs, "EXEC", "Synthesizing 720p 30fps dual-gradient neon audio waveform...")

    filtergraph = "[0:a]showwaves=s=1280x720:mode=p2p:colors=0x6366f1|0x06b6d4:rate=30,format=yuv420p[v]"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-threads", "0",
        "-i", str(in_path),
        "-filter_complex", filtergraph,
        "-map", "[v]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "aac",
        "-b:a", "256k",
        "-movflags", "+faststart",
        "-shortest",
        str(out_path)
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode(errors="replace")
        log_entry(logs, "ERROR", f"FFmpeg showwaves failed: {err_msg[:200]}")
        raise RuntimeError(f"Waveform video generation failed: {err_msg[:300]}")

    log_entry(logs, "DONE", f"Waveform video synthesized: {out_path.name} ({out_path.stat().st_size:,} bytes).")
    return route


async def handle_document_to_images(
    in_path: Path,
    out_path: Path,
    target_format: str,
    in_stem: str,
    in_ext: str,
    tmp_dir: Path,
    logs: List[str],
    dpi: Optional[int] = 200,
    color_filter: Optional[str] = None,
) -> Tuple[Path, str, str]:
    """
    Renders documents (PDF, MD, DOCX, TXT, HTML) into high-resolution images
    with configurable DPI and color filters, and extracts any embedded raster images/figures into a unified package.
    """
    actual_dpi = int(dpi) if dpi and 72 <= int(dpi) <= 600 else 200
    route = f"Document ({in_ext.upper()}) ➔ Vector Typesetter ➔ Poppler pdftoppm ({actual_dpi} DPI) ➔ {target_format.upper()}"
    log_entry(logs, "ROUTE", route)

    # 1. Determine or compile vector PDF
    if in_ext == "pdf":
        pdf_path = in_path
    else:
        pdf_path = tmp_dir / f"{in_stem}_compiled.pdf"
        log_entry(logs, "EXEC", f"Compiling {in_ext.upper()} document into vector PDF for page rasterization...")
        await handle_document_to_pdf(in_path, pdf_path, in_stem, in_ext, logs)

    # 2. Extract embedded images & figures
    extracted_figures: List[Path] = []

    # 2a. If PDF, extract raw embedded images via pdfimages
    if pdf_path.exists() and shutil.which("pdfimages"):
        img_prefix = tmp_dir / "raw_fig"
        try:
            cmd = ["pdfimages", "-png", str(pdf_path), str(img_prefix)]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            if proc.returncode == 0:
                raw_imgs = sorted(tmp_dir.glob("raw_fig-*.png"))
                for idx, rimg in enumerate(raw_imgs, 1):
                    if rimg.stat().st_size > 100:
                        fig_target = tmp_dir / f"{in_stem}_figure_{idx:02d}.png"
                        shutil.copy(rimg, fig_target)
                        extracted_figures.append(fig_target)
        except Exception as e:
            logger.debug(f"pdfimages extraction warning: {e}")

    # 2b. If Markdown or HTML or TXT, extract inline base64 images
    if in_ext in ["md", "markdown", "html", "htm", "txt"]:
        try:
            text = in_path.read_text(encoding="utf-8", errors="ignore")
            base64_idx = len(extracted_figures) + 1
            for m in re.finditer(r'!\[([^\]]*)\]\(data:image/([a-zA-Z0-9+.-]+);base64,([A-Za-z0-9+/=]+)\)', text):
                fmt = m.group(2).lower()
                b64 = m.group(3)
                try:
                    raw = base64.b64decode(b64)
                    if len(raw) > 50:
                        b64_file = tmp_dir / f"{in_stem}_embedded_{base64_idx:02d}.{fmt}"
                        b64_file.write_bytes(raw)
                        extracted_figures.append(b64_file)
                        base64_idx += 1
                except Exception:
                    pass
            for m in re.finditer(r'<img[^>]+src=[\'"]data:image/([a-zA-Z0-9+.-]+);base64,([A-Za-z0-9+/=]+)[\'"]', text):
                fmt = m.group(1).lower()
                b64 = m.group(2)
                try:
                    raw = base64.b64decode(b64)
                    if len(raw) > 50:
                        b64_file = tmp_dir / f"{in_stem}_embedded_{base64_idx:02d}.{fmt}"
                        b64_file.write_bytes(raw)
                        extracted_figures.append(b64_file)
                        base64_idx += 1
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Base64 image extraction warning: {e}")

    # 2c. If DOCX / PPTX / ODT, extract media files from zip
    if in_ext in ["docx", "pptx", "odt", "epub"] and zipfile.is_zipfile(in_path):
        try:
            with zipfile.ZipFile(in_path, "r") as z:
                zip_idx = len(extracted_figures) + 1
                for item in sorted(z.infolist(), key=lambda x: x.filename):
                    fname = item.filename
                    is_media = any(prefix in fname for prefix in ["word/media/", "ppt/media/", "Pictures/"])
                    has_img_ext = Path(fname).suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]
                    if (is_media or has_img_ext) and item.file_size > 100:
                        ext = Path(fname).suffix.lower().lstrip(".") or "png"
                        img_path = tmp_dir / f"{in_stem}_media_{zip_idx:02d}.{ext}"
                        img_path.write_bytes(z.read(item))
                        extracted_figures.append(img_path)
                        zip_idx += 1
        except Exception as e:
            logger.debug(f"Zip document media extraction warning: {e}")

    # 3. Render PDF pages at actual_dpi vector clarity via pdftoppm
    page_prefix = tmp_dir / "page"
    img_fmt = "png" if target_format in ["png", "images_zip", "zip"] else target_format
    if img_fmt not in ["png", "jpeg", "tiff"]:
        img_fmt = "png"

    cmd = ["pdftoppm", f"-{img_fmt}", "-r", str(actual_dpi), str(pdf_path), str(page_prefix)]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0 and not extracted_figures:
        raise RuntimeError(f"pdftoppm rendering failed: {stderr.decode(errors='replace')[:300]}")

    rendered_pages = sorted(tmp_dir.glob("page-*.png")) + sorted(tmp_dir.glob("page-*.jpg")) + sorted(tmp_dir.glob("page-*.jpeg"))
    log_entry(logs, "INFO", f"Rendered {len(rendered_pages)} pages at {actual_dpi} DPI; extracted {len(extracted_figures)} figures.")

    # Apply color filter if requested (grayscale, sepia, invert, monochrome)
    if color_filter in ["grayscale", "sepia", "invert", "monochrome"]:
        magick_bin = "magick" if shutil.which("magick") else "convert"
        filter_args = []
        if color_filter == "grayscale":
            filter_args = ["-colorspace", "Gray"]
        elif color_filter == "sepia":
            filter_args = ["-sepia-tone", "80%"]
        elif color_filter == "invert":
            filter_args = ["-negate"]
        elif color_filter == "monochrome":
            filter_args = ["-threshold", "50%"]

        for target_img in list(rendered_pages) + list(extracted_figures):
            try:
                proc_cf = await asyncio.create_subprocess_exec(
                    magick_bin, str(target_img), *filter_args, str(target_img)
                )
                await proc_cf.communicate()
            except Exception as cf_err:
                logger.debug(f"Color filter error on {target_img.name}: {cf_err}")
        log_entry(logs, "INFO", f"Applied '{color_filter}' filter to all generated images.")

    # 4. If ZIP target requested, or multi-page / multi-asset
    if target_format in ["images_zip", "zip"] or (len(rendered_pages) + len(extracted_figures) > 1 and out_path.suffix == ".zip"):
        zip_path = tmp_dir / f"{in_stem}_images.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for idx, p in enumerate(rendered_pages, 1):
                ext = p.suffix
                z.write(p, arcname=f"{in_stem}_page_{idx:02d}{ext}")
            for idx, f in enumerate(extracted_figures, 1):
                z.write(f, arcname=f"{f.name}")
        log_entry(logs, "DONE", f"Bundled {len(rendered_pages)} pages and {len(extracted_figures)} extracted figures into {zip_path.name} ({zip_path.stat().st_size:,} bytes).")
        return zip_path, f"{in_stem}_images.zip", route + " ➔ Multi-Asset ZIP"

    # 5. If single image target requested (png, jpg, webp, etc.)
    if rendered_pages:
        first_page = rendered_pages[0]
        out_ext = target_format if target_format in ["png", "jpg", "jpeg", "webp"] else first_page.suffix.lstrip(".")
        final_img_path = tmp_dir / f"{in_stem}.{out_ext}"
        if out_ext == "png" and first_page.suffix.lower() == ".png":
            shutil.copy(first_page, final_img_path)
        else:
            with Image.open(first_page) as im:
                im.convert("RGB").save(str(final_img_path))
        log_entry(logs, "DONE", f"Extracted single page image: {final_img_path.name} ({final_img_path.stat().st_size:,} bytes).")
        return final_img_path, final_img_path.name, route + f" ➔ {out_ext.upper()}"

    if extracted_figures:
        first_fig = extracted_figures[0]
        out_ext = first_fig.suffix.lstrip(".")
        final_img_path = tmp_dir / f"{in_stem}.{out_ext}"
        shutil.copy(first_fig, final_img_path)
        log_entry(logs, "DONE", f"Extracted figure image: {final_img_path.name} ({final_img_path.stat().st_size:,} bytes).")
        return final_img_path, final_img_path.name, route + f" ➔ {out_ext.upper()}"

    raise RuntimeError(f"No pages or images could be extracted from {in_stem}.{in_ext}.")


async def handle_pdf_to_images(
    in_path: Path,
    out_path: Path,
    target_format: str,
    in_stem: str,
    tmp_dir: Path,
    logs: List[str],
    dpi: Optional[int] = 200,
    color_filter: Optional[str] = None,
) -> Tuple[Path, str, str]:
    """Backward compatible wrapper forwarding to handle_document_to_images."""
    return await handle_document_to_images(
        in_path, out_path, target_format, in_stem, "pdf", tmp_dir, logs, dpi=dpi, color_filter=color_filter
    )


async def merge_pdfs(
    pdf_paths: List[Path],
    out_path: Path,
    logs: List[str]
) -> Tuple[Path, str]:
    """Merges multiple PDF files in sequential order using poppler pdfunite."""
    route = "PDF Documents ➔ Poppler pdfunite Engine ➔ Merged PDF Document"
    log_entry(logs, "ROUTE", route)
    log_entry(logs, "EXEC", f"Merging {len(pdf_paths)} PDF documents in sequence...")

    cmd = ["pdfunite"] + [str(p) for p in pdf_paths] + [str(out_path)]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"pdfunite failed: {stderr.decode(errors='replace')[:300]}")

    log_entry(logs, "DONE", f"Successfully merged {len(pdf_paths)} PDFs into {out_path.name} ({out_path.stat().st_size:,} bytes).")
    return out_path, route


async def split_pdf(
    pdf_path: Path,
    page_range: str,
    tmp_dir: Path,
    logs: List[str]
) -> Tuple[Path, str, str]:
    """
    Splits or extracts page ranges from a PDF document using poppler pdfseparate/pdfunite.
    page_range can be:
      - 'all': returns a ZIP archive of all individual page PDFs
      - '1-3': extracts and merges pages 1 to 3 into a single PDF
      - '2': extracts single page 2
    """
    stem = pdf_path.stem
    range_str = (page_range or "all").strip().lower()

    if range_str == "all":
        route = "PDF Document ➔ Poppler pdfseparate ➔ Split Pages ZIP"
        log_entry(logs, "ROUTE", route)
        log_entry(logs, "EXEC", f"Separating all pages from {pdf_path.name}...")

        page_pattern = tmp_dir / f"{stem}_page_%d.pdf"
        cmd = ["pdfseparate", str(pdf_path), str(page_pattern)]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"pdfseparate failed: {stderr.decode(errors='replace')[:300]}")

        pages = sorted(tmp_dir.glob(f"{stem}_page_*.pdf"))
        if not pages:
            raise RuntimeError("No pages could be extracted from PDF.")

        zip_path = tmp_dir / f"{stem}_split_pages.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in pages:
                z.write(p, arcname=p.name)

        log_entry(logs, "DONE", f"Bundled {len(pages)} split pages into {zip_path.name} ({zip_path.stat().st_size:,} bytes).")
        return zip_path, f"{stem}_split_pages.zip", route

    # Specific range extraction
    route = f"PDF Document ➔ Poppler Range Extractor ({range_str}) ➔ Extracted PDF"
    log_entry(logs, "ROUTE", route)

    start_p, end_p = 1, 1
    if "-" in range_str:
        parts = range_str.split("-")
        start_p = max(1, int(parts[0]))
        end_p = max(start_p, int(parts[1]))
    else:
        start_p = max(1, int(range_str))
        end_p = start_p

    log_entry(logs, "EXEC", f"Extracting pages {start_p} to {end_p} from {pdf_path.name}...")
    page_pattern = tmp_dir / f"{stem}_part_%d.pdf"
    cmd = ["pdfseparate", "-f", str(start_p), "-l", str(end_p), str(pdf_path), str(page_pattern)]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"pdfseparate failed: {stderr.decode(errors='replace')[:300]}")

    seps = sorted(tmp_dir.glob(f"{stem}_part_*.pdf"))
    if not seps:
        raise RuntimeError(f"No pages extracted in range {range_str}.")

    if len(seps) == 1:
        out_single = tmp_dir / f"{stem}_page_{start_p}.pdf"
        shutil.copy(seps[0], out_single)
        log_entry(logs, "DONE", f"Extracted single page {start_p}: {out_single.name} ({out_single.stat().st_size:,} bytes).")
        return out_single, out_single.name, route

    out_merged = tmp_dir / f"{stem}_pages_{start_p}-{end_p}.pdf"
    cmd_u = ["pdfunite"] + [str(p) for p in seps] + [str(out_merged)]
    proc_u = await asyncio.create_subprocess_exec(
        *cmd_u, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await proc_u.communicate()
    log_entry(logs, "DONE", f"Extracted and merged pages {start_p}-{end_p} into {out_merged.name} ({out_merged.stat().st_size:,} bytes).")
    return out_merged, out_merged.name, route


async def handle_image_to_svg(
    in_path: Path,
    out_path: Path,
    logs: List[str]
) -> str:
    route = "Raster Image ➔ Potrace Vectorization Engine ➔ Scalable Vector Graphics (SVG)"
    log_entry(logs, "ROUTE", route)
    log_entry(logs, "EXEC", "Extracting high-contrast luminance bitmap for vector tracing...")

    pbm_path = in_path.parent / "trace_input.pbm"
    magick_bin = "magick" if shutil.which("magick") else "convert"

    if shutil.which("potrace"):
        cmd_pbm = [magick_bin, str(in_path), "-flatten", "-threshold", "50%", str(pbm_path)]
        proc_pbm = await asyncio.create_subprocess_exec(
            *cmd_pbm, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await proc_pbm.communicate()

        if pbm_path.exists() and pbm_path.stat().st_size > 0:
            log_entry(logs, "EXEC", "Tracing vector bezier paths with Potrace (arm64)...")
            cmd_potrace = ["potrace", "-s", str(pbm_path), "-o", str(out_path)]
            proc_potrace = await asyncio.create_subprocess_exec(
                *cmd_potrace, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await proc_potrace.communicate()
            if out_path.exists() and out_path.stat().st_size > 0:
                log_entry(logs, "DONE", f"Vector SVG synthesized: {out_path.name} ({out_path.stat().st_size:,} bytes).")
                return route

    # Responsive SVG container fallback
    log_entry(logs, "INFO", "Packaging image in responsive vector SVG container...")
    with Image.open(in_path) as im:
        w, h = im.size
    import base64
    raw_b64 = base64.b64encode(in_path.read_bytes()).decode("ascii")
    mime = "image/png" if in_path.suffix.lower() == ".png" else "image/jpeg"
    svg_data = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <image href="data:{mime};base64,{raw_b64}" width="{w}" height="{h}"/>
</svg>'''
    out_path.write_text(svg_data, encoding="utf-8")
    log_entry(logs, "DONE", f"Responsive SVG generated: {out_path.name} ({out_path.stat().st_size:,} bytes).")
    return route


async def handle_document_to_pdf(
    in_path: Path,
    out_path: Path,
    in_stem: str,
    in_ext: str,
    logs: List[str]
) -> str:
    route = f"Document ({in_ext.upper()}) ➔ ReportLab High-Fidelity Typesetter ➔ PDF Document"
    log_entry(logs, "ROUTE", route)
    log_entry(logs, "INFO", f"Parsing {in_stem}.{in_ext} for PDF layout compilation...")

    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    import html

    # If input is docx, odt, epub, or html, extract clean markdown first via pandoc
    text_content = ""
    is_markdown = in_ext in ["md", "markdown"]
    is_code = in_ext in CODE_EXTENSIONS

    if in_ext in ["docx", "odt", "epub", "html", "htm"]:
        if shutil.which("pandoc"):
            log_entry(logs, "EXEC", f"Running Pandoc to extract Markdown structure from {in_ext.upper()}...")
            cmd = ["pandoc", str(in_path), "-t", "gfm"]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                text_content = stdout.decode("utf-8", errors="replace")
                is_markdown = True

    if not text_content:
        try:
            text_content = in_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text_content = in_path.read_text(encoding="latin-1", errors="replace")

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()

    doc_title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "DocH1",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    h2_style = ParagraphStyle(
        "DocH2",
        parent=styles["Heading3"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=8,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )
    code_style = ParagraphStyle(
        "DocCode",
        parent=styles["Code"],
        fontSize=8,
        leading=10.5,
        fontName="Courier",
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f8fafc"),
        borderColor=colors.HexColor("#e2e8f0"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=8,
    )

    story = [
        Paragraph(html.escape(in_stem.replace("_", " ").title()), doc_title_style),
        Paragraph(f"Source: {html.escape(in_path.name)} · Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Better VERT Universal Engine", meta_style),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#6366f1"), spaceAfter=14),
    ]

    if is_code:
        wrapped_lines = []
        for line in text_content.splitlines():
            while len(line) > 95:
                wrapped_lines.append(line[:95])
                line = "    " + line[95:]
            wrapped_lines.append(line)
        story.append(Preformatted("\n".join(wrapped_lines), code_style))
    else:
        in_code_block = False
        code_block_lines = []

        for line in text_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                if in_code_block:
                    story.append(Preformatted("\n".join(code_block_lines), code_style))
                    code_block_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_block_lines.append(line)
                continue

            if not stripped:
                story.append(Spacer(1, 4))
                continue

            if is_markdown and stripped.startswith("# "):
                h_text = html.escape(stripped[2:].strip())
                story.append(Paragraph(h_text, h1_style))
            elif is_markdown and stripped.startswith("## "):
                h_text = html.escape(stripped[3:].strip())
                story.append(Paragraph(h_text, h2_style))
            elif is_markdown and stripped.startswith("### "):
                h_text = html.escape(stripped[4:].strip())
                story.append(Paragraph(h_text, h2_style))
            elif is_markdown and (stripped.startswith("- ") or stripped.startswith("* ")):
                b_text = html.escape(stripped[2:].strip())
                b_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", b_text)
                b_text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", b_text)
                story.append(Paragraph(f"&bull; {b_text}", body_style))
            elif stripped in ["---", "***", "___"]:
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8, spaceBefore=4))
            else:
                p_text = html.escape(stripped)
                if is_markdown:
                    p_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", p_text)
                    p_text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", p_text)
                    p_text = re.sub(r"`(.*?)`", r"<code>\1</code>", p_text)
                story.append(Paragraph(p_text, body_style))

        if in_code_block and code_block_lines:
            story.append(Preformatted("\n".join(code_block_lines), code_style))

    doc.build(story)
    log_entry(logs, "DONE", f"PDF Document compiled: {out_path.name} ({out_path.stat().st_size:,} bytes).")
    return route


def df_to_markdown_table(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]).replace("\n", " ").replace("|", "\\|") for c in df.columns) + " |")
    return "\n".join(lines) + "\n"


def df_to_styled_html_table(df: pd.DataFrame, title: str = "Data Export") -> str:
    headers_html = "".join(f"<th>{re.sub(r'[^a-zA-Z0-9 _-]', '', str(c))}</th>" for c in df.columns)
    rows_html = []
    for _, row in df.iterrows():
        cells_html = "".join(f"<td>{str(row[c]).replace('<', '&lt;').replace('>', '&gt;')}</td>" for c in df.columns)
        rows_html.append(f"<tr>{cells_html}</tr>")
    body_html = "\n".join(rows_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 2rem;
      background: #0b0f19;
      color: #f1f5f9;
    }}
    h1 {{ font-size: 1.4rem; margin-bottom: 1.25rem; color: #818cf8; font-weight: 600; }}
    .table-container {{
      overflow-x: auto;
      border: 1px solid #1e293b;
      border-radius: 8px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.88rem;
    }}
    th {{
      background: #1e293b;
      color: #94a3b8;
      padding: 0.75rem 1rem;
      font-weight: 600;
      border-bottom: 1px solid #334155;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    td {{
      padding: 0.75rem 1rem;
      border-bottom: 1px solid #1e293b;
    }}
    tr:nth-child(even) {{
      background: rgba(30, 41, 59, 0.35);
    }}
    tr:hover {{
      background: rgba(99, 102, 241, 0.12);
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="table-container">
    <table>
      <thead>
        <tr>{headers_html}</tr>
      </thead>
      <tbody>
        {body_html}
      </tbody>
    </table>
  </div>
</body>
</html>"""


def handle_data_cross_conversion(
    input_bytes: bytes,
    in_ext: str,
    target_format: str,
    logs: List[str]
) -> Tuple[bytes, str]:
    route = f"Data File ({in_ext.upper()}) ➔ Schema Parser (Pandas/OpenPyXL/PyYAML) ➔ Serializer ➔ {target_format.upper()}"
    log_entry(logs, "ROUTE", route)
    log_entry(logs, "EXEC", f"Ingesting and validating {in_ext.upper()} document payload...")

    df = None
    data_obj = None

    if in_ext in ["xlsx", "xls"]:
        df = pd.read_excel(io.BytesIO(input_bytes), engine="openpyxl")
        data_obj = df.to_dict(orient="records")
    elif in_ext == "json":
        text_content = input_bytes.decode("utf-8", errors="replace")
        data_obj = json.loads(text_content)
        if isinstance(data_obj, list):
            df = pd.DataFrame(data_obj)
        elif isinstance(data_obj, dict):
            if any(isinstance(v, list) for v in data_obj.values()):
                df = pd.DataFrame(data_obj)
            else:
                df = pd.DataFrame([data_obj])
    elif in_ext in ["csv", "tsv"]:
        text_content = input_bytes.decode("utf-8", errors="replace")
        sep = "\t" if in_ext == "tsv" else ","
        df = pd.read_csv(io.StringIO(text_content), sep=sep)
        data_obj = df.to_dict(orient="records")
    elif in_ext in ["yaml", "yml"]:
        text_content = input_bytes.decode("utf-8", errors="replace")
        data_obj = yaml.safe_load(text_content)
        if isinstance(data_obj, list):
            df = pd.DataFrame(data_obj)
        elif isinstance(data_obj, dict):
            df = pd.DataFrame([data_obj])
    elif in_ext == "xml":
        text_content = input_bytes.decode("utf-8", errors="replace")
        root = ET.fromstring(text_content)
        records = []
        for child in root:
            row = {elem.tag: elem.text for elem in child}
            if row:
                records.append(row)
        if records:
            df = pd.DataFrame(records)
            data_obj = records
        else:
            data_obj = {root.tag: {c.tag: c.text for c in root}}
            df = pd.DataFrame([data_obj[root.tag]])
    else:
        raise ValueError(f"Unsupported data source extension: {in_ext}")

    count = len(df) if df is not None else (len(data_obj) if isinstance(data_obj, list) else 1)
    log_entry(logs, "INFO", f"Parsed tabular structure successfully: {count} rows/records.")

    if target_format in ["xlsx", "xls"]:
        buf = io.BytesIO()
        if df is not None:
            df.to_excel(buf, index=False, engine="openpyxl")
        else:
            pd.DataFrame([data_obj] if isinstance(data_obj, dict) else data_obj).to_excel(buf, index=False, engine="openpyxl")
        excel_bytes = buf.getvalue()
        log_entry(logs, "DONE", f"Compiled Excel workbook (.xlsx): {len(excel_bytes):,} bytes.")
        return excel_bytes, route

    out_str = ""
    if target_format == "json":
        if data_obj is not None:
            out_str = json.dumps(data_obj, indent=2, ensure_ascii=False)
        elif df is not None:
            out_str = df.to_json(orient="records", indent=2)
    elif target_format == "csv":
        if df is not None:
            out_str = df.to_csv(index=False)
        else:
            df = pd.DataFrame([data_obj] if isinstance(data_obj, dict) else data_obj)
            out_str = df.to_csv(index=False)
    elif target_format == "tsv":
        if df is not None:
            out_str = df.to_csv(index=False, sep="\t")
        else:
            df = pd.DataFrame([data_obj] if isinstance(data_obj, dict) else data_obj)
            out_str = df.to_csv(index=False, sep="\t")
    elif target_format in ["yaml", "yml"]:
        if data_obj is not None:
            out_str = yaml.dump(data_obj, sort_keys=False, allow_unicode=True)
        elif df is not None:
            out_str = yaml.dump(df.to_dict(orient="records"), sort_keys=False, allow_unicode=True)
    elif target_format == "xml":
        root_tag = "data"
        item_tag = "item"
        xml_lines = [f"<{root_tag}>"]
        records = df.to_dict(orient="records") if df is not None else ([data_obj] if isinstance(data_obj, dict) else data_obj)
        for rec in records:
            xml_lines.append(f"  <{item_tag}>")
            for k, v in rec.items():
                safe_k = re.sub(r"[^\w]", "_", str(k))
                xml_lines.append(f"    <{safe_k}>{v}</{safe_k}>")
            xml_lines.append(f"  </{item_tag}>")
        xml_lines.append(f"</{root_tag}>")
        out_str = "\n".join(xml_lines)
    elif target_format in ["md", "markdown"]:
        if df is not None:
            out_str = df_to_markdown_table(df)
        else:
            out_str = f"```json\n{json.dumps(data_obj, indent=2)}\n```"
    elif target_format in ["html", "htm"]:
        if df is not None:
            out_str = df_to_styled_html_table(df, title=f"Data Export ({in_ext.upper()})")
        else:
            df = pd.DataFrame([data_obj] if isinstance(data_obj, dict) else data_obj)
            out_str = df_to_styled_html_table(df, title=f"Data Export ({in_ext.upper()})")
    else:
        raise ValueError(f"Unsupported data target format: {target_format}")

    log_entry(logs, "DONE", f"Serialized output to {target_format.upper()} ({len(out_str):,} characters).")
    return out_str.encode("utf-8"), route


async def handle_media_to_transcript_markdown(
    in_path: Path,
    in_ext: str,
    in_stem: str,
    logs: List[str]
) -> Tuple[bytes, str]:
    route = f"Media ({in_ext.upper()}) ➔ Audio Demuxer ➔ Speech Recognition & FFprobe Telemetry ➔ Markdown"
    log_entry(logs, "ROUTE", route)
    log_entry(logs, "EXEC", "Demuxing audio stream to 16kHz mono WAV...")

    duration = await get_media_duration(in_path)
    wav_path = in_path.parent / "audio_extract.wav"

    cmd = [
        "ffmpeg", "-y", "-i", str(in_path),
        "-vn", "-ac", "1", "-ar", "16000",
        str(wav_path)
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    transcript_text = "*(No human speech detected or recognition engine could not transcribe)*"
    if wav_path.exists() and wav_path.stat().st_size > 4000:
        log_entry(logs, "EXEC", "Running speech-to-text recognition model...")
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(str(wav_path)) as source:
                audio_data = r.record(source)
                try:
                    text = r.recognize_google(audio_data)
                    if text:
                        transcript_text = text
                        log_entry(logs, "INFO", f"Transcribed speech successfully ({len(text.split())} words).")
                except Exception as stt_err:
                    log_entry(logs, "WARN", f"STT notice: {stt_err}")
        except Exception as e:
            log_entry(logs, "WARN", f"STT unavailable: {e}")

    md_content = f"""# Audio & Speech Transcript: {in_stem}

> Generated locally via Better VERT Universal Media Engine.

## File Telemetry
- **Source File**: `{in_stem}.{in_ext}`
- **Duration**: {format_duration(duration)} ({duration:.2f} seconds)
- **Extracted Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Channel Layout**: 1 Channel (Mono 16kHz for speech processing)

---

## Speech-to-Text Transcription

{transcript_text}

---
*Generated by Better VERT Universal Engine.*
"""
    log_entry(logs, "DONE", f"Compiled audio transcript and telemetry into Markdown ({len(md_content):,} chars).")
    return md_content.encode("utf-8"), route


# ---------------------------------------------------------------------------
# Master Conversion Dispatcher
# ---------------------------------------------------------------------------

async def convert_media(
    input_bytes: bytes,
    input_filename: str,
    target_format: str,
    speed: str = "fast",
    crf: Optional[int] = None,
    resolution: Optional[str] = None,
    video_codec: Optional[str] = None,
    audio_bitrate: Optional[str] = None,
    fps: Optional[str] = None,
    quality: Optional[int] = None,
    trim_start: Optional[str] = None,
    trim_duration: Optional[str] = None,
    loudnorm: bool = False,
    audio_channels: Optional[str] = None,
    playback_speed: Optional[str] = None,
    color_filter: Optional[str] = None,
    dpi: Optional[int] = 200,
) -> Tuple[bytes, str, str, List[str]]:
    """
    Universal Converter with cross-medium traversion pipelines and studio-grade tuning.
    Returns: (output_bytes, output_filename, route_description, execution_logs)
    """
    start_time = time.perf_counter()
    target_format = target_format.lstrip(".").lower()
    in_ext = Path(input_filename).suffix.lstrip(".").lower()
    in_stem = Path(input_filename).stem

    in_cat = get_category(in_ext)
    out_cat = get_category(target_format)

    logs: List[str] = []
    log_entry(logs, "INIT", f"Better VERT Universal Engine initialized ({os.cpu_count() or 1} cores active).")
    log_entry(logs, "INFO", f"Input: {input_filename} ({len(input_bytes):,} bytes, Category: {in_cat.upper()})")
    log_entry(logs, "INFO", f"Target: {target_format.upper()} (Category: {out_cat.upper()})")

    tmp_dir = Path(tempfile.mkdtemp(prefix="vert_conv_"))
    try:
        in_path = tmp_dir / f"input.{in_ext}"
        in_path.write_bytes(input_bytes)

        # -------------------------------------------------------------------
        # CASE 1: Video -> PDF Storyboard
        # -------------------------------------------------------------------
        if in_cat == "video" and target_format in ["pdf_storyboard", "storyboard"]:
            out_path = tmp_dir / f"{in_stem}_storyboard.pdf"
            route = await handle_video_to_storyboard_pdf(in_path, out_path, in_stem, logs)
            output_bytes = out_path.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Execution complete: {out_path.name} in {elapsed:.2f}s.")
            return output_bytes, f"{in_stem}_storyboard.pdf", route, logs

        # -------------------------------------------------------------------
        # CASE 2: Audio -> Waveform Video
        # -------------------------------------------------------------------
        if in_cat == "audio" and target_format in ["waveform_video", "waveform"]:
            out_path = tmp_dir / f"{in_stem}_waveform.mp4"
            route = await handle_audio_to_waveform_video(in_path, out_path, logs)
            output_bytes = out_path.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Execution complete: {out_path.name} in {elapsed:.2f}s.")
            return output_bytes, f"{in_stem}_waveform.mp4", route, logs

        # -------------------------------------------------------------------
        # CASE 3: Media -> Speech Transcript / Audio Telemetry Markdown
        # -------------------------------------------------------------------
        if (in_cat in ["audio", "video"]) and target_format in ["transcript_md", "transcript"]:
            data, route = await handle_media_to_transcript_markdown(in_path, in_ext, in_stem, logs)
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Execution complete: {in_stem}_transcript.md in {elapsed:.2f}s.")
            return data, f"{in_stem}_transcript.md", route, logs

        # -------------------------------------------------------------------
        # CASE 4: Documents (PDF, MD, DOCX, TXT, HTML, etc.) -> Page Images or ZIP
        # -------------------------------------------------------------------
        if (in_cat == "document" or in_ext in ["pdf", "md", "markdown", "docx", "txt", "html", "htm", "epub", "odt"]) and \
           (out_cat == "image" or target_format in ["images_zip", "zip"]):
            img_file, out_name, route = await handle_document_to_images(
                in_path, tmp_dir / f"output.{target_format}", target_format, in_stem, in_ext, tmp_dir, logs,
                dpi=dpi, color_filter=color_filter
            )
            output_bytes = img_file.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Execution complete: {out_name} in {elapsed:.2f}s.")
            return output_bytes, out_name, route, logs

        # -------------------------------------------------------------------
        # CASE 5: Image -> Vector SVG
        # -------------------------------------------------------------------
        if in_cat == "image" and target_format == "svg":
            out_path = tmp_dir / f"{in_stem}.svg"
            route = await handle_image_to_svg(in_path, out_path, logs)
            output_bytes = out_path.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Execution complete: {out_path.name} in {elapsed:.2f}s.")
            return output_bytes, f"{in_stem}.svg", route, logs

        # -------------------------------------------------------------------
        # CASE 6: Image(s) -> PDF Document
        # -------------------------------------------------------------------
        if in_cat == "image" and target_format == "pdf":
            out_path = tmp_dir / f"{in_stem}.pdf"
            route = "Raster Image ➔ Pillow Canvas ➔ PDF Document"
            log_entry(logs, "ROUTE", route)
            log_entry(logs, "EXEC", "Composing raster image into PDF document...")
            with Image.open(in_path) as im:
                im.convert("RGB").save(str(out_path), "PDF", resolution=100.0)
            output_bytes = out_path.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Saved PDF document ({len(output_bytes):,} bytes) in {elapsed:.2f}s.")
            return output_bytes, f"{in_stem}.pdf", route, logs

        # -------------------------------------------------------------------
        # CASE 7: Video -> High-Fidelity 2-Pass GIF
        # -------------------------------------------------------------------
        if in_cat == "video" and target_format == "gif":
            out_path = tmp_dir / f"{in_stem}.gif"
            route = await handle_video_to_gif(
                in_path, out_path, fps, resolution, logs,
                trim_start=trim_start, trim_duration=trim_duration
            )
            output_bytes = out_path.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Execution complete: {out_path.name} in {elapsed:.2f}s.")
            return output_bytes, f"{in_stem}.gif", route, logs

        # -------------------------------------------------------------------
        # CASE 8: Data Cross-Conversion (JSON, CSV, TSV, YAML, XML, XLSX, Markdown, HTML)
        # -------------------------------------------------------------------
        if (in_cat == "data" or in_ext in ["json", "csv", "yaml", "yml", "xml", "tsv", "xlsx", "xls"]) and \
           (out_cat == "data" or target_format in ["json", "csv", "yaml", "yml", "xml", "tsv", "xlsx", "xls", "md", "markdown", "html", "htm"]):
            data_bytes, route = handle_data_cross_conversion(input_bytes, in_ext, target_format, logs)
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"Execution complete: {in_stem}.{target_format} in {elapsed:.2f}s.")
            return data_bytes, f"{in_stem}.{target_format}", route, logs

        # -------------------------------------------------------------------
        # CASE 9: Video & Audio (FFmpeg Multi-Threaded Engine)
        # -------------------------------------------------------------------
        if in_cat in ["video", "audio"] or out_cat in ["video", "audio"]:
            is_moving_video = await has_moving_video_stream(in_path)
            has_audio = await has_audio_stream(in_path)

            if in_cat == "video" and out_cat == "audio":
                if not has_audio:
                    raise ValueError(f"The input video '{input_filename}' contains no audio track to extract.")

            out_path = tmp_dir / f"output.{target_format}"
            route = f"{in_cat.upper()} ({in_ext.upper()}) ➔ FFmpeg Multi-Threaded Engine ➔ {out_cat.upper()} ({target_format.upper()})"
            log_entry(logs, "ROUTE", route)

            cmd = ["ffmpeg", "-y", "-nostdin", "-hide_banner", "-loglevel", "error", "-threads", "0"]

            # Input trimming (fast timestamp seek)
            if trim_start and str(trim_start).strip():
                cmd.extend(["-ss", str(trim_start).strip()])
                log_entry(logs, "INFO", f"Configured input trim start: {trim_start}")

            cmd.extend(["-i", str(in_path)])

            # Duration limit
            if trim_duration and str(trim_duration).strip():
                cmd.extend(["-t", str(trim_duration).strip()])
                log_entry(logs, "INFO", f"Configured duration limit: {trim_duration}")

            # Check if input is audio or has no genuine moving video (e.g. audiobook with cover art)
            # but target container is a video format (e.g. mp4, mkv, mov, webm, avi, av1)
            if (in_cat == "audio" or not is_moving_video) and target_format in VIDEO_ENCODER_MAP:
                log_entry(logs, "INFO", f"Input has no moving video track; packaging audio into {target_format.upper()} container (-vn).")
                if target_format in ["mp4", "m4v", "mov"]:
                    cmd.extend(["-vn", "-c:a", "aac", "-b:a", audio_bitrate or "192k", "-movflags", "+faststart"])
                elif target_format == "webm":
                    cmd.extend(["-vn", "-c:a", "libopus", "-b:a", audio_bitrate or "128k"])
                elif target_format == "avi":
                    cmd.extend(["-vn", "-c:a", "mp3", "-b:a", audio_bitrate or "192k"])
                elif target_format == "av1":
                    cmd.extend(["-vn", "-c:a", "libopus", "-b:a", audio_bitrate or "128k", "-f", "mp4"])
                else:
                    cmd.extend(["-vn", "-c:a", "aac", "-b:a", audio_bitrate or "192k"])

            elif target_format in VIDEO_ENCODER_MAP:
                # Video target with genuine moving video input: map primary video and audio streams
                cmd.extend(["-map", "0:v:0?", "-map", "0:a:0?"])
                base_args = list(VIDEO_ENCODER_MAP[target_format])
                if video_codec:
                    if "-c:v" in base_args:
                        idx = base_args.index("-c:v")
                        base_args[idx + 1] = video_codec
                    else:
                        base_args.extend(["-c:v", video_codec])
                if crf is not None:
                    if "-crf" in base_args:
                        idx = base_args.index("-crf")
                        base_args[idx + 1] = str(crf)
                    else:
                        base_args.extend(["-crf", str(crf)])
                if audio_bitrate:
                    if "-b:a" in base_args:
                        idx = base_args.index("-b:a")
                        base_args[idx + 1] = audio_bitrate
                    else:
                        base_args.extend(["-b:a", audio_bitrate])
                cmd.extend(base_args)

            elif target_format in AUDIO_ENCODER_MAP:
                base_args = ["-vn"] + list(AUDIO_ENCODER_MAP[target_format])
                if "-ac" not in base_args and target_format not in ["wav", "flac"]:
                    base_args.extend(["-ac", "2"])
                if audio_bitrate:
                    if "-b:a" in base_args:
                        idx = base_args.index("-b:a")
                        base_args[idx + 1] = audio_bitrate
                    else:
                        base_args.extend(["-b:a", audio_bitrate])
                cmd.extend(base_args)
            else:
                cmd.extend(["-threads", "0"])

            # Resolution scaling
            if resolution and resolution not in ["original", "none", ""]:
                scale_map = {
                    "4k": "scale=-2:2160",
                    "2160p": "scale=-2:2160",
                    "1080p": "scale=-2:1080",
                    "720p": "scale=-2:720",
                    "480p": "scale=-2:480",
                }
                scale_val = scale_map.get(resolution.lower(), f"scale={resolution}")
                if "-vf" in cmd:
                    vf_idx = cmd.index("-vf")
                    cmd[vf_idx + 1] += f",{scale_val}"
                else:
                    cmd.extend(["-vf", scale_val])

            # FPS adjustment
            if fps and fps not in ["original", "none", ""]:
                cmd.extend(["-r", str(fps)])

            # Audio channel selection (mono / stereo / mute)
            if audio_channels in ["mono", "1"]:
                cmd.extend(["-ac", "1"])
                log_entry(logs, "INFO", "Configured mono channel downmix (-ac 1).")
            elif audio_channels in ["stereo", "2"]:
                cmd.extend(["-ac", "2"])
                log_entry(logs, "INFO", "Configured stereo channel mapping (-ac 2).")
            elif audio_channels in ["mute", "strip", "none"]:
                cmd.append("-an")
                log_entry(logs, "INFO", "Stripped audio stream (-an).")

            # Loudness normalization (EBU R128 standard)
            if loudnorm:
                norm_f = "loudnorm=I=-16:TP=-1.5:LRA=11"
                if "-af" in cmd:
                    af_idx = cmd.index("-af")
                    cmd[af_idx + 1] += f",{norm_f}"
                else:
                    cmd.extend(["-af", norm_f])
                log_entry(logs, "INFO", "Applied EBU R128 broadcast loudness normalization.")

            # Playback speed adjustment
            if playback_speed and str(playback_speed) not in ["1.0", "1", "original", "", "none"]:
                try:
                    s_val = float(playback_speed)
                    if 0.25 <= s_val <= 4.0 and s_val != 1.0:
                        v_pts = f"setpts={1.0/s_val:.4f}*PTS"
                        a_tempo = f"atempo={s_val:.2f}"
                        if "-vf" in cmd:
                            vf_idx = cmd.index("-vf")
                            cmd[vf_idx + 1] += f",{v_pts}"
                        else:
                            cmd.extend(["-vf", v_pts])
                        if "-af" in cmd:
                            af_idx = cmd.index("-af")
                            cmd[af_idx + 1] += f",{a_tempo}"
                        else:
                            cmd.extend(["-af", a_tempo])
                        log_entry(logs, "INFO", f"Applied playback speed multiplier: {s_val}x.")
                except Exception as s_err:
                    logger.warning(f"Error parsing speed: {s_err}")

            cmd.append(str(out_path))

            log_entry(logs, "EXEC", f"Running FFmpeg ARM64 worker: {' '.join(cmd[1:6])}...")
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                err_msg = stderr.decode(errors="replace")
                log_entry(logs, "ERROR", f"FFmpeg error: {err_msg[:200]}")
                raise RuntimeError(f"FFmpeg conversion failed: {err_msg[:300]}")

            output_bytes = out_path.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"FFmpeg encoding complete: {out_path.name} ({len(output_bytes):,} bytes) in {elapsed:.2f}s.")
            return output_bytes, f"{in_stem}.{target_format}", route, logs

        # -------------------------------------------------------------------
        # CASE 10: Image -> Image (ImageMagick)
        # -------------------------------------------------------------------
        if in_cat == "image" and out_cat == "image":
            out_path = tmp_dir / f"output.{target_format}"
            route = f"Image ({in_ext.upper()}) ➔ ImageMagick Studio ➔ Image ({target_format.upper()})"
            log_entry(logs, "ROUTE", route)

            magick_bin = "magick" if shutil.which("magick") else "convert"
            cmd = [magick_bin, str(in_path)]
            if quality and 1 <= quality <= 100:
                cmd.extend(["-quality", str(quality)])
            if resolution and resolution not in ["original", "none", ""]:
                res_map = {"1080p": "1920x1080>", "720p": "1280x720>", "4k": "3840x2160>"}
                cmd.extend(["-resize", res_map.get(resolution.lower(), resolution)])
            if color_filter == "grayscale":
                cmd.extend(["-colorspace", "Gray"])
                log_entry(logs, "INFO", "Applied grayscale color conversion.")
            elif color_filter == "sepia":
                cmd.extend(["-sepia-tone", "80%"])
                log_entry(logs, "INFO", "Applied sepia tone color filter.")
            elif color_filter == "invert":
                cmd.append("-negate")
                log_entry(logs, "INFO", "Applied color inversion / negative filter.")
            elif color_filter == "monochrome":
                cmd.extend(["-threshold", "50%"])
                log_entry(logs, "INFO", "Applied 50% luminance monochrome threshold.")

            cmd.append(str(out_path))

            log_entry(logs, "EXEC", f"Running ImageMagick: {magick_bin}...")
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"ImageMagick failed: {stderr.decode(errors='replace')[:300]}")

            output_bytes = out_path.read_bytes()
            elapsed = time.perf_counter() - start_time
            log_entry(logs, "DONE", f"ImageMagick conversion complete: {out_path.name} ({len(output_bytes):,} bytes) in {elapsed:.2f}s.")
            return output_bytes, f"{in_stem}.{target_format}", route, logs

        # -------------------------------------------------------------------
        # CASE 11: Document & Code (Pandoc & ReportLab Typesetter)
        # -------------------------------------------------------------------
        if in_cat == "document" and (out_cat == "document" or target_format == "pdf"):
            out_path = tmp_dir / f"output.{target_format}"

            if target_format == "pdf":
                route = await handle_document_to_pdf(in_path, out_path, in_stem, in_ext, logs)
                output_bytes = out_path.read_bytes()
                elapsed = time.perf_counter() - start_time
                log_entry(logs, "DONE", f"Document PDF compiled: {out_path.name} ({len(output_bytes):,} bytes) in {elapsed:.2f}s.")
                return output_bytes, f"{in_stem}.pdf", route, logs

            if in_ext == "pdf":
                route = f"PDF Document ➔ Text & Structure Extractor (pdfplumber) ➔ {target_format.upper()}"
                log_entry(logs, "ROUTE", route)
                import pdfplumber
                import html
                with pdfplumber.open(in_path) as pdf:
                    pages_text = [page.extract_text() or "" for page in pdf.pages]

                if target_format == "txt":
                    full_text = "\n\n".join(pages_text)
                    out_path.write_text(full_text, encoding="utf-8")
                elif target_format in ["md", "markdown"]:
                    md_parts = [f"# Page {i+1}\n\n{text}" for i, text in enumerate(pages_text) if text.strip()]
                    out_path.write_text("\n\n---\n\n".join(md_parts), encoding="utf-8")
                elif target_format in ["html", "htm"]:
                    html_parts = [f"<section><h2>Page {i+1}</h2><p>{html.escape(text).replace(chr(10), '<br>')}</p></section>" for i, text in enumerate(pages_text) if text.strip()]
                    out_path.write_text(f"<!DOCTYPE html><html><head><title>{in_stem}</title></head><body>{''.join(html_parts)}</body></html>", encoding="utf-8")
                elif target_format == "docx" and shutil.which("pandoc"):
                    md_tmp = tmp_dir / "extracted.md"
                    md_parts = [f"# Page {i+1}\n\n{text}" for i, text in enumerate(pages_text) if text.strip()]
                    md_tmp.write_text("\n\n---\n\n".join(md_parts), encoding="utf-8")
                    cmd = ["pandoc", str(md_tmp), "-o", str(out_path)]
                    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    await proc.communicate()
                else:
                    out_path.write_text("\n\n".join(pages_text), encoding="utf-8")

                output_bytes = out_path.read_bytes()
                elapsed = time.perf_counter() - start_time
                log_entry(logs, "DONE", f"Extracted {len(pages_text)} pages to {out_path.name} ({len(output_bytes):,} bytes) in {elapsed:.2f}s.")
                return output_bytes, f"{in_stem}.{target_format}", route, logs

            route = f"Document ({in_ext.upper()}) ➔ Pandoc Universal Parser ➔ {target_format.upper()}"
            log_entry(logs, "ROUTE", route)

            if shutil.which("pandoc") and target_format in ["html", "htm", "docx", "epub", "md", "txt", "rtf", "odt"]:
                cmd = ["pandoc", str(in_path), "-o", str(out_path), "--standalone", f"--metadata=title:{in_stem}"]
                if target_format in ["html", "htm"]:
                    cmd.extend(["--highlight-style=tango"])
                log_entry(logs, "EXEC", f"Running Pandoc document compiler ({' '.join(cmd[1:6])})...")
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"Pandoc conversion failed: {stderr.decode(errors='replace')[:300]}")
                output_bytes = out_path.read_bytes()
                elapsed = time.perf_counter() - start_time
                log_entry(logs, "DONE", f"Pandoc conversion complete: {out_path.name} ({len(output_bytes):,} bytes) in {elapsed:.2f}s.")
                return output_bytes, f"{in_stem}.{target_format}", route, logs
            else:
                raise ValueError(f"Direct document conversion from {in_ext} to {target_format} not supported directly via pandoc.")

        raise ValueError(f"No conversion route found for: {in_ext} -> {target_format}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
