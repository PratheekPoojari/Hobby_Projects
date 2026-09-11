from patterns import *
# Represents calendar dates and clock times together(year, month, day, hour, minute, second....)
from datetime import date, datetime
# date.today() -> gives today's date.
session_date = date.today()

class BaseClass:
    def __init__(self, name:str, email:str, number:str) -> None:
        self.name = name
        self.email = email
        self.number = number
    @property
    def name(self):
        return self._name
    @name.setter
    def name(self, name):
        if is_valid_name(name):
            self._name = name
        else:
            raise ValueError(f"Invalid Name: {name}")
    @property
    def email(self):
        return self._email
    @email.setter
    def email(self, email):
        if is_valid_email(email):
            self._email = email
        else:
            raise ValueError(f"Invalid Email-Id: {email}")
    @property
    def number(self):
        return self._number
    @number.setter
    def number(self, number):
        if is_valid_phone_number(number):
            self._number = number 
        else:
            raise ValueError(f"Invalid Phone Number: {number}")

class User(BaseClass):
    def __init__(self, patient_id:str, date_of_birth:str, symptoms:str, name:str, email:str, number:str) -> None:
        self.patient_id = patient_id
        self.date_of_birth = date_of_birth
        self.symptoms = symptoms
        super().__init__(name, email, number)
    @property
    def patient_id(self) -> str:
        return self._patient_id
    @patient_id.setter
    def patient_id(self, patient_id):
        if is_valid_patient_id(patient_id, disease_codes):
            self._patient_id = patient_id  
        else:
            raise ValueError(f"Invalid Patient_Id: {patient_id}")
    @property
    def date_of_birth(self) -> date:
        return self._date_of_birth
    @date_of_birth.setter
    def date_of_birth(self, date_of_birth):
        if is_valid_date_of_birth(date_of_birth):
            try:
                date_object = datetime.strptime(date_of_birth, "%d-%m-%Y")
                date_object = date_object.date()
            except ValueError:
                raise ValueError(f"Invalid Date of Birth: {date_of_birth}")
            else:
                if date_object < session_date:
                    self._date_of_birth = date_object
                else:
                    raise ValueError(f"Invalid Date of Birth: {date_of_birth}")
        else:
            raise ValueError(f"Invalid Date of Birth: {date_of_birth}")
    @property
    def age(self) -> int:
        year = session_date.year - self.date_of_birth.year
        if (session_date.month, session_date.day) < (self.date_of_birth.month, self.date_of_birth.day):
            return year - 1
        return year
    @property
    def symptoms(self) -> str:
        return self._symptoms
    @symptoms.setter
    def symptoms(self, symptoms):
        if symptoms == "" or symptoms is None:
            raise ValueError(f"The input is empty: {symptoms}")
        else:
            if len(symptoms.split()) >= 750:
                raise ValueError(f"Total Word Limit reached and at: {len(symptoms.split())} words.")
            else:
                self._symptoms = symptoms

class Relatives(BaseClass):
    def __init__(self, name:str, email:str, number:str, patient_id:str) -> None:
        super().__init__(name, email, number)
        self.patient_id = patient_id
    @property
    def patient_id(self):
        return self._patient_id
    @patient_id.setter
    def patient_id(self, patient_id:str):
        if is_valid_patient_id(patient_id, disease_codes):
            self._patient_id = patient_id
        else:
            raise ValueError(f"Invalid patient_id: {patient_id}")
