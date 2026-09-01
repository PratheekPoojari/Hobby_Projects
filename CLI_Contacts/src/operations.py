import patterns


def prompt_name() -> dict[str, str]:
    name_dict = {}
    while True:
        print("""
              First and Last names are mandatory. Enter in the following format:
              first_name <space> middle_name(optional) <space> "last_name".
              """)
        name:str = input("Enter Name: ").strip()
        if patterns.is_valid_name(name):
            name_list:list[str] = name.split()
            if len(name_list) == 2:
                first, last = name.split()
                name_dict.update({"first_name": first, "last_name": last})
                return name_dict
            elif len(name_list) == 3:
                first, middle, last = name.split()
                name_dict.update({"first_name": first, "middle_name": middle, "last_name": last})
                return name_dict


def prompt_date_of_birth() -> str:
    while True:
        print("""
              Input Date of Birth in the dd-mm-yyyy format. Make sure to use '-',
              in between the date, month and year to separate them. And use '01', '02', etc...
              instead of just '1', '2', etc...
              """)
        date_of_birth:str = input("Enter Date of Birth: ")
        if patterns.is_valid_date_of_birth(date_of_birth):
            return date_of_birth


def prompt_email() -> str:
    while True:
        email:str = input("Enter email: ")    
        if patterns.is_valid_email(email):
            return email


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

        


def main():
    #user1 = prompt_name()
    #print(user1)
    #user2 = prompt_date_of_birth()
    #print(user2)
    #user3 = prompt_email()
    #print(user3)
    user4 = prompt_symptoms()
    print(user4)


if __name__ == "__main__":
    main()
