"""
Defines the core data structures for Users and Relatives.
Uses __slots__ for memory optimization, avoiding dynamic dictionary creation for each object.
"""

from patterns import *
from datetime import date, datetime

# Calculates the exact age in years based on the provided date of birth.
def calc_age(current: date, birth: date) -> int: 
    year: int = current.year - birth.year
    if (current.month, current.day) < (birth.month, birth.day):
        return year - 1
    return year

class BaseClass:
    # Disable dynamic dictionary for memory optimization
    __slots__ = ('_name', '_email', '_number')
    
    def __init__(self, name: str, email: str, number: str) -> None:
        self.name = name
        self.email = email
        self.number = number

    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, name: str):
        if is_valid_name(name):
            self._name = name
        else:
            raise ValueError(f"Invalid Name: {name}")

    @property
    def email(self) -> str:
        return self._email
    
    @email.setter
    def email(self, email: str):
        if is_valid_email(email):
            self._email = email
        else:
            raise ValueError(f"Invalid Email-Id: {email}")

    @property
    def number(self) -> str:
        return self._number
    
    @number.setter
    def number(self, number: str):
        if is_valid_phone_number(number):
            self._number = number 
        else:
            raise ValueError(f"Invalid Phone Number: {number}")

class User(BaseClass):
    __slots__ = ('_patient_id', '_date_of_birth', '_symptoms')

    def __init__(self, patient_id: str, date_of_birth: str, symptoms: str, name: str, email: str, number: str) -> None:
        self.patient_id = patient_id
        self.date_of_birth = date_of_birth
        self.symptoms = symptoms
        super().__init__(name, email, number)

    @property
    def patient_id(self) -> str:
        return self._patient_id
    
    @patient_id.setter
    def patient_id(self, patient_id: str):
        if is_valid_patient_id(patient_id, disease_codes):
            self._patient_id = patient_id  
        else:
            raise ValueError(f"Invalid Patient_Id: {patient_id}")

    @property
    def date_of_birth(self) -> date:
        return self._date_of_birth
    
    @date_of_birth.setter
    def date_of_birth(self, date_of_birth: str):
        if is_valid_date_of_birth(date_of_birth):
            try:
                date_object = datetime.strptime(date_of_birth, "%d-%m-%Y").date()
            except ValueError:
                raise ValueError(f"Invalid Date of Birth: {date_of_birth}")
            
            # Use dynamic date.today() to prevent caching bugs if app runs past midnight
            if date_object < date.today():
                self._date_of_birth = date_object
            else:
                raise ValueError(f"Invalid Date of Birth (must be in past): {date_of_birth}")
        else:
            raise ValueError(f"Invalid Date of Birth format: {date_of_birth}")

    @property
    def age(self) -> int:
        return calc_age(date.today(), self._date_of_birth)

    @property
    def symptoms(self) -> str:
        return self._symptoms
    
    @symptoms.setter
    def symptoms(self, symptoms: str):
        if not symptoms:
            raise ValueError("The symptoms input cannot be empty.")
        
        # Word counting logic - split defaults to any whitespace
        if len(symptoms.split()) >= 750:
            raise ValueError(f"Total Word Limit reached at: {len(symptoms.split())} words.")
        self._symptoms = symptoms

class Relatives(BaseClass):
    __slots__ = ('_patient_id',)

    def __init__(self, name: str, email: str, number: str, patient_id: str) -> None:
        super().__init__(name, email, number)
        self.patient_id = patient_id

    @property
    def patient_id(self) -> str:
        return self._patient_id
    
    @patient_id.setter
    def patient_id(self, patient_id: str):
        if is_valid_patient_id(patient_id, disease_codes):
            self._patient_id = patient_id
        else:
            raise ValueError(f"Invalid patient_id: {patient_id}")
