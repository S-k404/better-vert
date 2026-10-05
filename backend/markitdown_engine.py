"""
Microsoft MarkItDown Engine with Tesseract OCR, Poppler & Image Extraction.
Incorporates and enhances the File Converter engine.
Extracts embedded figures, raster graphics, and visual images into standalone assets and data URIs.
"""

import base64
import io
import logging
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

from markitdown import MarkItDown
from PIL import Image

logger = logging.getLogger("better-vert.markitdown")

# Initialize MarkItDown with third-party plugins enabled
try:
    _md = MarkItDown(enable_plugins=True)
except Exception as e:
    logger.warning(f"Error initializing MarkItDown with plugins: {e}; falling back to default")
    _md = MarkItDown()


# Device names Windows refuses to create as a file, with or without an extension
# ("con.md", "NUL.txt"). Converted files land on the host through a bind mount, so
# a name the Linux container accepts can still fail to write on a Windows host.
_WINDOWS_RESERVED = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)}
)


def avoid_reserved_name(name: str) -> str:
    """Prefixes a Windows device name with '_' so it can be written on any host OS."""
    if name.split(".", 1)[0].strip().lower() in _WINDOWS_RESERVED:
        return f"_{name}"
    return name


def safe_stem(name: str) -> str:
    """Sanitizes filename stem for safe filesystem writing."""
    stem = Path(name).stem
    stem = re.sub(r"[^\w\-. ]+", "_", stem).strip() or "converted"
    return avoid_reserved_name(stem[:120])


def unique_name(filename: str, taken: set[str], target_ext: str = "md") -> str:
    """Ensures report.pdf and report.docx don't collide.

    Collisions are judged case-insensitively: macOS and Windows filesystems treat
    "Report.md" and "report.md" as one file, so the second would overwrite the first
    on disk (or when the zip is extracted there).
    """
    stem = safe_stem(filename)
    orig_ext = Path(filename).suffix.lstrip(".").lower()
    seen = {t.lower() for t in taken}
    candidate = f"{stem}.{target_ext}"
    if candidate.lower() in seen:
        candidate = f"{stem}-{orig_ext}.{target_ext}" if orig_ext else f"{stem}-1.{target_ext}"
    n = 2
    while candidate.lower() in seen:
        candidate = f"{stem}-{orig_ext}-{n}.{target_ext}" if orig_ext else f"{stem}-{n}.{target_ext}"
        n += 1
    taken.add(candidate)
    return candidate


def _ocr_fallback(file_path: Path) -> Optional[str]:
    """Fallback to Tesseract OCR directly if MarkItDown yields empty content on images."""
    try:
        res = subprocess.run(
            ["tesseract", str(file_path), "stdout", "-l", "eng", "--oem", "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception as e:
        logger.debug(f"Tesseract OCR fallback error: {e}")
    return None


def _poppler_pdf_fallback(file_path: Path) -> Optional[str]:
    """Fallback to pdftotext if MarkItDown had an issue reading a PDF text layer."""
    try:
        res = subprocess.run(
            ["pdftotext", "-layout", str(file_path), "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception as e:
        logger.debug(f"Poppler pdftotext fallback error: {e}")
    return None


def extract_images_from_document(doc_path: Path, tmp_dir: Path) -> List[Tuple[str, bytes, str]]:
    """
    Extracts embedded raster images and figures from documents.
    Returns a list of (image_filename, image_bytes, mime_type).
    Supports:
      - PDF via poppler 'pdfimages -png'
      - DOCX / PPTX / ODT / EPUB via zip structure inspection
      - Markdown / HTML via base64 data URI parsing
    """
    extracted: List[Tuple[str, bytes, str]] = []
    suffix = doc_path.suffix.lower()

    # 1. PDF Documents
    if suffix == ".pdf":
        img_prefix = tmp_dir / "extracted_pdf_img"
        try:
            res = subprocess.run(
                ["pdfimages", "-png", str(doc_path), str(img_prefix)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=45,
            )
            if res.returncode == 0:
                img_files = sorted(tmp_dir.glob("extracted_pdf_img-*.png"))
                for idx, img_file in enumerate(img_files, 1):
                    raw = img_file.read_bytes()
                    if len(raw) > 50:  # Skip 0-byte or trivial markers
                        extracted.append((f"figure_{idx:02d}.png", raw, "image/png"))
        except Exception as e:
            logger.warning(f"Error extracting PDF images with pdfimages: {e}")

    # 2. DOCX / PPTX / ODT / EPUB (ZIP archive based office formats)
    elif suffix in [".docx", ".pptx", ".odt", ".epub"] and zipfile.is_zipfile(doc_path):
        try:
            with zipfile.ZipFile(doc_path, "r") as z:
                idx = 1
                for item in sorted(z.infolist(), key=lambda x: x.filename):
                    fname = item.filename
                    # Check if inside media directories or image file extension
                    is_media = any(prefix in fname for prefix in ["word/media/", "ppt/media/", "Pictures/", "OEBPS/images/"])
                    has_img_ext = Path(fname).suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"]
                    if (is_media or has_img_ext) and item.file_size > 100:
                        raw = z.read(item)
                        ext = Path(fname).suffix.lower().lstrip(".")
                        if ext == "jpg":
                            ext = "jpeg"
                        mime = f"image/{ext}" if ext in ["png", "jpeg", "webp", "gif", "bmp", "tiff"] else "image/png"
                        extracted.append((f"embedded_image_{idx:02d}.{ext}", raw, mime))
                        idx += 1
        except Exception as e:
            logger.warning(f"Error extracting zip-based document media: {e}")

    # 3. Markdown / Plain Text with embedded base64 data URIs
    elif suffix in [".md", ".markdown", ".txt", ".html", ".htm"]:
        try:
            text = doc_path.read_text(encoding="utf-8", errors="ignore")
            # Match Markdown image tags: ![alt](data:image/ext;base64,data)
            idx = 1
            for m in re.finditer(r'!\[([^\]]*)\]\(data:image/([a-zA-Z0-9+.-]+);base64,([A-Za-z0-9+/=]+)\)', text):
                fmt = m.group(2).lower()
                b64 = m.group(3)
                try:
                    raw = base64.b64decode(b64)
                    if len(raw) > 50:
                        mime = f"image/{fmt}"
                        extracted.append((f"markdown_img_{idx:02d}.{fmt}", raw, mime))
                        idx += 1
                except Exception:
                    pass

            # Match HTML img tags: <img src="data:image/ext;base64,data" ...>
            for m in re.finditer(r'<img[^>]+src=[\'"]data:image/([a-zA-Z0-9+.-]+);base64,([A-Za-z0-9+/=]+)[\'"]', text):
                fmt = m.group(1).lower()
                b64 = m.group(2)
                try:
                    raw = base64.b64decode(b64)
                    if len(raw) > 50:
                        mime = f"image/{fmt}"
                        extracted.append((f"markdown_tag_{idx:02d}.{fmt}", raw, mime))
                        idx += 1
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Error parsing inline markdown images: {e}")

    return extracted


def convert_bytes_to_markdown_with_assets(data: bytes, filename: str) -> Tuple[str, List[Tuple[str, bytes]]]:
    """
    Converts file bytes to clean Markdown and extracts all embedded images and visual figures.
    Returns:
        (markdown_text, list_of_extracted_images_as_tuples(filename, bytes))
    """
    suffix = Path(filename).suffix.lower()
    tmp_dir = tempfile.mkdtemp(prefix="vert_md_")
    extracted_assets: List[Tuple[str, bytes]] = []

    try:
        tmp_path = Path(tmp_dir) / f"input{suffix}"
        tmp_path.write_bytes(data)

        # -------------------------------------------------------------------
        # CASE A: Input is an Image file (PNG, JPG, WebP, AVIF, TIFF, BMP, GIF)
        # -------------------------------------------------------------------
        image_suffixes = [".png", ".jpg", ".jpeg", ".webp", ".avif", ".tiff", ".tif", ".bmp", ".gif", ".ico"]
        if suffix in image_suffixes:
            width, height, fmt, mode = 0, 0, "IMAGE", "RGB"
            try:
                with Image.open(io.BytesIO(data)) as im:
                    width, height = im.size
                    fmt = (im.format or suffix.lstrip(".")).upper()
                    mode = im.mode
            except Exception as e:
                logger.debug(f"PIL probe warning: {e}")

            b64_str = base64.b64encode(data).decode("utf-8")
            fmt_lower = fmt.lower()
            if fmt_lower == "jpg":
                fmt_lower = "jpeg"
            mime_type = f"image/{fmt_lower}"

            # Run Tesseract OCR for text inside the image
            ocr_text = _ocr_fallback(tmp_path)

            md_lines = [
                f"# {filename}",
                "",
                f"![{filename}](data:{mime_type};base64,{b64_str})",
                "",
                f"*Visual Metadata: {width} × {height} px | Format: {fmt} | Color Mode: {mode} | Size: {len(data):,} bytes*",
                "",
            ]

            if ocr_text:
                md_lines.extend([
                    "## OCR Extracted Text",
                    "",
                    "```text",
                    ocr_text,
                    "```",
                    "",
                ])
            else:
                md_lines.extend([
                    "> *Visual image extracted successfully. No printed text detected via Tesseract OCR.*",
                    "",
                ])

            extracted_assets.append((filename, data))
            return "\n".join(md_lines), extracted_assets

        # -------------------------------------------------------------------
        # CASE B: Input is a Document (PDF, DOCX, PPTX, Markdown, Text, HTML)
        # -------------------------------------------------------------------
        markdown_text = ""
        try:
            result = _md.convert(str(tmp_path))
            markdown_text = (result.text_content or "").strip()
        except Exception as conv_err:
            logger.warning(f"MarkItDown native conversion error for {filename}: {conv_err}")

        # If PDF and text layer was empty, run poppler pdftotext
        if not markdown_text and suffix == ".pdf":
            pdf_res = _poppler_pdf_fallback(tmp_path)
            if pdf_res:
                markdown_text = pdf_res

        # Extract all embedded images and figures from the document
        doc_images = extract_images_from_document(tmp_path, Path(tmp_dir))
        stem = safe_stem(filename)

        if doc_images:
            image_sections = [
                "",
                "---",
                "",
                f"## Extracted Document Images & Figures ({len(doc_images)})",
                "",
                f"*The following {len(doc_images)} embedded images and visual figures were extracted from `{filename}`:*",
                "",
            ]

            for idx, (img_name, img_bytes, mime) in enumerate(doc_images, 1):
                b64_img = base64.b64encode(img_bytes).decode("utf-8")
                asset_name = f"{stem}_{img_name}"
                extracted_assets.append((asset_name, img_bytes))

                image_sections.extend([
                    f"### Figure {idx}: {img_name}",
                    "",
                    f"![Figure {idx}: {img_name}](data:{mime};base64,{b64_img})",
                    "",
                    f"*Asset: `{asset_name}` ({len(img_bytes):,} bytes | {mime})*",
                    "",
                ])

            if markdown_text:
                markdown_text = markdown_text + "\n" + "\n".join(image_sections)
            else:
                markdown_text = f"# {filename}\n\n" + "\n".join(image_sections)

        if not markdown_text:
            markdown_text = (
                f"<!-- No text or visual layers extracted from {filename}. "
                f"If this is a scanned document without OCR or binary file, content could not be parsed. -->\n"
            )

        return markdown_text, extracted_assets

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def convert_bytes_to_markdown(data: bytes, filename: str) -> str:
    """
    Converts file bytes to clean Markdown.
    Includes extracted images and figures embedded directly as data URIs.
    """
    md, _ = convert_bytes_to_markdown_with_assets(data, filename)
    return md
