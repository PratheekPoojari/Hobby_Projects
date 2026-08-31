import heapq
import database


raw_ids:list[str] = database.get_all_patient_ids()
id_number:list[int] = sorted(int(id[2:]) for id in raw_ids)
free_heap:list[int] = []


def get_counter(user_id:list[int]) -> int:
    try:
        return user_id[len(user_id) - 1] + 1
    except IndexError:
        return 0

counter = get_counter(id_number)


def allocate_heap(user_id:list[int], heap_list:list[int]) -> list:
    expected = 0
    for value in user_id:
        while expected < value:
            heapq.heappush(heap_list, expected)
            expected += 1
        expected = value + 1
    return heap_list

formatted_heap = allocate_heap(id_number, free_heap)


def generate_patient_id(code:str) -> str:
    #if formatted_heap != []:
    # does the same as above as empty containers in python are 'falsy'
    if formatted_heap:
        smallest_free_id:str = str(heapq.heappop(formatted_heap))
    else:
        global counter
        smallest_free_id:str = str(counter)
        counter += 1

    # str.zfill(n) -> makes it so that the string is padded with 0s until it's length reaches 4
    smallest_free_id = str(smallest_free_id).zfill(4)

    # My own way of doing what a string method called "zfill" does.
    #if len(str(smallest_free_id)) != 4:
        # actual:str = str(smallest_free_id)            
        # appendable:int = 4 - len(actual)
        # actual = ("0" * appendable) + actual
        # smallest_free_id = actual

    patient_id:str = code + smallest_free_id
    return patient_id


def free_patient_id(patient_id:str) -> None:
    patient_id_int:int = int(patient_id[2:])
    heapq.heappush(formatted_heap, patient_id_int)


# Testing
def main():
    # set of user id's accessed from the databases.py, no duplicate values.
    set_of_id:set = {0, 1, 13, 4, 2, 9, 8}
    print(f"set of id's: {set_of_id}")
    # sorted list of user id's. 
    sorted_id_list:list = sorted(set_of_id)
    print(f"sorted id list: {sorted_id_list}")
    # returns 1 + max value in the sorted list, to be used to set the next user id.
    count = get_counter(sorted_id_list)
    print(f"counter: {count}")
    # list of freed id's in between by various operations.
    free_id_list:list = [] # Is empty by default, refreshes value every run. 
    print(f"heap: {free_id_list}")
    # checks the user_id list and stores the unused(free) values in between the assigned values.
    refined_heap = allocate_heap(sorted_id_list, free_id_list)
    print(f"heap after allocation: {refined_heap}")


if __name__ == "__main__":
    main()
