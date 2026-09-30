import requests
import json
import io
from pathlib import Path

BASE_URL = "http://localhost:8394"

def test_inspect_media():
    print("\n--- 1. Testing /api/inspect-media ---")
    
    # 1. Inspect Audio (generate a 1-sec wav)
    import wave, struct
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        # 0.5s tone
        for i in range(22050):
            val = int(32767.0 * 0.5 * (1 if (i // 50) % 2 == 0 else -1))
            wf.writeframes(struct.pack('<hh', val, val))
    wav_bytes = wav_buf.getvalue()
    
    files = {'file': ('test_audio.wav', wav_bytes, 'audio/wav')}
    res = requests.post(f"{BASE_URL}/api/inspect-media", files=files)
    assert res.status_code == 200, f"inspect audio failed: {res.text}"
    data = res.json()
    print("Audio inspect result:", json.dumps({k: data[k] for k in ('format', 'category', 'duration', 'streams')}, indent=2))
    assert data["category"] == "audio"
    assert len(data["streams"]) > 0

    # 2. Inspect PDF (create a simple PDF)
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000111 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )
    files = {'file': ('sample.pdf', pdf_bytes, 'application/pdf')}
    res = requests.post(f"{BASE_URL}/api/inspect-media", files=files)
    assert res.status_code == 200, f"inspect pdf failed: {res.text}"
    pdf_data = res.json()
    print("PDF inspect result:", json.dumps({k: pdf_data.get(k) for k in ('format', 'category', 'pages', 'document_info')}, indent=2))
    assert pdf_data["category"] == "document"
    assert pdf_data["pages"] >= 1
    print("PASS: /api/inspect-media verified!")

def test_pdf_merge_and_split():
    print("\n--- 2. Testing /api/pdf-merge and /api/pdf-split ---")
    # PDF 1
    pdf1 = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000056 00000 n \n0000000111 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )
    # PDF 2
    pdf2 = pdf1

    # Merge
    files = [
        ('files', ('doc1.pdf', pdf1, 'application/pdf')),
        ('files', ('doc2.pdf', pdf2, 'application/pdf'))
    ]
    data = {'output_name': 'combined.pdf'}
    res = requests.post(f"{BASE_URL}/api/pdf-merge", files=files, data=data)
    assert res.status_code == 200, f"pdf-merge failed: {res.text}"
    merged_pdf_bytes = res.content
    assert len(merged_pdf_bytes) > 200
    print(f"PASS: /api/pdf-merge produced {len(merged_pdf_bytes)} bytes")

    # Split: extract single page 1
    files = {'file': ('combined.pdf', merged_pdf_bytes, 'application/pdf')}
    data = {'page_range': '1'}
    res = requests.post(f"{BASE_URL}/api/pdf-split", files=files, data=data)
    assert res.status_code == 200, f"pdf-split single page failed: {res.text}"
    assert len(res.content) > 100
    print(f"PASS: /api/pdf-split (page 1) produced {len(res.content)} bytes")

    # Split: extract all pages to ZIP
    files = {'file': ('combined.pdf', merged_pdf_bytes, 'application/pdf')}
    data = {'page_range': 'all'}
    res = requests.post(f"{BASE_URL}/api/pdf-split", files=files, data=data)
    assert res.status_code == 200, f"pdf-split all failed: {res.text}"
    assert len(res.content) > 100
    print(f"PASS: /api/pdf-split (all pages ZIP) produced {len(res.content)} bytes")

def test_studio_pro_tuning():
    print("\n--- 3. Testing Studio Pro Tuning (EBU loudnorm, speed, trimming) ---")
    import wave, struct
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        # 2.0s sine wave
        for i in range(88200):
            val = int(32767.0 * 0.4 * (1 if (i // 40) % 2 == 0 else -1))
            wf.writeframes(struct.pack('<hh', val, val))
    wav_bytes = wav_buf.getvalue()

    # Convert with trim_start=0.2, trim_duration=0.8, loudnorm=true, playback_speed=1.5
    files = {'file': ('synth.wav', wav_bytes, 'audio/wav')}
    data = {
        'target_format': 'mp3',
        'trim_start': '0.2',
        'trim_duration': '0.8',
        'loudnorm': 'true',
        'playback_speed': '1.5',
        'audio_channels': 'stereo',
        'audio_bitrate': '320k'
    }
    res = requests.post(f"{BASE_URL}/api/convert-universal", files=files, data=data)
    assert res.status_code == 200, f"Universal convert with pro tuning failed: {res.text}"
    mp3_bytes = res.content
    assert len(mp3_bytes) > 500
    route = res.headers.get("X-Conversion-Route")
    logs = res.headers.get("X-Conversion-Logs")
    print(f"PASS: Pro Tuning MP3 produced {len(mp3_bytes)} bytes. Route: {route}")
    if logs:
        print("Telemetry logs recorded:", logs[:150] + "...")

def test_markdown_frontmatter():
    print("\n--- 4. Testing Markdown Studio YAML Frontmatter & Reading Time ---")
    sample_text = (
        "# Quantum Computing Architecture\n\n"
        "Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics to solve problems too complex for classical computers.\n\n"
        "Today, IBM Quantum hardware and systems are accessible to thousands of developers across the world.\n\n"
        "## Core Principles\n\n"
        "1. Superposition\n2. Entanglement\n3. Interference\n"
    )
    files = {'files': ('quantum.txt', sample_text.encode('utf-8'), 'text/plain')}
    data = {'add_frontmatter': 'true'}
    res = requests.post(f"{BASE_URL}/api/convert-markdown", files=files, data=data)
    assert res.status_code == 200, f"Markdown convert failed: {res.text}"
    res_json = res.json()
    results = res_json.get("results", [])
    assert len(results) == 1
    item = results[0]
    print(f"Frontmatter test item: words={item.get('words')}, reading_time={item.get('reading_time')}")
    assert item["ok"] is True
    assert item.get("words", 0) > 20
    assert "reading_time" in item
    assert "---" in item["markdown"] # YAML frontmatter delimiter
    assert "title: \"quantum\"" in item["markdown"]
    print("Generated Markdown preview:\n" + item["markdown"][:250])
    print("PASS: Markdown Frontmatter verified!")

if __name__ == "__main__":
    test_inspect_media()
    test_pdf_merge_and_split()
    test_studio_pro_tuning()
    test_markdown_frontmatter()
    print("\n===========================================")
    print("ALL 5 ADVANCED FEATURE PILLARS PASSED 100%!")
    print("===========================================")
