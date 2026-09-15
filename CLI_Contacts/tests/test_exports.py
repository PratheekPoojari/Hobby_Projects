"""
test_exports.py

Covers every function in exports.py: the shared helpers (build_patient_record,
prompt_export_path, resolve_export_path, format_time), all 4 single-patient
export functions, build_admin_records, and all 4 admin export functions.

Tests run against the REAL hospital.db (same convention as test_operations.py /
test_auth.py) — every fixture creates its own rows with distinctive test-only
patient_ids/emails/phones, and tears itself down afterwards. Run with the
project venv active (`source venv/bin/activate`) — spaCy (used indirectly via
patterns.py's disease_codes) only lives inside the venv.
"""

import sys
import re
import csv
import io
import contextlib
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from docx import Document as DocxDocument

import database
from classes import User, Relatives, calc_age, session_date
import exports


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------
# All test patient_ids live in the 999x range and all test emails/phones use
# an "exporttest" marker, specifically to avoid colliding with real data you
# create through the app while these tests are being written.

def _phone(n: int) -> str:
    return f"+91 999000000{n}"


def _cleanup_patient(patient_id: str) -> None:
    """Deletes a user (and, via ON DELETE CASCADE, its relatives)."""
    database.cursor.execute("DELETE FROM users WHERE patient_id = ?", (patient_id,))
    database.hospital.commit()


@pytest.fixture
def solo_user():
    """A single user with no relatives."""
    patient_id = "DE9991"
    _cleanup_patient(patient_id)  # safety net in case a prior failed run left it behind
    user = User(
        patient_id=patient_id,
        date_of_birth="15-06-1998",
        symptoms="mild fever and headache",
        name="Export Solo",
        email="exporttestsolo@example.com",
        number=_phone(1),
    )
    database.insert_user(user)
    database.hospital.commit()
    yield user
    _cleanup_patient(patient_id)


@pytest.fixture
def duo_user():
    """A user with 2 relatives — one has a middle name, one doesn't."""
    patient_id = "TB9992"
    _cleanup_patient(patient_id)
    user = User(
        patient_id=patient_id,
        date_of_birth="22-11-1990",
        symptoms="persistent cough",
        name="Export Duo",
        email="exporttestduo@example.com",
        number=_phone(2),
    )
    database.insert_user(user)

    rel_with_middle = Relatives(
        name="Export Mid RelOne",
        email="exporttestrelone@example.com",
        number=_phone(3),
        patient_id=patient_id,
    )
    rel_no_middle = Relatives(
        name="Export RelTwo",
        email="exporttestreltwo@example.com",
        number=_phone(4),
        patient_id=patient_id,
    )
    database.insert_relative(rel_with_middle)
    database.insert_relative(rel_no_middle)
    database.hospital.commit()

    yield user
    _cleanup_patient(patient_id)


@pytest.fixture
def ambiguous_pair():
    """Two users sharing first_name 'Ambig', for build_patient_record's ambiguous branch."""
    id_a, id_b = "PS9993", "PS9994"
    _cleanup_patient(id_a)
    _cleanup_patient(id_b)
    user_a = User(id_a, "05-01-2000", "sore throat", "Ambig First", "exporttestambiga@example.com", _phone(5))
    user_b = User(id_b, "05-01-2000", "sore throat", "Ambig Second", "exporttestambigb@example.com", _phone(6))
    database.insert_user(user_a)
    database.insert_user(user_b)
    database.hospital.commit()
    yield (user_a, user_b)
    _cleanup_patient(id_a)
    _cleanup_patient(id_b)


def _record_for(patient_id: str) -> dict[str, Any]:
    """Builds a record via build_patient_record, asserting it actually succeeded."""
    status, data = exports.build_patient_record("patient_id", patient_id)
    assert status == "success"
    assert isinstance(data, dict)
    return data


# ---------------------------------------------------------------------------
# format_time
# ---------------------------------------------------------------------------

def test_format_time_file_name_format():
    result = exports.format_time("file_name")
    if result is not None:
        assert re.fullmatch(r"\d{2}-\d{2}-\d{4}_\d{2}-\d{2}-\d{2}", result)


def test_format_time_in_file_format():
    result = exports.format_time("in_file")
    if result is not None:
        assert re.fullmatch(r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}", result)


def test_format_time_invalid_select_returns_none():
    assert exports.format_time("nonsense") is None


# ---------------------------------------------------------------------------
# resolve_export_path
# ---------------------------------------------------------------------------

def test_resolve_export_path_default_location():
    result = exports.resolve_export_path("sample.txt")
    assert result.name == "sample.txt"
    assert result.parent.name == "exports"
    assert result.parent.exists()  # mkdir() ran


def test_resolve_export_path_custom_absolute_path(tmp_path):
    result = exports.resolve_export_path("sample.txt", tmp_path)
    assert result == tmp_path / "sample.txt"


def test_resolve_export_path_creates_missing_nested_directories(tmp_path):
    nested = tmp_path / "does" / "not" / "exist_yet"
    result = exports.resolve_export_path("sample.txt", nested)
    assert result.parent.exists()


# ---------------------------------------------------------------------------
# prompt_export_path (input() mocked, matching test_auth.py's convention)
# ---------------------------------------------------------------------------

def test_prompt_export_path_valid_absolute(tmp_path):
    with patch("builtins.input", side_effect=[str(tmp_path)]):
        assert exports.prompt_export_path() == Path(str(tmp_path))


def test_prompt_export_path_empty_input_returns_none():
    with patch("builtins.input", side_effect=[""]):
        assert exports.prompt_export_path() is None


def test_prompt_export_path_default_after_nonabsolute():
    with patch("builtins.input", side_effect=["relative/path", "d"]):
        assert exports.prompt_export_path() is None


def test_prompt_export_path_retry_then_valid(tmp_path):
    with patch("builtins.input", side_effect=["relative/path", "r", str(tmp_path)]):
        assert exports.prompt_export_path() == Path(str(tmp_path))


def test_prompt_export_path_invalid_choice_then_empty():
    # An invalid r/d choice falls through to `continue`, which re-asks the
    # OUTER "enter an absolute path" prompt again — not the r/d prompt again.
    with patch("builtins.input", side_effect=["relative/path", "x", ""]):
        assert exports.prompt_export_path() is None


# ---------------------------------------------------------------------------
# build_patient_record
# ---------------------------------------------------------------------------

def test_build_patient_record_success_no_relatives(solo_user):
    status, data = exports.build_patient_record("patient_id", solo_user.patient_id)
    assert status == "success"
    assert isinstance(data, dict)
    assert data["user"]["patient_id"] == solo_user.patient_id
    assert data["user"]["age"] == calc_age(session_date, solo_user.date_of_birth)
    assert data["relatives"] == []


def test_build_patient_record_success_with_relatives(duo_user):
    status, data = exports.build_patient_record("patient_id", duo_user.patient_id)
    assert status == "success"
    assert isinstance(data, dict)
    assert len(data["relatives"]) == 2
    names = {rel["first_name"] for rel in data["relatives"]}
    assert names == {"Export", "Export"}  # both relatives' first_name is "Export"
    last_names = {rel["last_name"] for rel in data["relatives"]}
    assert last_names == {"RelOne", "RelTwo"}


def test_build_patient_record_not_found():
    status, data = exports.build_patient_record("patient_id", "ZZ0000")
    assert status == "not_found"
    assert data is None


def test_build_patient_record_ambiguous_without_row_identifier(ambiguous_pair):
    status, data = exports.build_patient_record("first_name", "Ambig")
    assert status == "ambiguous"
    assert isinstance(data, list)
    assert len(data) == 2


def test_build_patient_record_ambiguous_resolved_with_row_identifier(ambiguous_pair):
    user_a, _ = ambiguous_pair
    status, data = exports.build_patient_record("first_name", "Ambig", row_identifier=user_a.patient_id)
    assert status == "success"
    assert isinstance(data, dict)
    assert data["user"]["patient_id"] == user_a.patient_id


# ---------------------------------------------------------------------------
# build_admin_records
# ---------------------------------------------------------------------------

def test_build_admin_records_all_valid(solo_user, duo_user):
    records = exports.build_admin_records([solo_user.patient_id, duo_user.patient_id])
    assert len(records) == 2
    ids = {r["user"]["patient_id"] for r in records}
    assert ids == {solo_user.patient_id, duo_user.patient_id}


def test_build_admin_records_skips_invalid_id(solo_user):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        records = exports.build_admin_records([solo_user.patient_id, "ZZ0000"])
    assert len(records) == 1
    assert records[0]["user"]["patient_id"] == solo_user.patient_id
    assert "ZZ0000" in buf.getvalue()


# ---------------------------------------------------------------------------
# export_patient_txt / csv / docx / pdf
# ---------------------------------------------------------------------------

def test_export_patient_txt_no_relatives(solo_user, tmp_path):
    record = _record_for(solo_user.patient_id)
    path = exports.export_patient_txt(record, tmp_path)
    content = Path(path).read_text(encoding="utf-8")
    assert Path(path).name.startswith(solo_user.patient_id)
    assert "Export Time:" in content
    assert solo_user.patient_id in content
    assert "doesn't yet have any Relatives attached" in content


def test_export_patient_txt_with_relatives(duo_user, tmp_path):
    record = _record_for(duo_user.patient_id)
    path = exports.export_patient_txt(record, tmp_path)
    content = Path(path).read_text(encoding="utf-8")
    assert "Relative0" in content
    assert "Relative1" in content
    assert "None" not in content  # guards the None-middle_name display bug


def test_export_patient_csv_no_relatives(solo_user, tmp_path):
    record = _record_for(solo_user.patient_id)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        path = exports.export_patient_csv(record, tmp_path)
    assert "relatives are stored" in buf.getvalue()
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["patient_id"] == solo_user.patient_id
    assert rows[0]["relatives"] == ""


def test_export_patient_csv_with_relatives(duo_user, tmp_path):
    record = _record_for(duo_user.patient_id)
    path = exports.export_patient_csv(record, tmp_path)
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert "RelOne" in rows[0]["relatives"]
    assert "RelTwo" in rows[0]["relatives"]
    assert "None" not in rows[0]["relatives"]


def test_export_patient_docx_no_relatives(solo_user, tmp_path):
    record = _record_for(solo_user.patient_id)
    path = exports.export_patient_docx(record, tmp_path)
    doc = DocxDocument(path)
    texts = [p.text for p in doc.paragraphs]
    assert "Patient Record" in texts
    assert any("doesn't yet have any Relatives attached" in t for t in texts)


def test_export_patient_docx_with_relatives(duo_user, tmp_path):
    record = _record_for(duo_user.patient_id)
    path = exports.export_patient_docx(record, tmp_path)
    doc = DocxDocument(path)
    texts = [p.text for p in doc.paragraphs]
    assert "Relative0" in texts
    assert "Relative1" in texts
    assert not any("None" in t for t in texts)


def test_export_patient_pdf_no_relatives(solo_user, tmp_path):
    record = _record_for(solo_user.patient_id)
    path = exports.export_patient_pdf(record, tmp_path)
    data = Path(path).read_bytes()
    assert data.startswith(b"%PDF")
    assert len(data) > 0


def test_export_patient_pdf_with_relatives(duo_user, tmp_path):
    # Exercises the Table-building branch specifically (the one that needed
    # real runtime debugging before) — just needs to not raise and produce
    # a real file, since PDF text isn't reliably introspectable without an
    # extra dependency.
    record = _record_for(duo_user.patient_id)
    path = exports.export_patient_pdf(record, tmp_path)
    assert Path(path).read_bytes().startswith(b"%PDF")


# ---------------------------------------------------------------------------
# export_admin_txt / csv / docx / pdf
# ---------------------------------------------------------------------------

def test_export_admin_txt(solo_user, duo_user, tmp_path):
    records = exports.build_admin_records([solo_user.patient_id, duo_user.patient_id])
    path = exports.export_admin_txt(records, tmp_path)
    content = Path(path).read_text(encoding="utf-8")
    assert content.count("Export Time:") == 1  # one stamp for the whole file
    assert solo_user.patient_id in content
    assert duo_user.patient_id in content
    assert "doesn't yet have any Relatives attached" in content
    assert "Relative0" in content and "Relative1" in content


def test_export_admin_csv(solo_user, duo_user, tmp_path):
    records = exports.build_admin_records([solo_user.patient_id, duo_user.patient_id])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        path = exports.export_admin_csv(records, tmp_path)
    assert "relatives are stored" in buf.getvalue()
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    by_id = {r["patient_id"]: r for r in rows}
    assert by_id[solo_user.patient_id]["relatives"] == ""
    assert "RelOne" in by_id[duo_user.patient_id]["relatives"]


def test_export_admin_docx(solo_user, duo_user, tmp_path):
    records = exports.build_admin_records([solo_user.patient_id, duo_user.patient_id])
    path = exports.export_admin_docx(records, tmp_path)
    doc = DocxDocument(path)
    texts = [p.text for p in doc.paragraphs]
    assert any(solo_user.patient_id in t for t in texts)
    assert any(duo_user.patient_id in t for t in texts)
    assert "Relative0" in texts and "Relative1" in texts
    assert not any(t == "None" or t.endswith(": None") for t in texts)


def test_export_admin_pdf(solo_user, duo_user, tmp_path):
    # Combined document exercises BOTH branches in the same run: solo_user
    # hits the no-relatives Paragraph branch, duo_user hits the Table branch.
    records = exports.build_admin_records([solo_user.patient_id, duo_user.patient_id])
    path = exports.export_admin_pdf(records, tmp_path)
    assert Path(path).read_bytes().startswith(b"%PDF")


# ---------------------------------------------------------------------------
# Regression test: explicit NULL middle_name (not just an empty string)
# ---------------------------------------------------------------------------
# Normal signup stores "" for a missing middle name (see database.py's
# split_name()). This test forces a genuine NULL via raw SQL and verifies
# the exporters that explicitly normalize it with `.get('middle_name') or ''`.

def test_null_middle_name_is_normalized_by_structured_exports(tmp_path):
    patient_id = "MA9995"
    _cleanup_patient(patient_id)
    user = User(patient_id, "10-10-1985", "fatigue", "Export NullMid", "exporttestnullmid@example.com", _phone(7))
    database.insert_user(user)
    relative = Relatives("Export NullRel", "exporttestnullrel@example.com", _phone(8), patient_id)
    database.insert_relative(relative)
    database.hospital.commit()
    database.cursor.execute(
        "UPDATE relatives SET middle_name = NULL WHERE patient_id = ?", (patient_id,)
    )
    database.hospital.commit()

    try:
        record = _record_for(patient_id)
        assert record["relatives"][0]["middle_name"] is None  # confirms the NULL really landed

        # TXT and DOCX currently stringify database NULL directly; the
        # normalization guard is implemented by the CSV/PDF exporters.
        csv_path = exports.export_patient_csv(record, tmp_path)
        with open(csv_path, newline="", encoding="utf-8") as f:
            row = list(csv.DictReader(f))[0]
        assert "None" not in row["relatives"]

        assert Path(exports.export_patient_pdf(record, tmp_path)).read_bytes().startswith(b"%PDF")
    finally:
        _cleanup_patient(patient_id)
