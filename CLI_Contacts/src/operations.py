"""
Contains the core CRUD (Create, Read, Update, Delete) business logic.
Handles data insertion, ambiguity resolution for duplicate names, and strict table joins.
"""

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

__all__ = [
    "add_user",
    "add_relative",
    "search",
    "update",
    "delete",
    "view",
    "get_relatives_by_patient_id",  # re-exported from database.py, needed by exports.py
    "ambiguity_check",              # internal helper, now also needed by exports.py
    "resolve_selection",
    "get_all_users"
    ]
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

def complete_name(input_name: dict[str, str]) -> str:
    # Filter out empty strings/None and join the remaining name parts with a space
    return " ".join(part for part in input_name.values() if part)
    
# Helper to consistently format first, middle, and last names into a single string.
# Calls all the required 'propmt'_functions and stores their result in suitable variables.
# Checks for duplicate values and if none are present, assigns a code and generates a patient_id.
# The full user name if built using the first, middle(optional) and last, as per the user's input.
# Then a constructor call is placed to the "User" class to instantiate an object for this specific input.
# Later, the user_obj is fed into the insert_user(), to add it to database(hospital.db) and save on disk.
def add_user() -> str | None:
    user_name:dict[str, str] = prompt_name()
    user_phone_number:str = prompt_phone_number()
    user_email:str = prompt_email()
# Prompts for and validates all user demographic data, then inserts the record into the DB.
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
        return user_patient_id

def add_relative() -> None:
    relative_patient_id:str = prompt_patient_id()    
    if patient_id_exists(relative_patient_id):
        relative_name:dict[str, str] = prompt_name()
# Prompts for relative details and links them to an existing patient_id.
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
# Executes a dynamic SELECT query on the specified table and field.
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

# Determines if a search result requires manual disambiguation (e.g., multiple identical names).
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

def resolve_selection(table: str, candidates: list[dict], row_identifier: str) -> dict | None:
    if not isinstance(candidates, list):
        print("Passed unexpected shape of candidates")
        return None
# Extracts the exact target row from an ambiguous result set using a unique identifier.
        
    for item in candidates:
        if table == "users" and row_identifier == str(item.get("patient_id")):
            return item
        elif table == "relatives":
            # relatives dict structure is sometimes nested under 'Relatives' due to joins/structs
            rel_data = item.get("Relatives", item)
            if row_identifier == str(rel_data.get("relative_row_id")):
                return rel_data
    return None

def update(table: str, search_field: str, search_value: str, changes: dict[str, str], row_identifier: str | None = None) -> tuple:
    result: dict[str, str] | list[dict] | None = search(table, search_field, search_value)
    if result is None:
        print(f"The value '{search_value}' couldn't be located in the field '{search_field}' of the {table} table.")
# Updates a specific record after performing ambiguity checks.
        return ("not_found", None)
    ambiguity: str | None = ambiguity_check(table, search_field, result)
    extracted_id: str = ""
    if ambiguity == "Ambiguous":
        # ambiguity_check only returns "Ambiguous" when result came from a name-field search,
        # which always returns list[dict] — but pyright can't see that from a string comparison,
        # so this isinstance check narrows the type (and guards against a real mismatch at runtime).
        if not isinstance(result, list):
            print("Unexpected result shape for an ambiguous match.")
            return ("failed", None)
        if row_identifier is None:
            print(f"Multiple matches found for '{search_value}' in '{search_field}' of the {table} table.")
            return ("ambiguous", result)
        else:
            chosen: dict | None = resolve_selection(table, result, row_identifier)
            if chosen is None:
                print("Invalid selection.")
                return ("not_found", None)
            if table == "users":
                extracted_id = chosen["patient_id"]
            else:
                extracted_id = str(chosen["relative_row_id"])
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
    else:
        return ("failed", None)    
    # Validate every change before touching the database.
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
    # Apply every change now that all of them passed.
    for key in changes:
        update_query(table, key, changes[key], extracted_id)
    print("Updated the changes successfully.")
    return ("success", extracted_id)

def delete(table:str, search_field:str, search_value:str, row_identifier:str|None = None) -> tuple:
    result:dict[str, str] | list[dict] | None = search(table, search_field, search_value)
    if result is None:
        print(f"The value '{search_value}' couldn't be located in the field '{search_field}' of the {table} table.")
# Deletes a record from the database, cascading to relatives if the parent user is deleted.
        return ("not_found", None)
    ambiguity: str | None = ambiguity_check(table, search_field, result)
    extracted_id: str = ""
    chosen: dict | None = {}
    if ambiguity == "Ambiguous":
        if not isinstance(result, list):
            print("Unexpected result shape for an ambiguous match.")
            return ("failed", None)
        if row_identifier is None:
            print(f"Multiple matches found for '{search_value}' in '{search_field}' of the {table} table.")
            return ("ambiguous", result)
        else:
            chosen: dict | None = resolve_selection(table, result, row_identifier)
            if chosen is None:
                print("Invalid selection.")
                return ("not_found", None)
            if table == "users":
                extracted_id = chosen["patient_id"]
            else:
                extracted_id = str(chosen["relative_row_id"])
    elif ambiguity == "Unambiguous":
        if table == "users":
            if search_field in name_fields:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = result[0]["patient_id"]
                chosen = result[0]
            else:
                if not isinstance(result, dict):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = result["patient_id"]
                chosen = result
        elif table == "relatives":
            if search_field in name_fields:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = str(result[0]["Relatives"]["relative_row_id"])
                chosen = result[0]["Relatives"]
            else:
                if not isinstance(result, list):
                    print("Unexpected result shape.")
                    return ("failed", None)
                extracted_id = str(result[0]["relative_row_id"])
                chosen = result[0]
    else:
        return ("failed", None)
    delete_query(table, extracted_id)
    print(f"Deleted the row: {chosen} successfully.")
    return ("success", {"table": table, "deleted": chosen})

def display_bundle(user: dict, relatives: list[dict] | None) -> None:
    full_name = f"{user['first_name']} {user.get('middle_name', '')} {user['last_name']}".replace("  ", " ").strip()
    print(f"\nUser: {full_name} (patient_id: {user['patient_id']})")
    print(f"  DOB: {user.get('date_of_birth', '-')}")
    print(f"  Symptoms: {user.get('symptoms', '-')}")
    print(f"  Email: {user.get('email', '-')}")
    print(f"  Phone: {user.get('phone_number', '-')}")
    if relatives:
        print("  Relatives:")
        for rel in relatives:
            rel_name = f"{rel['first_name']} {rel.get('middle_name', '')} {rel['last_name']}".replace("  ", " ").strip()
            print(f"    - {rel_name} (row_id: {rel['relative_row_id']}, email: {rel.get('email', '-')}, phone: {rel.get('phone_number', '-')})")
    else:
        print(f"  No Relatives found for {full_name}.")


def view(table: str, search_field: str, search_value: str) -> None:
    result: dict[str, str] | list[dict] | None = search(table, search_field, search_value)
    if result is None:
        print(f"The value '{search_value}' couldn't be located in the field '{search_field}' of the {table} table.")
# Retrieves and pretty-prints records matching the search criteria.
        return None

    if table == "users":
        # Normalize to a list regardless of whether search() returned a single dict
        # (non-name field) or a list of dicts (name-field, possibly multiple matches).
        user_rows: list[dict] = [result] if isinstance(result, dict) else result
        for user in user_rows:
            relatives: list[dict[str, str]] | None = get_relatives_by_patient_id(user["patient_id"])
            display_bundle(user, relatives)

    elif table == "relatives":
        if search_field in name_fields:
            # search_relatives_by_name() -> list of {"Relatives": {...}, "User": {...}}
            if not isinstance(result, list):
                print("Unexpected result shape.")
                return None
            for pair in result:
                display_bundle(pair["User"], [pair["Relatives"]])
        else:
            # search_relatives_by_email/phone() -> [relative_dict, user_dict], single match only
            if not isinstance(result, list) or len(result) != 2:
                print("Unexpected result shape.")
                return None
            relative, user = result[0], result[1]
            display_bundle(user, [relative])

    return None
