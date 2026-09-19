import sys
import os

# Ensure imports resolve whether the script is run from src/ or from the project root.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import sign_up, login
from database import link_patient_id
from operations import (
    add_user,
    add_relative,
    update,
    delete,
    view,
    get_relatives_by_patient_id,
    get_all_users,
)
from exports import (
    build_patient_record,
    build_admin_records,
    export_patient_txt,
    export_patient_csv,
    export_patient_docx,
    export_patient_pdf,
    export_admin_txt,
    export_admin_csv,
    export_admin_docx,
    export_admin_pdf,
    prompt_export_path,
)
from patient_id import free_patient_id


# ══════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ══════════════════════════════════════════════════════════════════════

def draw_menu(title: str, options: list[str]) -> dict[int, str]:
    """
    Renders a double-line ASCII box with a centred title and an auto-numbered
    list of options.

    Width is the greater of the terminal window width and the minimum content
    width, so the box always spans the full terminal. Falls back to 80 columns
    when stdout is not a TTY (e.g. during piped tests).

    Returns a {number: original_label} dict for use by the caller's dispatch
    logic.
    """
    PADDING = 2
    PAD = " " * PADDING

    # Pre-format every option with its [ N ]  prefix
    numbered: dict[int, str] = {
        i + 1: f"[ {i + 1} ]  {opt}" for i, opt in enumerate(options)
    }

    # Minimum content area: wide enough to hold title and every formatted option
    min_content_width: int = max(len(title), max(len(s) for s in numbered.values()))

    # Expand to fill the full terminal; fall back to 80 if not a real TTY
    try:
        terminal_cols: int = os.get_terminal_size().columns
    except OSError:
        terminal_cols: int = 80

    # inner_width = space between the two ║ border chars
    # terminal_cols - 2 accounts for the border chars themselves
    inner_width: int = max(min_content_width + PADDING * 2, terminal_cols - 2)
    content_width: int = inner_width - PADDING * 2

    top    = f"╔{'═' * inner_width}╗"
    sep    = f"╠{'═' * inner_width}╣"
    bottom = f"╚{'═' * inner_width}╝"
    blank  = f"║{' ' * inner_width}║"

    print()
    print(top)
    print(f"║{PAD}{title.center(content_width)}{PAD}║")
    print(sep)
    print(blank)
    for opt_str in numbered.values():
        print(f"║{PAD}{opt_str:<{content_width}}{PAD}║")
    print(blank)
    print(bottom)
    print()

    return {num: options[num - 1] for num in numbered}


def get_valid_choice(menu_map: dict[int, str]) -> int:
    """Loops until the user enters a valid integer key that exists in menu_map."""
    while True:
        try:
            choice: int = int(input("  Enter your choice: ").strip())
            if choice in menu_map:
                return choice
            print(f"  Please enter a number between 1 and {max(menu_map)}.")
        except ValueError:
            print("  Invalid input — please enter a number.")


# ══════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════

def profile_completion(username: str) -> str | None:
    """
    Runs add_user() to collect and store the new patient's details, then
    links the generated patient_id back to the account row.

    Called both after a fresh sign-up and after a first login where
    patient_id is still None.

    Returns the patient_id string on success, None on failure.
    """
    print("\n  Please complete your patient profile to continue.\n")
    patient_id: str | None = add_user()
    if patient_id is None:
        print("\n  Profile setup failed. Please try again after logging in.")
        return None
    link_patient_id(username, patient_id)
    print(f"\n  Profile complete! Your Patient ID is: {patient_id}")
    return patient_id


def handle_signup() -> None:
    status, data = sign_up()
    if status == "password_mismatch":
        print("\n  Passwords do not match. Please try again.")
        return
    if status == "username_taken":
        print("\n  That username is already taken. Please choose another.")
        return
    # status == "success"
    print(f"\n  Account created! Welcome, {data['username']}.")
    patient_id: str | None = profile_completion(data['username'])
    if patient_id:
        user_menu({"username": data['username'], "role": "user", "patient_id": patient_id})


def handle_login() -> None:
    status, session = login()
    if status == "invalid_credentials":
        print("\n  Invalid credentials. Please try again.")
        return
    # status == "success"
    if session['role'] == "user" and session['patient_id'] is None:
        patient_id: str | None = profile_completion(session['username'])
        if patient_id is None:
            return
        session['patient_id'] = patient_id
    if session['role'] == "user":
        user_menu(session)
    elif session['role'] == "admin":
        admin_menu(session)


# ══════════════════════════════════════════════════════════════════════
#  USER MENU — HANDLERS
# ══════════════════════════════════════════════════════════════════════

def handle_user_view(session: dict) -> None:
    view("users", "patient_id", session['patient_id'])


def handle_user_update(session: dict) -> None:
    field_map = draw_menu(
        "UPDATE PROFILE — Choose a field",
        ["First Name", "Middle Name", "Last Name", "Date of Birth", "Email", "Phone Number", "Back"]
    )
    field_choice: int = get_valid_choice(field_map)
    if field_map[field_choice] == "Back":
        return
    label_to_field: dict[str, str] = {
        "First Name":    "first_name",
        "Middle Name":   "middle_name",
        "Last Name":     "last_name",
        "Date of Birth": "date_of_birth",
        "Email":         "email",
        "Phone Number":  "phone_number",
    }
    db_field: str = label_to_field[field_map[field_choice]]
    new_value: str = input(f"  Enter new value for {field_map[field_choice]}: ").strip()
    # patient_id is a UNIQUE field — no ambiguity possible.
    status, _ = update("users", "patient_id", session['patient_id'], {db_field: new_value})
    if status != "success":
        print(f"  Update failed ({status}).")


def handle_user_delete(session: dict) -> bool:
    """
    Prompts for confirmation and deletes the user's own profile.
    Returns True on success so user_menu() knows to break out and return
    to the main menu.
    """
    confirm: str = input(
        "\n  Are you sure you want to delete your profile? "
        "This cannot be undone. [yes/no]: "
    ).strip().lower()
    if confirm != "yes":
        print("  Deletion cancelled.")
        return False
    status, data = delete("users", "patient_id", session['patient_id'])
    if status == "success":
        free_patient_id(session['patient_id'])
        print("\n  Your profile has been deleted. Returning to the main menu.")
        return True
    print(f"  Deletion failed ({status}).")
    return False


def _pick_own_relative(session: dict) -> dict | None:
    """
    Displays the logged-in user's relatives and returns the dict of whichever
    one they pick. Returns None if there are no relatives or they cancel.
    """
    relatives: list[dict] | None = get_relatives_by_patient_id(session['patient_id'])
    if not relatives:
        print("\n  You have no relatives linked to your profile.")
        return None
    print("\n  Your relatives:\n")
    for i, rel in enumerate(relatives, 1):
        middle: str = rel.get('middle_name') or ''
        full_name: str = (
            f"{rel['first_name']} {middle} {rel['last_name']}"
            .replace("  ", " ").strip()
        )
        print(f"  {i}. {full_name}  |  row_id: {rel['relative_row_id']}  |  email: {rel['email']}")
    print()
    while True:
        try:
            pick: int = int(input("  Enter the number of the relative: ").strip())
            if 1 <= pick <= len(relatives):
                return relatives[pick - 1]
            print(f"  Please enter a number between 1 and {len(relatives)}.")
        except ValueError:
            print("  Invalid input — please enter a number.")


def handle_add_relative(session: dict) -> None:
    confirm_map = draw_menu(
        "ADD A RELATIVE",
        ["Proceed", "Back"]
    )
    if get_valid_choice(confirm_map) == 2:
        return
    # add_relative() internally prompts for a patient_id — show the user's own as a hint.
    print(f"\n  Your Patient ID is: {session['patient_id']}")
    add_relative()


def handle_update_relative(session: dict) -> None:
    chosen: dict | None = _pick_own_relative(session)
    if chosen is None:
        return
    field_map = draw_menu(
        "UPDATE RELATIVE — Choose a field",
        ["First Name", "Middle Name", "Last Name", "Email", "Phone Number", "Back"]
    )
    field_choice: int = get_valid_choice(field_map)
    if field_map[field_choice] == "Back":
        return
    label_to_field: dict[str, str] = {
        "First Name":   "first_name",
        "Middle Name":  "middle_name",
        "Last Name":    "last_name",
        "Email":        "email",
        "Phone Number": "phone_number",
    }
    db_field: str = label_to_field[field_map[field_choice]]
    new_value: str = input(f"  Enter new value for {field_map[field_choice]}: ").strip()
    # The relative's email is globally unique — guaranteed unambiguous match.
    status, _ = update("relatives", "email", chosen['email'], {db_field: new_value})
    if status != "success":
        print(f"  Update failed ({status}).")


def handle_delete_relative(session: dict) -> None:
    chosen: dict | None = _pick_own_relative(session)
    if chosen is None:
        return
    middle: str = chosen.get('middle_name') or ''
    full_name: str = (
        f"{chosen['first_name']} {middle} {chosen['last_name']}"
        .replace("  ", " ").strip()
    )
    confirm: str = input(f"\n  Delete relative '{full_name}'? [yes/no]: ").strip().lower()
    if confirm != "yes":
        print("  Deletion cancelled.")
        return
    # Email is globally unique — guaranteed unambiguous single-row match.
    status, _ = delete("relatives", "email", chosen['email'])
    if status != "success":
        print(f"  Deletion failed ({status}).")


def handle_user_export(session: dict) -> None:
    status, record = build_patient_record("patient_id", session['patient_id'])
    if status != "success":
        print("\n  Could not retrieve your data for export.")
        return
    fmt_map = draw_menu("EXPORT FORMAT", ["TXT", "CSV", "DOCX", "PDF", "Back"])
    fmt_choice: int = get_valid_choice(fmt_map)
    if fmt_map[fmt_choice] == "Back":
        return
    path = prompt_export_path()
    export_funcs: dict = {
        "TXT":  export_patient_txt,
        "CSV":  export_patient_csv,
        "DOCX": export_patient_docx,
        "PDF":  export_patient_pdf,
    }
    saved_path: str = export_funcs[fmt_map[fmt_choice]](record, path)
    print(f"\n  Exported to: {saved_path}")


def user_menu(session: dict) -> None:
    while True:
        menu_map = draw_menu(
            f"USER MENU  —  {session['username']}",
            [
                "View my profile",
                "Update my profile",
                "Delete my profile",
                "Add a relative",
                "Update a relative",
                "Delete a relative",
                "Export my data",
                "Logout",
            ]
        )
        choice: int = get_valid_choice(menu_map)
        if choice == 1:
            handle_user_view(session)
        elif choice == 2:
            handle_user_update(session)
        elif choice == 3:
            if handle_user_delete(session):
                return          # profile deleted → back to main menu
        elif choice == 4:
            handle_add_relative(session)
        elif choice == 5:
            handle_update_relative(session)
        elif choice == 6:
            handle_delete_relative(session)
        elif choice == 7:
            handle_user_export(session)
        elif choice == 8:
            print(f"\n  Goodbye, {session['username']}!\n")
            return


# ══════════════════════════════════════════════════════════════════════
#  ADMIN HELPERS
# ══════════════════════════════════════════════════════════════════════

def _prompt_table() -> str:
    """
    Asks admin to pick users, relatives, or go back.
    Returns the DB table name string, or the sentinel "back".
    """
    table_map = draw_menu("Choose a table", ["Users", "Relatives", "Back"])
    choice = get_valid_choice(table_map)
    if table_map[choice] == "Back":
        return "back"
    return "users" if choice == 1 else "relatives"


def _prompt_search_params(table: str) -> tuple[str, str]:
    """
    Prompts the admin for a search field and a search value.
    Returns ("back", "") if the admin picks Back, otherwise (db_field, value).
    """
    if table == "users":
        field_opts = [
            "patient_id", "email", "phone_number",
            "first_name", "middle_name", "last_name", "Back",
        ]
        field_map = draw_menu("SEARCH USERS — Choose a field", field_opts)
    else:
        field_opts = [
            "email", "phone_number",
            "first_name", "middle_name", "last_name", "Back",
        ]
        field_map = draw_menu("SEARCH RELATIVES — Choose a field", field_opts)

    field_choice: int = get_valid_choice(field_map)
    if field_map[field_choice] == "Back":
        return "back", ""
    db_field: str = field_map[field_choice]     # already a valid DB field name
    value: str = input("  Enter search value: ").strip()
    return db_field, value


def _resolve_ambiguity(table: str, candidates: list[dict]) -> str | None:
    """
    Prints all ambiguous candidates and prompts the admin to pick one by
    its row identifier (patient_id for users, relative_row_id for relatives).
    Returns the chosen identifier string, or None if cancelled.
    """
    print(f"\n  {len(candidates)} matches found:\n")
    for candidate in candidates:
        if table == "users":
            middle: str = candidate.get('middle_name') or ''
            full_name: str = (
                f"{candidate['first_name']} {middle} {candidate['last_name']}"
                .replace("  ", " ").strip()
            )
            print(f"  patient_id: {candidate['patient_id']}  |  {full_name}  |  {candidate['email']}")
        else:
            # search_relatives_by_name returns {"Relatives": {...}, "User": {...}}
            rel: dict = candidate.get("Relatives", candidate)
            middle = rel.get('middle_name') or ''
            full_name = (
                f"{rel['first_name']} {middle} {rel['last_name']}"
                .replace("  ", " ").strip()
            )
            print(f"  row_id: {rel['relative_row_id']}  |  {full_name}  |  {rel['email']}")

    id_label: str = "patient_id" if table == "users" else "relative row_id"
    chosen_id: str = input(
        f"\n  Enter the {id_label} to act on (or press Enter to cancel): "
    ).strip()
    if not chosen_id:
        print("  Action cancelled.")
        return None
    return chosen_id


# ══════════════════════════════════════════════════════════════════════
#  ADMIN MENU — HANDLERS
# ══════════════════════════════════════════════════════════════════════

def handle_admin_view() -> None:
    table: str = _prompt_table()
    if table == "back":
        return
    field, value = _prompt_search_params(table)
    if field == "back":
        return
    view(table, field, value)


def handle_admin_update() -> None:
    table: str = _prompt_table()
    if table == "back":
        return
    field, value = _prompt_search_params(table)
    if field == "back":
        return

    update_opts = (
        ["First Name", "Middle Name", "Last Name", "Date of Birth", "Email", "Phone Number", "Back"]
        if table == "users"
        else ["First Name", "Middle Name", "Last Name", "Email", "Phone Number", "Back"]
    )
    update_field_map = draw_menu("Choose field to update", update_opts)
    update_field_choice: int = get_valid_choice(update_field_map)
    if update_field_map[update_field_choice] == "Back":
        return
    label_to_field: dict[str, str] = {
        "First Name":    "first_name",
        "Middle Name":   "middle_name",
        "Last Name":     "last_name",
        "Date of Birth": "date_of_birth",
        "Email":         "email",
        "Phone Number":  "phone_number",
    }
    db_field: str = label_to_field[update_field_map[update_field_choice]]
    new_value: str = input(f"  Enter new value for {update_field_map[update_field_choice]}: ").strip()

    status, data = update(table, field, value, {db_field: new_value})
    if status == "ambiguous":
        row_id: str | None = _resolve_ambiguity(table, data)
        if row_id:
            update(table, field, value, {db_field: new_value}, row_identifier=row_id)
    elif status != "success":
        print(f"  Update failed ({status}).")


def handle_admin_delete() -> None:
    table: str = _prompt_table()
    if table == "back":
        return
    field, value = _prompt_search_params(table)
    if field == "back":
        return

    confirm: str = input(
        "\n  Are you sure you want to delete this record? [yes/no]: "
    ).strip().lower()
    if confirm != "yes":
        print("  Deletion cancelled.")
        return

    status, data = delete(table, field, value)
    if status == "ambiguous":
        row_id: str | None = _resolve_ambiguity(table, data)
        if row_id:
            status, data = delete(table, field, value, row_identifier=row_id)
            if status == "success" and table == "users":
                free_patient_id(data['deleted']['patient_id'])
    elif status == "success":
        if table == "users":
            free_patient_id(data['deleted']['patient_id'])
    else:
        print(f"  Deletion failed ({status}).")


def handle_admin_add_relative() -> None:
    confirm_map = draw_menu("ADD A RELATIVE", ["Proceed", "Back"])
    if get_valid_choice(confirm_map) == 2:
        return
    add_relative()


def handle_admin_export() -> None:
    all_users: list[dict] = get_all_users()
    if not all_users:
        print("\n  No patients in the database.")
        return

    print("\n  All patients:\n")
    for i, user in enumerate(all_users, 1):
        middle: str = user.get('middle_name') or ''
        full_name: str = (
            f"{user['first_name']} {middle} {user['last_name']}"
            .replace("  ", " ").strip()
        )
        print(f"  {i:>3}.  {user['patient_id']}  |  {full_name}")

    print("\n  Enter patient_ids to export, comma-separated")
    print("  (or press Enter to export all):")
    selection: str = input("  > ").strip()

    selected_ids: list[str] = (
        [pid.strip() for pid in selection.split(",") if pid.strip()]
        if selection
        else [u['patient_id'] for u in all_users]
    )

    records: list[dict] = build_admin_records(selected_ids)
    if not records:
        print("\n  No valid records found for the selected IDs.")
        return

    fmt_map = draw_menu("EXPORT FORMAT", ["TXT", "CSV", "DOCX", "PDF", "Back"])
    fmt_choice: int = get_valid_choice(fmt_map)
    if fmt_map[fmt_choice] == "Back":
        return
    path = prompt_export_path()
    export_funcs: dict = {
        "TXT":  export_admin_txt,
        "CSV":  export_admin_csv,
        "DOCX": export_admin_docx,
        "PDF":  export_admin_pdf,
    }
    saved_path: str = export_funcs[fmt_map[fmt_choice]](records, path)
    print(f"\n  Exported {len(records)} patient(s) to: {saved_path}")


def admin_menu(session: dict) -> None:
    while True:
        menu_map = draw_menu(
            f"ADMIN MENU  —  {session['username']}",
            [
                "View a record",
                "Update a record",
                "Delete a record",
                "Add a relative",
                "Bulk export",
                "Logout",
            ]
        )
        choice: int = get_valid_choice(menu_map)
        if choice == 1:
            handle_admin_view()
        elif choice == 2:
            handle_admin_update()
        elif choice == 3:
            handle_admin_delete()
        elif choice == 4:
            handle_admin_add_relative()
        elif choice == 5:
            handle_admin_export()
        elif choice == 6:
            print(f"\n  Goodbye, {session['username']}!\n")
            return


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

def main_menu() -> None:
    while True:
        menu_map = draw_menu(
            "HOSPITAL RECORDS MANAGER",
            ["Sign Up", "Login", "Exit"]
        )
        choice: int = get_valid_choice(menu_map)
        if choice == 1:
            handle_signup()
        elif choice == 2:
            handle_login()
        elif choice == 3:
            print("\n  Goodbye!\n")
            sys.exit(0)


if __name__ == "__main__":
    main_menu()
