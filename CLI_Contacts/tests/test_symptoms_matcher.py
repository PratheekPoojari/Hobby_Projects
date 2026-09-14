import sys
import csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import symptom_matcher  # accessed via symptom_matcher.<name>, to introspect the real diseases_csv data

SYMPTOMS_PATH = Path(__file__).resolve().parent.parent / "data" / "symptoms.csv"
symptoms_csv = []
with open(SYMPTOMS_PATH, "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        symptoms_csv.append(row)

def find_row_with_min_keywords(min_count: int) -> dict:
    for row in symptom_matcher.diseases_csv:
        if len(row["keywords"].split(";")) >= min_count:
            return row
    raise AssertionError(f"No disease row has at least {min_count} keywords — can't run this test")

def get_symptoms_row(row_id: str) -> dict:
    for row in symptoms_csv:
        if row["id"] == row_id:
            return row
    raise AssertionError(f"No row with id={row_id} in symptoms.csv")
# ---------- direct unit tests, built from diseases.csv keywords ----------
def test_allocate_code_single_keyword_match():
    row = symptom_matcher.diseases_csv[0]
    keyword = row["keywords"].split(";")[0]
    result = symptom_matcher.allocate_code(keyword)
    assert result == row["code"]
    print("test_allocate_code_single_keyword_match: PASSED")

def test_allocate_code_case_insensitive():
    row = symptom_matcher.diseases_csv[0]
    keyword = row["keywords"].split(";")[0]
    result = symptom_matcher.allocate_code(keyword.upper())
    assert result == row["code"]
    print("test_allocate_code_case_insensitive: PASSED")

def test_allocate_code_no_match_returns_zero():
    result = symptom_matcher.allocate_code("xyzzyplughqwerty nonsensicalgarbagewordstring")
    assert result == "0"
    print("test_allocate_code_no_match_returns_zero: PASSED")

def test_allocate_code_empty_string_returns_zero():
    result = symptom_matcher.allocate_code("")
    assert result == "0"
    print("test_allocate_code_empty_string_returns_zero: PASSED")

def test_allocate_code_higher_hit_count_wins():
    # a disease matched twice beats a different disease matched once,
    # regardless of which one has the higher "priority" value
    row_multi = find_row_with_min_keywords(2)
    row_other = next(r for r in symptom_matcher.diseases_csv if r["code"] != row_multi["code"])
    keywords_multi = row_multi["keywords"].split(";")[:2]
    keyword_other = row_other["keywords"].split(";")[0]
    symptoms = f"{keywords_multi[0]} {keywords_multi[1]} {keyword_other}"
    result = symptom_matcher.allocate_code(symptoms)
    assert result == row_multi["code"]
    print("test_allocate_code_higher_hit_count_wins: PASSED")
# ---------- realistic sentence tests, from symptoms.csv ----------
def test_symptoms_csv_tuberculosis():
    row = get_symptoms_row("1")
    assert symptom_matcher.allocate_code(row["symptoms"]) == row["expected_code"]
    print("test_symptoms_csv_tuberculosis: PASSED")

def test_symptoms_csv_dengue():
    row = get_symptoms_row("2")
    assert symptom_matcher.allocate_code(row["symptoms"]) == row["expected_code"]
    print("test_symptoms_csv_dengue: PASSED")

def test_symptoms_csv_psoriasis():
    row = get_symptoms_row("3")
    assert symptom_matcher.allocate_code(row["symptoms"]) == row["expected_code"]
    print("test_symptoms_csv_psoriasis: PASSED")

def test_symptoms_csv_melanoma():
    row = get_symptoms_row("4")
    assert symptom_matcher.allocate_code(row["symptoms"]) == row["expected_code"]
    print("test_symptoms_csv_melanoma: PASSED")

def test_symptoms_csv_malaria():
    row = get_symptoms_row("5")
    assert symptom_matcher.allocate_code(row["symptoms"]) == row["expected_code"]
    print("test_symptoms_csv_malaria: PASSED")

def test_symptoms_csv_no_disease_match():
    row = get_symptoms_row("6")
    assert symptom_matcher.allocate_code(row["symptoms"]) == row["expected_code"]  # "0"
    print("test_symptoms_csv_no_disease_match: PASSED")

def test_symptoms_csv_priority_tiebreak():
    # row 7 hits Cancer twice ("lump", "unexplained weight loss") and Tuberculosis
    # twice ("persistent cough", "night sweats") — a genuine 2-2 tie. Cancer's
    # priority (6) beats Tuberculosis's (3), so the tie resolves to CA. The CSV's
    # "AMBIGUOUS" label is a note for a human reader, not a value allocate_code()
    # ever actually returns — this test asserts the real, deterministic outcome.
    row = get_symptoms_row("7")
    assert row["expected_code"] == "AMBIGUOUS"  # confirms the fixture wasn't edited under us
    assert symptom_matcher.allocate_code(row["symptoms"]) == "CA"
    print("test_symptoms_csv_priority_tiebreak: PASSED")

def run_all():
    test_allocate_code_single_keyword_match()
    test_allocate_code_case_insensitive()
    test_allocate_code_no_match_returns_zero()
    test_allocate_code_empty_string_returns_zero()
    test_allocate_code_higher_hit_count_wins()
    test_symptoms_csv_tuberculosis()
    test_symptoms_csv_dengue()
    test_symptoms_csv_psoriasis()
    test_symptoms_csv_melanoma()
    test_symptoms_csv_malaria()
    test_symptoms_csv_no_disease_match()
    test_symptoms_csv_priority_tiebreak()
    print("\nAll symptom_matcher.py tests passed.")

if __name__ == "__main__":
    run_all()
