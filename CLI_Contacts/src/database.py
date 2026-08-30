import sqlite3
from pathlib import Path

# Path(__file__) -> returns a path object containing the path of the file it was called from. Ex: "src/database.py"
# .resolve() -> a Path method that completes(from ~/ -> current file) the relative/incomplete path returned by Path(__file__)
# .parent -> a property of Path that return the address of the parent directory of current file by stripping of one layer at a time.
# Here the first .parent strips away the "database.py" returning ".../CLI_Contacts/src/", the next .parent returns ".../CLI_Contacts/"
# Then, the '/' operator is already overloaded by the pathlib module, that concatanates the new path. This is then stored in a variable.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hospital.db"

# sqlite3.connect -> opens the existing ".db" file at the location or creates one if it does not exist.
hospital = sqlite3.connect(DB_PATH)

# this is a method that lets user run the actual SQL commands, such as 'CREATE', 'INSERT', 'SELECT', etc...
cursor =  hospital.cursor()

# executes the SQL Queries passed as arguments. "PRAGMA foreign_keys(plural) = ON",
# is a must if we need to use FKs, as they are OFF by default
hospital.execute("PRAGMA foreign_keys = ON")

# Creates a Table called 'users'. Triple Commas are required to write multi-line commands.
# Double Quotes can be used for single-line commands.
# 'IF NOT EXISTS' -> this makes it so that if the table of the given name already exists, 
# it can't be changed in anyway, and the entire CREATE TABLE code is skipped. So any changes 
# made to the code here after already having created the database once would mean that, we 
# need to DELETE the databse and then run the code again for thr changes to take place.
cursor.execute(
    """CREATE TABLE IF NOT EXISTS users(
    patient_id TEXT PRIMARY KEY NOT NULL,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    last_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    symptoms TEXT NOT NULL, 
    email TEXT UNIQUE,
    phone_number TEXT UNIQUE
    )"""
)

# Creates a 'relatives' Tables, with a foreign key(patient_id) from 'users' table.
cursor.execute(
    """CREATE TABLE IF NOT EXISTS relatives(
    relative_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    first_name TEXT NOT NULL,
    middle_name TEXT,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone_number TEXT UNIQUE,
    FOREIGN KEY(patient_id) REFERENCES users(patient_id) ON DELETE CASCADE
    )"""
)

# Creates a 'accounts' Tables, with a foreign key(patient_id) from 'users' table.
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS accounts(
    username TEXT PRIMARY KEY NOT NULL,
    hashed_password TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
    patient_id TEXT,
    FOREIGN KEY(patient_id) REFERENCES users(patient_id) ON DELETE SET NULL
    )
    """
)

def get_all_patient_ids() -> list[str]:

    # "SELECTS" and stores all the patient_id from the users table.
    cursor.execute("SELECT patient_id FROM users")
    # Returns a list of tuples containing the patient_ids. Ex: [("CA0001",), ("TB2003",), etc....]
    patient_id_raw:list[tuple] = cursor.fetchall()
    # declare a empty list to avoid the 'possibly unbound' error.
    patient_id_formatted:list[str] = []
    
    # row -> set to each value in the list of tuples, until it reaches the last tuple of the list.
    for row in patient_id_raw:
        # appends to the empty list all the patient_ids that exist, 
        # as strings by accessing the very fisrt element of the tuple.
        patient_id_formatted.append(row[0])
    # returns the entire list. 
    return patient_id_formatted

def close_connection():

    # Saves all the changes to the disk, as permanent change.
    hospital.commit()
    # Closes the connection, hence closing the file and no further operations are possible.
    hospital.close()
