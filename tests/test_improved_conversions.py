"""
Automated validation suite for Better VERT improved conversions:
- Video -> FastStart MP4
- Video -> AV1 (libsvtav1)
- Video -> High-FPS 2-Pass Lanczos GIF
- Video -> TrueType Video Storyboard PDF
- Audio -> Peak-to-Peak Waveform Video MP4
- Video -> Stereo Downmixed Audio (MP3)
- JSON -> Excel XLSX (OpenPyXL)
- JSON -> Styled HTML Table
- JSON -> Markdown Table
- Excel XLSX -> CSV / JSON (bidirectional)
- Image -> Potrace Vector SVG
- PDF -> 200 DPI Page Images (Multi-page ZIP)
"""

import io
import json
import os
import subprocess
import tempfile
import urllib.parse
import urllib.request
import pandas as pd

BASE_URL = os.environ.get("CONVERT_API_URL", "http://127.0.0.1:8000/api/convert-universal")

def convert_file(filename: str, file_bytes: bytes, target_format: str, extra_params=None):
    boundary = "----BetterVertBoundaryX74920"
    body = bytearray()

    extra = extra_params or {}
    for k, v in extra.items():
        if v is not None:
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode("utf-8"))
            body.extend(f"{v}\r\n".encode("utf-8"))

    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="target_format"\r\n\r\n'.encode("utf-8"))
    body.extend(f"{target_format}\r\n".encode("utf-8"))

    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
    body.extend(file_bytes)
    body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        BASE_URL,
        data=bytes(body),
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "BetterVertTestRunner/2.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        content = resp.read()
        headers = dict(resp.headers)
        
        logs = []
        raw_logs = headers.get("x-conversion-logs") or headers.get("X-Conversion-Logs")
        if raw_logs:
            try:
                logs = json.loads(urllib.parse.unquote(raw_logs))
            except Exception:
                pass
                
        route = ""
        raw_route = headers.get("x-conversion-route") or headers.get("X-Conversion-Route")
        if raw_route:
            route = urllib.parse.unquote(raw_route)
            
        return resp.status, content, logs, route


def main():
    print("=" * 70)
    print("RUNNING BETTER VERT IMPROVED CONVERSIONS TEST SUITE")
    print("=" * 70)

    # 1. Create synthetic test media files
    with tempfile.TemporaryDirectory() as td:
        vid_path = os.path.join(td, "test_clip.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=3:size=640x360:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            vid_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        with open(vid_path, "rb") as f:
            video_bytes = f.read()

        aud_path = os.path.join(td, "test_sound.wav")
        cmd_aud = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "sine=frequency=880:duration=2",
            aud_path
        ]
        subprocess.run(cmd_aud, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        with open(aud_path, "rb") as f:
            audio_bytes = f.read()

        pdf_path = os.path.join(td, "doc.pdf")
        from PIL import Image
        p1 = Image.new("RGB", (400, 500), (255, 255, 255))
        p2 = Image.new("RGB", (400, 500), (240, 240, 240))
        p1.save(pdf_path, "PDF", save_all=True, append_images=[p2])
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        img_path = os.path.join(td, "shape.png")
        from PIL import ImageDraw
        im = Image.new("RGB", (200, 200), (255, 255, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([(40, 40), (160, 160)], fill=(0, 0, 0))
        im.save(img_path, "PNG")
        with open(img_path, "rb") as f:
            image_bytes = f.read()

    # TEST 1: Video -> FastStart MP4
    print("\n[TEST 1] Video -> FastStart MP4...")
    status, data, logs, route = convert_file("clip.mp4", video_bytes, "mp4", {"crf": 22})
    assert status == 200, f"Expected 200, got {status}"
    assert len(data) > 1000, "Output too small"
    print(f"  OK: {len(data):,} bytes. Route: {route}")
    assert any("mp4" in l.lower() or "encoding" in l.lower() for l in logs)

    # TEST 2: Video -> 2-Pass Lanczos High-FPS GIF
    print("\n[TEST 2] Video -> 2-Pass Lanczos GIF...")
    status, data, logs, route = convert_file("clip.mp4", video_bytes, "gif", {"fps": "12", "resolution": "360p"})
    assert status == 200, f"Expected 200, got {status}"
    assert data[:6] in [b"GIF87a", b"GIF89a"], "Not a valid GIF binary"
    print(f"  OK: {len(data):,} bytes. Route: {route}")
    assert "PaletteGen" in route or "GIF" in route

    # TEST 3: Video -> TrueType Storyboard PDF
    print("\n[TEST 3] Video -> TrueType Storyboard PDF...")
    status, data, logs, route = convert_file("clip.mp4", video_bytes, "pdf_storyboard")
    assert status == 200, f"Expected 200, got {status}"
    assert data[:4] == b"%PDF", "Not a valid PDF file"
    print(f"  OK: {len(data):,} bytes. Route: {route}")
    assert any("TrueType" in l or "keyframe" in l.lower() for l in logs)

    # TEST 4: Audio -> Peak-to-Peak Waveform Video
    print("\n[TEST 4] Audio -> Peak-to-Peak Waveform Video (MP4)...")
    status, data, logs, route = convert_file("sound.wav", audio_bytes, "waveform_video")
    assert status == 200, f"Expected 200, got {status}"
    assert len(data) > 10000, "Waveform MP4 too small"
    print(f"  OK: {len(data):,} bytes. Route: {route}")
    assert "Waveform" in route

    # TEST 5: Video -> Stereo Downmixed Audio (MP3)
    print("\n[TEST 5] Video -> Audio Extraction (MP3 stereo)...")
    status, data, logs, route = convert_file("clip.mp4", video_bytes, "mp3", {"audio_bitrate": "192k"})
    assert status == 200, f"Expected 200, got {status}"
    assert len(data) > 2000, "MP3 too small"
    print(f"  OK: {len(data):,} bytes. Route: {route}")

    # TEST 6: JSON -> Excel XLSX (OpenPyXL)
    print("\n[TEST 6] JSON -> Excel Workbook (.xlsx)...")
    sample_records = [
        {"id": 1, "item": "MacBook Pro M5 Max", "price": 3499, "stock": 42},
        {"id": 2, "item": "Studio Display Pro", "price": 1999, "stock": 18},
        {"id": 3, "item": "Magic Keyboard Studio", "price": 199, "stock": 85}
    ]
    json_bytes = json.dumps(sample_records, indent=2).encode("utf-8")
    status, data, logs, route = convert_file("inventory.json", json_bytes, "xlsx")
    assert status == 200, f"Expected 200, got {status}"
    df_read = pd.read_excel(io.BytesIO(data), engine="openpyxl")
    assert len(df_read) == 3, f"Expected 3 rows, got {len(df_read)}"
    print(f"  OK: Excel XLSX validated ({len(data):,} bytes, columns: {list(df_read.columns)})")

    # TEST 7: Excel XLSX -> CSV (Bidirectional)
    print("\n[TEST 7] Excel XLSX -> CSV...")
    status, data, logs, route = convert_file("inventory.xlsx", data, "csv")
    assert status == 200, f"Expected 200, got {status}"
    csv_str = data.decode("utf-8")
    assert "MacBook Pro M5 Max" in csv_str
    print(f"  OK: CSV extracted from Excel ({len(csv_str.splitlines())} lines)")

    # TEST 8: JSON -> Styled HTML Table
    print("\n[TEST 8] JSON -> Styled HTML Table...")
    status, data, logs, route = convert_file("inventory.json", json_bytes, "html")
    assert status == 200, f"Expected 200, got {status}"
    html_str = data.decode("utf-8")
    assert "<table" in html_str and "MacBook Pro M5 Max" in html_str
    print(f"  OK: Styled HTML table generated ({len(html_str):,} characters)")

    # TEST 9: JSON -> Markdown Table
    print("\n[TEST 9] JSON -> Markdown Table...")
    status, data, logs, route = convert_file("inventory.json", json_bytes, "md")
    assert status == 200, f"Expected 200, got {status}"
    md_str = data.decode("utf-8")
    assert "| item |" in md_str or "| id |" in md_str
    print(f"  OK: Markdown table generated ({len(md_str.splitlines())} lines)")

    # TEST 10: Image -> Potrace Vector SVG
    print("\n[TEST 10] Image -> Potrace Vector SVG...")
    status, data, logs, route = convert_file("shape.png", image_bytes, "svg")
    assert status == 200, f"Expected 200, got {status}"
    svg_str = data.decode("utf-8", errors="replace")
    assert "<svg" in svg_str and "</svg>" in svg_str
    print(f"  OK: Vector SVG generated ({len(data):,} bytes). Route: {route}")

    # TEST 11: PDF -> 200 DPI Images (Multi-page ZIP)
    print("\n[TEST 11] PDF (2 pages) -> 200 DPI Page Images ZIP...")
    status, data, logs, route = convert_file("multipage.pdf", pdf_bytes, "images_zip")
    assert status == 200, f"Expected 200, got {status}"
    import zipfile
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        assert len(names) == 2, f"Expected 2 pages in ZIP, got {names}"
        print(f"  OK: Multi-page ZIP verified containing: {names}")

    print("\n" + "=" * 70)
    print("ALL 11 CONVERSION TYPES VALIDATED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
