import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import patient_id  # accessed via patient_id.<name> throughout, so module state stays visible

def snapshot_state() -> dict:
    return {"counter": patient_id.counter, "heap": list(patient_id.formatted_heap)}

def restore_state(snapshot: dict) -> None:
    patient_id.counter = snapshot["counter"]
    patient_id.formatted_heap = snapshot["heap"]

# ---------- build_free_heap() — pure function, no global state involved ----------
def test_build_free_heap_empty_input():
    assert patient_id.build_free_heap([]) == []
    print("test_build_free_heap_empty_input: PASSED")

def test_build_free_heap_no_gaps():
    assert sorted(patient_id.build_free_heap([0, 1, 2, 3])) == []
    print("test_build_free_heap_no_gaps: PASSED")

def test_build_free_heap_with_gaps():
    # heapify doesn't guarantee strict total ordering internally, so we sort the output for asserting the contents
    assert sorted(patient_id.build_free_heap([0, 2, 5])) == [1, 3, 4]
    print("test_build_free_heap_with_gaps: PASSED")

def test_build_free_heap_starting_above_zero():
    # everything below the lowest existing id is treated as free
    assert sorted(patient_id.build_free_heap([3, 4, 5])) == [0, 1, 2]
    print("test_build_free_heap_starting_above_zero: PASSED")

# ---------- generate_patient_id() / free_patient_id() — mutate module-level state, snapshot+restore around each ----------
def test_generate_patient_id_zero_padding():
    snapshot = snapshot_state()
    patient_id.formatted_heap = []
    patient_id.counter = 7
    result = patient_id.generate_patient_id("TT")
    assert result == "TT0007"
    assert patient_id.counter == 8
    restore_state(snapshot)
    print("test_generate_patient_id_zero_padding: PASSED")

def test_generate_patient_id_no_padding_needed():
    snapshot = snapshot_state()
    patient_id.formatted_heap = []
    patient_id.counter = 9999
    result = patient_id.generate_patient_id("TT")
    assert result == "TT9999"
    restore_state(snapshot)
    print("test_generate_patient_id_no_padding_needed: PASSED")

def test_generate_patient_id_prefers_heap_over_counter():
    snapshot = snapshot_state()
    patient_id.formatted_heap = [3, 5]
    patient_id.counter = 100
    result = patient_id.generate_patient_id("TT")
    assert result == "TT0003"
    assert patient_id.counter == 100
    assert patient_id.formatted_heap == [5]
    restore_state(snapshot)
    print("test_generate_patient_id_prefers_heap_over_counter: PASSED")

def test_generate_patient_id_sequential_without_frees():
    snapshot = snapshot_state()
    patient_id.formatted_heap = []
    patient_id.counter = 50
    first = patient_id.generate_patient_id("TT")
    second = patient_id.generate_patient_id("TT")
    assert first == "TT0050"
    assert second == "TT0051"
    restore_state(snapshot)
    print("test_generate_patient_id_sequential_without_frees: PASSED")

def test_free_and_regenerate_reuses_id():
    snapshot = snapshot_state()
    patient_id.formatted_heap = []
    patient_id.counter = 200
    generated = patient_id.generate_patient_id("TT")
    patient_id.free_patient_id(generated)
    regenerated = patient_id.generate_patient_id("TT")
    assert regenerated == generated == "TT0200"
    restore_state(snapshot)
    print("test_free_and_regenerate_reuses_id: PASSED")

def test_heap_returns_smallest_regardless_of_free_order():
    snapshot = snapshot_state()
    patient_id.formatted_heap = []
    patient_id.counter = 300
    id_a = patient_id.generate_patient_id("TT")
    id_b = patient_id.generate_patient_id("TT")
    id_c = patient_id.generate_patient_id("TT")
    
    patient_id.free_patient_id(id_c)
    patient_id.free_patient_id(id_a)
    patient_id.free_patient_id(id_b)
    next_id = patient_id.generate_patient_id("TT")
    assert next_id == id_a
    restore_state(snapshot)
    print("test_heap_returns_smallest_regardless_of_free_order: PASSED")

def test_free_patient_id_ignores_code_prefix():
    snapshot = snapshot_state()
    patient_id.formatted_heap = []
    patient_id.free_patient_id("ZZ0042")
    assert patient_id.formatted_heap == [42]
    restore_state(snapshot)
    print("test_free_patient_id_ignores_code_prefix: PASSED")

def run_all():
    test_build_free_heap_empty_input()
    test_build_free_heap_no_gaps()
    test_build_free_heap_with_gaps()
    test_build_free_heap_starting_above_zero()
    test_generate_patient_id_zero_padding()
    test_generate_patient_id_no_padding_needed()
    test_generate_patient_id_prefers_heap_over_counter()
    test_generate_patient_id_sequential_without_frees()
    test_free_and_regenerate_reuses_id()
    test_heap_returns_smallest_regardless_of_free_order()
    test_free_patient_id_ignores_code_prefix()
    print("\nAll patient_id.py tests passed.")

if __name__ == "__main__":
    run_all()
