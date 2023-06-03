import sys
from typing import Callable
from .parser_inference import make_parser, BoolParser

def single_dispatch(func: Callable):
    help_parser = BoolParser(default_value=False)
    parser = make_parser(func, help=help_parser)
    try:
        parsed_args = parser._parse_argv(sys.argv[1:])
        if parsed_args["help"]:
            print(parser.help_message)
            sys.exit(0)
        parser._validate_args(parsed_args)
        if "help" in parsed_args:
            del parsed_args["help"]

    except (ValueError, AssertionError) as e:
        print(f"Error parsing args: {e}")
        print(parser.help_message)
        sys.exit(1)

    else:
        func(**parsed_args)
