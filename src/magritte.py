import string
import inspect
# from argparse import Namespace
from typing import List, Generic, Optional, TypeVar, Dict, Tuple, Callable, Type
from collections import defaultdict
T = TypeVar('T')
from pprint import pprint
UNINITIALIZED = object()


class SingleArgParser(Generic[T]):
    # TODO: This metaclass could automagically register stuff with margritte
    #       Not sure there's a real point to having the type parameter here...

    def __init__(self, default_value=inspect._empty):
        self.default_value = default_value

    def has_default_value(self):
        return self.default_value != inspect._empty

    def argname_representations(self, argname) -> List[str]:
        """Return (and store) a list of all possible ways this argname can be written."""
        # TODO: Might want to replace _ by - here?
        argname = argname.lower()
        assert argname and argname[0] in string.ascii_lowercase, f"Illegal argname: {repr(argname)}"

        c = argname[0]
        return [f'-{c}', f'--{argname}', f'-{argname}']

    def parse_single_arg(self, arg_format: str, args: List[str], parser) -> Tuple[int, T]:
        raise NotImplementedError

    def __call__(self, arg_format: str, args: List[str], parser) -> Tuple[int, T]:
        return self.parse_single_arg(arg_format, args, parser)


class ArgumentParser:
    def __init__(self, parsers: Dict[str, SingleArgParser], arg_annotation: Dict[str, Tuple[str, Type]], func: Callable):
        self.arg_parsers = parsers

        # Dict mapping some way to pass an arg to the corresponding parser
        # (e.g. '-argname', '-a', '--argname' -> the parser for the arg 'argname')
        self.arg_formats: Dict[str, str] = {}
        # Compute the indicating sets somehow
        _indicators = {argname: parser.argname_representations(argname)
                       for argname, parser in self.arg_parsers.items()}

        # If an argument could indicate other things,
        for argname in self.arg_parsers:
            indicates_self = set(_indicators[argname])
            for other_argname in self.arg_parsers:
                if other_argname == argname:
                    continue
                indicates_self.difference_update(_indicators[other_argname])

            assert indicates_self, f"Error (should never happen): no way to pass {argname}"
            for arg_format in indicates_self:
                self.arg_formats[arg_format] = argname

        _arg_formats_inverse = defaultdict(list)
        for fmt, argname in self.arg_formats.items():
            _arg_formats_inverse[argname].append(fmt)

        help_indent = ' ' * 4
        # TODO: Add "example call cmd" to help_message (see any manpage)
        self.help_message = f'{func.__name__}'
        if func.__doc__:
            self.help_message += ':\n' + help_indent + func.__doc__
        arg_help = '\nArguments:'

        # TODO: clearly the constructor should just be parsing everything here
        # or more pragmatically it should take in other stuff, and there should be an ArgumentParser.make_parser thing
        for argname, (help_str, argtype) in arg_annotation.items():
            arg_format_description = ', '.join(sorted(_arg_formats_inverse[argname], key=len)) + ':'
            arg_help += f'\n{help_indent}{arg_format_description:<50}{argtype}'
            if help_str:
                arg_help += '\n' + help_indent * 2 + help_str
            if self.arg_parsers[argname].has_default_value():
                default_value = self.arg_parsers[argname].default_value
                arg_help += '\n' + help_indent * 2 + f'Default: {default_value}'
        self.help_message += arg_help

    def _parse_argv(self, args: List[str]):
        result = {}

        while args:
            # TODO: Add support for positional args here somehow?
            argname = self.argstr_to_argname(args[0])
            assert argname is not None, f"Unknown arg {args[0]}"
            assert argname not in result, f"Arg {argname} passed a second time as {args[0]}"

            parser = self.arg_parsers[argname]
            num_parsed_args, argval = parser(args[0], args[1:], self)

            result[argname] = argval
            args = args[num_parsed_args + 1:]

        for argname, argparser in self.arg_parsers.items():
            if argname not in result:
                result[argname] = argparser.default_value if argparser.has_default_value() else UNINITIALIZED

        return result

    def _validate_args(self, result):
        for argname, argparser in self.arg_parsers.items():
            assert result[argname] != UNINITIALIZED, f"Didn't pass {argname}"

    def argstr_to_argname(self, argstr: str) -> Optional[str]:
        """Check which argname this arg string indicates, or None if it doesn't."""
        return self.arg_formats.get(argstr)
