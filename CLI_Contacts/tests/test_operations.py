import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from classes import User, Relatives
from patient_id import generate_patient_id
from database import close_connection, insert_user, insert_relative, search_user_by_patient_id, search_relatives_by_email
from operations import delete, view, update
import io
from contextlib import redirect_stdout


def test_case() -> None:
    # ---- Setup: 3 users, with 1, 2, and 3 relatives respectively ----
    # User 1 — 1 relative
    patient_id_1 = generate_patient_id("CA")
    user_1 = User(patient_id_1, "01-01-1990", "test symptoms for user one",
                  "Alice One", "aliceone1@test.com", "+91 9000000001")
    insert_user(user_1)
    relative_1a = Relatives("Bob One", "bobone1@test.com", "+91 9000000002", patient_id_1)
    insert_relative(relative_1a)
    # User 2 — 2 relatives
    patient_id_2 = generate_patient_id("TB")
    user_2 = User(patient_id_2, "02-02-1991", "test symptoms for user two",
                  "Alice Two", "alicetwo1@test.com", "+91 9000000003")
    insert_user(user_2)
    relative_2a = Relatives("Bob Two", "bobtwoa1@test.com", "+91 9000000004", patient_id_2)
    relative_2b = Relatives("Carl Two", "bobtwob1@test.com", "+91 9000000005", patient_id_2)
    insert_relative(relative_2a)
    insert_relative(relative_2b)
    # User 3 — 3 relatives
    patient_id_3 = generate_patient_id("MA")
    user_3 = User(patient_id_3, "03-03-1992", "test symptoms for user three",
                  "Alice Three", "alicethree1@test.com", "+91 9000000006")
    insert_user(user_3)
    relative_3a = Relatives("Bob Three", "bobthreea1@test.com", "+91 9000000007", patient_id_3)
    relative_3b = Relatives("Carl Three", "bobthreeb1@test.com", "+91 9000000008", patient_id_3)
    relative_3c = Relatives("Dave Three", "bobthreec1@test.com", "+91 9000000009", patient_id_3)
    insert_relative(relative_3a)
    insert_relative(relative_3b)
    insert_relative(relative_3c)
    print("\n--- Setup complete: 3 users created with 1, 2, and 3 relatives ---\n")
    # ---- Action 1: delete user 1 entirely — relies on FK cascade to remove relative_1a ----
    status, data = delete("users", "patient_id", patient_id_1)
    print(f"\nDelete user 1 status: {status}")
    assert status == "success", "Expected user 1 deletion to succeed."
    cascade_check = search_relatives_by_email("bobone1@test.com")
    assert cascade_check is None, "FAIL: relative_1a still exists — cascade didn't fire."
    print("PASS: user 1 and their relative were both removed (cascade confirmed).")
    # ---- Action 2: delete the first relative of user 2 (relative_2a) ----
    status, data = delete("relatives", "email", "bobtwoa1@test.com")
    print(f"\nDelete relative_2a status: {status}")
    assert status == "success", "Expected relative_2a deletion to succeed."
    assert search_relatives_by_email("bobtwoa1@test.com") is None, "FAIL: relative_2a still exists."
    assert search_relatives_by_email("bobtwob1@test.com") is not None, "FAIL: relative_2b was wrongly removed."
    assert search_user_by_patient_id(patient_id_2) is not None, "FAIL: user 2 was wrongly removed."
    print("PASS: relative_2a removed; relative_2b and user 2 untouched.")
    # ---- Action 3: delete the last two relatives of user 3 (relative_3b, relative_3c) ----
    status, data = delete("relatives", "email", "bobthreeb1@test.com")
    print(f"\nDelete relative_3b status: {status}")
    assert status == "success", "Expected relative_3b deletion to succeed."
    status, data = delete("relatives", "email", "bobthreec1@test.com")
    print(f"Delete relative_3c status: {status}")
    assert status == "success", "Expected relative_3c deletion to succeed."
    assert search_relatives_by_email("bobthreeb1@test.com") is None, "FAIL: relative_3b still exists."
    assert search_relatives_by_email("bobthreec1@test.com") is None, "FAIL: relative_3c still exists."
    assert search_relatives_by_email("bobthreea1@test.com") is not None, "FAIL: relative_3a was wrongly removed."
    assert search_user_by_patient_id(patient_id_3) is not None, "FAIL: user 3 was wrongly removed."
    print("PASS: relative_3b and relative_3c removed; relative_3a and user 3 untouched.")
    print("\nAll delete() test cases passed.\n")

    # ---- Action 4: two USERS sharing the same first AND last name ----
    patient_id_4a = generate_patient_id("PS")
    user_4a = User(patient_id_4a, "04-04-1993", "test symptoms for user four a",
                   "John Doe", "johndoea1@test.com", "+91 9000000010")
    insert_user(user_4a)

    patient_id_4b = generate_patient_id("DE")
    user_4b = User(patient_id_4b, "05-05-1994", "test symptoms for user four b",
                   "John Kumar Doe", "johndoeb1@test.com", "+91 9000000011")
    insert_user(user_4b)

    print(f"\n--- Setup complete: two users sharing first_name='John', last_name='Doe' "
          f"({patient_id_4a} without a middle name, {patient_id_4b} with middle_name='Kumar') ---\n")

    status, data = delete("users", "first_name", "John")
    print(f"\nAmbiguous same-name delete, first call status: {status}")
    assert status == "ambiguous", "Expected an ambiguous match for two users named John."
    assert isinstance(data, list) and len(data) == 2, "Expected exactly two candidates."
    print(f"Candidates returned: {[row['patient_id'] for row in data]}")

    status, data = delete("users", "first_name", "John", row_identifier=patient_id_4b)
    print(f"Ambiguous same-name delete, second call status: {status}")
    assert status == "success", "Expected deletion of user 4b to succeed."
    assert data["deleted"]["patient_id"] == patient_id_4b, "FAIL: wrong user was deleted."
    print(f"PASS: correctly deleted {patient_id_4b} (the one with middle_name='Kumar').")

    assert search_user_by_patient_id(patient_id_4b) is None, "FAIL: user 4b still exists."
    assert search_user_by_patient_id(patient_id_4a) is not None, "FAIL: user 4a was wrongly removed."
    print("PASS: user 4a (same name, no middle name) untouched after sibling's deletion.")

    status, data = delete("users", "patient_id", patient_id_4a)
    assert status == "success", "Expected cleanup deletion of user 4a to succeed."
    assert search_user_by_patient_id(patient_id_4a) is None, "FAIL: user 4a still exists after cleanup."
    print("PASS: user 4a cleaned up successfully.")

    print("\nAll same-name ambiguity test cases passed.\n")

    # ---- update() tests ----

    # Setup: one user with two relatives sharing first_name "Ravi" — the classic
    # ambiguity case update() was originally built and verified against.
    patient_id_u1 = generate_patient_id("ME")
    user_u1 = User(patient_id_u1, "08-08-1988", "test symptoms for update user",
                    "Sunita Rao", "sunitarao1@test.com", "+91 9000000030")
    insert_user(user_u1)
    relative_u1a = Relatives("Ravi Kumar", "ravikumar1@test.com", "+91 9000000031", patient_id_u1)
    relative_u1b = Relatives("Ravi Sharma", "ravisharma1@test.com", "+91 9000000032", patient_id_u1)
    insert_relative(relative_u1a)
    insert_relative(relative_u1b)

    print(f"\n--- Setup complete for update() tests: {patient_id_u1} with two relatives "
          f"sharing first_name='Ravi' (Kumar and Sharma) ---\n")

    # Case 1: unambiguous update — change the user's own phone_number directly by patient_id.
    status, data = update("users", "patient_id", patient_id_u1, {"phone_number": "+91 9000000099"})
    print(f"\nUnambiguous user update status: {status}")
    assert status == "success", "Expected the unambiguous user update to succeed."
    updated_user = search_user_by_patient_id(patient_id_u1)
    assert updated_user is not None and updated_user["phone_number"] == "+91 9000000099", \
        "FAIL: user's phone_number wasn't actually updated."
    print("PASS: unambiguous update on a user succeeded and is reflected in the DB.")

    # Case 2: ambiguous update — two relatives share first_name "Ravi", no row_identifier given.
    intended_changes = {"email": "ravisharmaupdated1@test.com"}
    status, data = update("relatives", "first_name", "Ravi", intended_changes)
    print(f"Ambiguous relative update, first call status: {status}")
    assert status == "ambiguous", "Expected an ambiguous match for two relatives named Ravi."
    assert isinstance(data, list) and len(data) == 2, "Expected exactly two candidates."

    # Pick out Sharma's relative_row_id specifically, to prove resolution updates the
    # CORRECT one, not just whichever candidate happens to come first.
    sharma_row_id = None
    for pair in data:
        if pair["Relatives"]["last_name"] == "Sharma":
            sharma_row_id = str(pair["Relatives"]["relative_row_id"])
    assert sharma_row_id is not None, "FAIL: couldn't find Sharma among the ambiguous candidates."

    # Case 3: re-call with the resolved row_identifier — should now succeed.
    status, data = update("relatives", "first_name", "Ravi", intended_changes, row_identifier=sharma_row_id)
    print(f"Ambiguous relative update, second call status: {status}")
    assert status == "success", "Expected the resolved update to succeed."

    # Verify: Sharma's email changed, Kumar's did not.
    sharma_check = search_relatives_by_email("ravisharmaupdated1@test.com")
    kumar_check = search_relatives_by_email("ravikumar1@test.com")
    assert sharma_check is not None, "FAIL: Sharma's email wasn't actually updated."
    assert kumar_check is not None, "FAIL: Kumar was wrongly modified or removed."
    print("PASS: correctly updated Ravi Sharma's email; Ravi Kumar untouched.")

    print("\nAll update() test cases passed.\n")

    # ---- Cleanup: remove everything created for the update() tests ----
    delete("relatives", "email", "ravikumar1@test.com")
    delete("relatives", "email", "ravisharmaupdated1@test.com")
    delete("users", "patient_id", patient_id_u1)
    print("Cleanup complete for update() tests.\n")

    # ---- view() tests ----
    patient_id_v1 = generate_patient_id("CA")
    user_v1 = User(patient_id_v1, "06-06-1990", "test symptoms for view user one",
                    "Meera Rao", "meerarao1@test.com", "+91 9000000020")
    insert_user(user_v1)
    relative_v1a = Relatives("Kiran Rao", "kiranrao1@test.com", "+91 9000000021", patient_id_v1)
    relative_v1b = Relatives("Divya Rao", "divyarao1@test.com", "+91 9000000022", patient_id_v1)
    insert_relative(relative_v1a)
    insert_relative(relative_v1b)

    patient_id_v2 = generate_patient_id("TB")
    user_v2 = User(patient_id_v2, "07-07-1991", "test symptoms for view user two",
                    "Meera Rao", "meerarao2@test.com", "+91 9000000023")
    insert_user(user_v2)

    print(f"\n--- Setup complete for view() tests: {patient_id_v1} (2 relatives), "
          f"{patient_id_v2} (0 relatives), both named 'Meera Rao' ---\n")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        ret = view("users", "patient_id", patient_id_v1)
    output = buffer.getvalue()
    assert ret is None, "FAIL: view() should always return None."
    assert "Meera Rao" in output, "FAIL: user_v1's name missing from output."
    assert "Kiran Rao" in output, "FAIL: relative_v1a missing from output."
    assert "Divya Rao" in output, "FAIL: relative_v1b missing from output."
    assert "No Relatives found" not in output, "FAIL: user_v1 wrongly shown as having no relatives."
    print("PASS: view() on a user with 2 relatives shows the user and both relatives.")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        view("users", "patient_id", patient_id_v2)
    output = buffer.getvalue()
    assert "No Relatives found for Meera Rao." in output, "FAIL: zero-relatives message missing or malformed."
    print("PASS: view() on a user with 0 relatives shows the correct 'No Relatives found' message.")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        view("users", "first_name", "Meera")
    output = buffer.getvalue()
    assert output.count("Meera Rao") >= 2, "FAIL: expected both Meera Raos to be shown, not just one."
    assert "Kiran Rao" in output and "Divya Rao" in output, "FAIL: user_v1's relatives missing."
    assert "No Relatives found for Meera Rao." in output, "FAIL: user_v2's zero-relatives case missing."
    print("PASS: view() on an ambiguous name shows every matching user, each with correct relatives.")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        ret = view("relatives", "email", "kiranrao1@test.com")
    output = buffer.getvalue()
    assert ret is None
    assert "Kiran Rao" in output, "FAIL: relative_v1a missing."
    assert "Meera Rao" in output, "FAIL: attached user missing."
    print("PASS: view() on a relative (by email) shows the relative and their attached user, no crash.")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        view("relatives", "last_name", "Rao")
    output = buffer.getvalue()
    assert "Kiran Rao" in output and "Divya Rao" in output, "FAIL: expected both relatives named Rao."
    print("PASS: view() on an ambiguous relative name shows every matching relative correctly.")

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        ret = view("users", "email", "doesnotexist@test.com")
    output = buffer.getvalue()
    assert ret is None, "FAIL: view() should return None even on not-found."
    assert "couldn't be located" in output, "FAIL: expected the not-found message."
    print("PASS: view() on a nonexistent value prints the not-found message and returns None.")

    print("\nAll view() test cases passed.\n")

    delete("relatives", "email", "kiranrao1@test.com")
    delete("relatives", "email", "divyarao1@test.com")
    delete("users", "patient_id", patient_id_v1)
    delete("users", "patient_id", patient_id_v2)
    print("Cleanup complete for view() tests.\n")

    close_connection()


if __name__ == "__main__":
    test_case()
