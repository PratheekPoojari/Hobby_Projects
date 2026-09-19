"""
Test suite for authentication mechanisms, including password hashing, uniqueness constraints, and session generation.
"""

import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from auth import *      # sign_up, login, hash_password, verify_password —
                         # plus link_patient_id/get_account, re-exported transitively
                         # since auth.py has no __all__ of its own
import database          # direct cursor/hospital access, for commits and raw verification

VALID_USERNAME = "testuser1"
VALID_PASSWORD = "Valid#Pass1"
def cleanup_account(username: str) -> None:
    database.cursor.execute("DELETE FROM accounts WHERE username = ?", (username,))
    database.hospital.commit()

def cleanup_user(patient_id: str) -> None:
    database.cursor.execute("DELETE FROM users WHERE patient_id = ?", (patient_id,))
    database.hospital.commit()

def get_account_row(username: str) -> dict | None:
    database.cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
    row = database.cursor.fetchone()
    return dict(row) if row else None
# defensive cleanup up front, in case a previous crashed run left rows behind
for leftover in ["testuser1", "testuser2", "dupeuser", "linkeduser"]:
    cleanup_account(leftover)
cleanup_user("CA9999")

# ---------- hash_password() / verify_password() — pure functions, no input() involved ----------
def test_hash_password_unique_salt_and_hash():
    hashed1, salt1 = hash_password(VALID_PASSWORD)
    hashed2, salt2 = hash_password(VALID_PASSWORD)
    assert salt1 != salt2      # secrets.token_hex is random per call, even for the same password
    assert hashed1 != hashed2  # different salt -> different hash, despite identical input password
    print("test_hash_password_unique_salt_and_hash: PASSED")
def test_hash_password_output_lengths():
    hashed, salt = hash_password(VALID_PASSWORD)
    assert len(salt) == 32    # secrets.token_hex(16) -> 16 bytes -> 32 hex chars
    assert len(hashed) == 64  # sha256 digest -> 32 bytes -> 64 hex chars
    print("test_hash_password_output_lengths: PASSED")
def test_verify_password_correct():
    hashed, salt = hash_password(VALID_PASSWORD)
    assert verify_password(VALID_PASSWORD, hashed, salt) is True
    print("test_verify_password_correct: PASSED")
def test_verify_password_wrong_password():
    hashed, salt = hash_password(VALID_PASSWORD)
    assert verify_password("WrongPass1!", hashed, salt) is False
    print("test_verify_password_wrong_password: PASSED")
def test_verify_password_tampered_hash():
    hashed, salt = hash_password(VALID_PASSWORD)
    tampered = ("0" if hashed[0] != "0" else "1") + hashed[1:]  # simulate a corrupted/tampered stored hash
    assert verify_password(VALID_PASSWORD, tampered, salt) is False
    print("test_verify_password_tampered_hash: PASSED")
# ---------- sign_up() ----------
# sign_up() drives 3 input() calls in order: prompt_username() (loops until valid),
# prompt_password() (loops until valid), prompt_confirm_password() (loops until valid).
def test_signup_success():
    with patch("builtins.input", side_effect=[VALID_USERNAME, VALID_PASSWORD, VALID_PASSWORD]):
        status, data = sign_up()
    assert status == "success"
    assert data == {"username": VALID_USERNAME, "role": "user", "patient_id": None}
    row = get_account_row(VALID_USERNAME)
    assert row is not None
    assert row["role"] == "user"
    assert row["patient_id"] is None
    assert row["hashed_password"] != VALID_PASSWORD  # never stored in plaintext
    assert len(row["salt"]) == 32
    cleanup_account(VALID_USERNAME)
    print("test_signup_success: PASSED")

def test_signup_password_mismatch():
    with patch("builtins.input", side_effect=[VALID_USERNAME, VALID_PASSWORD, "Different#Pass2"]):
        status, data = sign_up()
    assert status == "password_mismatch"
    assert data is None
    assert get_account_row(VALID_USERNAME) is None  # nothing should have been inserted
    print("test_signup_password_mismatch: PASSED")

def test_signup_username_taken():
    with patch("builtins.input", side_effect=["dupeuser", VALID_PASSWORD, VALID_PASSWORD]):
        first_status, _ = sign_up()
    assert first_status == "success"
    with patch("builtins.input", side_effect=["dupeuser", "Another#Pass9", "Another#Pass9"]):
        second_status, second_data = sign_up()
    assert second_status == "username_taken"
    assert second_data is None
    database.cursor.execute("SELECT COUNT(*) FROM accounts WHERE username = ?", ("dupeuser",))
    assert database.cursor.fetchone()[0] == 1  # only the first insert should exist
    cleanup_account("dupeuser")
    print("test_signup_username_taken: PASSED")

def test_signup_username_retry_loop():
    # "ab" is under prompt_username()'s 3-char minimum, so the loop must re-prompt —
    # a second, valid username is required before the function can return at all.
    with patch("builtins.input", side_effect=["ab", "testuser2", VALID_PASSWORD, VALID_PASSWORD]):
        status, data = sign_up()
    assert status == "success"
    assert data["username"] == "testuser2"
    cleanup_account("testuser2")
    print("test_signup_username_retry_loop: PASSED")

def test_signup_password_retry_loop():
    # no uppercase, no symbol — fails is_valid_password(), forcing prompt_password() to loop once.
    with patch("builtins.input", side_effect=[VALID_USERNAME, "alllowercase1", VALID_PASSWORD, VALID_PASSWORD]):
        status, data = sign_up()
    assert status == "success"
    cleanup_account(VALID_USERNAME)
    print("test_signup_password_retry_loop: PASSED")
# ---------- login() ----------
# login() drives input() directly for role, then prompt_username() (its own loop), then a
# direct input() for password.
def test_login_success():
    with patch("builtins.input", side_effect=[VALID_USERNAME, VALID_PASSWORD, VALID_PASSWORD]):
        sign_up()
    with patch("builtins.input", side_effect=["user", VALID_USERNAME, VALID_PASSWORD]):
        status, data = login()
    assert status == "success"
    assert data == {"username": VALID_USERNAME, "role": "user", "patient_id": None}
    cleanup_account(VALID_USERNAME)
    print("test_login_success: PASSED")

def test_login_wrong_password():
    with patch("builtins.input", side_effect=[VALID_USERNAME, VALID_PASSWORD, VALID_PASSWORD]):
        sign_up()
    with patch("builtins.input", side_effect=["user", VALID_USERNAME, "WrongPass1!"]):
        status, data = login()
    assert status == "invalid_credentials"
    assert data is None
    cleanup_account(VALID_USERNAME)
    print("test_login_wrong_password: PASSED")

def test_login_nonexistent_username():
    with patch("builtins.input", side_effect=["user", "ghostuser99", "Whatever#Pass1"]):
        status, data = login()
    assert status == "invalid_credentials"
    assert data is None
    print("test_login_nonexistent_username: PASSED")

def test_login_wrong_role():
    with patch("builtins.input", side_effect=[VALID_USERNAME, VALID_PASSWORD, VALID_PASSWORD]):
        sign_up()
    with patch("builtins.input", side_effect=["admin", VALID_USERNAME, VALID_PASSWORD]):
        status, data = login()
    assert status == "invalid_credentials"
    assert data is None
    cleanup_account(VALID_USERNAME)
    print("test_login_wrong_role: PASSED")

def test_login_role_case_insensitive():
    with patch("builtins.input", side_effect=[VALID_USERNAME, VALID_PASSWORD, VALID_PASSWORD]):
        sign_up()
    with patch("builtins.input", side_effect=["  User  ", VALID_USERNAME, VALID_PASSWORD]):
        status, data = login()
    assert status == "success"
    assert data["role"] == "user"
    cleanup_account(VALID_USERNAME)
    print("test_login_role_case_insensitive: PASSED")

def test_login_returns_linked_patient_id():
    with patch("builtins.input", side_effect=["linkeduser", VALID_PASSWORD, VALID_PASSWORD]):
        sign_up()
    # accounts.patient_id has a real FK to users(patient_id), and foreign_keys is ON —
    # so link_patient_id() needs a users row to actually point at, or it raises IntegrityError.
    database.cursor.execute("""
        INSERT INTO users (patient_id, first_name, last_name, date_of_birth, symptoms)
        VALUES (?, ?, ?, ?, ?)
        """, ("CA9999", "Test", "Patient", "01-01-2000", "none"))
    link_patient_id("linkeduser", "CA9999")
    database.hospital.commit()
    with patch("builtins.input", side_effect=["user", "linkeduser", VALID_PASSWORD]):
        status, data = login()
    assert status == "success"
    assert data["patient_id"] == "CA9999"
    cleanup_account("linkeduser")
    cleanup_user("CA9999")
    print("test_login_returns_linked_patient_id: PASSED")

def run_all():
    test_hash_password_unique_salt_and_hash()
    test_hash_password_output_lengths()
    test_verify_password_correct()
    test_verify_password_wrong_password()
    test_verify_password_tampered_hash()
    test_signup_success()
    test_signup_password_mismatch()
    test_signup_username_taken()
    test_signup_username_retry_loop()
    test_signup_password_retry_loop()
    test_login_success()
    test_login_wrong_password()
    test_login_nonexistent_username()
    test_login_wrong_role()
    test_login_role_case_insensitive()
    test_login_returns_linked_patient_id()
    print("\nAll auth.py tests passed.")

if __name__ == "__main__":
    run_all()
