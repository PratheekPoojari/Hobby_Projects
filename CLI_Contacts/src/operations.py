from patterns import *
from classes import User, Relatives
from database import is_duplicate, insert_user
from symptom_matcher import allocate_code
from patient_id import generate_patient_id


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


def prompt_email() -> str:
    while True:
        email:str = input("Enter email: ").strip()    
        if is_valid_email(email):
            return email
        else:
            print("Invalid Email. Please enter a Valid Email.")


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


def prompt_phone_number() -> str:
    while True:
        print("The number should be in the format: +91 1234567890, (+91 is mandatory.)")
        number:str = input("Enter your phone number: ").strip()
        if is_valid_phone_number(number):
            return number
        else:
            print("Invalid Phone Number. Please enter a Valid Phone Number")


def add_user():

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

        name_dict = user_name.values()
        name_list:list[str] = [val for val in name_dict]
        if len(name_list) == 2:
            full_name:str = name_list[0] + " " + name_list[1]
        else:
            full_name:str = name_list[0] + " " + name_list[1] + " " + name_list[2]

        user:User = User(user_patient_id, user_date_of_birth, user_symptoms, full_name, user_email, user_phone_number)
        insert_user(user)

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
