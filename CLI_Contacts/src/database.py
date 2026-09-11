import sqlite3
from pathlib import Path
from classes import User, Relatives 

__all__:list[str] = [
                     "insert_user", "insert_relative", "is_duplicate",
                     "patient_id_exists", "search_user_by_patient_id", 
                     "search_user_by_email", "search_user_by_phone", 
                     "search_users_by_name", "search_relatives_by_email", 
                     "search_relatives_by_phone", "search_relatives_by_name",
                     "update_query", "delete_query"
                     ]

# Path(__file__) -> returns a path object containing the path of the file it was called from. Ex: "src/database.py"
# .resolve() -> a Path method that completes(from ~/ -> current file) the relative/incomplete path returned by Path(__file__)
# .parent -> a property of Path that return the address of the parent directory of current file by stripping of one layer at a time.
# Here the first .parent strips away the "database.py" returning ".../CLI_Contacts/src/", the next .parent returns ".../CLI_Contacts/"
# Then, the '/' operator is already overloaded by the pathlib module, that concatanates the new path. This is then stored in a variable.
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hospital.db"
# sqlite3.connect -> opens the existing ".db" file at the location or creates one if it does not exist.
hospital = sqlite3.connect(DB_PATH)
# makes it so that each query call returns a "Row" object that can be accessed either by index value, or column_name.
hospital.row_factory = sqlite3.Row
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
    patient_id TEXT NOT NULL,
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
    patient_id_raw:list[sqlite3.Row] = cursor.fetchall()
    # declare a empty list to avoid the 'possibly unbound' error.
    patient_id_formatted:list[str] = []    
    # row -> set to each value in the list of tuples, until it reaches the last tuple of the list.
    for row in patient_id_raw:
        # appends to the empty list all the patient_ids that exist, 
        # as strings by accessing the very fisrt element of the tuple.
        patient_id_formatted.append(row[0])
    # returns the entire list. 
    return patient_id_formatted

def is_duplicate(phone: str | None = None, email: str | None = None) -> bool:
    if phone is None and email is None:
        return False
    conditions: list[str] = []
    params: list[str] = []
    if phone is not None:
        conditions.append("phone_number = ?")
        params.append(phone)
    if email is not None:
        conditions.append("email = ?")
        params.append(email)
    where_clause: str = " OR ".join(conditions)
    # The "WHERE" clause is used to check for a specific value in the database internally, rather than selecting
    # all rows and then running comparision checks, which is a waste of resources.
    cursor.execute(f"SELECT phone_number, email FROM users WHERE {where_clause}", params)
    # cursor.fetchone() -> returns a single row(in this case only if mathed.)
    users_match: sqlite3.Row = cursor.fetchone()
    # cursor.execute() can hold the value of only one query at a time. 
    # Hence after each "SELECT" execution call, we need to store the values.
    cursor.execute(f"SELECT phone_number, email FROM relatives WHERE {where_clause}", params)
    relatives_match: sqlite3.Row = cursor.fetchone()       
    # if the users_match or the relatives_match contain any value(match found), then the if statement executes,
    # as the presence of value is considered 'Truthy' in Python. Else it return 'False' as per the code.
    if users_match or relatives_match:
        return True
    else:
        return False

def split_name(input_name:str) -> dict[str, str]:
    name:str = input_name
    first:str
    middle:str = ""
    last:str
    collection:dict[str, str] = {}
    if len(name.split()) == 2:
        first, last = name.split()
        collection.update({"First": first, "Middle": middle, "Last": last})
        return collection
    else:
        first, middle, last = name.split()
        collection.update({"First": first, "Middle": middle, "Last": last})
        return collection

# Takes a 'user_obj' as input and inserts the attributes of that object into the various fields of the 'users' table.
def insert_user(user:User):
    name_dict:dict[str,str] = split_name(user.name)
    first:str = name_dict["First"]
    middle:str = name_dict["Middle"]
    last:str = name_dict["Last"]
    # Converts the actual date_obj into a string.
    dob:str = user.date_of_birth.strftime("%d-%m-%Y")    
    # (?, ?) -> is used to make sure that the values passed are just plain text(string), and avoid sql injections.
    cursor.execute("""
                   INSERT INTO users (patient_id, first_name, middle_name, last_name, date_of_birth, 
                   symptoms, email, phone_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   """, (user.patient_id, first, middle, last, dob, user.symptoms, user.email, user.number))

def patient_id_exists(patient_id:str) -> bool:
    cursor.execute("SELECT patient_id FROM users WHERE patient_id = ?", (patient_id,))
    matched_id:sqlite3.Row = cursor.fetchone()
    if matched_id:
        return True
    else:
        return False

def insert_relative(relative:Relatives):
    name_dict:dict[str,str] = split_name(relative.name)
    first:str = name_dict["First"]
    middle:str = name_dict["Middle"]
    last:str = name_dict["Last"]
    cursor.execute("""
                   INSERT INTO relatives (patient_id, first_name, middle_name, last_name, email,
                   phone_number) VALUES (?, ?, ?, ?, ?, ?)
                   """, (relative.patient_id, first, middle, last, relative.email, relative.number))

def search_user_by_patient_id(patient_id:str) -> dict[str, str] | None:
    cursor.execute("SELECT * FROM users WHERE patient_id = ?", (patient_id,))
    matched_id:sqlite3.Row = cursor.fetchone()
    if matched_id:
        matched_id_dict:dict[str, str] = dict(matched_id)
        return matched_id_dict
    else:
        return None

def search_user_by_email(email:str) -> dict[str, str] | None:
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    matched_email:sqlite3.Row = cursor.fetchone()    
    if matched_email:
        matched_email_dict:dict[str, str] = dict(matched_email)
        return matched_email_dict
    else:
        return None

def search_user_by_phone(phone:str) -> dict[str, str] | None:
    cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone,))
    matched_number:sqlite3.Row = cursor.fetchone()
    if matched_number:
        matched_number_dict:dict[str, str] = dict(matched_number)
        return matched_number_dict
    else:
        return None

def search_users_by_name(field:str, name:str) -> list[dict]| None:
    # Here the direct use of an f-string is permitted because the field is a stored value in dict-map,
    # and though input by user to the search() function, it is later on referenced to the dict map and
    # a "key" of type string is given as argument for this function.
    cursor.execute(f"SELECT * FROM users WHERE {field} = ?", (name,))
    matched_name:list[sqlite3.Row] = cursor.fetchall()
    if matched_name:
        matched_name_dict:list[dict] = [dict(row) for row in matched_name]
        return matched_name_dict
    else:
        return None

def get_user_by_patient_id(patient_id:str) -> dict[str, str]:
    cursor.execute("SELECT patient_id, first_name, middle_name, last_name FROM users WHERE patient_id = ?", (patient_id,))
    matched_users:sqlite3.Row = cursor.fetchone()
    matched_users_dict:dict[str, str] = dict(matched_users)
    return matched_users_dict

def search_relatives_by_email(email:str) -> list[dict] | None:
    cursor.execute("SELECT * FROM relatives WHERE email = ?", (email,))
    matched_email:sqlite3.Row = cursor.fetchone()
    if matched_email:
        user_data:dict[str, str] = get_user_by_patient_id(matched_email["patient_id"])
        matched_email_dict:dict[str, str] = dict(matched_email)
        email_dict:list[dict] = []
        email_dict.append(matched_email_dict)
        email_dict.append(user_data)
        return email_dict
    else:
        return None

def search_relatives_by_phone(phone:str) -> list[dict] | None:
    cursor.execute("SELECT * FROM relatives WHERE phone_number = ?", (phone,))
    matched_number:sqlite3.Row = cursor.fetchone()
    if matched_number:
        user_data:dict[str, str] = get_user_by_patient_id(matched_number["patient_id"])
        matched_number_dict:dict[str, str] = dict(matched_number)
        number_dict:list[dict] = []
        number_dict.append(matched_number_dict)
        number_dict.append(user_data)
        return number_dict
    else:
        return None

def search_relatives_by_name(field:str, name:str) -> list[dict[str, dict]] | None:
    cursor.execute(f"SELECT * FROM relatives WHERE {field} = ?", (name,))
    matched_name:list[sqlite3.Row] = cursor.fetchall()
    if matched_name:
        results:list[dict[str, dict]] = []
        for row in matched_name:
            user_data:dict[str, str] = get_user_by_patient_id(row["patient_id"])
            matched_name_dict:dict = dict(row)
            combined_dict:dict[str, dict] = {"Relatives": matched_name_dict, "User": user_data}
            results.append(combined_dict)
        return results
    else:
        return None

def update_query(table: str, field: str, value: str, row_id: str) -> None:
    if table == "users":
        cursor.execute(f"UPDATE users SET {field} = ? WHERE patient_id = ?", (value, row_id))
    elif table == "relatives":
        cursor.execute(f"UPDATE relatives SET {field} = ? WHERE relative_row_id = ?", (value, row_id))

def delete_query(table:str, row_id:str) -> None:
    if table == "users":
        cursor.execute("DELETE FROM users WHERE patient_id = ?", (row_id,))
    elif table == "relatives":
        cursor.execute("DELETE FROM relatives WHERE relative_row_id = ?", (row_id,))

def close_connection():
    # Saves all the changes to the disk, as permanent change.
    hospital.commit()
    # Closes the connection, hence closing the file and no further operations are possible.
    hospital.close()
