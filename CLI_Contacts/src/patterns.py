import re
from pathlib import Path
import csv


__all__:list[str] = [
                     "is_valid_name", "is_valid_date_of_birth",
                     "is_valid_email", "is_valid_phone_number",
                     "is_valid_patient_id", "is_valid_middle_name" ,"disease_codes"
                     ]

# The expected pattern to match is "abcdef12345@domain_name.com"
email_pattern = r"^[a-zA-Z0-9]+@[a-zA-Z]+\.com$" 
def is_valid_email(email:str) -> bool:
    return bool(re.search(email_pattern, email))


# The expected pattern to match is "+91 1234567890"
phone_number_pattern = r"^\+91 {1}[0-9]{10}$"
def is_valid_phone_number(phone:str) -> bool:
    return bool(re.search(phone_number_pattern, phone))


# The expected pattern is: 1) fisrt middle last or only first and last
name_pattern = r"^[a-zA-Z]{3,12} ([a-zA-Z]{1,12} )?[a-zA-Z]{3,12}$"
def is_valid_name(name:str) -> bool:
    return bool(re.search(name_pattern, name))


# Single-word name check — used for middle_name, which is allowed to be empty
# (unlike first/last, which is_valid_name already requires as a full "first last" pair).
middle_name_pattern = r"^[a-zA-Z]{1,12}$"
def is_valid_middle_name(name: str) -> bool:
    if name == "":
        return True
    return bool(re.search(middle_name_pattern, name))

# The expected pattern to match is "AB1234"
patient_id_pattern = r"^[A-Z]{2}[0-9]{4}$"
def is_valid_patient_id_format(patient_id:str) -> bool:
    return bool(re.search(patient_id_pattern, patient_id))


CSV_PATH = Path(__file__).resolve().parent.parent / "data"/ "diseases.csv"
disease_codes:set[str] = set()
with open(CSV_PATH, "r") as file:
    reader:csv.DictReader = csv.DictReader(file)
    for row in reader:
        disease_codes.add(row["code"])


def is_valid_patient_id(patient_id:str, valid_disease_codes:set) -> bool:
    if not is_valid_patient_id_format(patient_id):
        return False
    prefix:str = patient_id[:2]
    return prefix in valid_disease_codes


date_of_birth_pattern = r"^[0-9]{2}-[0-9]{2}-[0-9]{4}$"
def is_valid_date_of_birth(date_of_birth:str) -> bool:
   return bool(re.search(date_of_birth_pattern, date_of_birth)) 

# Testing
def main():
    print(is_valid_email("pratheekspoojari1304@gmail.com")) # True 
    print(is_valid_phone_number("1593574862")) # False
    print(is_valid_name("Pratheek")) # False
    patient_id = ["CA0000", "CA85", "MA1455", "aE1478", "PS4532", "Ae1485"]
                  # True,   # False, #True,   # False,   # True,  # False
    for id in patient_id:
        print(f"{id} format: {is_valid_patient_id_format(id)}")
        print(f"{id}: {is_valid_patient_id(id, disease_codes)}")

    dob = ["1304-2005", "01-02-2000", "1-4-26", "13-051958", "14-05"]
           # False      # True        # False    # False     # False
    for d in dob:
        print(f"{d}: {is_valid_date_of_birth(d)}")


if __name__ == "__main__":
    main()
