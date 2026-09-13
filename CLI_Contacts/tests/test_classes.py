import sys
from pathlib import Path
from datetime import timedelta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from classes import *  # BaseClass, User, Relatives, session_date, date, datetime —
                        # plus patterns.py's names, re-exported transitively

def assert_raises_value_error(callable_, *args, **kwargs):
    try:
        callable_(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError(f"Expected ValueError, none was raised (args={args})")
# baseline valid values, reused across tests that aren't exercising that specific field
VALID_NAME = "John Doe"
VALID_EMAIL = "johndoe@gmail.com"
VALID_NUMBER = "+91 9876543210"
VALID_PATIENT_ID = "CA0001"          # CA = Cancer, a real code in diseases.csv
VALID_DOB = "15-01-1990"
VALID_SYMPTOMS = "cough fever headache"
# ---------- BaseClass ----------
def test_name_valid():
    obj = BaseClass(VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert obj.name == VALID_NAME
    print("test_name_valid: PASSED")

def test_name_valid_with_middle():
    obj = BaseClass("John Michael Doe", VALID_EMAIL, VALID_NUMBER)
    assert obj.name == "John Michael Doe"
    print("test_name_valid_with_middle: PASSED")

def test_name_invalid_raises():
    assert_raises_value_error(BaseClass, "John", VALID_EMAIL, VALID_NUMBER)  # single word, no last name
    print("test_name_invalid_raises: PASSED")

def test_email_valid():
    obj = BaseClass(VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert obj.email == VALID_EMAIL
    print("test_email_valid: PASSED")

def test_email_invalid_raises():
    assert_raises_value_error(BaseClass, VALID_NAME, "not-an-email", VALID_NUMBER)
    print("test_email_invalid_raises: PASSED")

def test_number_valid():
    obj = BaseClass(VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert obj.number == VALID_NUMBER
    print("test_number_valid: PASSED")

def test_number_invalid_raises():
    assert_raises_value_error(BaseClass, VALID_NAME, VALID_EMAIL, "9876543210")  # missing "+91 " prefix
    print("test_number_invalid_raises: PASSED")
# ---------- User: patient_id ----------
def test_patient_id_valid():
    user = User(VALID_PATIENT_ID, VALID_DOB, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert user.patient_id == VALID_PATIENT_ID
    print("test_patient_id_valid: PASSED")

def test_patient_id_invalid_format_raises():
    assert_raises_value_error(User, "ca0001", VALID_DOB, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_patient_id_invalid_format_raises: PASSED")

def test_patient_id_unknown_code_raises():
    # right format (2 letters + 4 digits), but "ZZ" isn't a real disease code in diseases.csv
    assert_raises_value_error(User, "ZZ1234", VALID_DOB, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_patient_id_unknown_code_raises: PASSED")
# ---------- User: date_of_birth ----------
def test_date_of_birth_valid():
    user = User(VALID_PATIENT_ID, VALID_DOB, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert user.date_of_birth == date(1990, 1, 15)
    print("test_date_of_birth_valid: PASSED")

def test_date_of_birth_invalid_format_raises():
    assert_raises_value_error(User, VALID_PATIENT_ID, "1990-01-15", VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_date_of_birth_invalid_format_raises: PASSED")

def test_date_of_birth_today_raises():
    # the setter requires strictly BEFORE today — today itself must fail
    today_str = session_date.strftime("%d-%m-%Y")
    assert_raises_value_error(User, VALID_PATIENT_ID, today_str, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_date_of_birth_today_raises: PASSED")

def test_date_of_birth_future_raises():
    future_str = (session_date + timedelta(days=1)).strftime("%d-%m-%Y")
    assert_raises_value_error(User, VALID_PATIENT_ID, future_str, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_date_of_birth_future_raises: PASSED")
# ---------- User: age ----------
def test_age_birthday_already_occurred_this_year():
    # Jan 1 — virtually guaranteed to be <= today's (month, day), so the full year count applies
    dob_str = date(session_date.year - 30, 1, 1).strftime("%d-%m-%Y")
    user = User(VALID_PATIENT_ID, dob_str, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert user.age == 30
    print("test_age_birthday_already_occurred_this_year: PASSED")

def test_age_birthday_not_yet_occurred_this_year():
    # Dec 31 — later than today's (month, day) on any day this test runs except Dec 31 itself,
    # so age should be one less than the raw year difference
    dob_str = date(session_date.year - 30, 12, 31).strftime("%d-%m-%Y")
    user = User(VALID_PATIENT_ID, dob_str, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert user.age == 29
    print("test_age_birthday_not_yet_occurred_this_year: PASSED")
# ---------- User: symptoms ----------
def test_symptoms_valid():
    user = User(VALID_PATIENT_ID, VALID_DOB, VALID_SYMPTOMS, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert user.symptoms == VALID_SYMPTOMS
    print("test_symptoms_valid: PASSED")

def test_symptoms_empty_string_raises():
    assert_raises_value_error(User, VALID_PATIENT_ID, VALID_DOB, "", VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_symptoms_empty_string_raises: PASSED")

def test_symptoms_none_raises():
    assert_raises_value_error(User, VALID_PATIENT_ID, VALID_DOB, None, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_symptoms_none_raises: PASSED")

def test_symptoms_under_limit_passes():
    symptoms = " ".join(["word"] * 749)
    user = User(VALID_PATIENT_ID, VALID_DOB, symptoms, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    assert len(user.symptoms.split()) == 749
    print("test_symptoms_under_limit_passes: PASSED")

def test_symptoms_at_limit_raises():
    symptoms = " ".join(["word"] * 750)
    assert_raises_value_error(User, VALID_PATIENT_ID, VALID_DOB, symptoms, VALID_NAME, VALID_EMAIL, VALID_NUMBER)
    print("test_symptoms_at_limit_raises: PASSED")
# ---------- Relatives ----------
def test_relatives_valid():
    rel = Relatives("Jane Doe", "janedoe@gmail.com", "+91 9876543211", VALID_PATIENT_ID)
    assert rel.patient_id == VALID_PATIENT_ID
    assert rel.name == "Jane Doe"
    print("test_relatives_valid: PASSED")

def test_relatives_patient_id_invalid_raises():
    assert_raises_value_error(Relatives, "Jane Doe", "janedoe@gmail.com", "+91 9876543211", "ZZ1234")
    print("test_relatives_patient_id_invalid_raises: PASSED")

def test_relatives_inherits_name_validation():
    # confirms BaseClass's validation actually applies through Relatives, not just User
    assert_raises_value_error(Relatives, "Jane", "janedoe@gmail.com", "+91 9876543211", VALID_PATIENT_ID)
    print("test_relatives_inherits_name_validation: PASSED")

def run_all():
    test_name_valid()
    test_name_valid_with_middle()
    test_name_invalid_raises()
    test_email_valid()
    test_email_invalid_raises()
    test_number_valid()
    test_number_invalid_raises()
    test_patient_id_valid()
    test_patient_id_invalid_format_raises()
    test_patient_id_unknown_code_raises()
    test_date_of_birth_valid()
    test_date_of_birth_invalid_format_raises()
    test_date_of_birth_today_raises()
    test_date_of_birth_future_raises()
    test_age_birthday_already_occurred_this_year()
    test_age_birthday_not_yet_occurred_this_year()
    test_symptoms_valid()
    test_symptoms_empty_string_raises()
    test_symptoms_none_raises()
    test_symptoms_under_limit_passes()
    test_symptoms_at_limit_raises()
    test_relatives_valid()
    test_relatives_patient_id_invalid_raises()
    test_relatives_inherits_name_validation()
    print("\nAll classes.py tests passed.")

if __name__ == "__main__":
    run_all()
