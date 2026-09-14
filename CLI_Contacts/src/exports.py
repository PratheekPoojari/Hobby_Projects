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
            

def resolve_export_path(filename:str, path:str | Path | None = None) -> Path:

    export_to_path:Path = Path(__file__).resolve().parent.parent / "exports" / filename   
    if path:
        if Path(path).is_absolute():
            export_to_path = Path(path) / filename
    export_to_path.parent.mkdir(parents=True, exist_ok=True)
    return export_to_path


def format_time(select:str) -> str | None:
    if select == "file_name":
        timestamp:datetime = datetime.now()
        file_time_stamp:str = timestamp.strftime("%d-%m-%Y_%H-%M-%S")
        return file_time_stamp
    elif select == "in_file":
        timestamp:datetime = datetime.now()
        formatted_timestamp:str = timestamp.strftime("%d-%m-%Y %H:%M:%S")
        return formatted_timestamp
    else:
        return None


def export_patient_txt(record:dict, path:str | Path | None = None) -> str:

    user_record:dict = record["user"]
    relatives_record:list[dict] = record["relatives"]

    txt_time_stamp:str | None = format_time("file_name")
    patient_id:str = user_record["patient_id"]
    filename:str = f"{patient_id}_{txt_time_stamp}.txt"

    write_to_path:Path = resolve_export_path(filename, path)

    with open(write_to_path, "w", encoding="utf-8") as file:

        file.write(f"Export Time: {format_time("in_file")}\n")
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

    return str(write_to_path)


def export_patient_csv(record:dict, path:str | None = None) -> str:

    user_record:dict = record["user"]
    relatives_record:list[dict] = record["relatives"]

    csv_time_stamp:str | None = format_time("file_name")
    patient_id:str = user_record["patient_id"]
    filename:str = f"{patient_id}_{csv_time_stamp}.csv"

    write_to_path:Path = resolve_export_path(filename, path)

    relatives_str:str = "; ".join(
        f"{rel['first_name']} {rel.get('middle_name') or ''} {rel['last_name']}({rel['email']}, {rel['phone_number']})"
        for rel in relatives_record)                                                                                                
    row:dict[str, str] = {**user_record, "relatives": relatives_str}
    fieldnames:list[str] = list(row.keys())

    with open(write_to_path, "w", newline="", encoding="utf-8") as file:
        print("Note: each patient's relatives are stored in a single ';'-separated field.")
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)

    return str(write_to_path)


def export_patient_docx(record:dict, path:str | None = None) -> str:
    user_record:dict = record["user"]
    relatives_record:list[dict] = record["relatives"]

    docx_time_stamp:str | None = format_time("file_name")
    patient_id:str = user_record["patient_id"]
    filename:str = f"{patient_id}_{docx_time_stamp}.docx"

    write_to_path:Path = resolve_export_path(filename, path)

    doc = Document()
    doc.add_heading("Patient Record", level=1)
    doc.add_paragraph(f"Export Time: {format_time("in_file")}")
    
    doc.add_heading("Patient Details", level=2)
    for key, val in user_record.items():
        doc.add_paragraph(f"{key}: {val}\n")

    doc.add_heading("Relatives Details", level=2)
    if relatives_record:
        for i, relative in enumerate(relatives_record):
            doc.add_paragraph(f"Relative{str(i)}\n")
            for key, val in relative.items():
                doc.add_paragraph(f"{key}: {val}\n")
    else:
        doc.add_paragraph("This User doesn't yet have any Relatives attached.")

    doc.save(str(write_to_path))

    return str(write_to_path)


def export_patient_pdf(record:dict, path:str | Path | None = None) -> str:
    ...
