import heapq


def get_counter(user_id:list) -> int:
    try:
        return user_id[len(user_id) - 1] + 1
    except IndexError:
        raise IndexError(f"There is no data in the list: {user_id}")


def allocate_heap(user_id:list, heap_list:list) -> list:
    expected = 0
    for value in user_id:
        while expected < value:
            heapq.heappush(heap_list, expected)
            expected += 1
        expected = value + 1
    return heap_list


def main():
    set_of_id:set = {0, 1, 2, 4, 8, 9, 13}
    print(f"set of id's: {set_of_id}")
    sorted_id_list:list = sorted(set_of_id)
    print(f"sorted id list: {sorted_id_list}")
    counter = get_counter(sorted_id_list)
    print(f"counter: {counter}")
    free_id_list:list = [] # Is empty by default, refreshes value every run. 
    print(f"heap: {free_id_list}")
    formatted_heap = allocate_heap(sorted_id_list, free_id_list)
    #print(sorted(set(formatted_heap)))
    print(f"heap after allocation: {formatted_heap}")


if __name__ == "__main__":
    main()
