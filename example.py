from typing import Annotated, Optional, Literal
import magritte


def example_func(
        integers: Annotated[set[int], "A list of integers to sum or find the maximum of"],
        offset: Optional[int],
        operation: Annotated[Literal['add', 'max'], "The operation to use"] = 'add',
        double=False
) -> int:
    """Just an example function"""

    if offset is None:
        offset = 0
    if operation == 'add':
        v = offset + sum(integers)
    else:
        v = offset + max(integers)
    print(f"Example func computed result {2 * v if double else v}")



MyCustomType = tuple[int, Literal["good", "bad"]]

def another_example_func(
        list_of_tuples: list[MyCustomType],
        should_log=True
) -> int:
    """Just another example function"""

    if should_log:
        print(f"Other example func received: {repr(list_of_tuples)}")
    else:
        print("...")


if __name__ == '__main__':
    # Call e.g. as 'python example.py -i 1 2 3 --operation add --offset None --double'
    magritte.single_dispatch(example_func)

    # # or do this, and call as 'python example.py -l 1 good 2 bad 3 good'
    # magritte.single_dispatch(another_example_func)
    # # note: python example.py -l 1 good 2 oops_wrong_literal 3 bad shows you the issue with the current design,
    # # as the custom parser fails on the second tuple, concludes it must be done and leaves the rest. oops!
