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

# Writes all the changes to the disk.
hospital.commit()

# Closes the file.
hospital.close()
