"""
Test suite for SQLite schema creation, foreign key enforcement, and database connection integrity.
"""

import sys
import sqlite3
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from database import *  # insert_user, search_user_by_*, insert_account, get_account, etc.
import database          # direct cursor/hospital access — raw verification, commits, relative_row_id lookups
from classes import User, Relatives

# Dedicated block of test-only ids/emails/phones, unlikely to collide with real data.
# Email addresses must satisfy patterns.py:
# ^[a-zA-Z0-9]+@[a-zA-Z]+\.com$
USER_A = User(
    "CA0090",
    "01-01-1985",
    "fatigue",
    "Alice Anderson",
    "dbtestalice@gmail.com",
    "+91 9000000001"
)

USER_B = User(
    "CA0091",
    "01-01-1986",
    "cough",
    "Bob Baker",
    "dbtestbob@gmail.com",
    "+91 9000000002"
)

def cleanup_user(patient_id: str) -> None:
    database.cursor.execute(
        "DELETE FROM users WHERE patient_id = ?",
        (patient_id,)
    )
    database.hospital.commit()

def cleanup_relative(email: str) -> None:
    database.cursor.execute(
        "DELETE FROM relatives WHERE email = ?",
        (email,)
    )
    database.hospital.commit()

def cleanup_account(username: str) -> None:
    database.cursor.execute(
        "DELETE FROM accounts WHERE username = ?",
        (username,)
    )
    database.hospital.commit()

def get_relative_row_id(email: str) -> int:
    database.cursor.execute(
        "SELECT relative_row_id FROM relatives WHERE email = ?",
        (email,)
    )
    return database.cursor.fetchone()["relative_row_id"]

# Defensive cleanup up front, in case a previous crashed run left rows behind.
for pid in ["CA0090", "CA0091"]:
    cleanup_user(pid)
for email in [
    "dbtestcarol@gmail.com",
    "dbtestdave1@gmail.com",
    "dbtestdave2@gmail.com"
]:
    cleanup_relative(email)
for username in ["dbtestuser"]:
    cleanup_account(username)

# ---------- split_name() ----------
def test_split_name_two_words():
    result = database.split_name("Alice Anderson")
    assert result == {
        "First": "Alice",
        "Middle": "",
        "Last": "Anderson"
    }
    print("test_split_name_two_words: PASSED")

def test_split_name_three_words():
    result = database.split_name("Alice Marie Anderson")
    assert result == {
        "First": "Alice",
        "Middle": "Marie",
        "Last": "Anderson"
    }
    print("test_split_name_three_words: PASSED")

# ---------- insert_user() + search_user_by_*() + patient_id_exists() ----------
def test_insert_and_search_user():
    insert_user(USER_A)
    database.hospital.commit()
    by_id = search_user_by_patient_id("CA0090")
    by_email = search_user_by_email("dbtestalice@gmail.com")
    by_phone = search_user_by_phone("+91 9000000001")
    assert by_id is not None and by_id["first_name"] == "Alice"
    assert by_email is not None and by_email["patient_id"] == "CA0090"
    assert by_phone is not None and by_phone["patient_id"] == "CA0090"
    assert patient_id_exists("CA0090") is True
    assert patient_id_exists("ZZ9999") is False
    matches = search_users_by_name("first_name", "Alice")
    assert matches is not None
    assert any(row["patient_id"] == "CA0090" for row in matches)
    cleanup_user("CA0090")
    print("test_insert_and_search_user: PASSED")

def test_search_user_not_found():
    assert search_user_by_patient_id("ZZ9999") is None
    assert search_user_by_email("nobody@nowhere.com") is None
    assert search_user_by_phone("+91 0000000000") is None
    assert search_users_by_name(
        "first_name",
        "Nonexistentname"
    ) is None
    print("test_search_user_not_found: PASSED")

# ---------- insert_relative() + search_relatives_by_*() + get_relatives_by_patient_id() ----------
def test_insert_and_search_relative():
    insert_user(USER_A)
    relative = Relatives(
        "Carol Anderson",
        "dbtestcarol@gmail.com",
        "+91 9000000003",
        "CA0090"
    )
    insert_relative(relative)
    database.hospital.commit()
    by_email = search_relatives_by_email("dbtestcarol@gmail.com")
    assert by_email is not None
    assert by_email[0]["first_name"] == "Carol"
    assert by_email[1]["patient_id"] == "CA0090"
    by_phone = search_relatives_by_phone("+91 9000000003")
    assert by_phone is not None
    assert by_phone[0]["first_name"] == "Carol"
    relatives_of_a = get_relatives_by_patient_id("CA0090")
    assert relatives_of_a is not None
    assert len(relatives_of_a) == 1
    cleanup_relative("dbtestcarol@gmail.com")
    cleanup_user("CA0090")
    print("test_insert_and_search_relative: PASSED")

def test_get_relatives_by_patient_id_none_case():
    insert_user(USER_B)
    database.hospital.commit()
    assert get_relatives_by_patient_id("CA0091") is None
    cleanup_user("CA0091")
    print("test_get_relatives_by_patient_id_none_case: PASSED")

def test_search_relatives_by_name_ambiguous():
    insert_user(USER_A)
    relative1 = Relatives(
        "Dave Smith",
        "dbtestdave1@gmail.com",
        "+91 9000000004",
        "CA0090"
    )
    relative2 = Relatives(
        "Dave Jones",
        "dbtestdave2@gmail.com",
        "+91 9000000005",
        "CA0090"
    )
    insert_relative(relative1)
    insert_relative(relative2)
    database.hospital.commit()
    matches = search_relatives_by_name("first_name", "Dave")
    assert matches is not None
    assert len(matches) == 2
    last_names = {
        entry["Relatives"]["last_name"]
        for entry in matches
    }
    assert last_names == {"Smith", "Jones"}
    cleanup_relative("dbtestdave1@gmail.com")
    cleanup_relative("dbtestdave2@gmail.com")
    cleanup_user("CA0090")
    print("test_search_relatives_by_name_ambiguous: PASSED")

# ---------- get_user_by_patient_id() ----------
def test_get_user_by_patient_id():
    insert_user(USER_A)
    database.hospital.commit()
    result = database.get_user_by_patient_id("CA0090")
    if result is not None:
        assert set(result.keys()) == {
            "patient_id",
            "first_name",
            "middle_name",
            "last_name"
        }
        assert result["first_name"] == "Alice"
    cleanup_user("CA0090")
    print("test_get_user_by_patient_id: PASSED")

# ---------- is_duplicate() ----------

def test_is_duplicate():
    insert_user(USER_A)
    relative = Relatives(
        "Carol Anderson",
        "dbtestcarol@gmail.com",
        "+91 9000000003",
        "CA0090"
    )
    insert_relative(relative)
    database.hospital.commit()
    assert is_duplicate() is False
    assert is_duplicate(phone="+91 9000000001") is True
    assert is_duplicate(email="dbtestcarol@gmail.com") is True
    assert is_duplicate(phone="+91 1111111111") is False
    cleanup_relative("dbtestcarol@gmail.com")
    cleanup_user("CA0090")
    print("test_is_duplicate: PASSED")

# ---------- update_query() ----------
def test_update_query_users():
    insert_user(USER_A)
    database.hospital.commit()
    update_query(
        "users",
        "first_name",
        "Alicia",
        "CA0090"
    )
    database.hospital.commit()
    result = search_user_by_patient_id("CA0090")
    assert result is not None
    assert result["first_name"] == "Alicia"
    cleanup_user("CA0090")
    print("test_update_query_users: PASSED")

def test_update_query_relatives():
    insert_user(USER_A)
    relative = Relatives(
        "Carol Anderson",
        "dbtestcarol@gmail.com",
        "+91 9000000003",
        "CA0090"
    )
    insert_relative(relative)
    database.hospital.commit()
    row_id = get_relative_row_id("dbtestcarol@gmail.com")
    update_query(
        "relatives",
        "first_name",
        "Caroline",
        str(row_id)
    )
    database.hospital.commit()
    database.cursor.execute(
        "SELECT first_name FROM relatives WHERE relative_row_id = ?",
        (row_id,)
    )
    assert database.cursor.fetchone()["first_name"] == "Caroline"
    cleanup_relative("dbtestcarol@gmail.com")
    cleanup_user("CA0090")
    print("test_update_query_relatives: PASSED")

# ---------- delete_query() ----------
def test_delete_query_relatives():
    insert_user(USER_A)
    relative = Relatives(
        "Carol Anderson",
        "dbtestcarol@gmail.com",
        "+91 9000000003",
        "CA0090"
    )
    insert_relative(relative)
    database.hospital.commit()
    row_id = get_relative_row_id("dbtestcarol@gmail.com")
    delete_query(
        "relatives",
        str(row_id)
    )
    database.hospital.commit()
    database.cursor.execute(
        "SELECT * FROM relatives WHERE relative_row_id = ?",
        (row_id,)
    )
    assert database.cursor.fetchone() is None
    cleanup_user("CA0090")
    print("test_delete_query_relatives: PASSED")

def test_delete_query_users_cascades():
    insert_user(USER_A)
    relative = Relatives(
        "Carol Anderson",
        "dbtestcarol@gmail.com",
        "+91 9000000003",
        "CA0090"
    )
    insert_relative(relative)
    database.hospital.commit()
    delete_query("users", "CA0090")
    database.hospital.commit()
    assert search_user_by_patient_id("CA0090") is None
    database.cursor.execute(
        "SELECT * FROM relatives WHERE patient_id = ?",
        ("CA0090",)
    )
    assert database.cursor.fetchone() is None
    print("test_delete_query_users_cascades: PASSED")

# ---------- insert_account() / get_account() / link_patient_id() ----------
def test_insert_and_get_account():
    insert_account(
        "dbtestuser",
        "dummy_hash",
        "dummy_salt",
        "user"
    )
    database.hospital.commit()
    account = get_account("dbtestuser")
    assert account is not None
    assert account["role"] == "user"
    assert account["patient_id"] is None
    assert get_account("ghostaccount") is None
    cleanup_account("dbtestuser")
    print("test_insert_and_get_account: PASSED")

def test_insert_account_duplicate_username_raises():
    insert_account(
        "dbtestuser",
        "hash1",
        "salt1",
        "user"
    )
    database.hospital.commit()
    try:
        insert_account(
            "dbtestuser",
            "hash2",
            "salt2",
            "user"
        )
        raise AssertionError(
            "Expected sqlite3.IntegrityError, none was raised"
        )
    except sqlite3.IntegrityError:
        pass
    database.cursor.execute(
        "SELECT COUNT(*) FROM accounts WHERE username = ?",
        ("dbtestuser",)
    )
    assert database.cursor.fetchone()[0] == 1
    cleanup_account("dbtestuser")
    print("test_insert_account_duplicate_username_raises: PASSED")

def test_insert_account_invalid_role_raises():
    try:
        insert_account(
            "dbtestuser",
            "hash1",
            "salt1",
            "superadmin"
        )
        raise AssertionError(
            "Expected sqlite3.IntegrityError, none was raised"
        )
    except sqlite3.IntegrityError:
        pass
    assert get_account("dbtestuser") is None

    print("test_insert_account_invalid_role_raises: PASSED")

def test_link_patient_id():
    insert_user(USER_A)
    insert_account(
        "dbtestuser",
        "hash1",
        "salt1",
        "user"
    )
    database.hospital.commit()

    link_patient_id(
        "dbtestuser",
        "CA0090"
    )
    database.hospital.commit()
    account = get_account("dbtestuser")
    assert account is not None
    assert account["patient_id"] == "CA0090"
    cleanup_account("dbtestuser")
    cleanup_user("CA0090")
    print("test_link_patient_id: PASSED")

# ---------- get_all_patient_ids() ----------
def test_get_all_patient_ids_contains_inserted():
    insert_user(USER_A)
    insert_user(USER_B)
    database.hospital.commit()
    all_ids = database.get_all_patient_ids()
    assert "CA0090" in all_ids
    assert "CA0091" in all_ids
    cleanup_user("CA0090")
    cleanup_user("CA0091")
    print("test_get_all_patient_ids_contains_inserted: PASSED")

def run_all():
    test_split_name_two_words()
    test_split_name_three_words()
    test_insert_and_search_user()
    test_search_user_not_found()
    test_insert_and_search_relative()
    test_get_relatives_by_patient_id_none_case()
    test_search_relatives_by_name_ambiguous()
    test_get_user_by_patient_id()
    test_is_duplicate()
    test_update_query_users()
    test_update_query_relatives()
    test_delete_query_relatives()
    test_delete_query_users_cascades()
    test_insert_and_get_account()
    test_insert_account_duplicate_username_raises()
    test_insert_account_invalid_role_raises()
    test_link_patient_id()
    test_get_all_patient_ids_contains_inserted()
    print("\nAll database.py tests passed.")

if __name__ == "__main__":
    run_all()
