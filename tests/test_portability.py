"""Host-portability checks that need no running server.

Unlike the other files in this folder (which call a live container on :8394),
these import the backend directly, so they run anywhere the backend
requirements are installed:

    pip install -r backend/requirements.txt pytest
    pytest tests/test_portability.py
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

# app.py creates its data directories at import time; keep them out of /data.
_tmp = tempfile.mkdtemp(prefix="vert_test_")
os.environ.setdefault("INPUT_DIR", os.path.join(_tmp, "in"))
os.environ.setdefault("OUTPUT_DIR", os.path.join(_tmp, "out"))

import app as vert_app  # noqa: E402
from markitdown_engine import avoid_reserved_name, safe_stem, unique_name  # noqa: E402


# --- filenames must be writable on every host OS ----------------------------

@pytest.mark.parametrize(
    "name",
    ["con", "CON", "nul", "Aux", "prn", "com1", "LPT9", "con.md", "NUL.tar.gz", "aux.pdf"],
)
def test_windows_device_names_are_prefixed(name):
    out = avoid_reserved_name(name)
    assert out == f"_{name}"
    assert vert_app.safe_filename(name) == f"_{name}"


@pytest.mark.parametrize("name", ["console.md", "com10.md", "report.pdf", "lpt.md", "my-con.md", "nullable"])
def test_ordinary_names_are_untouched(name):
    assert avoid_reserved_name(name) == name


def test_safe_stem_avoids_reserved_names():
    assert safe_stem("CON.pdf") == "_CON"
    assert safe_stem("notes.pdf") == "notes"


def test_path_traversal_still_blocked():
    assert vert_app.safe_filename("../../etc/passwd") == "passwd"
    # A Windows-style path from a client has no directory meaning here, but must
    # still come out as one harmless name with no separators.
    assert vert_app.safe_filename("C:\\Windows\\system32\\evil.dll") == "C_Windows_system32_evil.dll"


def test_unique_name_is_case_insensitive():
    """macOS/Windows would overwrite Report.md with report.md on disk."""
    taken = set()
    first = unique_name("Report.pdf", taken)
    second = unique_name("report.docx", taken)
    assert first.lower() != second.lower()
    assert first == "Report.md"
    assert second == "report-docx.md"


def test_unique_name_keeps_counting_on_repeat_collisions():
    taken = set()
    names = [unique_name("a.pdf", taken), unique_name("A.pdf", taken), unique_name("a.PDF", taken)]
    assert len({n.lower() for n in names}) == 3


# --- telemetry must not assume Apple Silicon --------------------------------

def test_arm_reports_neon_and_x86_does_not():
    assert vert_app._detect_simd("arm64") == "NEON"
    assert vert_app._detect_simd("aarch64") == "NEON"
    assert vert_app._detect_simd("x86_64") != "NEON"


def test_x86_simd_follows_cpu_flags(monkeypatch):
    monkeypatch.setattr(vert_app, "_x86_cpu_flags", lambda: {"sse4_2", "avx", "avx2"})
    assert vert_app._detect_simd("x86_64") == "AVX2"
    monkeypatch.setattr(vert_app, "_x86_cpu_flags", lambda: {"avx512f", "avx2"})
    assert vert_app._detect_simd("amd64") == "AVX-512"
    monkeypatch.setattr(vert_app, "_x86_cpu_flags", lambda: set())
    assert vert_app._detect_simd("x86_64") == "SSE2"


def test_unknown_architecture_reports_no_simd():
    assert vert_app._detect_simd("riscv64") is None
    assert vert_app._detect_simd("s390x") is None


@pytest.mark.parametrize("arch", ["x86_64", "aarch64", "arm64", "riscv64"])
def test_host_label_makes_no_vendor_claims(arch):
    label = vert_app._detect_host_label(arch, "Linux")
    assert "Apple" not in label
    assert "Linux container" in label


def test_system_info_is_self_consistent():
    info = vert_app.get_system_info()
    assert info["cores_logical"] >= 1
    assert info["cores_physical"] >= 1
    accel = info["acceleration"]
    assert accel["container_neon_simd"] == (accel["simd"] == "NEON")
    assert accel["container_threads"] == info["cores_logical"]
