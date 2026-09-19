import heapq
import database

def build_free_heap(existing_ids: list[int]) -> list[int]:
    """Finds missing IDs in O(N) time and heapifies them in O(N)."""
    if not existing_ids:
        return []
    
    max_id = existing_ids[-1]
    # Set difference to find all gaps
    missing = set(range(max_id + 1)) - set(existing_ids)
    
    free_heap = list(missing)
    heapq.heapify(free_heap)
    return free_heap

# Initialization happens once on module load
raw_ids: list[str] = database.get_all_patient_ids()
# Convert the numeric parts to sorted integers
id_number: list[int] = sorted(int(pid[2:]) for pid in raw_ids)

# The highest ID allocated plus 1 (the frontier for new IDs)
counter: int = id_number[-1] + 1 if id_number else 0

# Min-heap of previously freed IDs (available for reuse)
formatted_heap: list[int] = build_free_heap(id_number)

def generate_patient_id(code: str) -> str:
    global counter
    
    if formatted_heap:
        smallest_free_id: int = heapq.heappop(formatted_heap)
    else:
        smallest_free_id: int = counter
        counter += 1
        
    return f"{code}{str(smallest_free_id).zfill(4)}"

def free_patient_id(patient_id: str) -> None:
    patient_id_int: int = int(patient_id[2:])
    heapq.heappush(formatted_heap, patient_id_int)

