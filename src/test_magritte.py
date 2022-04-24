from typing import Tuple, Annotated, List, Optional, Literal
from parsers import make_parser, ArgumentParser, guess_parser

# def infer_parser_arg_from_type(argname: str, argtype: Type[T], argdefault: T) -> SingleArgParser[T]:
#     helpstr = f'Help for {argname}: {repr(argtype)}'
#     if argtype == inspect._empty and argdefault == inspect._empty:
#         logging.info(f"No type or default for {argname}")
#         return parser.add_argument(argname, help=helpstr)
#     if argtype != inspect._empty:
#         basetype, typeargs = typing.get_origin(argtype), typing.get_args(argtype)
#         if basetype in type_to_arg_parser:
#             logging.info(f"Inferring parsing for {argname} based on argtype {argtype}")
#             return type_to_arg_parser[basetype](typeargs, parser, argname, argdefault)
#         else:
#             logging.info(f"Inferring parsing for {argname} based on default arg {argdefault}")
#             return parser.add_argument(argname, help=helpstr)


TwoInts = Tuple[int, int]


def test_int_list_parser():
    parser = ArgumentParser(
        {"int_list": guess_parser(List[int]),
         "some_int": guess_parser(int),
         "two_ints": guess_parser(TwoInts),
         "int_pair_list": guess_parser(List[TwoInts]),
         "some_flag": guess_parser(bool)
         }
    )

    argv = ['--some_int', '2', '--int_list', '3', '4', '5',
            '--two_ints', '4', '5', '--int_pair_list', '9', '5', '0', '6', '--not-some_flag']
    print(parser._parse_argv(argv))


MyAnnotatedListType = Annotated[List[int], "some integers"]


def example_func(
        integers: MyAnnotatedListType,
        offset: Optional[int],
        operation: Literal['add', 'max'] = 'add',
        double=False
) -> int:
    if offset is None:
        offset = 0
    if operation == 'add':
        v = offset + sum(integers)
    else:
        v = offset + max(integers)
    return 2 * v if double else v


def test_example_func():
    parser = make_parser(example_func)
    print(parser._parse_argv(['-i', '1', '2', '4', '--operation', 'max', '--offset', 'None']))


test_int_list_parser()
test_example_func()
