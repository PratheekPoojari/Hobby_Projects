import secrets
import hashlib
import sqlite3
from patterns import *
from database import *

def hash_password(password:str) -> tuple:
    salt:str = secrets.token_hex(16)
    hashed:bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100_000
        )
    return (hashed.hex(), salt)

def verify_password(password:str, stored_hash:str, stored_salt:str) -> bool:
    new_hash:bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            stored_salt.encode(),
            100_000
        )
    return secrets.compare_digest(stored_hash, new_hash.hex())

def prompt_username() -> str:
    while True:
        name:str = input("Enter your 'Username': ")
        if is_valid_username(name):
            return name

def prompt_password() -> str:
    while True:
        password:str = input("Enter your password: ")
        if is_valid_password(password):
            return password

def prompt_confirm_password() -> str:
    while True:
        confirm_password:str = input("Re-Enter your Password: ")
        if is_valid_password(confirm_password):
            return confirm_password

def sign_up() -> tuple:
    print("""
          The Username may contain alphabets, both upper and lowercase, numbers and underscore.
          The minimum number of character need to be 3 and the maximum is 12. Use a mix of all 
          the available character so as to get a unique Username all to yourself, witout errors.
          """)
    username:str = prompt_username()
    print("""
          The Password must be of a minimum length of 9 characters and a maximum of 18 characters.
          Characters used in the password needs to be a mix of lowercase and uppercase letters along
          with digits and a special symbol like '#','$', etc... Use atleast one of each kind.
          """)
    password:str = prompt_password()
    confirm_password:str = prompt_confirm_password()
    if password != confirm_password:
        return ("password_mismatch", None)
    hashed_hex, salt = hash_password(password)
    try:
       insert_account(username, hashed_hex, salt, "user")
    except sqlite3.IntegrityError:
        return ("username_taken", None)
    return ("success", {"username": username, "role": "user", "patient_id":None})

def login() -> tuple:
    print("Choose your role: User or Admin")
    role:str = input("Enter your role: ").lower().strip()
    username:str = prompt_username()
    password:str = input("Enter your Password: ").strip()
    data:dict | None = get_account(username)
    if data is None:
        return ("invalid_credentials", None)
    if role != data["role"]:
        return ("invalid_credentials", None)
    verification:bool = verify_password(password, data["hashed_password"], data["salt"])
    if verification:
        return ("success", {"username": username, "role": role, "patient_id": data["patient_id"]})
    return ("invalid_credentials", None)
