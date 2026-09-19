import re
from pathlib import Path
import csv

__all__: list[str] = [
    "is_valid_name", "is_valid_date_of_birth",
    "is_valid_email", "is_valid_phone_number",
    "is_valid_patient_id", "is_valid_middle_name", 
    "is_valid_name_part", "disease_codes",
    "is_valid_username", "is_valid_password"
]

# Pre-compile regex patterns for O(1) setup time during validation checks.
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9]+@[a-zA-Z]+\.com$")
PHONE_NUMBER_PATTERN = re.compile(r"^\+91 {1}[0-9]{10}$")
NAME_PATTERN = re.compile(r"^[a-zA-Z]{3,12} ([a-zA-Z]{1,12} )?[a-zA-Z]{3,12}$")
MIDDLE_NAME_PATTERN = re.compile(r"^[a-zA-Z]{1,12}$")
NAME_PART_PATTERN = re.compile(r"^[a-zA-Z]{3,12}$")
PATIENT_ID_PATTERN = re.compile(r"^[A-Z]{2}[0-9]{4}$")
DATE_OF_BIRTH_PATTERN = re.compile(r"^[0-9]{2}-[0-9]{2}-[0-9]{4}$")
USERNAME_PATTERN = re.compile(r"^\w{3,12}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!-/:-@\[-`{-~])\S{9,18}$")

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.search(email))

def is_valid_phone_number(phone: str) -> bool:
    return bool(PHONE_NUMBER_PATTERN.search(phone))

def is_valid_name(name: str) -> bool:
    return bool(NAME_PATTERN.search(name))

def is_valid_middle_name(name: str) -> bool:
    if not name:
        return True
    return bool(MIDDLE_NAME_PATTERN.search(name))

def is_valid_name_part(name: str) -> bool:
    return bool(NAME_PART_PATTERN.search(name))

def is_valid_patient_id_format(patient_id: str) -> bool:
    return bool(PATIENT_ID_PATTERN.search(patient_id))

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "diseases.csv"

# Using a set comprehension to build the set directly from the file in one pass
with open(CSV_PATH, "r", encoding="utf-8") as file:
    disease_codes: set[str] = {row["code"] for row in csv.DictReader(file)}

def is_valid_patient_id(patient_id: str, valid_disease_codes: set) -> bool:
    if not is_valid_patient_id_format(patient_id):
        return False
    return patient_id[:2] in valid_disease_codes

def is_valid_date_of_birth(date_of_birth: str) -> bool:
   return bool(DATE_OF_BIRTH_PATTERN.search(date_of_birth))

def is_valid_username(username: str) -> bool:
    return bool(USERNAME_PATTERN.search(username))

def is_valid_password(password: str) -> bool:
    return bool(PASSWORD_PATTERN.search(password))

