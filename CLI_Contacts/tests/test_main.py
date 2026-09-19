"""
Test suite for the CLI driver, using robust mocking to simulate STDIN/STDOUT and validate UI routing logic.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import main

# Test UI Helpers

def test_draw_menu(capsys):
    options = ["Option A", "Option B", "Exit"]
    result = main.draw_menu("TEST MENU", options)
    assert result == {1: "Option A", 2: "Option B", 3: "Exit"}
    captured = capsys.readouterr().out
    assert "TEST MENU" in captured
    assert "[ 1 ]  Option A" in captured


@patch("builtins.input", side_effect=["invalid", "0", "4", "2"])
def test_get_valid_choice(mock_input, capsys):
    menu_map = {1: "Opt 1", 2: "Opt 2", 3: "Opt 3"}
    choice = main.get_valid_choice(menu_map)
    assert choice == 2


# Test Auth Flows

@patch("builtins.print")
@patch("main.link_patient_id")
@patch("main.add_user", return_value="CA1234")
def test_profile_completion_success(mock_add_user, mock_link, mock_print):
    patient_id = main.profile_completion("test_user")
    assert patient_id == "CA1234"
    mock_add_user.assert_called_once()
    mock_link.assert_called_once_with("test_user", "CA1234")


@patch("builtins.print")
@patch("main.add_user", return_value=None)
def test_profile_completion_failure(mock_add_user, mock_print):
    patient_id = main.profile_completion("test_user")
    assert patient_id is None


@patch("main.sign_up", return_value=("password_mismatch", None))
def test_handle_signup_password_mismatch(mock_signup, capsys):
    main.handle_signup()
    assert "Passwords do not match" in capsys.readouterr().out


@patch("main.sign_up", return_value=("username_taken", None))
def test_handle_signup_username_taken(mock_signup, capsys):
    main.handle_signup()
    assert "already taken" in capsys.readouterr().out


@patch("main.user_menu")
@patch("main.profile_completion", return_value="CA1234")
@patch("main.sign_up", return_value=("success", {"username": "test", "role": "user", "patient_id": None}))
def test_handle_signup_success(mock_signup, mock_profile, mock_user_menu, capsys):
    main.handle_signup()
    mock_profile.assert_called_once_with("test")
    mock_user_menu.assert_called_once_with({"username": "test", "role": "user", "patient_id": "CA1234"})


@patch("main.login", return_value=("invalid_credentials", None))
def test_handle_login_invalid(mock_login, capsys):
    main.handle_login()
    assert "Invalid credentials" in capsys.readouterr().out


@patch("main.user_menu")
@patch("main.login", return_value=("success", {"username": "test", "role": "user", "patient_id": "CA1234"}))
def test_handle_login_user(mock_login, mock_user_menu):
    main.handle_login()
    mock_user_menu.assert_called_once_with({"username": "test", "role": "user", "patient_id": "CA1234"})


@patch("main.admin_menu")
@patch("main.login", return_value=("success", {"username": "admin", "role": "admin", "patient_id": None}))
def test_handle_login_admin(mock_login, mock_admin_menu):
    main.handle_login()
    mock_admin_menu.assert_called_once_with({"username": "admin", "role": "admin", "patient_id": None})


# Test User Handlers

@patch("main.view")
def test_handle_user_view(mock_view):
    main.handle_user_view({"patient_id": "CA1234"})
    mock_view.assert_called_once_with("users", "patient_id", "CA1234")


@patch("main.update", return_value=("success", None))
@patch("builtins.input", return_value="New Name")
@patch("main.get_valid_choice", return_value=1) # "First Name"
@patch("main.draw_menu", return_value={1: "First Name", 2: "Back"})
def test_handle_user_update(mock_draw, mock_choice, mock_input, mock_update, capsys):
    main.handle_user_update({"patient_id": "CA1234"})
    mock_update.assert_called_once_with("users", "patient_id", "CA1234", {"first_name": "New Name"})


@patch("main.free_patient_id")
@patch("main.delete", return_value=("success", None))
@patch("builtins.input", return_value="yes")
def test_handle_user_delete_success(mock_input, mock_delete, mock_free, capsys):
    result = main.handle_user_delete({"patient_id": "CA1234"})
    assert result is True
    mock_delete.assert_called_once_with("users", "patient_id", "CA1234")
    mock_free.assert_called_once_with("CA1234")


@patch("builtins.input", side_effect=["invalid", "2"])
@patch("main.get_relatives_by_patient_id", return_value=[{"relative_row_id": 1, "first_name": "A", "last_name": "B", "email": "a@b.com"}, {"relative_row_id": 2, "first_name": "C", "last_name": "D", "email": "c@d.com"}])
def test_pick_own_relative(mock_get_rel, mock_input, capsys):
    result = main._pick_own_relative({"patient_id": "CA1234"})
    assert result == {"relative_row_id": 2, "first_name": "C", "last_name": "D", "email": "c@d.com"}


@patch("main.add_relative")
@patch("main.get_valid_choice", return_value=1) # Proceed
@patch("main.draw_menu", return_value={1: "Proceed", 2: "Back"})
def test_handle_add_relative(mock_draw, mock_choice, mock_add, capsys):
    main.handle_add_relative({"patient_id": "CA1234"})
    mock_add.assert_called_once()


@patch("main.update", return_value=("success", None))
@patch("builtins.input", return_value="NewEmail@test.com")
@patch("main.get_valid_choice", return_value=4) # Email
@patch("main.draw_menu", return_value={4: "Email"})
@patch("main._pick_own_relative", return_value={"email": "old@test.com"})
def test_handle_update_relative(mock_pick, mock_draw, mock_choice, mock_input, mock_update):
    main.handle_update_relative({"patient_id": "CA1234"})
    mock_update.assert_called_once_with("relatives", "email", "old@test.com", {"email": "NewEmail@test.com"})


@patch("main.delete", return_value=("success", None))
@patch("builtins.input", return_value="yes")
@patch("main._pick_own_relative", return_value={"first_name": "A", "last_name": "B", "email": "a@test.com"})
def test_handle_delete_relative(mock_pick, mock_input, mock_delete):
    main.handle_delete_relative({"patient_id": "CA1234"})
    mock_delete.assert_called_once_with("relatives", "email", "a@test.com")


@patch("main.export_patient_txt", return_value="/path/to/file.txt")
@patch("main.prompt_export_path", return_value="/path")
@patch("main.get_valid_choice", return_value=1) # TXT
@patch("main.draw_menu", return_value={1: "TXT"})
@patch("main.build_patient_record", return_value=("success", {"user": {"patient_id": "CA1234"}}))
def test_handle_user_export_txt(mock_build, mock_draw, mock_choice, mock_path, mock_export, capsys):
    main.handle_user_export({"patient_id": "CA1234"})
    mock_export.assert_called_once()


# Test Admin Handlers

@patch("main.view")
@patch("main._prompt_table", return_value="users")
@patch("main._prompt_search_params", return_value=("patient_id", "CA1234"))
def test_handle_admin_view(mock_prompt_search, mock_prompt_table, mock_view):
    main.handle_admin_view()
    mock_view.assert_called_once_with("users", "patient_id", "CA1234")


@patch("main.update", return_value=("success", None))
@patch("builtins.input", side_effect=["Bob"])
@patch("main._prompt_table", return_value="users")
@patch("main._prompt_search_params", return_value=("patient_id", "CA1234"))
@patch("main.get_valid_choice", return_value=1) # First Name
@patch("main.draw_menu", return_value={1: "First Name"})
def test_handle_admin_update(mock_draw, mock_choice, mock_prompt_search, mock_prompt_table, mock_input, mock_update, capsys):
    main.handle_admin_update()
    mock_update.assert_called_once_with("users", "patient_id", "CA1234", {"first_name": "Bob"})


@patch("main.delete", return_value=("success", {"deleted": {"patient_id": "CA1234"}}))
@patch("builtins.input", side_effect=["yes"])
@patch("main._prompt_table", return_value="users")
@patch("main._prompt_search_params", return_value=("patient_id", "CA1234"))
@patch("main.free_patient_id")
def test_handle_admin_delete_user(mock_free, mock_prompt_search, mock_prompt_table, mock_input, mock_delete, capsys):
    main.handle_admin_delete()
    mock_delete.assert_called_once_with("users", "patient_id", "CA1234")
    mock_free.assert_called_once_with("CA1234")


@patch("main.add_relative")
@patch("main.get_valid_choice", return_value=1)
@patch("main.draw_menu", return_value={1: "Proceed"})
def test_handle_admin_add_relative(mock_draw, mock_choice, mock_add):
    main.handle_admin_add_relative()
    mock_add.assert_called_once()


@patch("main.export_admin_csv")
@patch("main.prompt_export_path", return_value=None)
@patch("main.get_valid_choice", return_value=2) # CSV
@patch("main.draw_menu", return_value={2: "CSV"})
@patch("builtins.input", return_value="")
@patch("main.build_admin_records", return_value=[{}])
@patch("main.get_all_users", return_value=[{"patient_id": "CA1234", "first_name": "A", "last_name": "B", "email": "a@b.com"}])
def test_handle_admin_export_all(mock_get_all, mock_build, mock_input, mock_draw, mock_choice, mock_path, mock_export):
    main.handle_admin_export()
    mock_export.assert_called_once()


# Menu Loop Exits

@patch("main.get_valid_choice", return_value=8) # Logout
@patch("main.draw_menu", return_value={8: "Logout"})
def test_user_menu_exit(mock_draw, mock_choice):
    main.user_menu({"patient_id": "CA1234", "username": "test"})


@patch("main.get_valid_choice", return_value=6) # Logout
@patch("main.draw_menu", return_value={6: "Logout"})
def test_admin_menu_exit(mock_draw, mock_choice):
    main.admin_menu({"patient_id": None, "username": "admin"})


@patch("main.get_valid_choice", return_value=3) # Exit
@patch("main.draw_menu", return_value={3: "Exit"})
def test_main_menu_exit(mock_draw, mock_choice, capsys):
    with pytest.raises(SystemExit) as e:
        main.main_menu()
    assert e.type == SystemExit
    assert e.value.code == 0
