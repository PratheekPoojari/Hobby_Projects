# To validate the prompted inputs from user.
from patterns import *

# To use as type annotations in the add_user and add_relative functions.
from classes import User, Relatives

# The actual query functions that perform the said action.
from database import *

# Used to take the user symptom as input for the function, and generate a matching disease_code
from symptom_matcher import allocate_code

# Generates patient_id using the code and then checking internally for a number to assign(0000-9999)
from patient_id import free_patient_id, generate_patient_id

# Type annotation.
from types import FunctionType


# Get user's name, and return a dict containing the key: value pairs of
# first, middle(optional) and last with their values.
def prompt_name() -> dict[str, str]:
    name_dict = {}
    while True:
        print("""
              First and Last names are mandatory. Enter in the following format:
              first_name <space> middle_name(optional) <space> "last_name".
              """)
        name:str = input("Enter Name: ").strip()
        if is_valid_name(name):
            name_list:list[str] = name.split()
            if len(name_list) == 2:
                first, last = name.split()
                name_dict.update({"first_name": first, "last_name": last})
                return name_dict
            elif len(name_list) == 3:
                first, middle, last = name.split()
                name_dict.update({"first_name": first, "middle_name": middle, "last_name": last})
                return name_dict
        else:
            print("Invalid User Name. Please Enter a Valid Name.")


# Get user's date of birth, returns it as a string.
def prompt_date_of_birth() -> str:
    while True:
        print("""
              Input Date of Birth in the dd-mm-yyyy format. Make sure to use '-',
              in between the date, month and year to separate them. And use '01', '02', etc...
              instead of just '1', '2', etc...
              """)
        date_of_birth:str = input("Enter Date of Birth: ").strip()
        if is_valid_date_of_birth(date_of_birth):
            return date_of_birth
        else:
            print("Invalid Date of Birth. Please Enter a Valid Date of Birth.")


# Get user's email, returns it as a string
def prompt_email() -> str:
    while True:
        email:str = input("Enter email: ").strip()    
        if is_valid_email(email):
            return email
        else:
            print("Invalid Email. Please enter a Valid Email.")


# Get user's symptoms, and returns it as a plain string after performing certain validations.
def prompt_symptoms() -> str:
    while True:
        symptoms: str = input("Enter your issues: ").strip()
        word_count: int = len(symptoms.split())

        if 1 <= word_count <= 750:
            print(word_count)
            return symptoms
        elif word_count == 0:
            print("Please enter at least one symptom.")
        else:
            print(f"Input is too long ({word_count} words). Please keep it under 750 words.")


# Get user's phone number, return it as string.
def prompt_phone_number() -> str:
    while True:
        print("The number should be in the format: +91 1234567890, (+91 is mandatory.)")
        number:str = input("Enter your phone number: ").strip()
        if is_valid_phone_number(number):
            return number
        else:
            print("Invalid Phone Number. Please enter a Valid Phone Number")


def prompt_patient_id() -> str:
    while True:
        print("The format for patient_id is: 'AB1234'.")
        patient_id:str = input("Enter the patient_id of the user admitted: ")
        if is_valid_patient_id(patient_id, disease_codes):
            return patient_id
        else:
            print("Invalid 'patient_id'. Please Enter a valid patient_id")

def complete_name(input_name:dict[str, str]) -> str:
    name_dict = input_name.values()
    name_list:list[str] = [val for val in name_dict]
    if len(name_list) == 2:
        full_name:str = name_list[0] + " " + name_list[1]
        return full_name
    else:
        full_name:str = name_list[0] + " " + name_list[1] + " " + name_list[2]
        return full_name
    

# Calls all the required 'propmt'_functions and stores their result in suitable variables.
# Checks for duplicate values and if none are present, assigns a code and generates a patient_id.
# The full user name if built using the first, middle(optional) and last, as per the user's input.
# Then a constructor call is placed to the "User" class to instantiate an object for this specific input.
# Later, the user_obj is fed into the insert_user(), to add it to database(hospital.db) and save on disk.
def add_user() -> None:

    user_name:dict[str, str] = prompt_name()
    user_phone_number:str = prompt_phone_number()
    user_email:str = prompt_email()
    user_date_of_birth:str = prompt_date_of_birth()
    user_symptoms:str = prompt_symptoms()

    if is_duplicate(user_phone_number, user_email):
        print("The phone number/email has already been taken. Use a different one.")
        return None
    else:
        code:str = allocate_code(user_symptoms)
        user_patient_id:str = generate_patient_id(code)

        full_name:str = complete_name(user_name)
        try:
            user:User = User(user_patient_id, user_date_of_birth, user_symptoms, full_name, user_email, user_phone_number)
            insert_user(user)
        except ValueError as e:
            free_patient_id(user_patient_id)
            print(f"Failed to create user: {e}")
            return None


def add_relative() -> None:
    relative_patient_id:str = prompt_patient_id()
    
    if patient_id_exists(relative_patient_id):
        relative_name:dict[str, str] = prompt_name()
        relative_email:str = prompt_email()
        relative_phone_number:str = prompt_phone_number()
        if is_duplicate(relative_phone_number, relative_email):
            print("The phone number/email has already been taken. Use a different one.")
            return None
        else:
            full_name:str = complete_name(relative_name)
            try:
                relative:Relatives = Relatives(full_name, relative_email, relative_phone_number, relative_patient_id)
                insert_relative(relative)
            except ValueError as e:
                print(f"Failed to create relative: {e}")
                return None
    else:
        print(f"The patient_id: {relative_patient_id} doesn't exist.")
        return None


users_search_fields:dict[str, FunctionType] = {
    "patient_id":   search_user_by_patient_id,
    "email":        search_user_by_email,
    "phone_number": search_user_by_phone,
    "first_name":   search_users_by_name,
    "middle_name":  search_users_by_name,
    "last_name":    search_users_by_name,
}

relatives_search_fields:dict[str, FunctionType] = {
    "email":        search_relatives_by_email,
    "phone_number": search_relatives_by_phone,
    "first_name":   search_relatives_by_name,
    "middle_name":  search_relatives_by_name,
    "last_name":    search_relatives_by_name,
}


def search(table:str, field:str, value:str) -> dict[str, str] | list[dict] | None:
    if table == "users":
        dispatch_dict:dict[str, FunctionType] = users_search_fields
    elif table == "relatives":
        dispatch_dict:dict[str, FunctionType] = relatives_search_fields
    else:
        print("Invalid Table")
        return None

    query_function:FunctionType | None = dispatch_dict.get(field)
    if query_function is None:
        print(f"The entered field '{field}' is not present in {dispatch_dict}.")
        return None
    
    name_fields:tuple = ("first_name", "middle_name", "last_name")
    if field in name_fields:
        result:dict[str, str] | list[dict] | None = query_function(field, value)
    else:
        result:dict[str, str] | list[dict] | None = query_function(value)
    
    if result is None:
        print(f"No match for {value} in {field} found in the table {table}")

    return result


update_validate:dict[str, FunctionType] = {
        "first_name": is_valid_name_part,
        "middle_name": is_valid_middle_name,
        "last_name": is_valid_name_part,
        "date_of_birth" : is_valid_date_of_birth,
        "email": is_valid_email,
        "phone_number": is_valid_phone_number
        }


name_fields: tuple = ("first_name", "middle_name", "last_name")

def ambiguity_check(table: str, search_field: str, result: dict[str, str] | list[dict] | None) -> str | None:
    if result is None:
        return None

    if table == "users":
        if search_field in name_fields:
            if isinstance(result, list) and len(result) == 1:
                return "Unambiguous"
            if isinstance(result, list) and len(result) > 1:
                return "Ambiguous"
        else:
            return "Unambiguous"

    if table == "relatives":
        if search_field in name_fields:
            if isinstance(result, list) and len(result) == 1:
                return "Unambiguous"
            if isinstance(result, list) and len(result) > 1:
                return "Ambiguous"
        else:
            return "Unambiguous"

    return None


def update(table: str, search_field: str, search_value: str, changes: dict[str, str], row_identifier: str | None = None) -> tuple:
    result: dict[str, str] | list[dict] | None = search(table, search_field, search_value)

    if result is None:
        print(f"The value '{search_value}' couldn't be located in the field '{search_field}' of the {table} table.")
        return ("not_found", None)

    ambiguity: str | None = ambiguity_check(table, search_field, result)

    extracted_id: str = ""

    if ambiguity == "Ambiguous":
        # update_assist only returns "Ambiguous" when result came from a name-field search,
        # which always returns list[dict] — but pyright can't see that from a string comparison,
        # so this isinstance check narrows the type (and guards against a real mismatch at runtime).
        if not isinstance(result, list):
            print("Unexpected result shape for an ambiguous match.")
            return ("failed", None)

        if row_identifier is None:
            print(f"Multiple matches found for '{search_value}' in '{search_field}' of the {table} table.")
            return ("ambiguous", result)
        else:
            # A prior call already returned the candidate list; caller picked one by relative_row_id.
            chosen: dict | None = None
            for pair in result:
                # relative_row_id comes back from sqlite3 as an int; row_identifier is a str.
                # Cast before comparing or this silently never matches.
                if str(pair["Relatives"]["relative_row_id"]) == row_identifier:
                    chosen = pair
                    break
            if chosen is None:
                print("Invalid selection.")
                return ("not_found", None)
            extracted_id = row_identifier

    elif ambiguity == "Unambiguous":
        if table == "users":
            if search_field in name_fields:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = result[0]["patient_id"]
            else:
                if not isinstance(result, dict):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = result["patient_id"]
        elif table == "relatives":
            if search_field in name_fields:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = str(result[0]["Relatives"]["relative_row_id"])
            else:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = str(result[0]["relative_row_id"])

    # Pass 1: validate every change before touching the database.
    for key in changes:
        validate_func: FunctionType | None = update_validate.get(key)
        if validate_func is None:
            print(f"'{key}' is not an updatable field.")
            return ("failed", None)
        if not validate_func(changes[key]):
            print(f"Invalid value '{changes[key]}' for field '{key}'.")
            return ("failed", None)

    # Duplicate check, only for email/phone_number is actually being changed.
    new_phone: str | None = changes.get("phone_number")
    new_email: str | None = changes.get("email")
    if new_phone or new_email:
        if is_duplicate(phone=new_phone, email=new_email):
            print("The phone number/email has already been taken. Use a different one.")
            return ("failed", None)

    # Pass 2: apply every change now that all of them passed.
    for key in changes:
        update_query(table, key, changes[key], extracted_id)

    print("Updated the changes successfully.")
    return ("success", extracted_id)


def delete(table:str, search_field:str, search_value:str, row_identifier:str|None = None) -> tuple:
    result:dict[str, str] | list[dict] | None = search(table, search_field, search_value)

    if result is None:
        print(f"The value '{search_value}' couldn't be located in the field '{search_field}' of the {table} table.")
        return ("not_found", None)

    ambiguity: str | None = ambiguity_check(table, search_field, result)

    extracted_id: str = ""

    row_delete:dict[str, str] | list[dict] | None = result

    if ambiguity == "Ambiguous":
        # update_assist only returns "Ambiguous" when result came from a name-field search,
        # which always returns list[dict] — but pyright can't see that from a string comparison,
        # so this isinstance check narrows the type (and guards against a real mismatch at runtime).
        if not isinstance(result, list):
            print("Unexpected result shape for an ambiguous match.")
            return ("failed", None)

        if row_identifier is None:
            print(f"Multiple matches found for '{search_value}' in '{search_field}' of the {table} table.")
            return ("ambiguous", result)
        else:
            # A prior call already returned the candidate list; caller picked one by relative_row_id.
            chosen: dict | None = None
            for pair in result:
                # relative_row_id comes back from sqlite3 as an int; row_identifier is a str.
                # Cast before comparing or this silently never matches.
                if str(pair["Relatives"]["relative_row_id"]) == row_identifier:
                    chosen = pair
                    break
            if chosen is None:
                print("Invalid selection.")
                return ("not_found", None)
            extracted_id = row_identifier
            row_delete = chosen

    elif ambiguity == "Unambiguous":
        if table == "users":
            if search_field in name_fields:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = result[0]["patient_id"]
                row_delete = result[0]
            else:
                if not isinstance(result, dict):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = result["patient_id"]
                row_delete = result
        elif table == "relatives":
            if search_field in name_fields:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = str(result[0]["Relatives"]["relative_row_id"])
                row_delete = result[0]["Relatives"]
            else:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = str(result[0]["relative_row_id"])
                row_delete = result[0]

    delete_query(table, extracted_id)
    print(f"Deleted the row: {row_delete} successfully.")
    return ("success", {"table": table, "deleted": row_delete})



def main():
    from database import close_connection

    # ---- Setup: 3 users, with 1, 2, and 3 relatives respectively ----

    # User 1 — 1 relative
    patient_id_1 = generate_patient_id("CA")
    user_1 = User(patient_id_1, "01-01-1990", "test symptoms for user one",
                  "Alice One", "aliceone1@test.com", "+91 9000000001")
    insert_user(user_1)
    relative_1a = Relatives("Bob One", "bobone1@test.com", "+91 9000000002", patient_id_1)
    insert_relative(relative_1a)

    # User 2 — 2 relatives
    patient_id_2 = generate_patient_id("TB")
    user_2 = User(patient_id_2, "02-02-1991", "test symptoms for user two",
                  "Alice Two", "alicetwo1@test.com", "+91 9000000003")
    insert_user(user_2)
    relative_2a = Relatives("Bob Two", "bobtwoa1@test.com", "+91 9000000004", patient_id_2)
    relative_2b = Relatives("Carl Two", "bobtwob1@test.com", "+91 9000000005", patient_id_2)
    insert_relative(relative_2a)
    insert_relative(relative_2b)

    # User 3 — 3 relatives
    patient_id_3 = generate_patient_id("MA")
    user_3 = User(patient_id_3, "03-03-1992", "test symptoms for user three",
                  "Alice Three", "alicethree1@test.com", "+91 9000000006")
    insert_user(user_3)
    relative_3a = Relatives("Bob Three", "bobthreea1@test.com", "+91 9000000007", patient_id_3)
    relative_3b = Relatives("Carl Three", "bobthreeb1@test.com", "+91 9000000008", patient_id_3)
    relative_3c = Relatives("Dave Three", "bobthreec1@test.com", "+91 9000000009", patient_id_3)
    insert_relative(relative_3a)
    insert_relative(relative_3b)
    insert_relative(relative_3c)

    print("\n--- Setup complete: 3 users created with 1, 2, and 3 relatives ---\n")

    # ---- Action 1: delete user 1 entirely — relies on FK cascade to remove relative_1a ----
    status, data = delete("users", "patient_id", patient_id_1)
    print(f"\nDelete user 1 status: {status}")
    assert status == "success", "Expected user 1 deletion to succeed."

    cascade_check = search_relatives_by_email("bobone1@test.com")
    assert cascade_check is None, "FAIL: relative_1a still exists — cascade didn't fire."
    print("PASS: user 1 and their relative were both removed (cascade confirmed).")

    # ---- Action 2: delete the first relative of user 2 (relative_2a) ----
    status, data = delete("relatives", "email", "bobtwoa1@test.com")
    print(f"\nDelete relative_2a status: {status}")
    assert status == "success", "Expected relative_2a deletion to succeed."

    assert search_relatives_by_email("bobtwoa1@test.com") is None, "FAIL: relative_2a still exists."
    assert search_relatives_by_email("bobtwob1@test.com") is not None, "FAIL: relative_2b was wrongly removed."
    assert search_user_by_patient_id(patient_id_2) is not None, "FAIL: user 2 was wrongly removed."
    print("PASS: relative_2a removed; relative_2b and user 2 untouched.")

    # ---- Action 3: delete the last two relatives of user 3 (relative_3b, relative_3c) ----
    status, data = delete("relatives", "email", "bobthreeb1@test.com")
    print(f"\nDelete relative_3b status: {status}")
    assert status == "success", "Expected relative_3b deletion to succeed."

    status, data = delete("relatives", "email", "bobthreec1@test.com")
    print(f"Delete relative_3c status: {status}")
    assert status == "success", "Expected relative_3c deletion to succeed."

    assert search_relatives_by_email("bobthreeb1@test.com") is None, "FAIL: relative_3b still exists."
    assert search_relatives_by_email("bobthreec1@test.com") is None, "FAIL: relative_3c still exists."
    assert search_relatives_by_email("bobthreea1@test.com") is not None, "FAIL: relative_3a was wrongly removed."
    assert search_user_by_patient_id(patient_id_3) is not None, "FAIL: user 3 was wrongly removed."
    print("PASS: relative_3b and relative_3c removed; relative_3a and user 3 untouched.")

    print("\nAll delete() test cases passed.\n")

    close_connection()


if __name__ == "__main__":
    main()
