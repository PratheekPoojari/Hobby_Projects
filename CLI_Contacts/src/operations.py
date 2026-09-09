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
                name_dict.update({"ambiguiousfirst_name": first, "last_name": last})
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
        "patient_id": is_valid_patient_id,
        "first_name": is_valid_name,
        "last_name": is_valid_name,
        "date_of_birth" : is_valid_date_of_birth,
        "email": is_valid_email,
        "phone_number": is_valid_phone_number
        }


def update_assist(table:str, result:dict[str, str] | list[dict] | None) -> str | None:
    if table == "users":
        if type(result) == dict[str, str]:
            return "Unambiguous"
        if type(result) == list[dict] and len(result) == 1:
            return "Unambiguous"
        if type(result) == list[dict] and len(result) > 1:
            return "Ambiguous"

    if table == "relatives": 
        if type(result) == list[dict] and len(result) == 2:
            return "Unambiguous"
        if type(result) == list[dict] and len(result) > 2:
            return "Ambiguous"


def update(table:str, search_field:str, search_value:str, changes:dict[str, str], row_identifier:int=0) -> tuple | dict[str, str] | list[dict] | None:
    result:dict[str, str] | list[dict] | None = search(table, search_field, search_value)
    
    if result is None:
        print(f"The value '{search_value}' couldn't be loacted in the field '{search_field}' of the {table} table.")
        return ("Not Found", None)
    
    ambiguity:str | None = update_assist(table, result)
    if ambiguity == "Ambiguous":
        print(f"Multiple matches found for '{search_value}' in '{search_field}' of the {table} table.")
        return ("ambiguous", result)
    if ambiguity == "Unambiguous":
        if table == "users":
            if type(result) == dict[str, str]:
                extracted_id:str = result["patient_id"]
            if type(result) == list[dict]:
                extracted_id:str = result[0]["patient_id"]
        if table == "relatives":
            if type(result) == list[dict]:
                id_dict:str  = result[0]["relative_row_id"]

    for key in changes:
        validate_func:FunctionType = update_validate[key]
        if validate_func(changes[key]):
            ...


    












#def main():
    #user1 = prompt_name()
    #print(user1)
    #user2 = prompt_date_of_birth()
    #print(user2)
    #user3 = prompt_email()
    #print(user3)
    #user4 = prompt_symptoms()
    #print(user4)
    #user5 = prompt_phone_number()
    #print(user5)



#if __name__ == "__main__":
#    main()
