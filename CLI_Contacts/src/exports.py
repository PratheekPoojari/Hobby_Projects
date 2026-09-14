import csv
from datetime import date, datetime
from pathlib import Path
from docx import Document
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from classes import calc_age, session_date
from operations import search, get_relatives_by_patient_id, ambiguity_check, resolve_selection


def build_patient_record(search_field:str, search_value:str, row_identifier:str | None = None) -> tuple[str, dict | list | None]:
    result:dict[str, str] | list[dict] | None = search("users", search_field, search_value)
    if result is None:
        print(f"The value '{search_value}' could not be found in the field '{search_field}' of the 'users' table")        
        return ("not_found", None)

    ambiguity:str | None = ambiguity_check("users", search_field, result)
    chosen:dict | None = {}

    if ambiguity == "Ambiguous":
        if not isinstance(result, list):
            print("Invalid data format.")
            return ("failed", None)
        if row_identifier is None:
            print("Multiple matches found. Please Select any one by their 'patient_id'")
            return ("ambiguous", result)
        else:
            chosen = resolve_selection("users", result, row_identifier)
            if chosen is None:
                return ("not_found", None)
    elif ambiguity == "Unambiguous":
        chosen = result[0] if isinstance(result, list) else result
    else:
        print(f"The value '{search_value}' could not be found in the field '{search_field}' of the 'users' table")
        return ("not_found", None)

    dob:date = datetime.strptime(chosen["date_of_birth"], "%d-%m-%Y").date()
    age:int = calc_age(session_date, dob)
    relatives:list[dict[str, str]] | None = get_relatives_by_patient_id(chosen["patient_id"])
    if relatives is None:
        relatives = []
    record:dict[str, dict | list] = {"user":{**chosen, "age": age}, "relatives":relatives}
    return ("success", record)


def prompt_export_path() -> Path | None:
    while True:
        path:str = input("Enter the absolute path to where you would like to export the file:").strip()
        if path:
            if Path(path).is_absolute():
                return Path(path)
            else:
                print("Incorrect Absolute Path Entered.")
                re_prompt:str = input("[r]e-enter / [d]efault").strip().lower()
                if re_prompt == "r":
                    continue
                elif re_prompt == "d":
                    return None
                else:
                    print("Invalid Choice.")
                    continue
        else:
            return None
            

def export_patient_txt(record:dict, path:str | Path | None = None) -> str:

    timestamp:datetime = datetime.now()
    file_time_stamp:str = timestamp.strftime("%d-%m-%Y_%H-%M-%S")
    patient_id:str = record["user"]["patient_id"]
    filename:str = f"{patient_id}_{file_time_stamp}.txt"

    export_to_path:Path = Path(__file__).resolve().parent.parent / "exports" / filename   
    if path:
        if Path(path).is_absolute():
            export_to_path = Path(path) / filename
    
    user_record:dict = record["user"]
    relatives_record:list[dict] = record["relatives"]

    export_to_path.parent.mkdir(parents=True, exist_ok=True)

    with open(export_to_path, "w", encoding="utf-8") as file:

        formatted_timestamp:str = timestamp.strftime("%d-%m-%Y %H:%M:%S")
        file.write(f"Export Time: {formatted_timestamp}\n")
        file.write("----------User Data----------\n")
        for key, val in user_record.items():
            file.write(f"{key}: {val}\n")

        file.write("----------Relatives Data----------\n")
        if relatives_record:
            for i, relative in enumerate(relatives_record):
                file.write(f"Relative{str(i)}\n")
                for key, val in relative.items():
                    file.write(f"{key}: {val}\n")
        else:
            file.write("This User doesn't yet have any Relatives attached.")

    return str(export_to_path)

def export_patient_csv(record:dict, path:str | None = None) -> str:
    ...
