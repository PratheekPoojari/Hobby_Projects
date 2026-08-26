import re

# The expected pattern to match is "abcdef12345@domain_name.com"
email_pattern = r"^[a-zA-Z0-9]+@[a-zA-Z]+\.com$" 
def is_valid_email(email:str) -> bool:
    return bool(re.search(email_pattern, email))


# The expected pattern to match is "+91 1234567890"
phone_number_pattern = r"^\+91 {1}[0-9]{10}$"
def is_valid_phone_number(phone:str) -> bool:
    return bool(re.search(phone_number_pattern, phone))


# The expected pattern is: 1) fisrt middle last or 2) first last
name_pattern = r"^[a-zA-Z]{3,12} ([a-zA-Z]{1,12} )?[a-zA-Z]{3,12}$"
def is_valid_name(name:str) -> bool:
    return bool(re.search(name_pattern, name))


# The expected pattern to match is "AB1234"
patient_id_pattern = r"^[A-Z]{2}[0-9]{4}$"
def is_valid_patient_id(patient_id:str) -> bool:
    return bool(re.search(patient_id_pattern, patient_id))


def main():
    print(is_valid_email("pratheekspoojari1304@gmail.com")) # True 
    print(is_valid_phone_number("1593574862")) # False
    print(is_valid_name("Pratheek")) # False
    patient_id = ["TA0000", "CA85", "MA145", "aD1478", "AE145632", "Ae1485"]
    for id in patient_id:
        print(is_valid_patient_id(id))

if __name__ == "__main__":
    main()
