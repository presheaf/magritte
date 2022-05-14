import sys
from parsers import BoolParser
from typing import Callable
from parsers import make_parser


def single_dispatch(func: Callable):
    help_parser = BoolParser(default_value=False)
    parser = make_parser(func, help=help_parser)
    try:
        args = parser._parse_argv(sys.argv[1:])
        if args["help"]:
            print(parser.help_message)
            sys.exit(0)
        parser._validate_args(args)

    except (ValueError, AssertionError) as e:
        print(f"Error parsing args: {e}")
        print(parser.help_message)
        sys.exit(1)

    else:
        print(f"Calling {func.__name__} with {args}")
        pass
