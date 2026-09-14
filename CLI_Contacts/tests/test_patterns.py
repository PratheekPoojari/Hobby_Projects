import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from patterns import *  # is_valid_email, is_valid_phone_number, is_valid_name, etc., plus disease_codes
from patterns import is_valid_patient_id_format

# ---------- is_valid_email() ----------
def test_email_valid():
    assert is_valid_email("abc123@gmail.com") is True
    print("test_email_valid: PASSED")

def test_email_missing_at_symbol():
    assert is_valid_email("abcgmail.com") is False
    print("test_email_missing_at_symbol: PASSED")

def test_email_digits_in_domain():
    assert is_valid_email("abc@gmail1.com") is False  # domain part only allows letters
    print("test_email_digits_in_domain: PASSED")

def test_email_missing_dot_com():
    assert is_valid_email("abc@gmail") is False
    print("test_email_missing_dot_com: PASSED")

def test_email_dot_in_local_part():
    assert is_valid_email("ab.c@gmail.com") is False  # local part class excludes "."
    print("test_email_dot_in_local_part: PASSED")

def test_email_extra_subdomain():
    assert is_valid_email("abc@mail.co.in") is False  # pattern only allows one dot, hardcoded ".com"
    print("test_email_extra_subdomain: PASSED")
# ---------- is_valid_phone_number() ----------
def test_phone_valid():
    assert is_valid_phone_number("+91 9876543210") is True
    print("test_phone_valid: PASSED")

def test_phone_missing_country_code():
    assert is_valid_phone_number("9876543210") is False
    print("test_phone_missing_country_code: PASSED")

def test_phone_wrong_digit_count():
    assert is_valid_phone_number("+91 987654321") is False   # 9 digits
    assert is_valid_phone_number("+91 98765432100") is False  # 11 digits
    print("test_phone_wrong_digit_count: PASSED")

def test_phone_missing_space():
    assert is_valid_phone_number("+919876543210") is False
    print("test_phone_missing_space: PASSED")

def test_phone_double_space():
    assert is_valid_phone_number("+91  9876543210") is False  # pattern requires exactly one space
    print("test_phone_double_space: PASSED")

def test_phone_non_digit_character():
    assert is_valid_phone_number("+91 987654321a") is False
    print("test_phone_non_digit_character: PASSED")
# ---------- is_valid_name() ----------
def test_name_valid_two_words():
    assert is_valid_name("John Doe") is True
    print("test_name_valid_two_words: PASSED")

def test_name_valid_three_words():
    assert is_valid_name("John Michael Doe") is True
    print("test_name_valid_three_words: PASSED")

def test_name_single_word_invalid():
    assert is_valid_name("John") is False
    print("test_name_single_word_invalid: PASSED")

def test_name_first_name_too_short():
    assert is_valid_name("Jo Doe") is False  # under the 3-char minimum
    print("test_name_first_name_too_short: PASSED")

def test_name_first_name_too_long():
    assert is_valid_name("Abcdefghijklm Doe") is False  # 13 chars, over the 12-char max
    print("test_name_first_name_too_long: PASSED")

def test_name_contains_digit():
    assert is_valid_name("John1 Doe") is False
    print("test_name_contains_digit: PASSED")

def test_name_four_words_invalid():
    assert is_valid_name("John Michael Andrew Doe") is False  # only one optional middle group allowed
    print("test_name_four_words_invalid: PASSED")
# ---------- is_valid_middle_name() ----------
def test_middle_name_empty_valid():
    assert is_valid_middle_name("") is True
    print("test_middle_name_empty_valid: PASSED")

def test_middle_name_single_word_valid():
    assert is_valid_middle_name("Michael") is True
    print("test_middle_name_single_word_valid: PASSED")

def test_middle_name_two_words_invalid():
    assert is_valid_middle_name("Michael Andrew") is False
    print("test_middle_name_two_words_invalid: PASSED")

def test_middle_name_too_long_invalid():
    assert is_valid_middle_name("Abcdefghijklm") is False  # 13 chars
    print("test_middle_name_too_long_invalid: PASSED")
# ---------- is_valid_name_part() ----------
def test_name_part_valid():
    assert is_valid_name_part("John") is True
    print("test_name_part_valid: PASSED")

def test_name_part_empty_invalid():
    assert is_valid_name_part("") is False
    print("test_name_part_empty_invalid: PASSED")

def test_name_part_too_short_invalid():
    assert is_valid_name_part("Jo") is False
    print("test_name_part_too_short_invalid: PASSED")

def test_name_part_two_words_invalid():
    assert is_valid_name_part("John Doe") is False  # must be a single word
    print("test_name_part_two_words_invalid: PASSED")
# ---------- is_valid_patient_id_format() ----------
def test_patient_id_format_valid():
    assert is_valid_patient_id_format("CA0001") is True
    print("test_patient_id_format_valid: PASSED")

def test_patient_id_format_lowercase_invalid():
    assert is_valid_patient_id_format("ca0001") is False
    print("test_patient_id_format_lowercase_invalid: PASSED")

def test_patient_id_format_wrong_digit_count():
    assert is_valid_patient_id_format("CA001") is False    # 3 digits
    assert is_valid_patient_id_format("CA00001") is False  # 5 digits
    print("test_patient_id_format_wrong_digit_count: PASSED")

def test_patient_id_format_wrong_letter_count():
    assert is_valid_patient_id_format("C0001") is False   # 1 letter
    assert is_valid_patient_id_format("CAB001") is False  # effectively 3 letters given the digit slots
    print("test_patient_id_format_wrong_letter_count: PASSED")
# ---------- is_valid_patient_id() ----------
def test_patient_id_valid_real_code():
    assert is_valid_patient_id("CA0001", disease_codes) is True
    print("test_patient_id_valid_real_code: PASSED")

def test_patient_id_bad_format_short_circuits():
    assert is_valid_patient_id("ca0001", disease_codes) is False
    print("test_patient_id_bad_format_short_circuits: PASSED")

def test_patient_id_unknown_code():
    assert is_valid_patient_id("ZZ1234", disease_codes) is False  # right format, not a real code
    print("test_patient_id_unknown_code: PASSED")
# ---------- is_valid_date_of_birth() ----------
# Note: this only checks the DD-MM-YYYY shape — it doesn't know Feb 30 isn't real.
# Actual calendar validity is enforced later in classes.py's date_of_birth setter, via strptime.
def test_dob_valid_format():
    assert is_valid_date_of_birth("01-01-2000") is True
    print("test_dob_valid_format: PASSED")

def test_dob_wrong_separator():
    assert is_valid_date_of_birth("01/01/2000") is False
    print("test_dob_wrong_separator: PASSED")

def test_dob_missing_leading_zeros():
    assert is_valid_date_of_birth("1-1-2000") is False
    print("test_dob_missing_leading_zeros: PASSED")

def test_dob_format_accepts_impossible_calendar_date():
    # 13th month, format-valid but not a real date — deliberately demonstrates
    # this function doesn't do calendar validation, only shape validation
    assert is_valid_date_of_birth("31-13-2020") is True
    print("test_dob_format_accepts_impossible_calendar_date: PASSED")
# ---------- is_valid_username() ----------
def test_username_valid():
    assert is_valid_username("user_123") is True
    print("test_username_valid: PASSED")

def test_username_boundary_lengths():
    assert is_valid_username("abc") is True             # 3 chars, minimum
    assert is_valid_username("abcdefghijkl") is True     # 12 chars, maximum
    assert is_valid_username("ab") is False              # 2 chars
    assert is_valid_username("abcdefghijklm") is False   # 13 chars
    print("test_username_boundary_lengths: PASSED")

def test_username_rejects_space():
    assert is_valid_username("user 123") is False
    print("test_username_rejects_space: PASSED")

def test_username_rejects_symbol():
    assert is_valid_username("user@123") is False
    print("test_username_rejects_symbol: PASSED")
# ---------- is_valid_password() ----------
def test_password_valid():
    assert is_valid_password("Valid#Pass1") is True
    print("test_password_valid: PASSED")

def test_password_missing_uppercase():
    assert is_valid_password("valid#pass1") is False
    print("test_password_missing_uppercase: PASSED")

def test_password_missing_lowercase():
    assert is_valid_password("VALID#PASS1") is False
    print("test_password_missing_lowercase: PASSED")

def test_password_missing_digit():
    assert is_valid_password("Validd#Pass") is False
    print("test_password_missing_digit: PASSED")

def test_password_missing_symbol():
    assert is_valid_password("ValidPass123") is False
    print("test_password_missing_symbol: PASSED")

def test_password_boundary_lengths():
    assert is_valid_password("Val#Pa12") is False              # 8 chars, one under minimum
    assert is_valid_password("Vali#Pa12") is True              # 9 chars, minimum
    assert is_valid_password("Valid#Password1234") is True     # 18 chars, maximum
    assert is_valid_password("Valid#Password12345") is False   # 19 chars, one over maximum
    print("test_password_boundary_lengths: PASSED")

def test_password_rejects_space():
    assert is_valid_password("Valid# Pass1") is False
    print("test_password_rejects_space: PASSED")

def test_password_symbol_range_endpoints():
    assert is_valid_password("Valid!Pass1") is True   # "!" — first character in the symbol range
    assert is_valid_password("Valid~Pass1") is True   # "~" — last character in the symbol range
    print("test_password_symbol_range_endpoints: PASSED")

def run_all():
    test_email_valid()
    test_email_missing_at_symbol()
    test_email_digits_in_domain()
    test_email_missing_dot_com()
    test_email_dot_in_local_part()
    test_email_extra_subdomain()
    test_phone_valid()
    test_phone_missing_country_code()
    test_phone_wrong_digit_count()
    test_phone_missing_space()
    test_phone_double_space()
    test_phone_non_digit_character()
    test_name_valid_two_words()
    test_name_valid_three_words()
    test_name_single_word_invalid()
    test_name_first_name_too_short()
    test_name_first_name_too_long()
    test_name_contains_digit()
    test_name_four_words_invalid()
    test_middle_name_empty_valid()
    test_middle_name_single_word_valid()
    test_middle_name_two_words_invalid()
    test_middle_name_too_long_invalid()
    test_name_part_valid()
    test_name_part_empty_invalid()
    test_name_part_too_short_invalid()
    test_name_part_two_words_invalid()
    test_patient_id_format_valid()
    test_patient_id_format_lowercase_invalid()
    test_patient_id_format_wrong_digit_count()
    test_patient_id_format_wrong_letter_count()
    test_patient_id_valid_real_code()
    test_patient_id_bad_format_short_circuits()
    test_patient_id_unknown_code()
    test_dob_valid_format()
    test_dob_wrong_separator()
    test_dob_missing_leading_zeros()
    test_dob_format_accepts_impossible_calendar_date()
    test_username_valid()
    test_username_boundary_lengths()
    test_username_rejects_space()
    test_username_rejects_symbol()
    test_password_valid()
    test_password_missing_uppercase()
    test_password_missing_lowercase()
    test_password_missing_digit()
    test_password_missing_symbol()
    test_password_boundary_lengths()
    test_password_rejects_space()
    test_password_symbol_range_endpoints()
    print("\nAll patterns.py tests passed.")

if __name__ == "__main__":
    run_all()
