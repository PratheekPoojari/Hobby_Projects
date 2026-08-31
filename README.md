# Hobby Projects

- This is where the minor projects that I build for better understanding the concepts I have learnt earlier will be built.

## Project 1 - CLI Contact Storage

- Work in Progress, rough copies of `database.py` and `pattern.py`, containing the codes for a `hospital.db` -> sqlite3 database and regex pattern
  matching to verify username, patient_id, email and numbers have been drafted.
- Drafted a rough copy of `classes.py` that took nearly 4 hours and alot of juggling around to get it done. Alot of guidance from Claude, and
  alot for me to learn.
- Claude generated a `diseases.csv` file containing 6 static entries for 6 types of diseases with their code, name, priority and keywords.
- Updated `classes.py` to make sure that the "Users" class has a 'super().__init__' method to use the properties of it's Parents class.
- Created `patient_id.py` to calculate the next number to allocate to a patient and reuse the deleted once using "heap"('heapq' module).
- `patient_id.py` completed after around a total of 5 hours or so spent to understand and build functions that do as intended, and fixing 
   previous minor bugs that were caught while going throug the file today.
- `symptom_matcher.py` completed to take the user input symptoms and assess them and assign the disease code, to help generate the patient_id.
